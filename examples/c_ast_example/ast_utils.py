from typing import Any

from pycparser import c_ast


def ast_signature(value: Any) -> tuple:
    """Return an AST signature excluding source coordinates."""
    if isinstance(value, c_ast.Node):
        field_names = set()

        for cls in type(value).__mro__:
            slots = getattr(cls, "__slots__", ())
            if isinstance(slots, str):
                slots = (slots,)

            field_names.update(slots)

        field_names.difference_update(
            {"coord", "__weakref__", "__dict__"}
        )

        fields = tuple(
            (
                name,
                ast_signature(getattr(value, name)),
            )
            for name in sorted(field_names)
        )

        return (
            "node",
            type(value).__name__,
            fields,
        )

    if isinstance(value, list):
        return (
            "list",
            tuple(ast_signature(item) for item in value),
        )

    if isinstance(value, tuple):
        return (
            "tuple",
            tuple(ast_signature(item) for item in value),
        )

    if value is None or isinstance(value, (str, int, float, bool)):
        return (
            "scalar",
            type(value).__name__,
            value,
        )

    raise TypeError(
        f"Unsupported AST field value: {type(value).__name__}"
    )