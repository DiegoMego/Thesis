import sys
import io
import contextlib
import ast
import astor
from trace import Trace
from copy import copy

class Executer:
    def __init__(self):
        self.trace = Trace()
        self.template = "main({}, {}, {})"
        self.print = "\tprint(locals())\n"
        self.executedLines = []

    def setInput(self, test):
        self.main = self.template.format(*test)

    @contextlib.contextmanager
    def stdoutIO(self, stdout=None):
        old = sys.stdout
        if stdout is None:
            stdout = io.StringIO()
        sys.stdout = stdout
        yield stdout
        sys.stdout = old

    def track(self, program):
        with self.stdoutIO() as s:
            exec(program)
            self.trace.runctx(self.main, None, locals())
        return s.getvalue()

    def getDict(self, program, regex):
        code = copy(program)
        for idx, line in enumerate(code):
            if regex.match(regex.defmain, line):
                code.insert(idx + 1, self.print)
        with self.stdoutIO() as s:
            exec("".join(code))
            exec(self.main)
        d = eval(s.getvalue())
        return d

    def executePath(self, end, l, d, g):
        code = ""
        for line in l:
            if line == end:
                if not isinstance(g.nodes[line]['value'], (ast.If, ast.Return)):
                    code += astor.to_source(g.nodes[line]['value'])
                break
            elif not isinstance(g.nodes[line]['value'], (ast.If, ast.Return)):
                code += astor.to_source(g.nodes[line]['value'])
        exec(code, None, d)
        state = copy(locals()['d'])
        return state
