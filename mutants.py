import subprocess
from regexManager import reManager
from settings import report_file, command, current_folder

class Mutant:
    def __init__(self, mutation, operator, state):
        self.line = int(mutation[1:4].strip(':'))
        self.mutation = mutation[5:].strip() + "\n"
        self.operator = operator[13:16]
        self.state = state
        self.executedLines = []
        self.states = {}
        self.killed = False

class MutantManager:
    def __init__(self):
        self.mutants = []
        self.idx = self.idx_operator = self.idx_state = 0
        self.activator = False
        self.mutation = self.operator = self.state = ""
        self.check = False

    def getMutation(self, line, regex):
        if regex.match(regex.mutant, line):
            self.mutation = line
            self.idx += 1

    def getType(self, line, regex):
        if regex.match(regex.operator, line.strip()):
            self.operator = line
            self.idx_operator += 1

    def getState(self, line, regex):
        if regex.match(regex.status, line):
            self.state = line
            self.idx_state += 1
            self.check = True

    def addMutant(self):
        if self.idx == self.idx_operator and self.check:
            self.check = False
            if not self.activator:
                self.mutants.append(Mutant(self.mutation, self.operator, self.state))
            else:
                self.activator = False

    def generateMutants(self, filename, regex):
        with open(filename, 'r') as f:
            for line in f:
                if regex.match(regex.mutantExceptions, line):
                    self.activator = True
                self.getType(line, regex)
                self.getMutation(line, regex)
                self.getState(line, regex)
                self.addMutant()

    def clear(self):
        for mutant in self.mutants:
            mutant.killed = False
