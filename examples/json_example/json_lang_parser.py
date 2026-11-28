from pathlib import Path

from parglare import Grammar, Parser
from parglare.actions import pass_single

from .json_lang_ast import (
    Json,
    JsonString,
    JsonNumber,
    JsonBool,
    JsonNull,
    JsonObject,
    JsonMember,
    JsonArray,
)


GRAMMAR_PATH = Path(__file__).parent / "json_lang_grammar.dsl"


def load_grammar_source() -> str:
    return GRAMMAR_PATH.read_text(encoding="utf-8")


actions = {
    "Json": lambda ctx, nodes, value: Json(value),
    "JsonValue": pass_single,
    "JsonString": lambda ctx, value: JsonString(value),
    "JsonNumber": lambda ctx, value: JsonNumber(value),
    "JsonBool": [
        lambda ctx, nodes: JsonBool(True),
        lambda ctx, nodes: JsonBool(False),
    ],
    "JsonNull": lambda ctx, nodes: JsonNull(),
    "JsonObject": lambda ctx, nodes, members=None: JsonObject(members),
    "JsonMember": lambda ctx, nodes, key, value: JsonMember(key, value),
    "JsonArray": lambda ctx, nodes, values=None: JsonArray(values),
}


def build_parser() -> Parser:
    grammar = Grammar.from_string(load_grammar_source())
    return Parser(grammar, actions=actions)


if __name__ == "__main__":
    grammar = Grammar.from_string(load_grammar_source())

    print("=== PRODUKCIJE ===")
    for p in grammar.productions:
        print(f"[{p.prod_id}] {p}")
        print("    symbol :", p.symbol, type(p.symbol).__name__)
        print("    rhs    :", [(s.name, type(s).__name__) for s in p.rhs])
        asg = getattr(p, "assignments", None)
        if asg:
            for name, a in asg.items():
                print("    assign :", name, "->", vars(a) if hasattr(a, "__dict__") else a)

    print("\n=== TERMINALI ===")
    for name, t in grammar.terminals.items():
        rec = getattr(t, "recognizer", None)
        print(name, "->", type(rec).__name__, getattr(rec, "value", None))

    print("\n=== ATRIBUTI JEDNE PRODUKCIJE ===")
    p0 = next(p for p in grammar.productions if p.symbol.name == "JsonObject")
    print(sorted(a for a in dir(p0) if not a.startswith("_")))

    parser = build_parser()
    print("\nAST:", parser.parse('{"x": 1, "y": [2, 3]}'))