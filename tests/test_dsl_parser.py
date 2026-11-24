import pytest

parglare = pytest.importorskip(
    "parglare", reason="parglare has not been installed - run 'pip install parglare' locally"
)
from parglare.exceptions import SyntaxError as ParglareSyntaxError
from parglare_formatter.dsl.grammar import DSL_GRAMMAR
from parglare_formatter.dsl.parser import parse_dsl, build_parser, get_grammar
from parglare_formatter.dsl.ast import (
    RuleFile, RuleDecl, AttrPath,
    DocConcat, DocText, DocLine, DocSoftline, DocNest, DocGroup, DocAlign,
    DocFormat, DocList, DocItem, DocAttrRef,
)


class TestGrammarLoads:
    def test_grammar_compiles_without_errors(self):
        grammar = get_grammar()
        assert grammar is not None

    def test_parser_builds_without_errors(self):
        parser = build_parser()
        assert parser is not None


class TestSimpleRules:
    def test_single_text_rule(self):
        src = 'rule greet = text("hello");'
        result = parse_dsl(src)
        assert isinstance(result, RuleFile)
        assert len(result.rules) == 1
        rule = result.rules[0]
        assert isinstance(rule, RuleDecl)
        assert rule.name == "greet"
        assert isinstance(rule.body, DocText)
        assert rule.body.value == "hello"

    def test_rule_has_no_params_field(self):
        rule = parse_dsl('rule constant = text("k");').rules[0]
        assert rule.name == "constant"
        assert not hasattr(rule, "params")


    def test_rule_with_parameter_list_is_rejected(self):
        with pytest.raises(ParglareSyntaxError):
            parse_dsl('rule greet(node) = text("hello");')

    def test_multiple_rules_in_file(self):
        src = (
            'rule a = text("A");\n'
            'rule b = text("B");\n'
        )
        result = parse_dsl(src)
        assert len(result.rules) == 2
        names = [r.name for r in result.rules]
        assert names == ["a", "b"]
        assert len(result) == 2
        assert "a" in result
        assert "b" in result
        assert "c" not in result
        assert result.get_rule("a").name == "a"
        assert result.get_rule("b").name == "b"

    def test_get_rule_missing_raises_keyerror(self):
        src = 'rule a = text("A");'
        result = parse_dsl(src)
        with pytest.raises(KeyError, match="a"):
            result.get_rule("nonexistent")


class TestDocTermVariants:
    def test_line_term(self):
        src = 'rule r = line();'
        rule = parse_dsl(src).rules[0]
        assert isinstance(rule.body, DocLine)

    def test_softline_term(self):
        src = 'rule r = softline();'
        rule = parse_dsl(src).rules[0]
        assert isinstance(rule.body, DocSoftline)

    def test_nest_term(self):
        src = 'rule r = nest(2, text("x"));'
        rule = parse_dsl(src).rules[0]
        assert isinstance(rule.body, DocNest)
        assert rule.body.indent == 2
        assert isinstance(rule.body.body, DocText)
        assert rule.body.body.value == "x"

    def test_group_term(self):
        src = 'rule r = group(text("x"));'
        rule = parse_dsl(src).rules[0]
        assert isinstance(rule.body, DocGroup)
        assert isinstance(rule.body.body, DocText)

    def test_align_term(self):
        src = 'rule r = align(text("x"));'
        rule = parse_dsl(src).rules[0]
        assert isinstance(rule.body, DocAlign)
        assert isinstance(rule.body.body, DocText)

    def test_format_term_simple_attr(self):
        src = 'rule r = format(node);'
        rule = parse_dsl(src).rules[0]
        assert isinstance(rule.body, DocFormat)
        assert str(rule.body.path) == "node"

    def test_format_term_nested_attr(self):
        src = 'rule r = format(node.left.value);'
        rule = parse_dsl(src).rules[0]
        assert isinstance(rule.body, DocFormat)
        assert rule.body.path.parts == ["node", "left", "value"]
        assert str(rule.body.path) == "node.left.value"

    def test_list_term(self):
        src = 'rule r = list(node.stmts, format(item));'
        rule = parse_dsl(src).rules[0]
        assert isinstance(rule.body, DocList)
        assert rule.body.path.parts == ["node", "stmts"]
        assert isinstance(rule.body.body, DocFormat)
        assert isinstance(rule.body.body.path, AttrPath)
        assert str(rule.body.body.path) == "item"

    def test_item_term(self):
        src = 'rule r = item;'
        rule = parse_dsl(src).rules[0]
        assert isinstance(rule.body, DocItem)

    def test_bare_attrpath_term(self):
        src = 'rule r = node.value;'
        rule = parse_dsl(src).rules[0]
        assert isinstance(rule.body, DocAttrRef)
        assert str(rule.body.path) == "node.value"


class TestConcatOperator:
    def test_two_way_concat(self):
        src = 'rule r = text("a") ++ text("b");'
        rule = parse_dsl(src).rules[0]
        assert isinstance(rule.body, DocConcat)
        assert isinstance(rule.body.left, DocText)
        assert rule.body.left.value == "a"
        assert isinstance(rule.body.right, DocText)
        assert rule.body.right.value == "b"

    def test_left_associative_chain(self):
        src = 'rule r = text("a") ++ text("b") ++ text("c");'
        rule = parse_dsl(src).rules[0]
        assert isinstance(rule.body, DocConcat)
        assert isinstance(rule.body.right, DocText)
        assert rule.body.right.value == "c"
        inner = rule.body.left
        assert isinstance(inner, DocConcat)
        assert inner.left.value == "a"
        assert inner.right.value == "b"


class TestRealisticRule:
    def test_binary_op_style_rule(self):
        src = 'rule binary_op = format(node.left) ++ text(" + ") ++ format(node.right);'
        rule = parse_dsl(src).rules[0]
        assert rule.name == "binary_op"
        top = rule.body
        assert isinstance(top, DocConcat)
        assert isinstance(top.right, DocFormat)
        assert str(top.right.path) == "node.right"
        mid = top.left
        assert isinstance(mid, DocConcat)
        assert isinstance(mid.left, DocFormat)
        assert str(mid.left.path) == "node.left"
        assert isinstance(mid.right, DocText)
        assert mid.right.value == " + "

    def test_block_style_rule_with_nest_and_list(self):
        src = (
            'rule block = text("{") ++ '
            'nest(2, line() ++ list(node.stmts, format(item))) ++ '
            'line() ++ text("}");'
        )
        rule = parse_dsl(src).rules[0]
        assert rule.name == "block"
        top = rule.body
        assert isinstance(top, DocConcat)
        assert isinstance(top.right, DocText)
        assert top.right.value == "}"

    def test_call_rule_with_comma_separated_args(self):
        q = chr(34)
        src = (
            "rule Call = node.callee ++ text(" + q + "(" + q + ") ++ "
            "list(node.args, item, text(" + q + ", " + q + ")) ++ text(" + q + ")" + q + ");"
        )
        rule = parse_dsl(src).rules[0]
        assert rule.name == "Call"


class TestWhitespaceHandling:
    def test_rule_with_varied_whitespace_and_newlines(self):
        src = '\n        rule   spaced   =\n            text( "hi" )   ++\n            line(  )\n        ;\n        '
        result = parse_dsl(src)
        rule = result.rules[0]
        assert rule.name == "spaced"
        assert isinstance(rule.body, DocConcat)
        assert rule.body.left.value == "hi"
        assert isinstance(rule.body.right, DocLine)


class TestStringLiteralEscaping:
    def test_string_with_escaped_quote(self):
        src = r'rule r = text("say \"hi\"");'
        rule = parse_dsl(src).rules[0]
        assert isinstance(rule.body, DocText)
        assert rule.body.value == 'say "hi"'

class TestListWithoutSeparator:
    def test_list_two_args_separator_is_none(self):
        src = "rule r = list(node.stmts, format(item));"
        rule = parse_dsl(src).rules[0]
        assert isinstance(rule.body, DocList)
        assert rule.body.separator is None


class TestListWithSeparator:
    def test_list_three_args_separator_is_set(self):
        q = chr(34)
        src = "rule r = list(node.args, format(item), text(" + q + ", " + q + "));"
        rule = parse_dsl(src).rules[0]
        assert isinstance(rule.body, DocList)
        assert rule.body.separator is not None
        assert isinstance(rule.body.separator, DocText)
        assert rule.body.separator.value == ", "

    def test_list_with_line_separator(self):
        src = "rule r = list(node.args, format(item), line());"
        rule = parse_dsl(src).rules[0]
        assert isinstance(rule.body.separator, DocLine)

    def test_list_with_softline_separator(self):
        src = "rule r = list(node.args, format(item), softline());"
        rule = parse_dsl(src).rules[0]
        assert isinstance(rule.body.separator, DocSoftline)