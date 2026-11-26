rule FileAST =
    list(
        node.ext,
        format(item, statement),
        line() ++ line()
    ) ++
    line();

rule FuncDef =
    format(node.decl) ++
    text(" ") ++
    format(node.body);

rule Decl =
    format(node.type) ++
    optional(
        node.init,
        text(" = ") ++ format(node.init)
    );

rule statement_Decl =
    format(node) ++ text(";");

rule FuncDecl =
    group(
        format(node.type) ++
        text("(") ++
        optional(node.args, format(node.args)) ++
        text(")")
    );

rule ParamList =
    list(
        node.params,
        item,
        text(",") ++ softline()
    );

rule Typename =
    format(node.type);

rule TypeDecl =
    format(node.type) ++
    optional(
        node.declname,
        text(" ") ++ node.declname
    );

rule IdentifierType =
    list(node.names, item, text(" "));

rule Compound =
    text("{") ++
    optional(
        node.block_items,
        nest(
            4,
            line() ++
            list(
                node.block_items,
                format(item, statement),
                line()
            )
        )
    ) ++
    line() ++
    text("}");

rule branch_Compound =
    text(" ") ++ format(node);

rule Return =
    text("return") ++
    optional(
        node.expr,
        text(" ") ++ format(node.expr)
    ) ++
    text(";");

rule Constant =
    node.value;

rule ID =
    node.name;

rule BinaryOp =
    group(
        text("(") ++
        format(node.left) ++
        text(" ") ++
        node.op ++
        nest(
            4,
            softline() ++ format(node.right)
        ) ++
        text(")")
    );

rule Assignment =
    text("(") ++ format(node, bare) ++ text(")");

rule bare_Assignment =
    format(node.lvalue) ++
    text(" ") ++
    node.op ++
    text(" ") ++
    format(node.rvalue);

rule statement_Assignment =
    format(node, bare) ++ text(";");

rule FuncCall =
    group(
        format(node.name) ++
        text("(") ++
        optional(node.args, format(node.args)) ++
        text(")")
    );

rule statement_FuncCall =
    format(node) ++ text(";");

rule ExprList =
    nest(
        4,
        list(
            node.exprs,
            item,
            text(",") ++ softline()
        )
    );

rule bare_BinaryOp =
    group(
        format(node.left) ++
        text(" ") ++
        node.op ++
        nest(
            4,
            softline() ++ format(node.right)
        )
    );

rule If =
    text("if (") ++
    format(node.cond, bare) ++
    text(")") ++
    format(node.iftrue, branch) ++
    optional(
        node.iffalse,
        format(node.iftrue, before_else) ++
        format(node.iffalse, else_branch)
    );

rule else_branch_If =
    text(" ") ++ format(node);

rule else_branch_default =
    format(node, branch);

rule before_else_Compound =
    text(" else");

rule before_else_default =
    line() ++ text("else");

rule While =
    text("while (") ++
    format(node.cond, bare) ++
    text(")") ++
    format(node.stmt, branch);

rule bare_UnaryOp =
    when(
        node.op, "p++",
        format(node.expr) ++ text("++"),
        when(
            node.op, "p--",
            format(node.expr) ++ text("--"),
            when(
                node.op, "sizeof",
                text("sizeof ") ++ format(node.expr),
                node.op ++ format(node.expr)
            )
        )
    );

rule UnaryOp =
    text("(") ++ format(node, bare) ++ text(")");

rule statement_UnaryOp =
    format(node, bare) ++ text(";");

rule DeclList =
    list(node.decls, item, text(", "));

rule For =
    text("for (") ++
    optional(node.init, format(node.init, bare)) ++
    text(";") ++
    optional(node.cond, text(" ") ++ format(node.cond, bare)) ++
    text(";") ++
    optional(node.next, text(" ") ++ format(node.next, bare)) ++
    text(")") ++
    format(node.stmt, branch);

rule branch_default =
    nest(4, line() ++ format(node, statement));