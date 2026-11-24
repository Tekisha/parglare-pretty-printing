rule FileAST =
    list(node.ext, item, line() ++ line()) ++ line();

rule FuncDef =
    format(node.decl) ++ text(" ") ++ format(node.body);

rule Decl =
    format(node.type);

rule FuncDecl =
    format(node.type.type) ++
    text(" ") ++
    node.type.declname ++
    text("(") ++
    format(node.args) ++
    text(")");

rule ParamList =
    list(node.params, item, text(",") ++ softline());

rule Typename =
    format(node.type);

rule TypeDecl =
    format(node.type);

rule IdentifierType =
    list(node.names, item, text(" "));

rule Compound =
    text("{") ++
    nest(
        4,
        line() ++ list(node.block_items, item, line())
    ) ++
    line() ++
    text("}");

rule Return =
    text("return ") ++ format(node.expr) ++ text(";");

rule Constant =
    node.value;