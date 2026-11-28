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

Convention: DSL rule `rule BinaryOp = ...` applies to EVERY AST node
whose Python class is `BinaryOp` (type(node).__name__).
"""

from typing import Any, Dict, Optional, List

from parglare_formatter.dsl.ast import RuleFile, IMPLICIT_PARAM, DocFormat
from parglare_formatter.dsl.compiler import compile_doc_expr, CompileError
from parglare_formatter.dsl.parser import parse_dsl
from parglare_formatter.document_model import Doc, text
from parglare_formatter.layout_engine import render
from parglare_formatter.grammar_introspection import extract_list_separators

from dataclasses import fields, is_dataclass


class FormatterError(Exception):
    """Raised when formatting fails e.g., no DSL rule for a node type"""
    pass

def _walk(expr):
    """Yield every DSL AST node reachable from `expr`."""
    yield expr
    if is_dataclass(expr):
        for f in fields(expr):
            value = getattr(expr, f.name)
            children = value if isinstance(value, list) else [value]
            for child in children:
                if is_dataclass(child):
                    yield from _walk(child)


class Formatter:
    """
    Main entry point: loads DSL rules and formats AST nodes by selecting
    the rule whose name matches the node's Python class.

    Example:

        formatter = Formatter.from_dsl_file("formatting_rules.dsl")
        text = formatter.format(my_ast_root, width=80)
    """
    _PRIMITIVE_TYPES = (str, int, float, bool)

    def __init__(self, rule_file: RuleFile, grammar=None):
        self.rule_file = rule_file
        self.list_separators = (
            extract_list_separators(grammar) if grammar is not None else {}
        )

    @classmethod
    def from_dsl_source(cls, source: str, grammar=None) -> "Formatter":
        return cls(parse_dsl(source), grammar=grammar)

    @classmethod
    def from_dsl_file(cls, path: str, grammar=None) -> "Formatter":
        with open(path, "r", encoding="utf-8") as f:
            return cls.from_dsl_source(f.read(), grammar=grammar)

    def _rule_name_for(
        self,
        node: Any,
        context: Optional[str] = None,
    ) -> str:
        """Pick the most specific rule: context+class, context default,
        then the plain class rule."""
        base_name = type(node).__name__

        if context is not None:
            for candidate in (
                f"{context}_{base_name}",
                f"{context}_default",
            ):
                if candidate in self.rule_file:
                    return candidate

        return base_name

    def format_node(
        self,
        node: Any,
        *,
        context: Optional[str] = None,
    ) -> Doc:
        """
        Compile a node using a contextual rule when available.

        Context is local to this invocation. Recursive calls use their
        own explicitly requested context, or the default rule.
        """
        rule_name = self._rule_name_for(node, context)

        if rule_name not in self.rule_file:
            if isinstance(node, self._PRIMITIVE_TYPES):
                return text(str(node))

            raise FormatterError(
                f"No DSL rule for node type {type(node).__name__!r} "
                f"in context {context!r}. "
                f"Define 'rule {rule_name} = ...;' in .dsl file."
            )

        rule = self.rule_file.get_rule(rule_name)
        bindings: Dict[str, Any] = {IMPLICIT_PARAM: node}

        try:
            return compile_doc_expr(
                rule.body,
                bindings,
                self.format_node,
                list_separators=self.list_separators,
            )
        except CompileError as e:
            raise FormatterError(
                f"Error compiling rule {rule_name!r} "
                f"for node {node!r}: {e}"
            ) from e

    def format(self, node: Any, width: int = 80) -> str:
        """
        Format given AST node (and all sub-nodes, recursively) to final
        string using layout_engine.render() with given line width.
        """
        doc = self.format_node(node)
        return render(doc, width=width)

    def check(self) -> List[str]:
        """Report likely mistakes in the rule file (never raises)."""
        rules = self.rule_file.rules
        names = [rule.name for rule in rules]

        used = {}
        for rule in rules:
            for expr in _walk(rule.body):
                if isinstance(expr, DocFormat) and expr.context:
                    used.setdefault(expr.context, rule.name)

        declared = {}
        for rule in rules:
            if rule.context:
                declared.setdefault(rule.context, rule.name)

        problems = []

        for context, rule_name in sorted(used.items()):
            if not any(name.startswith(context + "_") for name in names):
                problems.append(
                    f"Context {context!r} used in rule {rule_name!r} "
                    f"has no rules named '{context}_*'."
                )

        for context, rule_name in sorted(declared.items()):
            if context not in used:
                problems.append(
                    f"Rule {rule_name!r} is declared 'in {context}', but no "
                    f"rule uses context {context!r} (typo?)."
                )

        for rule in rules:
            if rule.context is not None:
                continue
            prefixes = {
                rule.name[:i]
                for i, c in enumerate(rule.name)
                if c == "_" and i
            }
            if prefixes and not prefixes & used.keys():
                problems.append(
                    f"Rule {rule.name!r} looks contextual, but no rule "
                    f"uses its context (typo?)."
                )

        return problems


def format_ast(node: Any, dsl_source: str, width: int = 80) -> str:
    """Functional facade: parse DSL source and immediately format given
    node in one call, useful for one-off usage / scripts."""
    formatter = Formatter.from_dsl_source(dsl_source)
    return formatter.format(node, width=width)