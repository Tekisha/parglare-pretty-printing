rule Identifier = node.name;

rule NumberLiteral = node.value;

rule BinaryOp = format(node.left) ++ text(" ") ++ node.op ++ text(" ") ++ format(node.right);

rule Call = node.callee ++ text("(") ++ list(node.args, item, text(", ")) ++ text(")");

rule Assign = node.target ++ text(" = ") ++ format(node.value) ++ text(";");

rule ExprStmt = format(node.expr) ++ text(";");

rule Block = text("{") ++ nest(2, line() ++ list(node.stmts, item)) ++ line() ++ text("}");

rule If = text("if (") ++ format(node.cond) ++ text(") ") ++ format(node.then_branch);

rule For = text("for (") ++ node.var ++ text(" in ") ++ format(node.start) ++ text("..") ++ format(node.end) ++ text(") ") ++ format(node.body);

rule FuncDef = text("function ") ++ node.name ++ text("(") ++ align(list(node.params, item, text(", "))) ++ text(") ") ++ format(node.body);