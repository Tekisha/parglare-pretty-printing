from dataclasses import dataclass, field
from typing import Union

from parglare.trees import NodeNonTerm, NodeTerm


@dataclass(frozen=True)
class SourceInfo:
    """Source metadata excluded from structural comparisons."""

    start: int
    end: int
    layout_before: str = ""


@dataclass(frozen=True)
class CToken:
    """A terminal with its grammar name and original text."""

    kind: str
    value: str
    source: SourceInfo = field(compare=False, repr=False)


@dataclass(frozen=True)
class CNode:
    """A nonterminal preserving the order of its syntax children."""

    children: tuple["CElement", ...]
    production_rhs: tuple[str, ...]
    source: SourceInfo = field(compare=False, repr=False)


CElement = Union[CNode, CToken]

_NODE_TYPES: dict[str, type[CNode]] = {}


def _node_type(rule_name: str) -> type[CNode]:
    """Cache one formatter node class per grammar rule name."""
    if rule_name not in _NODE_TYPES:
        _NODE_TYPES[rule_name] = type(
            rule_name,
            (CNode,),
            {
                "__module__": __name__,
                "__slots__": (),
            },
        )

    return _NODE_TYPES[rule_name]


def _source_info(tree: Union[NodeNonTerm, NodeTerm]) -> SourceInfo:
    layout = getattr(tree, "layout_content", "") or ""

    if not isinstance(layout, str):
        raise TypeError(
            "Expected textual layout_content, "
            f"got {type(layout).__name__}"
        )

    return SourceInfo(
        start=tree.start_position,
        end=tree.end_position,
        layout_before=layout,
    )


def adapt_tree(tree: Union[NodeNonTerm, NodeTerm]) -> CElement:
    """Copy syntax data without retaining parser or grammar objects."""
    if isinstance(tree, NodeTerm):
        if not isinstance(tree.value, str):
            raise TypeError(
                "Expected a textual C terminal, "
                f"got {type(tree.value).__name__}"
            )

        return CToken(
            kind=tree.symbol.name,
            value=tree.value,
            source=_source_info(tree),
        )

    if isinstance(tree, NodeNonTerm):
        node_class = _node_type(tree.production.symbol.name)

        return node_class(
            children=tuple(adapt_tree(child) for child in tree.children),
            production_rhs=tuple(
                symbol.name for symbol in tree.production.rhs
            ),
            source=_source_info(tree),
        )

    raise TypeError(
        f"Unsupported parse-tree node: {type(tree).__name__}"
    )


def tree_signature(node: CElement) -> tuple:
    """Return syntax structure, excluding positions and layout."""
    if isinstance(node, CToken):
        return ("terminal", node.kind, node.value)

    if isinstance(node, CNode):
        return (
            "nonterminal",
            type(node).__name__,
            node.production_rhs,
            tuple(tree_signature(child) for child in node.children),
        )

    raise TypeError(
        f"Unsupported adapted node: {type(node).__name__}"
    )


def iter_tokens(node: CElement):
    """Yield terminals in source order."""
    if isinstance(node, CToken):
        yield node
        return

    if isinstance(node, CNode):
        for child in node.children:
            yield from iter_tokens(child)
        return

    raise TypeError(
        f"Unsupported adapted node: {type(node).__name__}"
    )