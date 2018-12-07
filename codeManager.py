import random
import ast
import astor
import copy
from itertools import repeat
from scoop import futures, shared
from deap import base, creator, tools, algorithms
from settings import report_file, temp_folder
from regexManager import reManager
from mutants import MutantManager
from FileConverter import FileManager
from tracer import Executer
from CFGParser import Node, Tree

class GA:
    def __init__(self):
        self.codemanager = CodeManager()
        self.codemanager.getSource()
        self.mutantmanager = MutantManager()
        self.mutantmanager.generateMutants(report_file, self.codemanager.regex)
        self.executer = Executer()

    def getFitness(self, individual):
        score = 0
        self.executer.setInput(individual)
        self.d = self.executer.getDict(self.codemanager.source, self.codemanager.regex)
        reaches = map(self.getCost, self.mutantmanager.mutants, repeat(self.codemanager.source))
        return sum(reaches),

    def getCost(self, mutant, source):
        program = self.codemanager.replace(mutant.line - 1, mutant.mutation, source)
        trace = self.executer.track("".join(program))
        mutant.executedLines = self.codemanager.getExecutedLines(trace)
        if mutant.line in mutant.executedLines:
            mutant.reached = True
            return 0
        reach = 0
        mutant.reached = False
        node = Node()
        node.visit(ast.parse("".join(program)))
        commonPath = node.getCommonPath(mutant.executedLines, mutant.line)
        pathDifference = node.getPathDifference(mutant.line, commonPath)
        reach += len(pathDifference) - 1
        ifLine = node.getClosestIf(pathDifference)
        d = self.executer.executePath(ifLine, commonPath + pathDifference[1:], self.d, node.g)
        tree = Tree(d)
        reach += tree.visit(node.g.nodes[ifLine]['value'].test)
        return reach

    def prepare(self):
        creator.create("FitnessMin", base.Fitness, weights = (-1.0,))
        creator.create("Individual", list, fitness=creator.FitnessMin)
        self.toolbox = base.Toolbox()
        # Atributos
        self.toolbox.register("attr_bool", random.randint, 0, 10)
        # Initializers
        self.toolbox.register("map", futures.map)
        self.toolbox.register("individual", tools.initRepeat, creator.Individual, self.toolbox.attr_bool, 3)
        self.toolbox.register("population", tools.initRepeat, list, self.toolbox.individual)
        self.toolbox.register("evaluate", self.getFitness)
        self.toolbox.register("mate", tools.cxUniform, indpb=0.5)
        self.toolbox.register("mutate", tools.mutFlipBit, indpb=0.05)
        self.toolbox.register("select", tools.selTournament, tournsize=2)

    def run(self):
        creator.create("FitnessMin", base.Fitness, weights = (-1.0,))
        creator.create("Individual", list, fitness=creator.FitnessMin)
        self.toolbox = base.Toolbox()
        # Atributos
        self.toolbox.register("attr_bool", random.randint, 0, 10)
        # Initializers
        self.toolbox.register("map", futures.map)
        self.toolbox.register("individual", tools.initRepeat, creator.Individual, self.toolbox.attr_bool, 3)
        self.toolbox.register("population", tools.initRepeat, list, self.toolbox.individual)
        self.toolbox.register("evaluate", self.getFitness)
        self.toolbox.register("mate", tools.cxUniform, indpb=0.5)
        self.toolbox.register("mutate", tools.mutFlipBit, indpb=0.05)
        self.toolbox.register("select", tools.selTournament, tournsize=2)
        random.seed(64)
        pop = self.toolbox.population(n=10)
        CXPB, MUTPB = 0.5, 0.2
        print("Start of evolution")
        print(self.toolbox.individual)
        # Evaluate the entire population
        fitnesses = self.toolbox.map(self.toolbox.evaluate, pop)
        for ind, fit in zip(pop, fitnesses):
            ind.fitness.values = fit

        print("  Evaluated %i individuals" % len(pop))

        # Extracting all the fitnesses of
        fits = [ind.fitness.values[0] for ind in pop]

        # Variable keeping track of the number of generations
        g = 0

        # Begin the evolution
        while max(fits) > 100 and g < 10:
            # A new generation
            g = g + 1
            print("-- Generation %i --" % g)

            # Select the next generation individuals
            offspring = self.toolbox.select(pop, len(pop))
            # Clone the selected individuals
            offspring = list(self.toolbox.map(self.toolbox.clone, offspring))

            # Apply crossover and mutation on the offspring
            for child1, child2 in zip(offspring[::2], offspring[1::2]):

                # cross two individuals with probability CXPB
                if random.random() < CXPB:
                    self.toolbox.mate(child1, child2)

                    # fitness values of the children
                    # must be recalculated later
                    del child1.fitness.values
                    del child2.fitness.values

            for mutant in offspring:

                # mutate an individual with probability MUTPB
                if random.random() < MUTPB:
                    self.toolbox.mutate(mutant)
                    del mutant.fitness.values

            # Evaluate the individuals with an invalid fitness
            invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
            fitnesses = self.toolbox.map(self.toolbox.evaluate, invalid_ind)
            for ind, fit in zip(invalid_ind, fitnesses):
                ind.fitness.values = fit

            print("  Evaluated %i individuals" % len(invalid_ind))

            # The population is entirely replaced by the offspring
            pop[:] = offspring

            # Gather all the fitnesses in one list and print the stats
            fits = [ind.fitness.values[0] for ind in pop]

            length = len(pop)
            mean = sum(fits) / length
            sum2 = sum(x*x for x in fits)
            std = abs(sum2 / length - mean**2)**0.5

            print("  Min %s" % min(fits))
            print("  Max %s" % max(fits))
            print("  Avg %s" % mean)
            print("  Std %s" % std)

        print("-- End of (successful) evolution --")

        best_ind = tools.selBest(pop, 1)[0]
        print("Best individual is %s, %s" % (best_ind, best_ind.fitness.values))

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

if __name__ == "__main__":
    ga = GA()
    # ga.prepare()
    ga.run()
