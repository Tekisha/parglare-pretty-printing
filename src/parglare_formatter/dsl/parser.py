"""
Parglare parser for the DSL defined in dsl_grammar.py, with semantic
actions that build dsl_ast.py structures.

KEY RULES (see the project's introductory chapter on the parglare API):
  - An action's signature is ALWAYS action(context, nodes), where `nodes`
    is a list of sub-expression results in positional order from the
    RHS production - there's no nodes[0][2] style.
  - When a rule has multiple productions (alternatives separated by '|'),
    actions[rule] is a LIST of callables, one per production, in the
    same order as in the grammar.
  - For a terminal, the action's second parameter is not a list but the
    matched string itself.
  - Grammar.from_string(...) produces a Grammar instance; Parser(grammar,
    actions=actions) receives the actions dict directly via the
    constructor.
  - Named matches (name=, params=, body=, left=, right=) in the grammar
    AUTOMATICALLY generate the built-in 'obj' action if we don't define
    a custom action for that rule - but here we WRITE custom actions
    everywhere we need a typed dsl_ast class (e.g. RuleDecl instead of
    a generated anonymous class), which is the recommended approach
    when a custom dataclass hierarchy is needed. Named matches can still
    be received as extra keyword arguments to the action (e.g.
    action(context, nodes, name=..., params=..., body=...)) - we use
    that form wherever it shortens the code.
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

def _rule_file_action(context, nodes):
    # RuleFile: RuleDecl+ ;  -> nodes[0] is a list of RuleDecl (since
    # RuleDecl+ is a built-in repetition, parglare already collects it
    # into a list)
    return RuleFile(rules=list(nodes[0]))


def _rule_decl_action(context, nodes, name, params, body):
    # RuleDecl: "rule" name=Ident "(" params=ParamList? ")" "=" body=DocExpr ";" ;
    # named-match kwargs: name (str), params (list[str] or None), body (DocExpr)
    return RuleDecl(name=name, params=params or [], body=body)


def _param_list_action(context, nodes):
    # ParamList: Ident ("," Ident)* ;
    # nodes[0] is the first Ident (str), nodes[1] is a list of the
    # additional Idents collected from the ("," Ident)* repetition -
    # parglare returns a list of (",", Ident) pairs per iteration, or a
    # list of Ident values depending on the anonymous rule; here we
    # explicitly filter out only the Ident values.
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
# DocExpr / DocTerm actions
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


def _doc_term_list_action(context, nodes, path, body, opt_sep):
    separator = opt_sep.separator if opt_sep else None
    return DocList(path=path, body=body, separator=separator)

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
# actions dict - the order within the lists MUST follow the order of
# productions in DSL_GRAMMAR (dsl_grammar.py) for rules with multiple
# alternatives.
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
    """Lazily builds and caches the Grammar instance (parsing the grammar
    is relatively expensive and shouldn't be done more than once per
    process)."""
    global _grammar_cache
    if _grammar_cache is None:
        _grammar_cache = Grammar.from_string(DSL_GRAMMAR)
    return _grammar_cache


def build_parser() -> Parser:
    """Returns a new Parser with the semantic actions registered."""
    grammar = get_grammar()
    return Parser(grammar, actions=actions)


def parse_dsl(source: str) -> RuleFile:
    """Parses a DSL source string and returns the RuleFile AST."""
    parser = build_parser()
    result = parser.parse(source)
    return result