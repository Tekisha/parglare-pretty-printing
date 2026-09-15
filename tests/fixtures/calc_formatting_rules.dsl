rule Calc(node) =
    list(node.expressions, item, line());

rule ExprLine(node) =
    format(node.expr) ++ line();

rule BinaryOp(node) =
    group(
        format(node.left) ++ text(" ") ++ node.op ++ softline() ++ format(node.right)
    );

rule Number(node) =
    node.value;

rule Paren(node) =
    text("(") ++ format(node.expr) ++ text(")");