from cparser import CParser

from .tree_adapter import CNode, CToken, adapt_tree


SOURCE = """\
int main() {
    return 0;
}
"""


def dump(node, indent=0):
    prefix = " " * indent

    if isinstance(node, CToken):
        print(f"{prefix}{node.kind}: {node.value!r}")
        return

    if isinstance(node, CNode):
        print(f"{prefix}{type(node).__name__}")
        for child in node.children:
            dump(child, indent + 2)
        return

    raise TypeError(f"Unexpected node: {type(node).__name__}")


def main():
    tree = CParser().parse(SOURCE)
    root = adapt_tree(tree)
    dump(root)


if __name__ == "__main__":
    main()