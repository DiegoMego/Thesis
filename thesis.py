import random
import ast
import astor
import copy
import numpy as np
from operator import attrgetter
from itertools import repeat
from scoop import futures
from deap import base, creator, tools, algorithms
from settings import report_file, temp_folder
from regexManager import reManager
from mutants import MutantManager
from FileConverter import FileManager
from tracer import Executer
from CFGParser import Node, Tree
from tests import Suite, TestSuites

def initIndividual2D(individual, r, c):
    ind = np.random.randint(-10, 11, size=(r, c))
    return individual(ind)

def findItem(MyList, item):
    idx = 0
    for test in MyList:
        if (test == item).all():
            return idx
        idx += 1

def replacePop(pop, repl):
    aux = []
    for ind in repl:
        aux.append(copy.copy(pop.find(ind.id)))
    return aux

class CodeManager:
    def __init__(self):
        self.regex = reManager()

    def getSource(self):
        manager = FileManager()
        self.source = manager.execute()

    def replace(self, idx, repl, source):
        code = copy.copy(source)
        ident = self.regex.search(self.regex.ident, code[idx]).group(0)
        code[idx] = ident + repl
        return code

    def getExecutedLines(self, stdout):
        executedLines = []
        for line in stdout.splitlines():
            l = [int(item.strip("<string>()")) for item in self.regex.findall(self.regex.lines, line)]
            executedLines += l
        return executedLines

    def convertIfToEval(self, ifCode):
        pass

codemanager = CodeManager()
codemanager.getSource()
mutantmanager = MutantManager()
mutantmanager.generateMutants(report_file, codemanager.regex)
executer = Executer()
TestSuites = TestSuites()

dic = {}

#19 Mutants Killed
def report(mutant):
    if mutant.killed:
        return 1
    return 0

def getFitness(TestSuite):
    global dic, executer
    score = 0
    helper = []
    for test in TestSuite:
        executer.setInput(test)
        dic = executer.getDict(codemanager.source, codemanager.regex)
        trace = executer.track("".join(codemanager.source))
        executer.executedLines = codemanager.getExecutedLines(trace)
        cost = map(getCost, mutantmanager.mutants, repeat(codemanager.source))
        r = map(report, mutantmanager.mutants)
        helper.append(sum(cost))
        dic.clear()
    killed = [1 if mutant.killed else 0 for mutant in mutantmanager.mutants].count(1)
    score += killed / len(mutantmanager.mutants) * 100
    with open('out.txt', 'a') as file:
        file.write(str(score) + "\n")
    mutantmanager.clear()
    normal = sum(helper)
    score -= (normal / (normal + 1)) * 50
    return score,

def getCost(mutant, source):
    return getReachability(mutant, source)

def getReachability(mutant, source):
    global dic
    program = codemanager.replace(mutant.line - 1, mutant.mutation, source)
    trace = executer.track("".join(program))
    mutant.executedLines = codemanager.getExecutedLines(trace)
    if mutant.line in mutant.executedLines:
        mutant.reached = True
        return getNecessity(mutant, source, program)
    reach = 0
    mutant.reached = False
    node = Node()
    node.visit(ast.parse("".join(program)))
    commonPath = node.getCommonPath(mutant.executedLines, mutant.line)
    pathDifference = node.getPathDifference(mutant.line, commonPath)
    reach += len(pathDifference) - 1
    ifLine = node.getClosestIf(pathDifference)
    d = executer.executePath(ifLine, commonPath + pathDifference[1:], dic, node.g)
    isInside = node.isInside(mutant.line, ifLine)
    tree = Tree(d, isInside)
    distance = tree.visit(node.g.nodes[ifLine]['value'].test)
    reach += distance / (distance + 1)
    return reach

def getNecessity(mutant, source, program):
    global dic
    mutantNode = Node()
    mutantNode.visit(ast.parse("".join(program)))
    programNode = Node()
    programNode.visit(ast.parse("".join(source)))
    mutant_dic = executer.executePath(mutant.line, mutant.executedLines, dic, mutantNode.g)
    if mutantNode.isIf(mutant.line):
        isInside = eval(astor.to_source(programNode.getNode(mutant.line).test), None, mutant_dic)
        if isInside != eval(astor.to_source(mutantNode.getNode(mutant.line).test), None, mutant_dic):
            mutant.killed = True
            return 0
        mutantTree = Tree(mutant_dic, isInside)
        node = mutantNode.getNode(mutant.line).test
        distance = mutantTree.visit(node)
        return distance / (distance + 1)
    program_dic = executer.executePath(mutant.line, executer.executedLines, dic, programNode.g)
    if mutant_dic != program_dic:
        mutant.killed = True
        return 0
    return 0

creator.create("FitnessMin", base.Fitness, weights = (1.0,))
creator.create("Individual", np.ndarray, fitness=creator.FitnessMin)
toolbox = base.Toolbox()
# Atributos
toolbox.register("attr_bool", random.randint, 0, 10)
# Initializers
toolbox.register("map", futures.map)
toolbox.register("individual", initIndividual2D, creator.Individual, 10, 3)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)
toolbox.register("evaluate", getFitness)
toolbox.register("mate", tools.cxOnePoint)
toolbox.register("mutate", tools.mutFlipBit, indpb=0.05)
toolbox.register("select", tools.selTournament, tournsize=3)

def run():
    random.seed(64)
    idx = 0
    pop = toolbox.population(n=100)
    CXPB, MUTPB = 1.0, 0.2
    print("Start of evolution")
    # Evaluate the entire population
    fitnesses = list(toolbox.map(toolbox.evaluate, pop))
    for ind, fit in zip(pop, fitnesses):
        idx += 1
        ind.id = idx
        ind.fitness.values = fit

    print("  Evaluated %i individuals" % len(pop))

    # Extracting all the fitnesses of
    fits = [ind.fitness.values[0] for ind in pop]
    with open('out.txt', 'r+') as file:
        for line, ind in zip(file, pop):
            test = Suite(ind)
            test.id = ind.id
            test.score = float(line)
            TestSuites.addTestSuite(copy.copy(test))
        file.truncate(0)

    MS = [test.score for test in TestSuites.SuiteList]
    # Variable keeping track of the number of generations
    g = 0

    # Begin the evolution
    while max(MS) < 95 and g < 20:
        MS = None
        # A new generation
        g = g + 1
        print("-- Generation %i --" % g)

        # Select the next generation individuals
        offspring = toolbox.select(pop, len(pop))
        # Clone the selected individuals
        offspring = list(toolbox.map(toolbox.clone, offspring))
        TestSuites.SuiteList[:] = replacePop(TestSuites, offspring)

        # Apply crossover and mutation on the offspring
        for child1, child2 in zip(offspring[::2], offspring[1::2]):

            # cross two individuals with probability CXPB
            if random.random() < CXPB:
                toolbox.mate(child1, child2)

                # fitness values of the children
                # must be recalculated later
                del child1.fitness.values
                del child2.fitness.values

        for mutant in offspring:

            # mutate an individual with probability MUTPB
            if random.random() < MUTPB:
                toolbox.mutate(random.choice(mutant))
                del mutant.fitness.values

        # Evaluate the individuals with an invalid fitness
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = list(toolbox.map(toolbox.evaluate, invalid_ind))

        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit

        with open('out.txt', 'r+') as newfile:
            lines = newfile.readlines()
            for line, ind in zip(lines, invalid_ind):
                suite = TestSuites.find(ind.id)
                suite.tests[:] = ind
                suite.score = float(line)
            newfile.truncate(0)

        print("  Evaluated %i individuals" % len(invalid_ind))

        # The population is entirely replaced by the offspring
        pop[:] = offspring

        # Gather all the fitnesses in one list and print the stats
        fits = [ind.fitness.values[0] for ind in pop]
        MS = [test.score for test in TestSuites.SuiteList]

        length = len(pop)
        mean = sum(fits) / length
        MSmean = sum(MS) / length
        # sum2 = sum(x*x for x in fits)
        # MSsum2 = sum(z*z for z in MS)
        # std = abs(sum2 / length - mean**2)**0.5
        # MSstd = abs(MSsum2 / length - MSmean**2)**0.5
        std = np.std(fits)
        MSstd = np.std(MS)

        print("-- Mutant Score Statistics --")
        print("  Min %s" % min(MS))
        print("  Max %s" % max(MS))
        print("  Avg %s" % MSmean)
        print("  Std %s" % MSstd)
        print("-- Fitness Statistics --")
        print("  Min %s" % min(fits))
        print("  Max %s" % max(fits))
        print("  Avg %s" % mean)
        print("  Std %s" % std)

    print("-- End of (successful) evolution --")

    best_ind = tools.selBest(pop, 1)[0]
    best_killer = sorted(TestSuites.SuiteList, key=attrgetter('score'), reverse=True)[0]
    print("Best individual is %s, %s" % (best_ind, best_ind.fitness.values))
    print("Best killer is %s, %s" % (best_killer.tests, best_killer.score))

if __name__ == "__main__":
    run()
