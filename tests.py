class Suite:
    def __init__(self, tests):
        self.tests = tests

class TestSuites:
    def __init__(self):
        self.SuiteList = []
        self.new = []

    def find(self, id):
        for suite in self.SuiteList:
            if suite.id == id:
                return suite

    def addTestSuite(self, TestSuite):
        self.SuiteList.append(TestSuite)
