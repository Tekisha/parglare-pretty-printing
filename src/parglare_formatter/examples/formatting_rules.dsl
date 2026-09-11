rule Identifier(node) = node.name;

rule NumberLiteral(node) = node.value;

rule BinaryOp(node) = format(node.left) ++ text(" ") ++ node.op ++ text(" ") ++ format(node.right);

rule Call(node) = node.callee ++ text("(") ++ list(node.args, item, text(", ")) ++ text(")");

rule Assign(node) = node.target ++ text(" = ") ++ format(node.value) ++ text(";");

rule ExprStmt(node) = format(node.expr) ++ text(";");

rule Block(node) = text("{") ++ nest(2, line() ++ list(node.stmts, item)) ++ line() ++ text("}");

rule If(node) = text("if (") ++ format(node.cond) ++ text(") ") ++ format(node.then_branch);