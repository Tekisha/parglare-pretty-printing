"""
Compiles DocExpr AST (dsl_ast.py) into Doc (document_model.py), evaluating
it over a concrete AST node (any Python object, e.g., an instance from
ast_nodes.py).

Key idea: DocExpr tree is a "program" describing HOW to format ONE AST
node type. To format an ENTIRE AST tree (e.g., Block with a list of Stmts,
where each Stmt may be a different concrete type), the compiler must be
RECURSIVE via a formatter callback: when encountering `format(path)`, it
doesn't know the node type at `path` in advance so it accepts a
`format_node` callback (typically formatter.py's `format_node(node)`) which
finds the APPROPRIATE rule (by class name) for the given concrete node
and recursively compiles/renders it.

Attribute resolution (AttrPath -> value) works over a `bindings` map
(param_name -> value). Bindings ALWAYS contain rule parameters (usually
"node"), and INSIDE list(...) body additionally contains key "item" ->
current list item. This means AttrPath("item") or AttrPath("item", ...)
is syntactically IDENTICAL to resolving any other parameter - "item" is
parsed as AttrPath in grammar (Phase 2) when used inside format(...)
(e.g., format(item)), and as a separate DocItem node when used BARE as
DocTerm (e.g., list(node.stmts, item) without format() wrapper). Both
cases compile to the same: recursive format_node(item_value) call.
"""

from typing import Any, Callable, Dict

from ..document_model import Doc, text, line, softline, concat, nest, group, align, empty, concat_all
from .ast import (
    AttrPath, DocConcat, DocText, DocLine, DocSoftline, DocNest, DocGroup,
    DocAlign, DocFormat, DocList, DocItem, DocAttrRef,
)

# Callback signature: (node: Any) -> Doc
FormatCallback = Callable[[Any], Doc]

ITEM_KEY = "item"


class CompileError(Exception):
    """Error during DocExpr compilation over a concrete AST node (e.g.,
    non-existent attribute, wrong type for list(), unknown parameter)."""
    pass


def _resolve_attr_path(path: AttrPath, bindings: Dict[str, Any]) -> Any:
    """
    Resolves AttrPath (e.g., 'node.left.value' or 'item') over current
    bindings (param_name -> value mapping, e.g.,
    {"node": <BinaryOp instance>, "item": <current list item>}).

    First part of path MUST be a key from `bindings` (rule parameter name,
    or "item" if inside list() body), and the rest are .getattr chains
    over that value.
    """
    if not path.parts:
        raise CompileError("AttrPath is empty - ivalid DSL AST")

    first, *rest = path.parts
    if first not in bindings:
        raise CompileError(
            f"Unknown parame {first!r} in AttrPath {str(path)!r}. "
            f"Available params: {list(bindings)}"
        )
    value = bindings[first]
    for attr in rest:
        if not hasattr(value, attr):
            raise CompileError(
                f"Object type {type(value).__name__!r} does not have attribute {attr!r} "
                f"(full path: {str(path)!r})"
            )
        value = getattr(value, attr)
    return value


def compile_doc_expr(
    expr: Any,
    bindings: Dict[str, Any],
    format_node: FormatCallback,
) -> Doc:
    """
    Recursively compiles DocExpr AST node (expr) into Doc, using:
      - `bindings`     - param_name -> concrete value mapping
                         (e.g., {"node": <current AST node>}, and inside
                         list() body also {"item": <current item>})
      - `format_node`  - callback for recursively formatting child nodes
                         found via format(...) or item/list(...)
    """
    if isinstance(expr, DocText):
        return text(expr.value)

    elif isinstance(expr, DocLine):
        return line()

    elif isinstance(expr, DocSoftline):
        return softline()

    elif isinstance(expr, DocConcat):
        left_doc = compile_doc_expr(expr.left, bindings, format_node)
        right_doc = compile_doc_expr(expr.right, bindings, format_node)
        return concat(left_doc, right_doc)

    elif isinstance(expr, DocNest):
        inner = compile_doc_expr(expr.body, bindings, format_node)
        return nest(expr.indent, inner)

    elif isinstance(expr, DocGroup):
        inner = compile_doc_expr(expr.body, bindings, format_node)
        return group(inner)

    elif isinstance(expr, DocAlign):
        inner = compile_doc_expr(expr.body, bindings, format_node)
        return align(inner)

    elif isinstance(expr, DocFormat):
        target_node = _resolve_attr_path(expr.path, bindings)
        return format_node(target_node)

    elif isinstance(expr, DocList):
        collection = _resolve_attr_path(expr.path, bindings)
        try:
            items = list(collection)
        except TypeError:
            raise CompileError(
                f"list({expr.path}, ...) expects iterable, got "
                f"{type(collection).__name__!r}"
            )
        docs = []
        for item in items:
            item_bindings = dict(bindings)
            item_bindings[ITEM_KEY] = item
            docs.append(compile_doc_expr(expr.body, item_bindings, format_node))
        if not docs:
            return empty()
        result = docs[0]
        for d in docs[1:]:
            result = concat(result, concat(line(), d))
        return result

    elif isinstance(expr, DocItem):
        if ITEM_KEY not in bindings:
            raise CompileError(
                "'item' used outside list(...) body - 'item' is valid "
                "only inside second argument of list(path, <here>)"
            )
        return format_node(bindings[ITEM_KEY])

    elif isinstance(expr, DocAttrRef):
        value = _resolve_attr_path(expr.path, bindings)
        return text(str(value))

    else:
        raise CompileError(f"Unknown DocExpr type: {type(expr).__name__!r}")