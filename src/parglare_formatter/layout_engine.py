"""
Wadler/Leijen-style layout engine: converts a Doc tree (document_model.py)
into concrete text, choosing the flat or broken form for each Group based
on whether the flat form fits in the remaining space up to the given
margin.

The algorithm is iterative (an explicit stack instead of recursion),
since Doc trees can be deep and Python's recursion limit could be hit
on real-world programs.

NOTE: This module operates EXCLUSIVELY on the Doc types from
document_model.py (Text, Line, Concat, Nest, Group, Align, Empty).
"""

from enum import Enum
from typing import List, Tuple

from .document_model import Doc, Text, Line, Concat, Nest, Group, Align, Empty


class Mode(Enum):
    FLAT = "flat"
    BREAK = "break"


StackItem = Tuple[int, Mode, Doc]


def _fits(width_remaining: int, items: List[StackItem]) -> bool:
    """
    Checks whether the given row of items (work stack, top to bottom) can
    be rendered in FLAT mode within `width_remaining` columns, without
    any hard line break, up to the first newline (a Line in BREAK mode)
    or the end of the stack.
    """
    remaining = width_remaining
    stack = list(items)
    while stack:
        if remaining < 0:
            return False
        indent, mode, doc = stack.pop()
        if isinstance(doc, Text):
            remaining -= len(doc.s)
        elif isinstance(doc, Line):
            if mode == Mode.FLAT:
                if not doc.soft:
                    return False
                remaining -= 1
            else:
                return True
        elif isinstance(doc, Concat):
            stack.append((indent, mode, doc.right))
            stack.append((indent, mode, doc.left))
        elif isinstance(doc, Nest):
            stack.append((indent + doc.indent, mode, doc.doc))
        elif isinstance(doc, Group):
            stack.append((indent, Mode.FLAT, doc.doc))
        elif isinstance(doc, Align):
            stack.append((indent, mode, doc.doc))
        elif isinstance(doc, Empty):
            pass
        else:
            raise TypeError(f"Unknown Doc type in _fits: {type(doc)!r}")
    return remaining >= 0


def _contains_hard_line(doc: Doc) -> bool:
    """Checks whether doc contains a hard Line (soft=False) anywhere
    within itself, WITHOUT descending into nested Group nodes."""
    stack = [doc]
    while stack:
        d = stack.pop()
        if isinstance(d, Line):
            if not d.soft:
                return True
        elif isinstance(d, Concat):
            stack.append(d.left)
            stack.append(d.right)
        elif isinstance(d, Nest):
            stack.append(d.doc)
        elif isinstance(d, Align):
            stack.append(d.doc)
        elif isinstance(d, Group):
            continue
    return False


def render(doc: Doc, width: int = 80) -> str:
    """
    Renders a Doc tree into a string, using the Wadler/Leijen best-fit
    algorithm with the given maximum line width `width`.
    """
    out: List[str] = []
    column = 0

    stack: List[StackItem] = [(0, Mode.BREAK, doc)]

    while stack:
        indent, mode, d = stack.pop()

        if isinstance(d, Empty):
            continue

        elif isinstance(d, Text):
            out.append(d.s)
            column += len(d.s)

        elif isinstance(d, Line):
            if mode == Mode.FLAT and d.soft:
                out.append(" ")
                column += 1
            else:
                out.append("\n" + " " * indent)
                column = indent

        elif isinstance(d, Concat):
            stack.append((indent, mode, d.right))
            stack.append((indent, mode, d.left))

        elif isinstance(d, Nest):
            stack.append((indent + d.indent, mode, d.doc))

        elif isinstance(d, Align):
            stack.append((column, mode, d.doc))

        elif isinstance(d, Group):
            if _contains_hard_line(d.doc):
                stack.append((indent, Mode.BREAK, d.doc))
            else:
                remaining = width - column
                lookahead = [(indent, Mode.FLAT, d.doc)] + list(reversed(stack))
                if _fits(remaining, list(reversed(lookahead))):
                    stack.append((indent, Mode.FLAT, d.doc))
                else:
                    stack.append((indent, Mode.BREAK, d.doc))

        else:
            raise TypeError(f"Unknown Doc type in render: {type(d)!r}")

    return "".join(out)


def pretty(doc: Doc, width: int = 80) -> str:
    """Alias for render() - a more commonly used name in the pretty-printing literature."""
    return render(doc, width=width)