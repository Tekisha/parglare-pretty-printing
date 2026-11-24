from pathlib import Path

import pytest

from examples.json_example.json_lang_parser import build_parser
from examples.calc_example.calc_parser import parse_calc
from parglare_formatter.formatter import Formatter

FIXTURES_DIR = Path(__file__).parent / "fixtures"
WIDTHS = [1, 5, 10, 40, 80, 200]


def _formatter(name: str) -> Formatter:
    src = (FIXTURES_DIR / name).read_text(encoding="utf-8")
    return Formatter.from_dsl_source(src)


def assert_roundtrip(parse, formatter, source, width):
    ast1 = parse(source)
    out1 = formatter.format(ast1, width=width)

    ast2 = parse(out1)
    assert ast2 == ast1, (
        f"AST changed after format+parse (width={width}).\n"
        f"Formatted output:\n{out1}"
    )

    out2 = formatter.format(ast2, width=width)
    assert out2 == out1, f"Formatting is not idempotent (width={width})"


# ---------------- JSON ----------------

JSON_CASES = [
    '{"x": true, "y": [2, 3]}',
    '{"s": "x", "n": 1, "b": false, "u": null, "a": [1, 2]}',
    '{"a": [1, 2, 3], "b": {"c": null}}',
    '{"msg": "He said \\"hello\\"\\nPath: C\\\\temp"}',
    '[]',
    '{}',
    '[[1], [2, [3]]]',
]


@pytest.fixture(scope="module")
def json_parse():
    return build_parser().parse


@pytest.fixture(scope="module")
def json_formatter():
    return _formatter("json_formatting_rules.dsl")


@pytest.mark.parametrize("width", WIDTHS)
@pytest.mark.parametrize("source", JSON_CASES)
def test_json_roundtrip(json_parse, json_formatter, source, width):
    assert_roundtrip(json_parse, json_formatter, source, width)


# ---------------- Calc ----------------

CALC_CASES = [
    "1 + 2 * 3\n10 - 5\n",
    "1 + 2 * 3\n(1 + 2) * 3\n",
    "1 - (2 - 3)\n",
    "((1))\n",
    "1 + 2 + 3 + 4\n",
]


@pytest.fixture(scope="module")
def calc_formatter():
    return _formatter("calc_formatting_rules.dsl")


@pytest.mark.parametrize("width", WIDTHS)
@pytest.mark.parametrize("source", CALC_CASES)
def test_calc_roundtrip(calc_formatter, source, width):
    assert_roundtrip(parse_calc, calc_formatter, source, width)