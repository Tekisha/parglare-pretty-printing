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
    "int f(int n) { int s = 0; for (int i = 0; i < n; i++) { s = s + i; } return s; }",
    "int f(int n) { for (int i = 0; i < n; ++i) { ping(); } return n; }",
    "int f(int n) { int i; for (i = 0; i < n; i = i + 1) { ping(); } return i; }",
    "int f(int n) { for (;;) { ping(); } return n; }",
    "int f(int n) { for (int i = 0;;) { ping(); } return n; }",
    "int f(int n) { for (; n > 0;) { n = n - 1; } return n; }",
    "int f(int n) { for (; n > 0; n--) { ping(); } return n; }",
    "int f(int n) { for (int i = 0; i < n; i++) ping(); return n; }",
    "int f(int n) { for (int i = 0; i < n; i++) n = n - 1; return n; }",
    "int f(int n) { for (int i = 0; add(i, 1) < n; i++) {} return n; }",
    """
    int f(int n) {
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < n; j++) {
                if (i > j) {
                    ping();
                }
            }
        }
        return n;
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


def test_for_layout(formatter):
    source = """
    int sum(int n) {
        int s = 0;
        for (int i = 0; i < n; i++) { s = s + i; }
        return s;
    }
    """

    output = formatter.format(CParser().parse(source), width=80)

    assert output == (
        "int sum(int n) {\n"
        "    int s = 0;\n"
        "    for (int i = 0; i < n; i++) {\n"
        "        s = (s + i);\n"
        "    }\n"
        "    return s;\n"
        "}\n"
    )


@pytest.mark.parametrize(
    ("source", "fragment"),
    [
        ("int f(int n) { for (;;) { ping(); } return n; }", "    for (;;) {\n"),
        (
            "int f(int n) { for (int i = 0;;) { ping(); } return n; }",
            "    for (int i = 0;;) {\n",
        ),
        (
            "int f(int n) { for (; n > 0;) { n = n - 1; } return n; }",
            "    for (; n > 0;) {\n",
        ),
        (
            "int f(int n) { int i; for (i = 0; i < n; i = i + 1) { ping(); } return i; }",
            "    for (i = 0; i < n; i = (i + 1)) {\n",
        ),
        (
            "int f(int n) { for (int i = 0; i < n; i++) ping(); return n; }",
            "    for (int i = 0; i < n; i++) ping();\n",
        ),
    ],
)
def test_header_variants(formatter, source, fragment):
    output = formatter.format(CParser().parse(source), width=80)

    assert fragment in output
    assert "None" not in output