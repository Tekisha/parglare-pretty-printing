"""
dsl_parser.py

Parglare parser za DSL definisan u dsl_grammar.py, sa semantic akcijama
koje grade dsl_ast.py strukture.

KLJUCNA PRAVILA (v. uvodno poglavlje projekta o parglare API-ju):
  - Potpis akcije je UVEK action(context, nodes), gde je `nodes` lista
    rezultata pod-izraza pozicionim redosledom iz RHS produkcije - ne
    postoji nodes[0][2] stil.
  - Kad pravilo ima vise produkcija (alternative odvojene '|'), actions[rule]
    je LISTA callable-ova, jedan po produkciji, istim redosledom kao u
    gramatici.
  - Za terminal, drugi parametar akcije nije lista nego sam matched string.
  - Grammar.from_string(...) proizvodi Grammar instancu; Parser(grammar,
    actions=actions) prima actions dict direktno kroz konstruktor.
  - Named matches (name=, params=, body=, left=, right=) u gramatici
    generisu ugradjenu 'obj' akciju AUTOMATSKI ako ne definisemo custom
    akciju za to pravilo - ali ovde PISEMO custom akcije svuda gde nam
    treba tipizirana dsl_ast klasa (npr. RuleDecl umesto generisane
    anonimne klase), sto je preporucen pristup kad treba sopstvena
    dataclass hijerarhija. Named matches i dalje mogu da se prime kao
    extra keyword argumenti akcije (npr. action(context, nodes, name=...,
    params=..., body=...)) - koristimo taj oblik gde skracuje kod.
"""
import re

from parglare import Grammar, Parser
from parglare.actions import collect, collect_sep, pass_single, optional

from .grammar import DSL_GRAMMAR
from .ast import (
    RuleFile, RuleDecl, AttrPath,
    DocConcat, DocText, DocLine, DocSoftline, DocNest, DocGroup, DocAlign,
    DocFormat, DocList, DocItem, DocAttrRef,
)


# ---------------------------------------------------------------------------
# RuleFile / RuleDecl / ParamList akcije
# ---------------------------------------------------------------------------

def _rule_file_action(context, nodes):
    # RuleFile: RuleDecl+ ;  -> nodes[0] je lista RuleDecl (jer je RuleDecl+
    # ugradjena repeticija, parglare je vec sabira u listu)
    return RuleFile(rules=list(nodes[0]))


def _rule_decl_action(context, nodes, name, params, body):
    # RuleDecl: "rule" name=Ident "(" params=ParamList? ")" "=" body=DocExpr ";" ;
    # named-match kwargs: name (str), params (list[str] ili None), body (DocExpr)
    return RuleDecl(name=name, params=params or [], body=body)


def _param_list_action(context, nodes):
    # ParamList: Ident ("," Ident)* ;
    # nodes[0] je prvi Ident (str), nodes[1] je lista dodatnih Ident-a
    # prikupljenih iz ("," Ident)* repeticije - parglare vraca listu tuple-a
    # (",", Ident) po iteraciji ili listu Ident-a zavisno od anonimnog
    # pravila; ovde eksplicitno filtriramo samo Ident vrednosti.
    first = nodes[0]
    rest_group = nodes[1] if len(nodes) > 1 else []
    rest = []
    for item in rest_group:
        # svaka iteracija (","  Ident) - Parglare vraca listu [",", Ident]
        if isinstance(item, list):
            rest.append(item[1])
        else:
            rest.append(item)
    return [first] + rest


# ---------------------------------------------------------------------------
# DocExpr / DocTerm akcije
# ---------------------------------------------------------------------------

def _doc_expr_concat_action(context, nodes, left, right):
    # DocExpr: left=DocExpr "++" right=DocTerm {left} ;
    return DocConcat(left=left, right=right)


def _doc_expr_single_action(context, nodes):
    # DocExpr: DocTerm ;
    return nodes[0]


def _doc_term_text_action(context, nodes):
    # DocTerm: "text" "(" StringLiteral ")" ;
    # nodes: ["text", "(", <string literal incl. quotes>, ")"]
    raw = nodes[2]
    inner = raw[1:-1]
    unescaped = re.sub(r'\\(.)', r'\1', inner)
    return DocText(value=unescaped)


def _doc_term_line_action(context, nodes):
    return DocLine()


def _doc_term_softline_action(context, nodes):
    return DocSoftline()


def _doc_term_nest_action(context, nodes):
    # DocTerm: "nest" "(" IntLiteral "," DocExpr ")" ;
    # nodes: ["nest", "(", <int str>, ",", <DocExpr>, ")"]
    indent = int(nodes[2])
    body = nodes[4]
    return DocNest(indent=indent, body=body)


def _doc_term_group_action(context, nodes):
    # DocTerm: "group" "(" DocExpr ")" ;
    return DocGroup(body=nodes[2])


def _doc_term_align_action(context, nodes):
    # DocTerm: "align" "(" DocExpr ")" ;
    return DocAlign(body=nodes[2])


def _doc_term_format_action(context, nodes):
    # DocTerm: "format" "(" AttrPath ")" ;
    return DocFormat(path=nodes[2])


def _doc_term_list_action(context, nodes):
    # DocTerm: "list" "(" AttrPath "," DocExpr ")" ;
    # nodes: ["list", "(", <AttrPath>, ",", <DocExpr>, ")"]
    return DocList(path=nodes[2], body=nodes[4])


def _doc_term_item_action(context, nodes):
    # DocTerm: "item" ;
    return DocItem()


def _doc_term_attrpath_action(context, nodes):
    # DocTerm: AttrPath ;
    return DocAttrRef(path=nodes[0])


def _attr_path_action(context, nodes):
    # AttrPath: Ident ("." Ident)* ;
    first = nodes[0]
    rest_group = nodes[1] if len(nodes) > 1 else []
    rest = []
    for item in rest_group:
        if isinstance(item, list):
            rest.append(item[1])
        else:
            rest.append(item)
    return AttrPath(parts=[first] + rest)


# ---------------------------------------------------------------------------
# actions dict - redosled u listama MORA pratiti redosled produkcija u
# DSL_GRAMMAR (dsl_grammar.py) za pravila sa vise alternativa.
# ---------------------------------------------------------------------------

actions = {
    "RuleFile": _rule_file_action,
    "RuleDecl": _rule_decl_action,
    "ParamList": _param_list_action,
    "DocExpr": [
        _doc_expr_concat_action,   # DocExpr "++" DocTerm {left}
        _doc_expr_single_action,   # DocTerm
    ],
    "DocTerm": [
        _doc_term_text_action,      # "text" "(" StringLiteral ")"
        _doc_term_line_action,      # "line" "(" ")"
        _doc_term_softline_action,  # "softline" "(" ")"
        _doc_term_nest_action,      # "nest" "(" IntLiteral "," DocExpr ")"
        _doc_term_group_action,     # "group" "(" DocExpr ")"
        _doc_term_align_action,     # "align" "(" DocExpr ")"
        _doc_term_format_action,    # "format" "(" AttrPath ")"
        _doc_term_list_action,      # "list" "(" AttrPath "," DocExpr ")"
        _doc_term_item_action,      # "item"
        _doc_term_attrpath_action,  # AttrPath
    ],
    "AttrPath": _attr_path_action,
}


_grammar_cache = None


def get_grammar():
    """Lazy-builds i kesira Grammar instancu (parsiranje gramatike je
    relativno skupo, ne treba ga raditi vise puta po procesu)."""
    global _grammar_cache
    if _grammar_cache is None:
        _grammar_cache = Grammar.from_string(DSL_GRAMMAR)
    return _grammar_cache


def build_parser() -> Parser:
    """Vraca novi Parser sa registrovanim semantic akcijama."""
    grammar = get_grammar()
    return Parser(grammar, actions=actions)


def parse_dsl(source: str) -> RuleFile:
    """Parsira DSL source string i vraca RuleFile AST."""
    parser = build_parser()
    result = parser.parse(source)
    return result