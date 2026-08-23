"""
document_model.py

Document algebra (Hughes/Wadler/Leijen style) - osnovni tipovi za
deklarativno predstavljanje strukture teksta pre layout-a.

Doc stablo je immutable algebarska struktura:
    Text    - atomski komad teksta (ne sadrzi newline karaktere)
    Line    - prelom linije; soft=True znaci "razmak ili newline"
              (zavisi od flat/broken odluke okruzujuce Group), a
              soft=False je hard line break koji se UVEK renderuje
              kao newline, bez obzira na flat/broken odluku.
    Concat  - sekvencijalna kompozicija dva Doc-a (left <> right)
    Nest    - uvodi dodatnu indentaciju za sve Line prelome unutar doc-a
    Group   - tacka odluke: layout engine prvo probava flat rendering
              cele grupe u jednoj liniji; ako ne stane u sirinu (ili
              sadrzi hard Line), prelazi u broken rezim
    Align   - poravnava nastavak dokumenta na trenutnu kolonu (umesto
              na fiksni nest indent)
    Empty   - neutralni element konkatenacije (Concat(x, Empty()) == x)
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


# ---------------------------------------------------------------------------
# Kombinatori
# ---------------------------------------------------------------------------

def text(s: str) -> Doc:
    """Atomski tekst. Ne treba da sadrzi '\\n' - za prelome koristi line()."""
    if not isinstance(s, str):
        raise TypeError(f"text() ocekuje str, dobijeno {type(s)!r}")
    return Text(s)


def line() -> Doc:
    """Hard line break - uvek se renderuje kao newline (+ indent)."""
    return Line(soft=False)


def softline() -> Doc:
    """Soft line break - u flat rezimu je razmak, u broken rezimu newline."""
    return Line(soft=True)


def concat(left: Doc, right: Doc) -> Doc:
    """Sekvencijalna kompozicija dva dokumenta."""
    return Concat(left, right)


def nest(indent: int, doc: Doc) -> Doc:
    """Uvecava indentaciju svih Line preloma unutar doc za `indent` nivoa."""
    return Nest(indent, doc)


def group(doc: Doc) -> Doc:
    """Oznacava tacku flat/broken odluke za layout engine."""
    return Group(doc)


def align(doc: Doc) -> Doc:
    """Poravnava nastavak dokumenta na trenutnu kolonu pisanja."""
    return Align(doc)


def empty() -> Doc:
    """Neutralni (praznog) element - concat(x, empty()) == x."""
    return Empty()


# ---------------------------------------------------------------------------
# Pomocni kombinatori (varargs concat, cesto potrebni u praksi)
# ---------------------------------------------------------------------------

def concat_all(*docs: Doc) -> Doc:
    """Konkatenira proizvoljan broj dokumenata levo-asocijativno."""
    result: Doc = empty()
    for d in docs:
        result = concat(result, d)
    return result