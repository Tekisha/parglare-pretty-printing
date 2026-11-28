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
    "int f(int x) { x = 10; return x; }",
    "int f(int x) { x += 2; return x; }",
    "void g(void) { ping(); }",
    "int g(void) { return add(1, 2); }",
    "int g(void) { int r = add(1, 2); return r; }",
    "int g(void) { return add(add(1, 2), 3); }",
    "int g(int x) { x = add(x, 3); return x; }",
    "int g(int x, int y) { x = y = 1; return x; }",
    "int g(int x) { return add(x = 1, 2); }",
    "int g(int x) { int y = (x = 2); return y; }",
    """
    int add(int a, int b) {
        return a + b;
    }

    int main(void) {
        int result = add(1, 2);
        result = add(result, 3);
        add(result, 0);
        return result;
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
    assert formatter.format(reparsed, width=width) == output


def test_call_as_expression_and_as_statement(formatter):
    source = """
    int main(void) {int x = add(1, 2);add(x, 3);return x;}
    """

    output = formatter.format(CParser().parse(source), width=80)

    assert output == (
        "int main(void) {\n"
        "    int x = add(1, 2);\n"
        "    add(x, 3);\n"
        "    return x;\n"
        "}\n"
    )


def test_call_without_arguments(formatter):
    output = formatter.format(
        CParser().parse("void g(void) { ping(); }"), width=80
    )

    assert "    ping();\n" in output
    assert "None" not in output


def test_assignment_statement_has_no_parentheses(formatter):
    output = formatter.format(
        CParser().parse("int f(int x) { x += 2; return x; }"),
        width=80,
    )

    assert "    x += 2;\n" in output


def test_nested_assignment_is_parenthesized(formatter):
    output = formatter.format(
        CParser().parse(
            "int g(int x, int y) { x = y = 1; return x; }"
        ),
        width=80,
    )

    assert "    x = (y = 1);\n" in output


def test_long_argument_list_breaks_on_narrow_width(formatter):
    ast = CParser().parse(
        "int g(void) { return add(1000, 2000, 3000, 4000); }"
    )

    wide = formatter.format(ast, width=200)
    narrow = formatter.format(ast, width=20)

    assert narrow.count("\n") > wide.count("\n")
    assert ast_signature(CParser().parse(wide)) == ast_signature(
        CParser().parse(narrow)
    )