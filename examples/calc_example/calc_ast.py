from examples.ast_base import Node

class Number(Node):
    def __init__(self, value):
        self.value = int(value)

    def __repr__(self):
        return f"Number({self.value!r})"


class BinaryOp(Node):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op  # "+", "-", "*", "/"
        self.right = right

    def __repr__(self):
        return f"BinaryOp({self.left!r}, {self.op!r}, {self.right!r})"


class ExprLine(Node):
    def __init__(self, expr):
        self.expr = expr

    def __repr__(self):
        return f"ExprLine({self.expr!r})"


class Calc(Node):
    def __init__(self, expressions):
        self.expressions = expressions or []

    def __repr__(self):
        return f"Calc({self.expressions!r})"

class Paren(Node):
    def __init__(self, expr):
        self.expr = expr

    def __repr__(self):
        return f"Paren({self.expr!r})"