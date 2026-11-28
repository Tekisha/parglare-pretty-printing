from dataclasses import dataclass
from typing import Any

import pytest
from parglare.exceptions import SyntaxError

from parglare_formatter.dsl.parser import parse_dsl
from parglare_formatter.formatter import Formatter


@dataclass
class Num:
    value: int


@dataclass
class Name:
    value: str


@dataclass
class Pair:
    first: Any
    second: Any


@dataclass
class Container:
    child: Any


def test_names_expand_into_separate_rules():
    rules = parse_dsl('rule A, B = text("x");')

    assert len(rules) == 2
    assert "A" in rules and "B" in rules


def test_expanded_rules_share_the_same_body():
    rules = parse_dsl('rule A, B = text("x");')

    assert rules.get_rule("A").body is rules.get_rule("B").body


def test_single_name_still_works():
    rules = parse_dsl('rule A = text("x");')

    assert len(rules) == 1


def test_mixed_declarations_keep_order():
    rules = parse_dsl(
        """
        rule A, B, C = text("x");
        rule D = text("y");
        """
    )

    assert [r.name for r in rules.rules] == ["A", "B", "C", "D"]


def test_names_may_span_lines():
    rules = parse_dsl(
        """
        rule A,
             B =
            text("x");
        """
    )

    assert len(rules) == 2


@pytest.mark.parametrize(
    "source",
    [
        'rule A, A = text("x");',
        'rule A = text("x"); rule B, A = text("y");',
    ],
)
def test_duplicate_names_are_rejected(source):
    with pytest.raises(ValueError, match="Duplicate"):
        parse_dsl(source)


def test_trailing_comma_is_a_syntax_error():
    with pytest.raises(SyntaxError):
        parse_dsl('rule A, = text("x");')


def test_each_class_uses_the_shared_rule():
    formatter = Formatter.from_dsl_source(
        """
        rule Num, Name = node.value ++ text(";");
        rule Pair = format(node.first) ++ text(" ") ++ format(node.second);
        """
    )

    assert formatter.format(Pair(Num(1), Name("x"))) == "1; x;"


def test_contextual_rules_can_share_a_body():
    formatter = Formatter.from_dsl_source(
        """
        rule Container = format(node.child, statement);
        rule Num, Name = node.value;
        rule statement_Num, statement_Name = format(node) ++ text(";");
        """
    )

    assert formatter.format(Container(Num(7))) == "7;"
    assert formatter.format(Container(Name("x"))) == "x;"