class Node:
    """Base class: structural (value) equality for AST nodes."""

    def __eq__(self, other):
        if type(self) is not type(other):
            return False
        return vars(self) == vars(other)

    __hash__ = None