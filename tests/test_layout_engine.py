import pytest

from src.parglare_formatter.document_model import (
    text, line, softline, concat, nest, group, align, empty, concat_all,
)
from src.parglare_formatter.layout_engine import render, pretty, _fits, _contains_hard_line, Mode


class TestBasicRendering:
    def test_plain_text(self):
        assert render(text("hello"), width=80) == "hello"

    def test_empty_renders_to_empty_string(self):
        assert render(empty(), width=80) == ""

    def test_concat_joins_texts(self):
        doc = concat(text("foo"), text("bar"))
        assert render(doc, width=80) == "foobar"

    def test_concat_all_joins_multiple(self):
        doc = concat_all(text("a"), text("b"), text("c"))
        assert render(doc, width=80) == "abc"


class TestHardLine:
    def test_hard_line_always_breaks(self):
        doc = concat_all(text("a"), line(), text("b"))
        assert render(doc, width=80) == "a\nb"

    def test_hard_line_breaks_even_in_narrow_width_irrelevant(self):
        doc = concat_all(text("a"), line(), text("b"))
        assert render(doc, width=1000) == "a\nb"

    def test_group_with_hard_line_never_flattens(self):
        doc = group(concat_all(text("a"), line(), text("b")))
        result = render(doc, width=1000)
        assert "\n" in result
        assert result == "a\nb"


class TestSoftlineFlatVsBreak:
    def test_softline_flat_becomes_space(self):
        doc = group(concat_all(text("a"), softline(), text("b")))
        assert render(doc, width=80) == "a b"

    def test_softline_breaks_when_too_narrow(self):
        doc = group(concat_all(text("aaaaaaaaaa"), softline(), text("bbbbbbbbbb")))
        result = render(doc, width=5)
        assert result == "aaaaaaaaaa\nbbbbbbbbbb"

    def test_softline_at_exact_boundary_fits(self):
        doc = group(concat_all(text("a"), softline(), text("b")))
        assert render(doc, width=3) == "a b"


class TestNest:
    def test_nest_indents_after_break(self):
        doc = concat(
            group(concat_all(text("aaaaaaaaaa"), nest(2, concat(softline(), text("bbbbbbbbbb"))))),
            empty(),
        )
        result = render(doc, width=5)
        assert result == "aaaaaaaaaa\n  bbbbbbbbbb"

    def test_nest_zero_indent_is_noop(self):
        doc = nest(0, text("x"))
        assert render(doc, width=80) == "x"

    def test_nested_nest_accumulates_indent(self):
        doc = group(concat_all(
            text("a"),
            nest(2, concat_all(
                line(),
                text("b"),
                nest(2, concat(line(), text("c"))),
            )),
        ))
        result = render(doc, width=80)
        assert result == "a\n  b\n    c"


class TestGroupChoice:
    def test_group_flat_when_fits(self):
        doc = group(concat_all(text("["), text("a"), text(","), softline(), text("b"), text("]")))
        assert render(doc, width=80) == "[a, b]"

    def test_group_breaks_when_too_wide(self):
        doc = group(concat_all(text("["), text("a"), text(","), softline(), text("b"), text("]")))
        assert render(doc, width=5) == "[a,\nb]"

    def test_nested_group_independent_decision(self):
        doc = group(concat_all(
            text("outer("),
            nest(2, concat_all(
                softline(),
                group(concat_all(text("inner("), text("x"), text(")"))),
                text(","),
                softline(),
                text("y"),
            )),
            softline(),
            text(")"),
        ))
        result = render(doc, width=10)
        assert result == "outer(\n  inner(x),\n  y\n)"


class TestAlign:
    def test_align_uses_current_column(self):
        doc = concat_all(
            text("call("),
            align(concat_all(text("arg1,"), line(), text("arg2"))),
            text(")"),
        )
        result = render(doc, width=80)
        lines = result.split("\n")
        assert lines[0] == "call(arg1,"
        assert lines[1] == "     arg2)"

    def test_align_at_column_zero_behaves_like_no_indent(self):
        doc = align(concat(text("a"), concat(line(), text("b"))))
        assert render(doc, width=80) == "a\nb"


class TestLookahead:
    def test_fits_accounts_for_trailing_content_after_group(self):
        doc = concat(
            group(concat_all(text("["), text("abc"), softline(), text("def"), text("]"))),
            text(";"),
        )
        assert render(doc, width=10) == "[abc def];"
        result_narrow = render(doc, width=6)
        assert "\n" in result_narrow
        assert result_narrow == "[abc\ndef];"


class TestContainsHardLine:
    def test_detects_direct_hard_line(self):
        assert _contains_hard_line(line()) is True

    def test_detects_hard_line_inside_concat(self):
        assert _contains_hard_line(concat(text("a"), line())) is True

    def test_soft_line_is_not_hard(self):
        assert _contains_hard_line(softline()) is False

    def test_stops_at_nested_group_boundary(self):
        inner_with_hard = group(line())
        outer = concat(text("a"), inner_with_hard)
        assert _contains_hard_line(outer) is False

    def test_detects_hard_line_through_nest_and_align(self):
        assert _contains_hard_line(nest(2, line())) is True
        assert _contains_hard_line(align(line())) is True


class TestPrettyAlias:
    def test_pretty_is_alias_for_render(self):
        doc = text("same")
        assert pretty(doc, width=80) == render(doc, width=80)


class TestRealisticDocument:
    def test_function_call_pretty_printed_wide(self):
        args_doc = group(concat_all(
            text("f("),
            nest(2, concat_all(
                softline(),
                text("a,"), softline(),
                text("b,"), softline(),
                text("c"),
            )),
            softline(),
            text(")"),
        ))
        assert render(args_doc, width=80) == "f( a, b, c )"

    def test_function_call_pretty_printed_narrow(self):
        args_doc = group(concat_all(
            text("f("),
            nest(2, concat_all(
                softline(),
                text("a,"), softline(),
                text("b,"), softline(),
                text("c"),
            )),
            softline(),
            text(")"),
        ))
        result = render(args_doc, width=5)
        assert result == "f(\n  a,\n  b,\n  c\n)"