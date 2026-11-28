from pathlib import Path

import pytest
from parglare.exceptions import SyntaxError

from parglare_formatter.dsl.ast import DocText
from parglare_formatter.dsl.parser import parse_dsl
from parglare_formatter.formatter import Formatter

ROOT = Path(__file__).resolve().parents[1]


def test_comments_do_not_change_the_parsed_rules():
    plain = parse_dsl('rule A = "a" ++ "b";')
    commented = parse_dsl(
        """
        // leading comment
        rule A = // after the equals sign
            "a" // after the first operand
            ++ "b"; // after the rule
        // trailing comment
        """
    )

    assert plain == commented


def test_comment_at_end_of_file_without_newline():
    rules = parse_dsl('rule A = "a"; // no newline after this')

    assert len(rules) == 1


def test_comment_between_rule_names():
    rules = parse_dsl(
        """
        rule A, // first
             B = // second
            "x";
        """
    )

    assert [r.name for r in rules.rules] == ["A", "B"]


def test_comment_markers_inside_string_are_text():
    body = parse_dsl('rule A = "// not a comment";').get_rule("A").body

    assert isinstance(body, DocText)
    assert body.value == "// not a comment"


def test_comment_may_contain_quotes_and_code():
    rules = parse_dsl(
        """
        // rule B = "oops";  text("x") ++ "y"
        rule A = "a";
        """
    )

    assert len(rules) == 1
    assert "B" not in rules


def test_windows_line_endings():
    rules = parse_dsl('// c\r\nrule A = "a"; // d\r\nrule B = "b";\r\n')

    assert len(rules) == 2


def test_file_with_only_comments_is_an_error():
    with pytest.raises(SyntaxError):
        parse_dsl("// nothing here\n")


def test_formatter_works_with_commented_rules():
    formatter = Formatter.from_dsl_source(
        """
        // wraps a value in brackets
        rule Box = "[" ++ node.value ++ "]"; // done
        """
    )

    class Box:
        def __init__(self, value):
            self.value = value

    assert formatter.format(Box(5)) == "[5]"


@pytest.mark.parametrize(
    "path",
    sorted(ROOT.glob("examples/**/formatting_rules.dsl")),
    ids=lambda p: str(p.relative_to(ROOT)),
)
def test_existing_rule_files_still_parse(path):
    parse_dsl(path.read_text(encoding="utf-8"))