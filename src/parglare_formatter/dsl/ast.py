"""
dsl_ast.py

AST klase za DocExpr - rezultat parsiranja DSL-a definisanog u
dsl_grammar.py. Ovo JE PARSE-TIME predstava formatting pravila
(razlikuje se od Doc iz document_model.py, koji je RUNTIME predstava
konkretnog dokumenta nakon sto je DocExpr AST kompiliran/evaluiran nad
konkretnim AST cvorom u dsl_compiler.py, Faza 6).

Sve klase su plain dataclass-ovi bez ponasanja - cista struktura koju
kompajler (Faza 6) obilazi i prevodi u Doc pozive iz document_model.py.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class AttrPath:
    """Predstavlja pristup atributu AST cvora, npr. 'node.left.value'."""
    parts: List[str]

    def __str__(self) -> str:
        return ".".join(self.parts)


# ---------------------------------------------------------------------------
# DocExpr varijante - jedna klasa po alternativi DocTerm produkcije,
# plus DocConcat za '++' operator iz DocExpr produkcije.
# ---------------------------------------------------------------------------

@dataclass
class DocConcat:
    """DocExpr '++' DocTerm - levo asocijativna konkatenacija."""
    left: "DocExpr"
    right: "DocExpr"


@dataclass
class DocText:
    """text(StringLiteral)"""
    value: str


@dataclass
class DocLine:
    """line()"""
    pass


@dataclass
class DocSoftline:
    """softline()"""
    pass


@dataclass
class DocNest:
    """nest(IntLiteral, DocExpr)"""
    indent: int
    body: "DocExpr"


@dataclass
class DocGroup:
    """group(DocExpr)"""
    body: "DocExpr"


@dataclass
class DocAlign:
    """align(DocExpr)"""
    body: "DocExpr"


@dataclass
class DocFormat:
    """format(AttrPath) - rekurzivan poziv formatter-a nad podcvorom."""
    path: AttrPath


@dataclass
class DocList:
    """list(AttrPath, DocExpr) - mapira DocExpr preko svake stavke liste
    dostupne kroz AttrPath, uz 'item' kao referencu na trenutnu stavku
    unutar tela DocExpr (v. DocItem)."""
    path: AttrPath
    body: "DocExpr"


@dataclass
class DocItem:
    """'item' - referenca na trenutnu stavku unutar tela list(...)."""
    pass


@dataclass
class DocAttrRef:
    """Golo AttrPath kao DocTerm - referenca na atribut cvora cija se
    vrednost direktno umece kao tekst (npr. za primitivne tipove polja)."""
    path: AttrPath


DocExpr = "DocConcat | DocText | DocLine | DocSoftline | DocNest | " \
          "DocGroup | DocAlign | DocFormat | DocList | DocItem | DocAttrRef"


# ---------------------------------------------------------------------------
# RuleDecl / RuleFile - vrh AST-a DSL-a
# ---------------------------------------------------------------------------

@dataclass
class RuleDecl:
    """rule name(params) = body ;"""
    name: str
    params: List[str] = field(default_factory=list)
    body: Optional[object] = None  # DocExpr


@dataclass
class RuleFile:
    """Lista svih RuleDecl iz jednog .dsl fajla."""
    rules: List[RuleDecl] = field(default_factory=list)

    def as_dict(self) -> dict:
        """Vraca mapping rule_name -> RuleDecl, korisno za formatter.py."""
        return {r.name: r for r in self.rules}