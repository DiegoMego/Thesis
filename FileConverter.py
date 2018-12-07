import os
import subprocess
from settings import *
from regexManager import reManager

class FileManager:
    def __init__(self):
        self.regex = reManager()
        self.program = program_file + py_ext
        self.original = original + py_ext
        self.tempCreated = self.fileCreated = False
        self.text = []

    def createTemp(self):
        if not self.tempCreated:
            try:
                os.mkdir(temp_foldername)
            except FileExistsError:
                self.tempCreated = True

    def readLines(self):
        with open(self.program) as f:
            for line in f:
                if self.regex.match(self.regex.ifname, line):
                    return 0
                self.text.append(line)

    def createFormatedFile(self):
        self.readLines()
        with open(temp_folder + self.original, 'w') as f:
            f.write("".join(self.text))
            f.close()
        return self.text

    def generateReport(self):
        out = subprocess.check_output(command, shell=True, cwd=current_folder)
        out = out.decode('utf-8')
        with open(report_file, 'w') as f:
            f.write(out)
            f.close()

    def execute(self):
        self.createTemp()
        code = self.createFormatedFile()
        self.generateReport()
        return code
