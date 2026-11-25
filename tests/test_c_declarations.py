from pathlib import Path

import pytest
from pycparser import CParser, c_ast

from examples.c_ast_example.ast_utils import ast_signature
from parglare_formatter.formatter import Formatter


ROOT = Path(__file__).resolve().parents[1]

RULES_PATH = (
    ROOT
    / "examples"
    / "c_ast_example"
    / "formatting_rules.dsl"
)


@pytest.fixture
def formatter():
    return Formatter.from_dsl_file(str(RULES_PATH))


SOURCES = [
    "void noop(void) {}",
    "void noop(void) { return; }",
    "int main() { return 0; }",
    "int global = 10;",
    "int add(int a, int b);",
    """
    int add(int a, int b) {
        int result = a + b;
        return result;
    }
    """,
    """
    int compute(int a, int b, int c) {
        int result = (a + b) * c;
        return result;
    }
    """,
    """
    int compute(int a, int b, int c) {
        return a - (b - c);
    }
    """,
    """
    int main(void) {
        int x;
        int y = 0;
        return y;
    }
    """,
]


@pytest.mark.parametrize("source", SOURCES)
@pytest.mark.parametrize("width", [1, 5, 10, 40, 80, 200])
def test_roundtrip_and_idempotence(formatter, source, width):
    original = CParser().parse(source)

    output = formatter.format(original, width=width)
    reparsed = CParser().parse(output)

    assert ast_signature(original) == ast_signature(reparsed)

    second_output = formatter.format(reparsed, width=width)

    assert second_output == output


def test_add_layout(formatter):
    source = """
    int add(int a, int b) {
        int result = a + b;
        return result;
    }
    """

    output = formatter.format(
        CParser().parse(source),
        width=80,
    )

    assert output == (
        "int add(int a, int b) {\n"
        "    int result = (a + b);\n"
        "    return result;\n"
        "}\n"
    )


def test_width_changes_expression_layout(formatter):
    ast = CParser().parse(
        "int add(int a, int b) { return a + b; }"
    )

    wide = formatter.format(ast, width=200)
    narrow = formatter.format(ast, width=10)

    assert wide != narrow
    assert narrow.count("\n") > wide.count("\n")
    assert ast_signature(CParser().parse(wide)) == ast_signature(
        CParser().parse(narrow)
    )