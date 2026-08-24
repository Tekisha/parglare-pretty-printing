"""
Document algebra (Hughes/Wadler/Leijen style) - core types for
declaratively representing text structure prior to layout.

The Doc tree is an immutable algebraic structure:
    Text    - an atomic piece of text (contains no newline characters)
    Line    - a line break; soft=True means "space or newline"
              (depending on the flat/broken decision of the enclosing
              Group), while soft=False is a hard line break that is
              ALWAYS rendered as a newline, regardless of the
              flat/broken decision.
    Concat  - sequential composition of two Docs (left <> right)
    Nest    - introduces additional indentation for all Line breaks
              within the doc
    Group   - a decision point: the layout engine first tries flat
              rendering of the whole group on one line; if it doesn't
              fit the width (or contains a hard Line), it switches to
              broken mode
    Align   - aligns the continuation of the document to the current
              column (instead of a fixed nest indent)
    Empty   - the neutral element of concatenation (Concat(x, Empty()) == x)
"""

from dataclasses import dataclass
from typing import Union


@dataclass(frozen=True)
class Text:
    s: str


@dataclass(frozen=True)
class Line:
    soft: bool = True


@dataclass(frozen=True)
class Concat:
    left: "Doc"
    right: "Doc"


@dataclass(frozen=True)
class Nest:
    indent: int
    doc: "Doc"


@dataclass(frozen=True)
class Group:
    doc: "Doc"


@dataclass(frozen=True)
class Align:
    doc: "Doc"


@dataclass(frozen=True)
class Empty:
    pass


Doc = Union[Text, Line, Concat, Nest, Group, Align, Empty]

def text(s: str) -> Doc:
    """Atomic text. Should not contain '\\n' - use line() for breaks."""
    if not isinstance(s, str):
        raise TypeError(f"text() ocekuje str, dobijeno {type(s)!r}")
    return Text(s)


def line() -> Doc:
    """Hard line break - always rendered as a newline (+ indent)."""
    return Line(soft=False)


def softline() -> Doc:
    """Soft line break - a space in flat mode, a newline in broken mode."""
    return Line(soft=True)


def concat(left: Doc, right: Doc) -> Doc:
    """Sequential composition of two documents."""
    return Concat(left, right)


def nest(indent: int, doc: Doc) -> Doc:
    """Increases indentation of all Line breaks within doc by `indent` levels."""
    return Nest(indent, doc)


def group(doc: Doc) -> Doc:
    """Marks a flat/broken decision point for the layout engine."""
    return Group(doc)


def align(doc: Doc) -> Doc:
    """Aligns the continuation of the document to the current writing column."""
    return Align(doc)


def empty() -> Doc:
    """Neutral (empty) element - concat(x, empty()) == x."""
    return Empty()

def concat_all(*docs: Doc) -> Doc:
    """Concatenates an arbitrary number of documents, left-associatively."""
    result: Doc = empty()
    for d in docs:
        result = concat(result, d)
    return result