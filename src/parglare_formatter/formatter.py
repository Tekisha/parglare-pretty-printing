"""
Main entry point of the system: AST → Doc → text.

Formatter connects all previous phases:
  - Phase 2 (dsl_parser.py)   - parses .dsl file into RuleFile AST
  - Phase 6 (dsl_compiler.py) - compiles a SINGLE rule (DocExpr) to Doc
                                for a concrete AST node
  - Phase 3 (layout_engine.py) - renders Doc to final string

The key responsibility of formatter.py (not covered in previous phases) is
RULE SELECTION by Python class name of the concrete AST node. This is the
`format_node` callback that dsl_compiler.py calls recursively for
`format(...)`, `list(...)`, and bare `item`.

Convention: DSL rule `rule BinaryOp(node) = ...` applies to EVERY AST node
whose Python class is `BinaryOp` (type(node).__name__). The first parameter
name of the rule (typically "node") becomes the key in the bindings map
to which the node is bound.
"""

from typing import Any, Dict, Optional

from src.parglare_formatter.dsl.ast import RuleFile
from src.parglare_formatter.dsl.compiler import compile_doc_expr, CompileError
from src.parglare_formatter.dsl.parser import parse_dsl
from src.parglare_formatter.document_model import Doc, text
from src.parglare_formatter.layout_engine import render


class FormatterError(Exception):
    """Raised when formatting fails e.g., no DSL rule for a node type,
    or a rule has wrong number of parameters."""
    pass


class Formatter:
    """
    Main entry point: loads DSL rules and formats AST nodes by selecting
    the rule whose name matches the node's Python class.

    Example:

        formatter = Formatter.from_dsl_file("formatting_rules.dsl")
        text = formatter.format(my_ast_root, width=80)
    """
    _PRIMITIVE_TYPES = (str, int, float, bool)

    def __init__(self, rule_file: RuleFile):
        self.rule_file = rule_file

    @classmethod
    def from_dsl_source(cls, source: str) -> "Formatter":
        """Convenience constructor: parse DSL source and create Formatter."""
        return cls(parse_dsl(source))

    @classmethod
    def from_dsl_file(cls, path: str) -> "Formatter":
        """Load .dsl file from disk and create Formatter."""
        with open(path, "r", encoding="utf-8") as f:
            source = f.read()
        return cls.from_dsl_source(source)

    def _rule_name_for(self, node: Any) -> str:
        """Return DSL rule name for given AST node - by convention,
        the node's Python class name (type(node).__name__)."""
        return type(node).__name__

    def format_node(self, node: Any) -> Doc:
        """
        Compile single AST node to Doc by selecting matching DSL rule.
        This is the `format_node` callback that dsl_compiler.compile_doc_expr
        calls recursively for format(...), list(...), and bare item.
        """
        rule_name = self._rule_name_for(node)
        if rule_name not in self.rule_file:
            if isinstance(node, self._PRIMITIVE_TYPES):
                return text(str(node))

            raise FormatterError(
                f"No DSL rule for node type {rule_name!r}. "
                f"Define 'rule {rule_name}(node) = ...;' in .dsl file."
            )
        rule = self.rule_file.get_rule(rule_name)

        if len(rule.params) != 1:
            raise FormatterError(
                f"Rule {rule_name!r} must have exactly ONE parameter "
                f"(convention: 'node'), but has {len(rule.params)}: {rule.params}"
            )
        param_name = rule.params[0]
        bindings: Dict[str, Any] = {param_name: node}

        try:
            return compile_doc_expr(rule.body, bindings, self.format_node)
        except CompileError as e:
            raise FormatterError(
                f"Error compiling rule {rule_name!r} for node {node!r}: {e}"
            ) from e

    def format(self, node: Any, width: int = 80) -> str:
        """
        Format given AST node (and all sub-nodes, recursively) to final
        string using layout_engine.render() with given line width.
        """
        doc = self.format_node(node)
        return render(doc, width=width)


def format_ast(node: Any, dsl_source: str, width: int = 80) -> str:
    """Functional facade: parse DSL source and immediately format given
    node in one call, useful for one-off usage / scripts."""
    formatter = Formatter.from_dsl_source(dsl_source)
    return formatter.format(node, width=width)