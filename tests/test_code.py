import os

from src.parglare_formatter.examples.mini_lang.ast_nodes import (
    Identifier, NumberLiteral, BinaryOp, Call, Assign, ExprStmt, Block, If,
)
from src.parglare_formatter.formatter.formatter import Formatter


def build_sample_ast() -> Block:
    """
        x = 1 + 2 * 3;
        print(x, 42);
        if (x > 0) {
            y = x;
        }
    """
    return Block(stmts=[
        ExprStmt(expr=Assign(
            target="x",
            value=BinaryOp(
                op="+",
                left=NumberLiteral(value=1),
                right=BinaryOp(op="*", left=NumberLiteral(value=2), right=NumberLiteral(value=3)),
            ),
        )),
        ExprStmt(expr=Call(callee="print", args=[Identifier(name="x"), NumberLiteral(value=42)])),
        ExprStmt(expr=If(
            cond=BinaryOp(op=">", left=Identifier(name="x"), right=NumberLiteral(value=0)),
            then_branch=Block(stmts=[
                ExprStmt(expr=Assign(target="y", value=Identifier(name="x"))),
            ]),
        )),
    ])


def main() -> None:
    dsl_path = os.path.join(os.path.dirname(__file__), "formatting_rules.dsl")
    formatter = Formatter.from_dsl_file(dsl_path)

    ast_root = build_sample_ast()
    output = formatter.format(ast_root, width=40)
    print(output)


if __name__ == "__main__":
    main()