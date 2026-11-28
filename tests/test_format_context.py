from dataclasses import dataclass

import pytest

from parglare_formatter.dsl.ast import DocFormat
from parglare_formatter.dsl.parser import parse_dsl
from parglare_formatter.formatter import Formatter, FormatterError


@dataclass
class Value:
    value: int


@dataclass
class Container:
    child: Value


def test_parser_builds_contextual_format():
    rules = parse_dsl(
        "rule Container = format(node.child, statement);"
    )

    expr = rules.get_rule("Container").body

    assert isinstance(expr, DocFormat)
    assert expr.path.parts == ["node", "child"]
    assert expr.context == "statement"


def test_context_selects_specialized_rule():
    formatter = Formatter.from_dsl_source(
        """
        rule Container = format(node.child, statement);

        rule Value = node.value;

        rule statement_Value =
            format(node) ++ text(";");
        """
    )

    assert formatter.format(Container(Value(7))) == "7;"


def test_context_falls_back_to_default_rule():
    formatter = Formatter.from_dsl_source(
        """
        rule Container = format(node.child, statement);
        rule Value = node.value;
        """
    )

    assert formatter.format(Container(Value(7))) == "7"


def test_default_call_does_not_select_contextual_rule():
    formatter = Formatter.from_dsl_source(
        """
        rule Value = node.value;
        rule statement_Value = node.value ++ text(";");
        """
    )

    assert formatter.format(Value(7)) == "7"


def test_contextual_rule_can_delegate_to_default_without_recursion():
    formatter = Formatter.from_dsl_source(
        """
        rule Container = format(node.child, statement);

        rule Value = text("[") ++ node.value ++ text("]");

        rule statement_Value =
            format(node) ++ text(";");
        """
    )

    assert formatter.format(Container(Value(7))) == "[7];"


def test_none_is_not_silently_accepted():
    formatter = Formatter.from_dsl_source(
        'rule Value = text("value");'
    )

    with pytest.raises(FormatterError, match="NoneType"):
        formatter.format(None)

def test_context_default_rule_is_used_without_specific_rule():
    formatter = Formatter.from_dsl_source(
        """
        rule Container = format(node.child, wrap);
        rule Value = node.value;
        rule wrap_default = text("<") ++ format(node) ++ text(">");
        """
    )

    assert formatter.format(Container(Value(7))) == "<7>"


def test_specific_context_rule_wins_over_default():
    formatter = Formatter.from_dsl_source(
        """
        rule Container = format(node.child, wrap);
        rule Value = node.value;
        rule wrap_default = text("<") ++ format(node) ++ text(">");
        rule wrap_Value = text("[") ++ format(node) ++ text("]");
        """
    )

    assert formatter.format(Container(Value(7))) == "[7]"


def test_default_rule_is_ignored_without_context():
    formatter = Formatter.from_dsl_source(
        """
        rule Value = node.value;
        rule wrap_default = text("<") ++ format(node) ++ text(">");
        """
    )

    assert formatter.format(Value(7)) == "7"