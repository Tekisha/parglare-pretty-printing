rule Calc =
    list(node.expressions, item, line());

rule ExprLine =
    format(node.expr) ++ line();

rule BinaryOp =
    group(
        format(node.left) ++ text(" ") ++ node.op ++ softline() ++ format(node.right)
    );

rule Number =
    node.value;

rule Paren =
    text("(") ++ format(node.expr) ++ text(")");