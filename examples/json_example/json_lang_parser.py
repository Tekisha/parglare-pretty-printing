from pathlib import Path

from parglare import Grammar, Parser
from parglare.actions import pass_single

from json_lang_ast import (
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
    parser = build_parser()
    ast = parser.parse('{"x": 1, "y": [2, 3]}')
    print(f"AST: {ast}")