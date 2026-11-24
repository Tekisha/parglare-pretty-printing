from types import SimpleNamespace

import pytest

from parglare_formatter.document_model import Empty, text
from parglare_formatter.dsl.ast import (
    AttrPath,
    DocAttrRef,
    DocConcat,
    DocOptional,
    DocText,
)
from parglare_formatter.dsl.compiler import (
    CompileError,
    compile_doc_expr,
)
from parglare_formatter.dsl.parser import parse_dsl
from parglare_formatter.formatter import Formatter
from parglare_formatter.layout_engine import render


def test_parser_builds_optional_expression():
    rule_file = parse_dsl(
        'rule Example = optional(node.value, text("present"));'
    )

    body = rule_file.get_rule("Example").body

    assert isinstance(body, DocOptional)
    assert body.path.parts == ["node", "value"]
    assert isinstance(body.body, DocText)
    assert body.body.value == "present"


def test_parser_keeps_concatenation_inside_optional():
    rule_file = parse_dsl(
        'rule Example = '
        'optional(node.value, text(" ") ++ format(node.value));'
    )

    body = rule_file.get_rule("Example").body

    assert isinstance(body, DocOptional)
    assert isinstance(body.body, DocConcat)


def test_none_returns_empty_without_evaluating_body():
    expr = DocOptional(
        path=AttrPath(parts=["node", "value"]),
        body=DocAttrRef(
            path=AttrPath(parts=["node", "missing"])
        ),
    )

    def unexpected_format(_):
        pytest.fail("Formatting must not be called for an absent value")

    doc = compile_doc_expr(
        expr,
        {"node": SimpleNamespace(value=None)},
        unexpected_format,
    )

    assert isinstance(doc, Empty)


@pytest.mark.parametrize("value", [0, False, "", [], "text"])
def test_non_none_values_compile_body(value):
    expr = DocOptional(
        path=AttrPath(parts=["node", "value"]),
        body=DocText(value="present"),
    )

    doc = compile_doc_expr(
        expr,
        {"node": SimpleNamespace(value=value)},
        lambda node: text(str(node)),
    )

    assert render(doc, width=80) == "present"


def test_missing_guard_attribute_is_an_error():
    expr = DocOptional(
        path=AttrPath(parts=["node", "missing"]),
        body=DocText(value="present"),
    )

    with pytest.raises(CompileError, match="missing"):
        compile_doc_expr(
            expr,
            {"node": SimpleNamespace()},
            lambda node: text(str(node)),
        )


def test_present_value_does_not_hide_body_errors():
    expr = DocOptional(
        path=AttrPath(parts=["node", "value"]),
        body=DocAttrRef(
            path=AttrPath(parts=["node", "missing"])
        ),
    )

    with pytest.raises(CompileError, match="missing"):
        compile_doc_expr(
            expr,
            {"node": SimpleNamespace(value=0)},
            lambda node: text(str(node)),
        )


def test_optional_preserves_item_binding():
    formatter = Formatter.from_dsl_source(
        """
        rule SimpleNamespace =
            list(
                node.values,
                optional(item, format(item)),
                text(",")
            );
        """
    )

    result = formatter.format(
        SimpleNamespace(values=[0, False, ""])
    )

    assert result == "0,False,"


def test_optional_preserves_grammar_separator_context():
    formatter = Formatter.from_dsl_source(
        """
        rule SimpleNamespace =
            optional(
                node.values,
                list(node.values, item)
            );
        """
    )

    formatter.list_separators = {
        ("SimpleNamespace", "values"): ",",
    }

    result = formatter.format(
        SimpleNamespace(values=[1, 2])
    )

    assert result == "1,\n2"