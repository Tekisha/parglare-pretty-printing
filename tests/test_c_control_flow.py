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
    "int f(int x) { if (x) { return 1; } return 0; }",
    "int f(int x) { if (x) { return 1; } else { return 2; } }",
    "int f(int x) { if (x > 0) { return 1; } return 0; }",
    "int f(int x) { if (x) return 1; return 0; }",
    "int f(int x) { if (x) return 1; else return 2; }",
    "int f(int x) { if (x) x = 1; else x = 2; return x; }",
    "void f(int x) { if (x) ping(); }",
    """
    int sign(int x) {
        if (x > 0) {
            return 1;
        } else if (x < 0) {
            return 2;
        } else {
            return 0;
        }
    }
    """,
    "int f(int a, int b) { if (a) { if (b) { a = 1; } } else { a = 2; } return a; }",
    "int f(int a, int b) { if (a) { if (b) { a = 1; } else { a = 2; } } return a; }",
    "int f(int x) { if (x) {} return x; }",
    "int f(int x) { if (x) { return 1; } else {} return 0; }",
    "int f(int x) { while (x > 0) { x = x - 1; } return x; }",
    "int f(int x) { while (x) x = x - 1; return x; }",
    "int f(int x) { while (x) {} return x; }",
    "int f(int x) { while (add(x, 1) > 0) { x = x - 1; } return x; }",
    """
    int count(int n) {
        int i = 0;
        while (i < n) {
            if (i > 10) {
                return i;
            }
            i = i + 1;
        }
        return i;
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


def test_if_else_layout(formatter):
    source = "int max(int a, int b) { if (a > b) { return a; } else { return b; } }"

    output = formatter.format(CParser().parse(source), width=80)

    assert output == (
        "int max(int a, int b) {\n"
        "    if (a > b) {\n"
        "        return a;\n"
        "    } else {\n"
        "        return b;\n"
        "    }\n"
        "}\n"
    )


def test_else_if_chain_layout(formatter):
    source = """
    int sign(int x) {
        if (x > 0) { return 1; }
        else if (x < 0) { return 2; }
        else { return 0; }
    }
    """

    output = formatter.format(CParser().parse(source), width=80)

    assert output == (
        "int sign(int x) {\n"
        "    if (x > 0) {\n"
        "        return 1;\n"
        "    } else if (x < 0) {\n"
        "        return 2;\n"
        "    } else {\n"
        "        return 0;\n"
        "    }\n"
        "}\n"
    )


def test_while_layout(formatter):
    source = """
    int count(int n) {
        int i = 0;
        while (i < n) { i = i + 1; }
        return i;
    }
    """

    output = formatter.format(CParser().parse(source), width=80)

    assert output == (
        "int count(int n) {\n"
        "    int i = 0;\n"
        "    while (i < n) {\n"
        "        i = (i + 1);\n"
        "    }\n"
        "    return i;\n"
        "}\n"
    )


def test_condition_has_no_extra_parentheses(formatter):
    output = formatter.format(
        CParser().parse("int f(int a, int b) { if (a > b) { return a; } return b; }"),
        width=80,
    )

    assert "if (a > b) {" in output
    assert "((" not in output


def test_non_block_branch_gets_semicolon(formatter):
    output = formatter.format(
        CParser().parse("int f(int x) { if (x) x = 1; return x; }"),
        width=80,
    )

    assert "if (x) x = 1;" in output


def test_narrow_condition_breaks_but_stays_equivalent(formatter):
    ast = CParser().parse(
        "int f(int alpha, int beta) { while (alpha + beta > alpha * beta) { alpha = alpha - 1; } return alpha; }"
    )

    wide = formatter.format(ast, width=200)
    narrow = formatter.format(ast, width=15)

    assert narrow.count("\n") > wide.count("\n")
    assert ast_signature(CParser().parse(wide)) == ast_signature(
        CParser().parse(narrow)
    )