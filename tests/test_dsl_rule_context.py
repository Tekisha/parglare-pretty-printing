from dataclasses import dataclass
from typing import Any

from parglare_formatter.dsl.parser import parse_dsl
from parglare_formatter.formatter import Formatter


@dataclass
class Value:
    pass


@dataclass
class Container:
    child: Any


@dataclass
class Item:
    index: int


def test_context_prefixes_the_rule_name():
    rule = parse_dsl('rule Decl in statement = "x";').rules[0]

    assert rule.name == "statement_Decl"
    assert rule.context == "statement"


def test_rule_without_context_is_unchanged():
    rule = parse_dsl('rule Decl = "x";').rules[0]

    assert rule.name == "Decl"
    assert rule.context is None


def test_several_names_share_the_context():
    rules = parse_dsl('rule A, B in bare = "x";').rules

    assert [r.name for r in rules] == ["bare_A", "bare_B"]
    assert all(r.context == "bare" for r in rules)


def test_equivalent_to_prefix_form():
    new = parse_dsl('rule Decl in statement = "x";')
    old = parse_dsl('rule statement_Decl = "x";')

    assert new == old


def test_underscored_context_name():
    rule = parse_dsl('rule Compound in before_else = "x";').rules[0]

    assert rule.name == "before_else_Compound"


def test_identifiers_starting_with_in_still_work():
    formatter = Formatter.from_dsl_source("rule Item = node.index;")

    assert formatter.format(Item(3)) == "3"


def test_context_rule_is_selected_by_format():
    formatter = Formatter.from_dsl_source(
        """
        rule Container = format(node.child, statement);
        rule Value = "plain";
        rule Value in statement = "stmt;";
        """
    )

    assert formatter.format(Value()) == "plain"
    assert formatter.format(Container(Value())) == "stmt;"


def test_check_is_clean_with_new_syntax():
    formatter = Formatter.from_dsl_source(
        """
        rule Container = format(node.child, statement);
        rule Sub_Type in statement = "x";
        """
    )

    assert formatter.check() == []


def test_check_reports_declared_but_unused_context():
    formatter = Formatter.from_dsl_source(
        """
        rule Container = format(node.child, statement);
        rule Value in statment = "x;";
        """
    )

    problems = formatter.check()

    assert any("'statement'" in p and "no rules named" in p for p in problems)
    assert any("'statment'" in p and "declared" in p for p in problems)