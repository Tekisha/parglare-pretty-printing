from pathlib import Path

import pytest
from pycparser import CParser

from examples.c_ast_example.ast_utils import ast_signature
from parglare_formatter.formatter import Formatter


ROOT = Path(__file__).resolve().parents[1]

RULES_PATH = (
    ROOT / "examples" / "c_ast_example" / "formatting_rules.dsl"
)


@pytest.fixture
def formatter():
    return Formatter.from_dsl_file(str(RULES_PATH))


SOURCES = [
    "int f(int x) { return -x; }",
    "int f(int x) { return +x; }",
    "int f(int x) { return !x; }",
    "int f(int x) { return ~x; }",
    "int f(int x) { return &x; }",
    "int f(int x) { return *x; }",
    "int f(int x) { return - -x; }",
    "int f(int x) { return -(x + 1); }",
    "int f(int x) { return sizeof x; }",
    "int f(int x) { x++; return x; }",
    "int f(int x) { x--; return x; }",
    "int f(int x) { ++x; return x; }",
    "int f(int x) { --x; return x; }",
    "int f(int x) { return x++; }",
    "int f(int x) { return ++x; }",
    "int f(int x) { int y = -x; return y; }",
    "int f(int x) { x = -x; return x; }",
    "int f(int x) { return add(-x, !x); }",
    "int f(int x) { if (!x) { return 1; } return 0; }",
    "int f(int x) { while (x--) { ping(); } return x; }",
]


@pytest.mark.parametrize("source", SOURCES)
@pytest.mark.parametrize("width", [1, 5, 10, 40, 80, 200])
def test_roundtrip_and_idempotence(formatter, source, width):
    original = CParser().parse(source)

    output = formatter.format(original, width=width)
    reparsed = CParser().parse(output)

    assert ast_signature(original) == ast_signature(reparsed)
    assert formatter.format(reparsed, width=width) == output


@pytest.mark.parametrize(
    ("source", "fragment"),
    [
        ("int f(int x) { return -x; }", "    return (-x);\n"),
        ("int f(int x) { return x++; }", "    return (x++);\n"),
        ("int f(int x) { return ++x; }", "    return (++x);\n"),
        ("int f(int x) { return - -x; }", "    return (-(-x));\n"),
        ("int f(int x) { return sizeof x; }", "    return (sizeof x);\n"),
        ("int f(int x) { x++; return x; }", "    x++;\n"),
        ("int f(int x) { --x; return x; }", "    --x;\n"),
        ("int f(int x) { if (!x) { return 1; } return 0; }", "    if (!x) {\n"),
    ],
)
def test_exact_fragments(formatter, source, fragment):
    output = formatter.format(CParser().parse(source), width=80)

    assert fragment in output