"""
formatter.py

Glavni ulaz sistema: AST -> Doc -> text.

Formatter povezuje sve prethodne faze:
  - Faza 2 (dsl_parser.py)   - parsira .dsl fajl u RuleFile
  - Faza 6 (dsl_compiler.py) - kompilira JEDNO pravilo (DocExpr) u Doc,
                                nad konkretnim AST cvorom
  - Faza 3 (layout_engine.py) - renderuje Doc u konacan string

Kljucna odgovornost formatter.py koja NIJE bila u prethodnim fazama je
BIRANJE PRAVILA po imenu Python klase konkretnog AST cvora - to je
`format_node` callback koji dsl_compiler.py poziva rekurzivno za
`format(...)`, `list(...)` i goli `item`.

Konvencija: DSL pravilo `rule BinaryOp(node) = ...` se primenjuje na
SVAKI AST cvor cija je Python klasa `BinaryOp` (type(node).__name__).
Ime prvog parametra pravila (obicno "node") postaje kljuc u bindings
mapi na koji se cvor vezuje.
"""

from typing import Any, Dict, Optional

from src.parglare_formatter.dsl.ast import RuleFile
from src.parglare_formatter.dsl.compiler import compile_doc_expr, CompileError
from src.parglare_formatter.dsl.parser import parse_dsl
from src.parglare_formatter.document_model import Doc
from src.parglare_formatter.layout_engine import render


class FormatterError(Exception):
    """Greska pri formatiranju - nedostaje pravilo za dati tip cvora,
    ili je pravilo definisano sa pogresnim brojem parametara."""
    pass


class Formatter:
    """
    Formatter ucitava skup DSL pravila (RuleFile) i primenjuje ih nad
    konkretnim AST stablom, birajuci pravilo po imenu Python klase cvora.

    Primer koriscenja:

        rule_file = parse_dsl(open("formatting_rules.dsl").read())
        formatter = Formatter(rule_file)
        text_output = formatter.format(my_ast_root, width=80)
    """

    def __init__(self, rule_file: RuleFile):
        self.rule_file = rule_file

    @classmethod
    def from_dsl_source(cls, source: str) -> "Formatter":
        """Pogodan konstruktor: parsira DSL izvor i odmah pravi Formatter."""
        return cls(parse_dsl(source))

    @classmethod
    def from_dsl_file(cls, path: str) -> "Formatter":
        """Ucitava .dsl fajl sa diska i pravi Formatter."""
        with open(path, "r", encoding="utf-8") as f:
            source = f.read()
        return cls.from_dsl_source(source)

    def _rule_name_for(self, node: Any) -> str:
        """Ime DSL pravila koje odgovara datom AST cvoru - po konvenciji,
        ime Python klase cvora (type(node).__name__)."""
        return type(node).__name__

    def format_node(self, node: Any) -> Doc:
        """
        Kompilira JEDAN AST cvor u Doc, birajuci odgovarajuce DSL pravilo
        po imenu njegove Python klase. Ovo je `format_node` callback koji
        dsl_compiler.compile_doc_expr poziva rekurzivno za format(...),
        list(...) i goli item.
        """
        rule_name = self._rule_name_for(node)
        if rule_name not in self.rule_file:
            raise FormatterError(
                f"Nema DSL pravila za tip cvora {rule_name!r}. "
                f"Definisi 'rule {rule_name}(node) = ...;' u .dsl fajlu."
            )
        rule = self.rule_file.get_rule(rule_name)

        if len(rule.params) != 1:
            raise FormatterError(
                f"Pravilo {rule_name!r} mora imati tacno JEDAN parametar "
                f"(konvencija: 'node'), a ima {len(rule.params)}: {rule.params}"
            )
        param_name = rule.params[0]
        bindings: Dict[str, Any] = {param_name: node}

        try:
            return compile_doc_expr(rule.body, bindings, self.format_node)
        except CompileError as e:
            raise FormatterError(
                f"Greska pri kompilaciji pravila {rule_name!r} nad cvorom "
                f"{node!r}: {e}"
            ) from e

    def format(self, node: Any, width: int = 80) -> str:
        """
        Formatira dati AST cvor (i sve pod-cvorove, rekurzivno) u konacan
        string, koristeci layout_engine.render() sa datom sirinom linije.
        """
        doc = self.format_node(node)
        return render(doc, width=width)


def format_ast(node: Any, dsl_source: str, width: int = 80) -> str:
    """Funkcionalni prijatelj-fasada: parsira DSL izvor i odmah formatira
    dati cvor, u jednom pozivu - korisno za jednokratnu upotrebu / skripte."""
    formatter = Formatter.from_dsl_source(dsl_source)
    return formatter.format(node, width=width)