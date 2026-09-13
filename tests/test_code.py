import os

from tests.mini_lang.ast_nodes import (
    Identifier, NumberLiteral, BinaryOp, Call, Assign, ExprStmt, Block, If, For, FuncDef
)
from parglare_formatter.formatter import Formatter, FormatterError


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


def build_extended_ast() -> Block:
    """
        function sum_range(a, b) {
            total = 0;
            for (i in a..b) {
                total = total + i;
            }
        }
    """
    return Block(stmts=[
        FuncDef(
            name="sum_range",
            params=["a", "b"],
            body=Block(stmts=[
                Assign(target="total", value=NumberLiteral(value=0)),
                For(
                    var="i",
                    start=Identifier(name="a"),
                    end=Identifier(name="b"),
                    body=Block(stmts=[
                        Assign(
                            target="total",
                            value=BinaryOp(op="+", left=Identifier(name="total"), right=Identifier(name="i")),
                        ),
                    ]),
                ),
            ]),
        ),
    ])

class UnknownNode:
    """Node that INTENTIONALLY does not exist in formatting_rules.dsl used
    to demonstrate FormatterError message when DSL rule is missing."""
    pass


def demo_missing_rule_error(formatter: Formatter) -> None:
    try:
        formatter.format(UnknownNode())
    except FormatterError as e:
        print(f"Expected error (missing rule): {e}")


def main() -> None:
    dsl_path = os.path.join(os.path.dirname(__file__), "formatting_rules.dsl")
    formatter = Formatter.from_dsl_file(dsl_path)

    print("=== Simple example ===")
    print(formatter.format(build_sample_ast(), width=40))

    print()
    print("=== Extended example ===")
    print(formatter.format(build_extended_ast(), width=40))

    print()
    print("=== Error Demonstration (missing DSL rule) ===")
    demo_missing_rule_error(formatter)



if __name__ == "__main__":
    main()