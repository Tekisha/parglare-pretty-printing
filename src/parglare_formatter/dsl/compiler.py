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
import json
from typing import Any, Dict, Optional, Protocol

from ..document_model import Doc, text, line, softline, concat, nest, group, align, empty, concat_all
from .ast import (
    AttrPath, DocConcat, DocText, DocLine, DocSoftline, DocNest, DocGroup,
    DocAlign, DocFormat, DocList, DocItem, DocAttrRef, DocLower, DocUpper, DocJsonEscaped, DocOptional, DocWhen,
)

class FormatCallback(Protocol):
    def __call__(
        self,
        node: Any,
        *,
        context: Optional[str] = None,
    ) -> Doc:
        ...

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
            f"Available bindings: {list(bindings)}"
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

def _resolve_text_value(path: AttrPath, bindings: Dict[str, Any]) -> Any:
    """Resolve an attribute that will be inserted as text.

    None is rejected instead of being printed as the text "None"; use
    optional(path, ...) for attributes that may be absent.
    """
    value = _resolve_attr_path(path, bindings)

    if value is None:
        raise CompileError(
            f"Value at {str(path)!r} is None and cannot be inserted as "
            f"text; guard it with optional({path}, ...) if it may be absent"
        )

    return value

def _escape_json_string(value: str) -> str:
    s = json.dumps(value)
    return s[1:-1]

def _infer_separator(path, bindings, list_separators):
    """Separator literal for list(path, ...) from the grammar, or None."""
    if not list_separators or len(path.parts) < 2:
        return None
    *owner_parts, attr = path.parts
    first, *rest = owner_parts
    if first not in bindings:
        return None
    owner = bindings[first]
    for part in rest:
        owner = getattr(owner, part, None)
        if owner is None:
            return None
    return list_separators.get((type(owner).__name__, attr))


def compile_doc_expr(
    expr: Any,
    bindings: Dict[str, Any],
    format_node: FormatCallback,
    list_separators=None,
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
        left_doc = compile_doc_expr(expr.left, bindings, format_node, list_separators)
        right_doc = compile_doc_expr(expr.right, bindings, format_node, list_separators)
        return concat(left_doc, right_doc)

    elif isinstance(expr, DocNest):
        inner = compile_doc_expr(expr.body, bindings, format_node, list_separators)
        return nest(expr.indent, inner)

    elif isinstance(expr, DocGroup):
        inner = compile_doc_expr(expr.body, bindings, format_node, list_separators)
        return group(inner)

    elif isinstance(expr, DocAlign):
        inner = compile_doc_expr(expr.body, bindings, format_node, list_separators)
        return align(inner)

    elif isinstance(expr, DocOptional):
        value = _resolve_attr_path(expr.path, bindings)

        if value is None:
            return empty()

        return compile_doc_expr(
            expr.body,
            bindings,
            format_node,
            list_separators,
        )

    elif isinstance(expr, DocFormat):
        target_node = _resolve_attr_path(expr.path, bindings)

        if expr.context is None:
            return format_node(target_node)

        return format_node(
            target_node,
            context=expr.context,
        )

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
            docs.append(compile_doc_expr(expr.body, item_bindings, format_node, list_separators))
        if not docs:
            return empty()

        if expr.separator is not None:
            separator_doc = compile_doc_expr(expr.separator, bindings, format_node, list_separators)
        else:
            literal = _infer_separator(expr.path, bindings, list_separators)
            separator_doc = (
                concat(text(literal), softline())
                if literal is not None
                else line()
            )

        result = docs[0]
        for d in docs[1:]:
            result = concat(result, concat(separator_doc, d))
        return result

    elif isinstance(expr, DocItem):
        if ITEM_KEY not in bindings:
            raise CompileError(
                "'item' used outside list(...) body - 'item' is valid "
                "only inside second argument of list(path, <here>)"
            )
        return format_node(bindings[ITEM_KEY])

    elif isinstance(expr, DocWhen):
        value = _resolve_attr_path(expr.path, bindings)

        if isinstance(value, str) and value == expr.value:
            return compile_doc_expr(
                expr.then, bindings, format_node, list_separators
            )

        if expr.otherwise is not None:
            return compile_doc_expr(
                expr.otherwise, bindings, format_node, list_separators
            )

        return empty()

    elif isinstance(expr, DocLower):
        value = _resolve_text_value(expr.path, bindings)
        return text(str(value).lower())

    elif isinstance(expr, DocUpper):
        value = _resolve_text_value(expr.path, bindings)
        return text(str(value).upper())

    elif isinstance(expr, DocJsonEscaped):
        value = _resolve_text_value(expr.path, bindings)
        s = _escape_json_string(str(value))
        return text(s)

    elif isinstance(expr, DocAttrRef):
        value = _resolve_text_value(expr.path, bindings)
        return text(str(value))

    else:
        raise CompileError(f"Unknown DocExpr type: {type(expr).__name__!r}")