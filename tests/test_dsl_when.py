from dataclasses import dataclass
from typing import Any

import pytest

from parglare_formatter.dsl.ast import DocWhen
from parglare_formatter.dsl.parser import parse_dsl
from parglare_formatter.formatter import Formatter


@dataclass
class Op:
    op: Any


RULES = """
rule Op =
    when(node.op, "p++", text("post"), text("other"));
"""


def test_parser_builds_when_with_else():
    body = parse_dsl(RULES).get_rule("Op").body

    assert isinstance(body, DocWhen)
    assert body.value == "p++"
    assert body.path.parts == ["node", "op"]
    assert body.otherwise is not None


def test_parser_builds_when_without_else():
    body = parse_dsl(
        'rule Op = when(node.op, "x", text("y"));'
    ).get_rule("Op").body

    assert body.otherwise is None


@pytest.mark.parametrize(
    ("value", "expected"),
    [("p++", "post"), ("-", "other"), ("", "other")],
)
def test_matching_and_fallback(value, expected):
    assert Formatter.from_dsl_source(RULES).format(Op(value)) == expected


@pytest.mark.parametrize("value", [None, 1, False, ["p++"]])
def test_non_string_values_never_match(value):
    assert Formatter.from_dsl_source(RULES).format(Op(value)) == "other"


def test_missing_else_gives_empty_document():
    formatter = Formatter.from_dsl_source(
        'rule Op = text("[") ++ when(node.op, "x", text("y")) ++ text("]");'
    )

    assert formatter.format(Op("z")) == "[]"
    assert formatter.format(Op("x")) == "[y]"


def test_unselected_branch_is_not_evaluated():
    formatter = Formatter.from_dsl_source(
        'rule Op = when(node.op, "a", text("ok"), node.missing);'
    )

    assert formatter.format(Op("a")) == "ok"