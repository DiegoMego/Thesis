from FileConverter import FileManager

class Program:
    def __init__(self, file):
        self.states = {}
        self.executedLines = []
        self.getCode()

    def getCode(self):
        manager = FileManager()
        manager.execute()
        self.regex = manager.regex
        f = open(manager.original, "r")
        self.code = f.readlines()
        f.close()

    def inputValues(self, inputLine):
        f = "-j-".join(self.code)
        f = self.regex.sub(self.regex.main, inputLine, f)
        f = f.split("-j-")
        self.code = f

    def getProgram(self):
        source = "".join(self.code)
        return source

    def getLines(self, stdout):
        for line in stdout.splitlines():
            l = [item.strip("<string>()") for item in self.regex.findall(self.regex.lines, line)]
            self.executedLines += l

    def setStates(self, stdout):
        for line in stdout.splitlines():
            match = self.regex.search(self.regex.state, line)
            if match:
                line, state = match.group(0).split(" ", 1)
                self.states[line] = state

    def getState(self, n):
        if n in self.states.keys():
            return self.states[n]
        try:
            self.getState(self.executedLines[self.executedLines.index(n) + 1])
        except:
            pass

    def mutate(self, line, mutation):
        code = self.code
        code[line] = mutation
        return "".join(code)
