from cparser import CParser
from examples.c_example.tree_adapter import (
    CNode,
    adapt_tree,
    tree_signature,
)
from examples.c_example.tree_adapter import iter_tokens


MINIMAL_C_SOURCE = """\
int main() {
    return 0;
}
"""


def test_parse_minimal_c_program():
    parser = CParser()

    ast = parser.parse(MINIMAL_C_SOURCE)

    assert ast is not None

def test_adapt_minimal_c_program():
    parser = CParser()
    tree = parser.parse(MINIMAL_C_SOURCE)

    root = adapt_tree(tree)

    assert isinstance(root, CNode)
    assert type(root).__name__ == "translation_unit"
    assert len(root.children) == 1
    assert type(root.children[0]).__name__ == "external_decl_1"


def test_adapt_terminal_preserves_text():
    parser = CParser()
    root = adapt_tree(parser.parse(MINIMAL_C_SOURCE))

    assert [token.value for token in iter_tokens(root)] == [
        "int",
        "main",
        "(",
        ")",
        "{",
        "return",
        "0",
        ";",
        "}",
    ]


def test_signature_ignores_whitespace():
    compact = adapt_tree(
        CParser().parse("int main(){return 0;}")
    )
    spaced = adapt_tree(
        CParser().parse(MINIMAL_C_SOURCE)
    )

    assert tree_signature(compact) == tree_signature(spaced)


def test_signature_detects_changed_return_value():
    zero = adapt_tree(
        CParser().parse("int main(){return 0;}")
    )
    one = adapt_tree(
        CParser().parse("int main(){return 1;}")
    )

    assert tree_signature(zero) != tree_signature(one)