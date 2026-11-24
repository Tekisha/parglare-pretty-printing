from dataclasses import replace

import pytest
from cparser import CParser

from examples.c_example.tree_adapter import (
    CNode,
    CToken,
    SourceInfo,
    adapt_tree,
    iter_tokens,
    tree_signature,
)


SOURCE = """\
int main() {
    return 0;
}
"""


@pytest.fixture(scope="module")
def adapted_root():
    tree = CParser().parse(SOURCE)
    return adapt_tree(tree)


def test_root_uses_grammar_rule_name(adapted_root):
    assert isinstance(adapted_root, CNode)
    assert type(adapted_root).__name__ == "translation_unit"
    assert len(adapted_root.children) == 1

    child = adapted_root.children[0]
    assert type(child).__name__ == "external_decl_1"


def test_preserves_terminal_kinds_and_text(adapted_root):
    tokens = list(iter_tokens(adapted_root))

    assert [(token.kind, token.value) for token in tokens] == [
        ("int", "int"),
        ("id", "main"),
        ("(", "("),
        (")", ")"),
        ("{", "{"),
        ("return", "return"),
        ("int_const", "0"),
        (";", ";"),
        ("}", "}"),
    ]


def test_terminal_positions_match_source(adapted_root):
    for token in iter_tokens(adapted_root):
        start = token.source.start
        end = token.source.end

        assert 0 <= start <= end <= len(SOURCE)
        assert SOURCE[start:end] == token.value


def test_root_covers_program(adapted_root):
    assert adapted_root.source.start == SOURCE.index("int")
    assert adapted_root.source.end == SOURCE.rindex("}") + 1


def test_signature_ignores_source_metadata():
    original = CToken(
        kind="id",
        value="main",
        source=SourceInfo(start=4, end=8),
    )

    moved = replace(
        original,
        source=SourceInfo(
            start=20,
            end=24,
            layout_before="\n    ",
        ),
    )

    assert original == moved
    assert tree_signature(original) == tree_signature(moved)


def test_signature_preserves_terminal_kind():
    source = SourceInfo(start=0, end=1)

    identifier = CToken(kind="id", value="x", source=source)
    other_terminal = CToken(kind="other", value="x", source=source)

    assert tree_signature(identifier) != tree_signature(other_terminal)


def test_whitespace_does_not_change_syntax_signature(adapted_root):
    compact = adapt_tree(
        CParser().parse("int main(){return 0;}")
    )

    assert tree_signature(compact) == tree_signature(adapted_root)


def test_changed_value_changes_syntax_signature(adapted_root):
    changed = adapt_tree(
        CParser().parse("int main(){return 1;}")
    )

    assert tree_signature(changed) != tree_signature(adapted_root)


def test_changed_identifier_changes_syntax_signature(adapted_root):
    changed = adapt_tree(
        CParser().parse("int other(){return 0;}")
    )

    assert tree_signature(changed) != tree_signature(adapted_root)


def test_node_classes_are_reused(adapted_root):
    other = adapt_tree(
        CParser().parse("int other(){return 0;}")
    )

    assert type(other) is type(adapted_root)


def test_adapter_rejects_unsupported_objects():
    with pytest.raises(TypeError, match="Unsupported parse-tree node"):
        adapt_tree(object())