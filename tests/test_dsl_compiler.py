import pytest

from parglare_formatter.dsl.ast import (
    AttrPath, DocConcat, DocText, DocLine, DocSoftline, DocNest, DocGroup,
    DocAlign, DocFormat, DocList, DocItem, DocAttrRef,
)
from parglare_formatter.dsl.compiler import compile_doc_expr, CompileError, ITEM_KEY
from parglare_formatter.layout_engine import render
from tests.mini_lang.ast_nodes import (
    Identifier, NumberLiteral, BinaryOp, Call, Block, ExprStmt, )


def _noop_format_node(node):
    raise AssertionError(f"format_node should not be called for {node!r}")


class TestPrimitiveDocTerms:
    def test_doc_text(self):
        doc = compile_doc_expr(DocText(value="hello"), {}, _noop_format_node)
        assert render(doc) == "hello"

    def test_doc_line_is_hard_break(self):
        expr = DocConcat(left=DocText(value="a"), right=DocConcat(left=DocLine(), right=DocText(value="b")))
        doc = compile_doc_expr(expr, {}, _noop_format_node)
        assert render(doc, width=1000) == "a\nb"

    def test_doc_softline_flat_in_group(self):
        expr = DocGroup(body=DocConcat(left=DocText(value="a"), right=DocConcat(left=DocSoftline(), right=DocText(value="b"))))
        doc = compile_doc_expr(expr, {}, _noop_format_node)
        assert render(doc, width=80) == "a b"

    def test_doc_nest_and_align(self):
        expr = DocNest(indent=4, body=DocConcat(left=DocLine(), right=DocText(value="x")))
        doc = compile_doc_expr(expr, {}, _noop_format_node)
        assert render(doc, width=80) == "\n    x"

        expr2 = DocConcat(left=DocText(value="abc"), right=DocAlign(body=DocConcat(left=DocLine(), right=DocText(value="y"))))
        doc2 = compile_doc_expr(expr2, {}, _noop_format_node)
        assert render(doc2, width=80) == "abc\n   y"


class TestAttrPathResolution:
    def test_simple_attr_ref(self):
        node = Identifier(name="x")
        expr = DocAttrRef(path=AttrPath(["node", "name"]))
        doc = compile_doc_expr(expr, {"node": node}, _noop_format_node)
        assert render(doc) == "x"

    def test_nested_attr_ref(self):
        node = BinaryOp(op="+", left=Identifier(name="a"), right=NumberLiteral(value=5))
        expr = DocAttrRef(path=AttrPath(["node", "left", "name"]))
        doc = compile_doc_expr(expr, {"node": node}, _noop_format_node)
        assert render(doc) == "a"

    def test_unknown_parameter_raises_compile_error(self):
        expr = DocAttrRef(path=AttrPath(["unknown_param"]))
        with pytest.raises(CompileError, match="Unknown param"):
            compile_doc_expr(expr, {"node": Identifier(name="x")}, _noop_format_node)

    def test_unknown_attribute_raises_compile_error(self):
        node = Identifier(name="x")
        expr = DocAttrRef(path=AttrPath(["node", "does_not_exist"]))
        with pytest.raises(CompileError, match="does not have attribute"):
            compile_doc_expr(expr, {"node": node}, _noop_format_node)

    def test_empty_attr_path_raises(self):
        expr = DocAttrRef(path=AttrPath([]))
        with pytest.raises(CompileError, match="is empty"):
            compile_doc_expr(expr, {}, _noop_format_node)


class TestDocFormatDelegatesToCallback:
    def test_format_calls_format_node_with_resolved_target(self):
        called_with = []

        def fake_format_node(node):
            called_with.append(node)
            from parglare_formatter.document_model import text
            return text("<formatted>")

        inner = NumberLiteral(value=42)
        node = BinaryOp(op="+", left=Identifier(name="a"), right=inner)
        expr = DocFormat(path=AttrPath(["node", "right"]))
        doc = compile_doc_expr(expr, {"node": node}, fake_format_node)

        assert called_with == [inner]
        assert render(doc) == "<formatted>"


class TestDocListDefaultSeparator:
    def test_empty_list_produces_empty_doc(self):
        node = Block(stmts=[])
        expr = DocList(path=AttrPath(["node", "stmts"]), body=DocFormat(path=AttrPath([ITEM_KEY])))

        def fmt(n):
            raise AssertionError("should not be called for empty list")

        doc = compile_doc_expr(expr, {"node": node}, fmt)
        assert render(doc) == ""

    def test_single_item_no_separator_emitted(self):
        node = Block(stmts=[ExprStmt(expr=Identifier(name="a"))])
        expr = DocList(path=AttrPath(["node", "stmts"]), body=DocFormat(path=AttrPath([ITEM_KEY])))

        def fmt(n):
            from parglare_formatter.document_model import text
            return text("STMT")

        doc = compile_doc_expr(expr, {"node": node}, fmt)
        assert render(doc) == "STMT"

    def test_multiple_items_separated_by_default_line(self):
        node = Block(stmts=[ExprStmt(expr=Identifier(name="a")), ExprStmt(expr=Identifier(name="b")), ExprStmt(expr=Identifier(name="c"))])
        expr = DocList(path=AttrPath(["node", "stmts"]), body=DocFormat(path=AttrPath([ITEM_KEY])))

        call_count = [0]

        def fmt(n):
            from parglare_formatter.document_model import text
            call_count[0] += 1
            return text(f"S{call_count[0]}")

        doc = compile_doc_expr(expr, {"node": node}, fmt)
        assert render(doc, width=1000) == "S1\nS2\nS3"

    def test_default_separator_field_is_none_when_unset(self):
        expr = DocList(path=AttrPath(["node", "stmts"]), body=DocItem())
        assert expr.separator is None

    def test_list_over_non_iterable_raises_compile_error(self):
        class HasIntAttr:
            count = 5
        expr = DocList(path=AttrPath(["node", "count"]), body=DocFormat(path=AttrPath([ITEM_KEY])))
        with pytest.raises(CompileError, match="iterable"):
            compile_doc_expr(expr, {"node": HasIntAttr()}, _noop_format_node)


class TestDocListExplicitSeparator:
    def test_text_comma_separator_for_inline_list(self):
        node = Call(callee="print", args=[Identifier(name="x"), NumberLiteral(value=42)])
        expr = DocList(
            path=AttrPath(["node", "args"]),
            body=DocItem(),
            separator=DocText(value=", "),
        )

        def fmt(n):
            if isinstance(n, Identifier):
                return compile_doc_expr(DocAttrRef(path=AttrPath(["node", "name"])), {"node": n}, fmt)
            elif isinstance(n, NumberLiteral):
                return compile_doc_expr(DocAttrRef(path=AttrPath(["node", "value"])), {"node": n}, fmt)
            raise CompileError("no rule")

        doc = compile_doc_expr(expr, {"node": node}, fmt)
        assert render(doc, width=1000) == "x, 42"

    def test_separator_not_emitted_around_single_item(self):
        node = Call(callee="f", args=[Identifier(name="only")])
        expr = DocList(path=AttrPath(["node", "args"]), body=DocItem(), separator=DocText(value=", "))

        def fmt(n):
            return compile_doc_expr(DocAttrRef(path=AttrPath(["node", "name"])), {"node": n}, fmt)

        doc = compile_doc_expr(expr, {"node": node}, fmt)
        assert render(doc) == "only"

    def test_separator_not_emitted_for_empty_list(self):
        node = Call(callee="f", args=[])
        expr = DocList(path=AttrPath(["node", "args"]), body=DocItem(), separator=DocText(value=", "))
        doc = compile_doc_expr(expr, {"node": node}, _noop_format_node)
        assert render(doc) == ""

    def test_softline_separator_allows_flat_or_broken(self):
        node = Call(callee="f", args=[Identifier(name="x"), NumberLiteral(value=42)])
        sep = DocConcat(left=DocText(value=","), right=DocSoftline())
        expr = DocGroup(body=DocList(path=AttrPath(["node", "args"]), body=DocItem(), separator=sep))

        def fmt(n):
            if isinstance(n, Identifier):
                return compile_doc_expr(DocAttrRef(path=AttrPath(["node", "name"])), {"node": n}, fmt)
            elif isinstance(n, NumberLiteral):
                return compile_doc_expr(DocAttrRef(path=AttrPath(["node", "value"])), {"node": n}, fmt)
            raise CompileError("no rule")

        doc = compile_doc_expr(expr, {"node": node}, fmt)
        assert render(doc, width=80) == "x, 42"
        assert render(doc, width=3) == "x,\n42"

    def test_separator_resolved_in_outer_bindings_not_item_context(self):
        node = Call(callee="f", args=[Identifier(name="x"), NumberLiteral(value=42)])
        bad_separator = DocFormat(path=AttrPath(["item"]))
        expr = DocList(path=AttrPath(["node", "args"]), body=DocItem(), separator=bad_separator)

        def fmt(n):
            return compile_doc_expr(DocAttrRef(path=AttrPath(["node", "name"])), {"node": n}, fmt)

        with pytest.raises(CompileError, match="does not have attribute"):
            compile_doc_expr(expr, {"node": node}, fmt)

    def test_multi_item_list_with_custom_separator_and_nest(self):
        node = Call(callee="f", args=[Identifier(name="a"), Identifier(name="b"), Identifier(name="c")])
        expr = DocList(path=AttrPath(["node", "args"]), body=DocItem(), separator=DocText(value=" | "))

        def fmt(n):
            return compile_doc_expr(DocAttrRef(path=AttrPath(["node", "name"])), {"node": n}, fmt)

        doc = compile_doc_expr(expr, {"node": node}, fmt)
        assert render(doc) == "a | b | c"


class TestDocItemOutsideList:
    def test_item_key_present_delegates_to_format_node(self):
        item_node = NumberLiteral(value=7)

        def fmt(n):
            from parglare_formatter.document_model import text
            assert n is item_node
            return text("ITEM_FORMATTED")

        doc = compile_doc_expr(DocItem(), {ITEM_KEY: item_node}, fmt)
        assert render(doc) == "ITEM_FORMATTED"

    def test_item_outside_list_context_raises(self):
        with pytest.raises(CompileError, match="used outside list"):
            compile_doc_expr(DocItem(), {}, _noop_format_node)


class TestRealisticEndToEnd:
    def _make_format_node(self):
        def format_node(node):
            if isinstance(node, Identifier):
                return compile_doc_expr(DocAttrRef(path=AttrPath(["node", "name"])), {"node": node}, format_node)
            elif isinstance(node, NumberLiteral):
                return compile_doc_expr(DocAttrRef(path=AttrPath(["node", "value"])), {"node": node}, format_node)
            elif isinstance(node, BinaryOp):
                expr = DocConcat(
                    left=DocConcat(left=DocFormat(path=AttrPath(["node", "left"])), right=DocText(value=f" {node.op} ")),
                    right=DocFormat(path=AttrPath(["node", "right"])),
                )
                return compile_doc_expr(expr, {"node": node}, format_node)
            elif isinstance(node, ExprStmt):
                expr = DocConcat(left=DocFormat(path=AttrPath(["node", "expr"])), right=DocText(value=";"))
                return compile_doc_expr(expr, {"node": node}, format_node)
            elif isinstance(node, Block):
                expr = DocConcat(
                    left=DocConcat(
                        left=DocText(value="{"),
                        right=DocNest(
                            indent=2,
                            body=DocConcat(
                                left=DocLine(),
                                right=DocList(path=AttrPath(["node", "stmts"]), body=DocFormat(path=AttrPath([ITEM_KEY]))),
                            ),
                        ),
                    ),
                    right=DocConcat(left=DocLine(), right=DocText(value="}")),
                )
                return compile_doc_expr(expr, {"node": node}, format_node)
            else:
                raise CompileError(f"No rules for type {type(node).__name__}")
        return format_node

    def test_binary_op_end_to_end(self):
        fmt = self._make_format_node()
        node = BinaryOp(op="+", left=Identifier(name="a"), right=NumberLiteral(value=5))
        assert render(fmt(node)) == "a + 5"

    def test_nested_binary_op(self):
        fmt = self._make_format_node()
        inner = BinaryOp(op="*", left=Identifier(name="x"), right=NumberLiteral(value=2))
        outer = BinaryOp(op="+", left=Identifier(name="a"), right=inner)
        assert render(fmt(outer)) == "a + x * 2"

    def test_block_with_multiple_statements_each_on_own_line(self):
        fmt = self._make_format_node()
        block = Block(stmts=[
            ExprStmt(expr=Identifier(name="a")),
            ExprStmt(expr=BinaryOp(op="*", left=Identifier(name="x"), right=NumberLiteral(value=2))),
        ])
        result = render(fmt(block))
        assert result == "{\n  a;\n  x * 2;\n}"

    def test_missing_rule_raises_compile_error(self):
        fmt = self._make_format_node()
        with pytest.raises(CompileError, match="No rules"):
            fmt(Call(callee="f", args=[]))


class TestUnknownDocExprType:
    def test_unknown_expr_type_raises(self):
        class NotADocExpr:
            pass
        with pytest.raises(CompileError, match="Unknown DocExpr type"):
            compile_doc_expr(NotADocExpr(), {}, _noop_format_node)