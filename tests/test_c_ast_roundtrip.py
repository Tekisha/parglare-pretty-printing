from pathlib import Path

import pytest
from pycparser import c_parser

from examples.c_ast_example.ast_utils import ast_signature
from parglare_formatter.formatter import Formatter


RULES_PATH = (
    Path(__file__).resolve().parents[1]
    / "examples"
    / "c_ast_example"
    / "formatting_rules.dsl"
)

WIDTHS = [1, 5, 10, 40, 80, 200]

C_CASES = [
    "int main(void){return 0;}",
    "int answer(void) { return 42; }",
    "unsigned int answer(void) { return 42; }",
    """
    int first(void) {
        return 1;
    }

    int second(void) {
        return 2;
    }
    """,
    "void noop(void) {}",
    "void noop(void) { return; }",
    "int main() { return 0; }",
    "void noop() {}",
    "void noop() { return; }",
]


def parse_c(source):
    return c_parser.CParser().parse(source)


@pytest.fixture(scope="module")
def c_formatter():
    return Formatter.from_dsl_file(str(RULES_PATH))


def test_format_minimal_program(c_formatter):
    ast = parse_c("int main(void){return 0;}")

    result = c_formatter.format(ast, width=80)

    assert result == (
        "int main(void) {\n"
        "    return 0;\n"
        "}\n"
    )


@pytest.mark.parametrize("width", WIDTHS)
@pytest.mark.parametrize("source", C_CASES)
def test_c_ast_roundtrip(c_formatter, source, width):
    ast1 = parse_c(source)

    output1 = c_formatter.format(ast1, width=width)

    ast2 = parse_c(output1)

    assert ast_signature(ast2) == ast_signature(ast1), (
        f"AST changed after formatting, width={width}.\n"
        f"Formatted output:\n{output1}"
    )

    output2 = c_formatter.format(ast2, width=width)

    assert output2 == output1, (
        f"Formatting is not idempotent, width={width}.\n"
        f"First output:\n{output1}\n"
        f"Second output:\n{output2}"
    )


def test_signature_ignores_coordinates():
    compact = parse_c("int main(void){return 0;}")

    spaced = parse_c(
        "\n\nint main(void) {\n"
        "    return 0;\n"
        "}\n"
    )

    assert ast_signature(compact) == ast_signature(spaced)


def test_signature_detects_changed_constant():
    zero = parse_c("int main(void){return 0;}")
    one = parse_c("int main(void){return 1;}")

    assert ast_signature(zero) != ast_signature(one)


def test_signature_detects_changed_function_name():
    first = parse_c("int first(void){return 0;}")
    second = parse_c("int second(void){return 0;}")

    assert ast_signature(first) != ast_signature(second)


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (
            "void noop(void) {}",
            "void noop(void) {\n}\n",
        ),
        (
            "void noop(void) { return; }",
            "void noop(void) {\n    return;\n}\n",
        ),
        (
            "int main() { return 0; }",
            "int main() {\n    return 0;\n}\n",
        ),
    ],
)
def test_optional_c_construct_layout(c_formatter, source, expected):
    ast = parse_c(source)

    assert c_formatter.format(ast, width=80) == expected