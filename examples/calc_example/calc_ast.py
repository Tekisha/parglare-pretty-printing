class Number:
    def __init__(self, value):
        self.value = int(value)

    def __repr__(self):
        return f"Number({self.value!r})"


class BinaryOp:
    def __init__(self, left, op, right):
        self.left = left
        self.op = op  # "+", "-", "*", "/"
        self.right = right

    def __repr__(self):
        return f"BinaryOp({self.left!r}, {self.op!r}, {self.right!r})"


class ExprLine:
    def __init__(self, expr):
        self.expr = expr

    def __repr__(self):
        return f"ExprLine({self.expr!r})"


class Calc:
    def __init__(self, expressions):
        self.expressions = expressions or []

    def __repr__(self):
        return f"Calc({self.expressions!r})"

class Paren:
    def __init__(self, expr):
        self.expr = expr

    def __repr__(self):
        return f"ExprLine({self.expr!r})"