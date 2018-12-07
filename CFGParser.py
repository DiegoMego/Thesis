import networkx as nx
import ast
import astor
import operator

class Node(ast.NodeVisitor):
    def __init__(self):
        self.g = nx.DiGraph()

    def visit(self, node):
        """Visit a node."""
        method = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        """Called if no explicit visitor function exists for a node."""
        pass

    def link_list(self, node, bodyList, idx = 0, extra = None):
        if idx < len(bodyList):
            self.g.add_node(bodyList[idx].lineno, value=bodyList[idx], extra=extra)
            self.g.add_edge(node.lineno, bodyList[idx].lineno)
            self.link_list(bodyList[idx], bodyList, idx + 1)
            self.visit(bodyList[idx])

    def visit_Module(self, node):
        node.lineno = 0
        self.g.add_node(node.lineno, value=node)
        self.link_list(node, node.body)

    def visit_FunctionDef(self, node):
        self.g.nodes[node.lineno]['extra'] = next(self.g.neighbors(node.lineno), None)
        self.link_list(node, node.body)

    def visit_If(self, node):
        extra = next(self.g.neighbors(node.lineno), None)
        if extra:
            self.g.nodes[node.lineno]['extra'] = extra
            self.g.remove_edge(node.lineno, extra)
        self.link_list(node, node.body)
        self.appendLastIf(next(self.g.neighbors(node.lineno)), self.g.nodes[node.lineno]['extra'])
        if node.orelse:
            self.link_list(node, node.orelse, extra=self.g.nodes[node.lineno]['extra'])
            if not isinstance(node.orelse[0], ast.If):
                self.appendLastIf(list(self.g.neighbors(node.lineno))[1], self.g.nodes[node.lineno]['extra'])
        else:
            self.g.add_edge(node.lineno, self.g.nodes[node.lineno]['extra'])

    def appendLastIf(self, node, extra):
        if next(self.g.neighbors(node), None):
            self.appendLastIf(next(self.g.neighbors(node)), extra)
        elif not isinstance(self.g.nodes[node]['value'], ast.Return):
            self.g.add_edge(node, extra)

    def getPathDifference(self, mutantline, commonPath):
        l = eval((str(self.g.nodes)))
        mutantlines = nx.shortest_path(self.g, l[0], mutantline)
        idx = mutantlines.index(commonPath[-1])
        return mutantlines[idx:]

    def getClosestPath(self, start, end):
        return nx.shortest_path(self.g, start, end)

    def getClosestIf(self, l):
        for idx in reversed(l):
            if isinstance(self.g.nodes[idx]['value'], ast.If):
                return idx

    def getCommonPath(self, executedLines, mutantline):
        l = eval((str(self.g.nodes)))
        mutantlines = nx.shortest_path(self.g, l[0], mutantline)
        idx = 0
        for line in mutantlines:
            if line == executedLines[0]:
                mutantlines = mutantlines[idx:]
                break
            idx += 1
        idx = 0
        commonPath = []
        for mutant, test in zip(mutantlines, executedLines):
            if mutant != test:
                break
            commonPath.append(test)
        return commonPath

    def isIf(self, nodeLine):
        if isinstance(self.g.nodes[nodeLine]['value'], ast.If):
            return True
        return False

    def isInside(self, nodeLine, ifLine):
        node = self.g.nodes[nodeLine]['value']
        ifNode = self.g.nodes[ifLine]['value']
        if node in ifNode.body:
            return True
        return False

    def getNode(self, nodeLine):
        return self.g.nodes[nodeLine]['value']

class Tree(ast.NodeVisitor):
    def __init__(self, d, inside=True):
        self.d = d
        self.small = 1
        self.max = 100
        self.inside = inside

    def visit_UnaryOp(self, node):
        node.operand.inverse = operator.not_
        return self.visit(node.operand)

    def visit(self, node):
        """Visit a node."""
        method = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        """Called if no explicit visitor function exists for a node."""
        pass

    def visit_Compare(self, node):
        if not hasattr(node, 'inverse'):
            node.inverse = operator.truth
        if node.inverse(eval(astor.to_source(node), None, self.d)) == self.inside:
            return 0
        left = eval(astor.to_source(node.left), None, self.d)
        ops = astor.get_op_symbol(node.ops[0])
        right = eval(astor.to_source(node.comparators[0]), None, self.d)
        if node.inverse(self.inside):
            if len(ops) > 1:
                return min(abs(left - right), self.max)
            return min(abs(left - right) + self.small, self.max)
        if ops == "==":
            return self.small
        elif len(ops) > 1:
            return min(abs(left - right) + self.small, self.max)
        return min(abs(left - right), self.max)

    def visit_BoolOp(self, node):
        l = []
        op = astor.get_op_symbol(node.op)
        for value in node.values:
            if hasattr(node, 'inverse'):
                value.inverse = node.inverse
            l.append(self.visit(value))
        if self.inside:
            if op == "and":
                return sum(l)
            elif op == "or":
                return min(l)
        if op == "and":
            return min(l)
        elif op == "or":
            return sum(l)

# file = open('temp/original.py', 'r')
# source = "".join(file.readlines())
# file.close()
# code = ast.parse(source)
# t = Node()
# t.visit(code)
# print(t.getCommonAncestor(11, 15))
