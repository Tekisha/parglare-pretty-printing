from pathlib import Path

from parglare import Grammar, Parser

from .calc_ast import Number, BinaryOp, ExprLine, Calc


def _load_grammar_source() -> str:
    grammar_path = Path(__file__).parent / "calc_grammar.dsl"
    return grammar_path.read_text(encoding="utf-8")


GRAMMAR_SOURCE = _load_grammar_source()

actions = {
    "Number": lambda ctx, value: Number(value),

    "Expr": [
        # Expr: left=Expr op=("+" | "-") right=Term {left}
        lambda ctx, nodes, left, op, right: BinaryOp(left, op, right),
        # Expr: Term
        lambda ctx, nodes: nodes[0],
    ],

    "Term": [
        # Term: left=Term op=("*" | "/") right=Factor {left}
        lambda ctx, nodes, left, op, right: BinaryOp(left, op, right),
        # Term: Factor
        lambda ctx, nodes: nodes[0],
    ],

    "Factor": [
        # Factor: "(" Expr ")"
        lambda ctx, nodes, expr: nodes[1],
        # Factor: number=Number
        lambda ctx, nodes, number: number,
    ],

    "ExprLine": lambda ctx, nodes, expr: ExprLine(expr),

    "Calc": lambda ctx, nodes, expressions: Calc(expressions),
}


_grammar_cache = None


def get_grammar() -> Grammar:
    global _grammar_cache
    if _grammar_cache is None:
        _grammar_cache = Grammar.from_string(GRAMMAR_SOURCE)
    return _grammar_cache


def build_parser() -> Parser:
    grammar = get_grammar()
    return Parser(grammar, actions=actions, ws=" \t")


def parse_calc(source: str) -> Calc:
    parser = build_parser()
    return parser.parse(source)