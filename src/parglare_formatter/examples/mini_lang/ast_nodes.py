"""
Example AST nodes for a mini language used to test dsl_compiler.py
and formatter.py on a concrete, realistic tree.

This language is a simple expression/statement language:

    x = 1 + 2 * 3;
    if (x > 0) {
        print(x);
    }

Nodes are plain dataclasses without any built-in formatting logic,
all formatting logic lives in the .dsl file (formatting_rules.dsl)
which formatter.py loads and applies via dsl_compiler.py. This is
intentional: DSL should be the ONLY place where "how an AST node
looks when printed" is defined, while ast_nodes.py only defines
the AST STRUCTURE.

Note on class names: formatter (Phase 7/8) selects DSL rules by
the Python class name of the node (e.g., a `BinaryOp` node looks
for `rule BinaryOp(node) = ...` in the .dsl file) so class names
here MUST exactly match the `rule` declaration names in
formatting_rules.dsl.
"""

from dataclasses import dataclass, field
from typing import List, Union


@dataclass
class Identifier:
    name: str


@dataclass
class NumberLiteral:
    value: int


@dataclass
class BinaryOp:
    """left + right, left * right, left > right"""
    op: str
    left: "Expr"
    right: "Expr"


@dataclass
class Call:
    """print(x, y)"""
    callee: str
    args: List["Expr"] = field(default_factory=list)


Expr = Union[Identifier, NumberLiteral, BinaryOp, Call]


@dataclass
class Assign:
    """x = <expr>;"""
    target: str
    value: "Expr"


@dataclass
class ExprStmt:
    """print(x);"""
    expr: "Expr"


@dataclass
class Block:
    """{ stmt1; stmt2; ... }"""
    stmts: List["Stmt"] = field(default_factory=list)


@dataclass
class If:
    """if (cond) { then_branch }"""
    cond: "Expr"
    then_branch: "Block"


Stmt = Union[Assign, ExprStmt, Block, If]