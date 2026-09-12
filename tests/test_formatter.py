import os

import pytest

from src.parglare_formatter.dsl.ast import (
    RuleFile, RuleDecl, AttrPath,
    DocConcat, DocText, DocLine, DocFormat, DocList, DocItem, DocAttrRef,
)
from src.parglare_formatter.formatter.formatter import Formatter, FormatterError, format_ast
from src.parglare_formatter.examples.mini_lang.ast_nodes import (
    Identifier, NumberLiteral, BinaryOp, Call, Assign, ExprStmt, Block, If, FuncDef, For,
)


def AP(*parts):
    return AttrPath(list(parts))


def _make_minimal_rules():
    return RuleFile(rules=[
        RuleDecl(name="Identifier", params=["node"], body=DocAttrRef(path=AP("node", "name"))),
        RuleDecl(name="NumberLiteral", params=["node"], body=DocAttrRef(path=AP("node", "value"))),
        RuleDecl(name="BinaryOp", params=["node"], body=DocConcat(
            left=DocConcat(
                left=DocConcat(left=DocFormat(path=AP("node", "left")), right=DocText(value=" ")),
                right=DocConcat(left=DocAttrRef(path=AP("node", "op")), right=DocText(value=" ")),
            ),
            right=DocFormat(path=AP("node", "right")),
        )),
    ])


class TestFormatterBasic:
    def test_format_simple_identifier(self):
        rules = _make_minimal_rules()
        formatter = Formatter(rules)
        result = formatter.format(Identifier(name="x"))
        assert result == "x"

    def test_format_number_literal(self):
        rules = _make_minimal_rules()
        formatter = Formatter(rules)
        result = formatter.format(NumberLiteral(value=42))
        assert result == "42"

    def test_format_binary_op_recursive(self):
        rules = _make_minimal_rules()
        formatter = Formatter(rules)
        node = BinaryOp(op="+", left=Identifier(name="a"), right=NumberLiteral(value=5))
        assert formatter.format(node) == "a + 5"

    def test_format_nested_binary_op(self):
        rules = _make_minimal_rules()
        formatter = Formatter(rules)
        inner = BinaryOp(op="*", left=Identifier(name="x"), right=NumberLiteral(value=2))
        outer = BinaryOp(op="+", left=Identifier(name="a"), right=inner)
        assert formatter.format(outer) == "a + x * 2"


class TestFormatterMissingRule:
    def test_missing_rule_raises_formatter_error(self):
        rules = _make_minimal_rules()
        formatter = Formatter(rules)
        with pytest.raises(FormatterError, match="No DSL rule"):
            formatter.format(Call(callee="f", args=[]))

    def test_missing_rule_error_mentions_class_name(self):
        rules = _make_minimal_rules()
        formatter = Formatter(rules)
        with pytest.raises(FormatterError, match="Call"):
            formatter.format(Call(callee="f", args=[]))


class TestFormatterParamValidation:
    def test_rule_with_wrong_param_count_raises(self):
        rules = RuleFile(rules=[
            RuleDecl(name="Identifier", params=["node", "extra"], body=DocText(value="x")),
        ])
        formatter = Formatter(rules)
        with pytest.raises(FormatterError, match="Rule 'Identifier'"):
            formatter.format(Identifier(name="x"))

    def test_rule_with_zero_params_raises(self):
        rules = RuleFile(rules=[
            RuleDecl(name="Identifier", params=[], body=DocText(value="x")),
        ])
        formatter = Formatter(rules)
        with pytest.raises(FormatterError, match="Rule 'Identifier'"):
            formatter.format(Identifier(name="x"))


class TestFormatterCompileErrorWrapping:
    def test_compile_error_is_wrapped_as_formatter_error(self):
        rules = RuleFile(rules=[
            RuleDecl(name="Identifier", params=["node"], body=DocAttrRef(path=AP("node", "does_not_exist"))),
        ])
        formatter = Formatter(rules)
        with pytest.raises(FormatterError, match="Error compiling rule"):
            formatter.format(Identifier(name="x"))


class TestFormatterWithListAndBlocks:
    def _make_block_rules(self):
        return RuleFile(rules=[
            RuleDecl(name="Identifier", params=["node"], body=DocAttrRef(path=AP("node", "name"))),
            RuleDecl(name="NumberLiteral", params=["node"], body=DocAttrRef(path=AP("node", "value"))),
            RuleDecl(name="Assign", params=["node"], body=DocConcat(
                left=DocConcat(
                    left=DocConcat(left=DocAttrRef(path=AP("node", "target")), right=DocText(value=" = ")),
                    right=DocFormat(path=AP("node", "value")),
                ),
                right=DocText(value=";"),
            )),
            RuleDecl(name="Block", params=["node"], body=DocConcat(
                left=DocConcat(
                    left=DocText(value="{"),
                    right=DocConcat(
                        left=DocLine(),
                        right=DocList(path=AP("node", "stmts"), body=DocItem()),
                    ),
                ),
                right=DocConcat(left=DocLine(), right=DocText(value="}")),
            )),
        ])

    def test_block_with_multiple_statements(self):
        rules = self._make_block_rules()
        formatter = Formatter(rules)
        block = Block(stmts=[
            Assign(target="x", value=NumberLiteral(value=1)),
            Assign(target="y", value=Identifier(name="x")),
        ])
        result = formatter.format(block, width=80)
        assert result == "{\nx = 1;\ny = x;\n}"

    def test_empty_block(self):
        rules = self._make_block_rules()
        formatter = Formatter(rules)
        block = Block(stmts=[])
        result = formatter.format(block, width=80)
        assert result == "{\n\n}"


class TestRuleNameConvention:
    def test_rule_name_matches_python_class_name(self):
        rules = _make_minimal_rules()
        formatter = Formatter(rules)
        assert formatter._rule_name_for(Identifier(name="x")) == "Identifier"
        assert formatter._rule_name_for(NumberLiteral(value=1)) == "NumberLiteral"


class TestDslFileLoading:
    def setup_method(self):
        pytest.importorskip("parglare", reason="parglare nije instaliran - pokreni pip install parglare lokalno")

    def _dsl_path(self):
        import src.parglare_formatter.examples as examples_pkg
        return os.path.join(os.path.dirname(examples_pkg.__file__), "formatting_rules.dsl")

    def test_from_dsl_file_loads_and_formats(self):
        formatter = Formatter.from_dsl_file(self._dsl_path())
        node = BinaryOp(op="+", left=Identifier(name="a"), right=NumberLiteral(value=5))
        result = formatter.format(node)
        assert "a" in result and "5" in result

    def test_from_dsl_source_equivalent_to_from_dsl_file(self):
        with open(self._dsl_path(), "r", encoding="utf-8") as f:
            source = f.read()
        formatter = Formatter.from_dsl_source(source)
        node = Identifier(name="z")
        assert formatter.format(node) == "z"

    def test_format_ast_convenience_function(self):
        with open(self._dsl_path(), "r", encoding="utf-8") as f:
            source = f.read()
        node = NumberLiteral(value=7)
        assert format_ast(node, source) == "7"

class TestFormatterPrimitiveFallback:
    def test_bare_string_item_uses_fallback(self):
        rules = RuleFile(rules=[
            RuleDecl(name="FuncDef", params=["node"], body=DocList(
                path=AP("node", "params"), body=DocItem(), separator=DocText(value=", "),
            )),
        ])
        formatter = Formatter(rules)
        node = FuncDef(name="f", params=["a", "b", "c"], body=Block(stmts=[]))
        assert formatter.format(node) == "a, b, c"

    def test_bare_int_item_uses_fallback(self):
        class FakeIntListNode:
            def __init__(self, stmts):
                self.stmts = stmts

        rules = RuleFile(rules=[
            RuleDecl(name="FakeIntListNode", params=["node"], body=DocList(
                path=AP("node", "stmts"), body=DocItem(), separator=DocText(value=","),
            )),
        ])
        formatter = Formatter(rules)

        assert formatter.format(FakeIntListNode(stmts=[1, 2, 3])) == "1,2,3"

    def test_ast_node_without_rule_still_raises_not_fallback(self):
        formatter = Formatter(_make_minimal_rules())
        with pytest.raises(FormatterError):
            formatter.format(Call(callee="f", args=[]))

class TestFullProgramEndToEnd:
    def setup_method(self):
        pytest.importorskip("parglare", reason="parglare not installed")

    def _dsl_path(self):
        import src.parglare_formatter.examples as examples_pkg
        return os.path.join(os.path.dirname(examples_pkg.__file__), "formatting_rules.dsl")

    def _formatter(self):
        return Formatter.from_dsl_file(self._dsl_path())

    def test_basic_program_with_assign_call_and_if(self):
        formatter = self._formatter()
        program = Block(stmts=[
            Assign(
                target="x",
                value=BinaryOp(op="+", left=NumberLiteral(value=1), right=BinaryOp(op="*", left=NumberLiteral(value=2), right=NumberLiteral(value=3))),
            ),
            ExprStmt(expr=Call(callee="print", args=[Identifier(name="x"), NumberLiteral(value=42)])),
            If(
                cond=BinaryOp(op=">", left=Identifier(name="x"), right=NumberLiteral(value=0)),
                then_branch=Block(stmts=[Assign(target="y", value=Identifier(name="x"))]),
            ),
        ])
        result = formatter.format(program, width=40)
        assert result == "{\n  x = 1 + 2 * 3;\n  print(x, 42);\n  if (x > 0) {\n    y = x;\n  }\n}"

    def test_function_definition_with_for_loop(self):
        formatter = self._formatter()
        program = Block(stmts=[
            FuncDef(
                name="sum_range",
                params=["a", "b"],
                body=Block(stmts=[
                    Assign(target="total", value=NumberLiteral(value=0)),
                    For(
                        var="i", start=Identifier(name="a"), end=Identifier(name="b"),
                        body=Block(stmts=[
                            Assign(target="total", value=BinaryOp(op="+", left=Identifier(name="total"), right=Identifier(name="i"))),
                        ]),
                    ),
                ]),
            ),
        ])
        result = formatter.format(program, width=40)
        expected = (
            "{\n"
            "  function sum_range(a, b) {\n"
            "    total = 0;\n"
            "    for (i in a..b) {\n"
            "      total = total + i;\n"
            "    }\n"
            "  }\n"
            "}"
        )
        assert result == expected

    def test_all_ten_rules_are_exercised_across_both_programs(self):
        formatter = self._formatter()
        expected_rule_names = {
            "Identifier", "NumberLiteral", "BinaryOp", "Call", "Assign",
            "ExprStmt", "Block", "If", "For", "FuncDef",
        }
        assert expected_rule_names.issubset(set(formatter.rule_file._by_name.keys()))