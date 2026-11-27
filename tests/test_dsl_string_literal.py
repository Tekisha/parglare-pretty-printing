from dataclasses import dataclass
from typing import Any, List, Optional

from parglare_formatter.dsl.ast import DocText
from parglare_formatter.dsl.parser import parse_dsl
from parglare_formatter.formatter import Formatter


@dataclass
class Num:
    value: int


@dataclass
class Box:
    items: Optional[List[Any]]


def test_bare_string_parses_as_text():
    body = parse_dsl('rule A = "x";').get_rule("A").body

    assert isinstance(body, DocText)
    assert body.value == "x"


def test_bare_string_is_equivalent_to_text():
    short = parse_dsl('rule A = "a" ++ "b";')
    long = parse_dsl('rule A = text("a") ++ text("b");')

    assert short == long


def test_text_and_bare_string_can_be_mixed():
    formatter = Formatter.from_dsl_source(
        'rule Num = "(" ++ node.value ++ text(")");'
    )

    assert formatter.format(Num(7)) == "(7)"


def test_escaped_quotes_are_unescaped():
    formatter = Formatter.from_dsl_source(
        r'rule Num = "say \"hi\"";'
    )

    assert formatter.format(Num(1)) == 'say "hi"'


def test_empty_string_produces_no_output():
    formatter = Formatter.from_dsl_source('rule Num = "";')

    assert formatter.format(Num(1)) == ""


def test_bare_strings_inside_optional_and_list():
    formatter = Formatter.from_dsl_source(
        'rule Box = optional(node.items, "[" ++ list(node.items, item, ", ") ++ "]");'
    )

    assert formatter.format(Box([1, 2])) == "[1, 2]"
    assert formatter.format(Box([])) == "[]"
    assert formatter.format(Box(None)) == ""