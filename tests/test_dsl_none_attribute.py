from dataclasses import dataclass
from typing import Any

import pytest

from parglare_formatter.formatter import Formatter, FormatterError


@dataclass
class Item:
    value: Any


@pytest.mark.parametrize(
    "body",
    [
        "node.value",
        "lower(node.value)",
        "upper(node.value)",
        "escaped(node.value)",
    ],
)
def test_none_is_rejected_as_text(body):
    formatter = Formatter.from_dsl_source(f"rule Item = {body};")

    with pytest.raises(FormatterError, match="is None"):
        formatter.format(Item(None))


def test_error_message_names_the_attribute_and_suggests_optional():
    formatter = Formatter.from_dsl_source("rule Item = node.value;")

    with pytest.raises(FormatterError) as info:
        formatter.format(Item(None))

    message = str(info.value)
    assert "node.value" in message
    assert "optional" in message


@pytest.mark.parametrize(
    ("value", "expected"),
    [(0, "0"), (False, "False"), ("", ""), ("x", "x")],
)
def test_other_falsy_values_are_still_printed(value, expected):
    formatter = Formatter.from_dsl_source("rule Item = node.value;")

    assert formatter.format(Item(value)) == expected


def test_optional_guards_a_none_attribute():
    formatter = Formatter.from_dsl_source(
        'rule Item = "<" ++ optional(node.value, node.value) ++ ">";'
    )

    assert formatter.format(Item(None)) == "<>"
    assert formatter.format(Item("x")) == "<x>"