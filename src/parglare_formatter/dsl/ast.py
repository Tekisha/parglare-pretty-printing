"""
AST classes for DocExpr - the result of parsing the DSL defined in
dsl_grammar.py. This is the PARSE-TIME representation of formatting
rules (as opposed to Doc from document_model.py, which is the RUNTIME
representation of a concrete document after the DocExpr AST has been
compiled/evaluated against a concrete AST node in dsl_compiler.py,
Phase 6).

All classes are plain, behaviorless dataclasses - pure structure that
the compiler (Phase 6) traverses and translates into Doc calls from
document_model.py.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Union, Dict


@dataclass
class AttrPath:
    """Represents access to an AST node's attribute, e.g. 'node.left.value'."""
    parts: List[str]

    def __str__(self) -> str:
        return ".".join(self.parts)


@dataclass
class DocConcat:
    """DocExpr '++' DocTerm - left-associative concatenation."""
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
    """format(AttrPath) - recursive call into the formatter for a sub-node."""
    path: AttrPath


@dataclass
class DocList:
    """list(AttrPath, DocExpr) - maps DocExpr over every item reachable via
    AttrPath, with 'item' as the reference to the current element inside
    the DocExpr body (see DocItem)."""
    path: AttrPath
    body: "DocExpr"
    separator: Optional["DocExpr"] = None


@dataclass
class DocItem:
    """'item' - reference to the current element inside a list(...) body."""
    pass


@dataclass
class DocAttrRef:
    """A bare AttrPath as a DocTerm - a reference to a node's attribute
    whose value is inserted directly as text (e.g. for primitive fields)."""
    path: AttrPath


# DocExpr = "DocConcat | DocText | DocLine | DocSoftline | DocNest | " \
#           "DocGroup | DocAlign | DocFormat | DocList | DocItem | DocAttrRef"

DocExpr = Union[
    DocConcat, DocText, DocLine, DocSoftline, DocNest,
    DocGroup, DocAlign, DocFormat, DocList, DocItem, DocAttrRef
]

# ---------------------------------------------------------------------------
# RuleDecl / RuleFile - top of the DSL's AST
# ---------------------------------------------------------------------------

@dataclass
class RuleDecl:
    """rule name(params) = body ;"""
    name: str
    params: List[str] = field(default_factory=list)
    body: Optional[object] = None  # DocExpr


@dataclass
class RuleFile:
    """All RuleDecl entries parsed from a single .dsl file."""
    rules: List[RuleDecl] = field(default_factory=list)
    _by_name: Dict[str, RuleDecl] = field(
        default_factory=dict, init=False, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        by_name: Dict[str, RuleDecl] = {}
        for r in self.rules:
            if r.name in by_name:
                raise ValueError(
                    f"Duplicate rule name {r.name!r} in RuleFile "
                    f"(rule names must be unique)"
                )
            by_name[r.name] = r
        self._by_name = by_name

    def get_rule(self, name: str) -> RuleDecl:
        """Looks up a rule by name; raises a KeyError listing available
        rule names if not found, instead of a bare KeyError(name)."""
        try:
            return self._by_name[name]
        except KeyError:
            available = list(self._by_name)
            raise KeyError(
                f"No rule named {name!r}. Available rules: {available}"
            ) from None

    def __contains__(self, name: str) -> bool:
        return name in self._by_name

    def __len__(self) -> int:
        return len(self.rules)