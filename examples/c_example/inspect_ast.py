from cparser import CParser


SOURCE = """\
int main() {
    return 0;
}
"""


def dump_tree(node, indent=0):
    prefix = " " * indent

    if isinstance(node, (list, tuple)):
        print(f"{prefix}{type(node).__name__}")
        for child in node:
            dump_tree(child, indent + 2)
        return

    production = getattr(node, "production", None)
    children = getattr(node, "children", None)

    if production is not None and children is not None:
        print(f"{prefix}{production.symbol.name}")
        for child in children:
            dump_tree(child, indent + 2)
        return

    symbol = getattr(node, "symbol", None)
    if symbol is not None and hasattr(node, "value"):
        print(f"{prefix}{symbol.name}: {node.value!r}")
        return

    print(f"{prefix}{type(node).__name__}: {node!r}")


def main():
    parser = CParser()
    tree = parser.parse(SOURCE)

    print("=== RESULT TYPE ===")
    print(f"{type(tree).__module__}.{type(tree).__name__}")

    print("\n=== PARSE TREE ===")
    dump_tree(tree)


if __name__ == "__main__":
    main()