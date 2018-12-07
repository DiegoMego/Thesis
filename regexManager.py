import re
import inspect

class reManager:
    def __init__(self):
        self.state = r'\d* \{.*\}$'
        self.lines = r'<string>\(\d*\)'
        self.ident = r'^\s*'
        self.main = r'main\((.*\d)*\)'
        self.exceptions = r'(\t*)(return|yield|else|#|^\n|main\(.*\)$)'
        self.ifname = r'if __name__'
        self.defmain = r'def main'
        self.colon = r'^.*:$'
        self.mutant = r'~'
        self.operator = r'- \['
        self.status = r'(\[.*)(survived|killed)'
        self.mutantExceptions = r'(~.*if.*__name__)|(~\d*:[ ]*main)|~.*print'
        self.getFunctions()

    def getFunctions(self):
        functions = inspect.getmembers(re, inspect.isfunction)
        for f, t in functions:
            setattr(self, f, t)
