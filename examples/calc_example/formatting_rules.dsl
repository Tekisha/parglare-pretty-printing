rule Calc(node) = list(node.expressions, item, line());

rule ExprLine(node) = format(node.expr) ++ line();

rule BinaryOp(node) = format(node.left) ++ text(" ") ++ node.op ++ text(" ") ++ format(node.right);

rule Number(node) = node.value;