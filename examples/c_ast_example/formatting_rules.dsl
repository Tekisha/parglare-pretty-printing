rule FileAST =
    list(
        node.ext,
        format(item, statement),
        line() ++ line()
    ) ++
    line();

rule FuncDef =
    format(node.decl) ++
    " " ++
    format(node.body);

rule Decl =
    format(node.type) ++
    optional(
        node.init,
        " = " ++ format(node.init)
    );

rule FuncDecl =
    group(
        format(node.type) ++
        "(" ++
        optional(node.args, format(node.args)) ++
        ")"
    );

rule ParamList =
    list(
        node.params,
        item,
        "," ++ softline()
    );

rule Typename =
    format(node.type);

rule TypeDecl =
    format(node.type) ++
    optional(
        node.declname,
        " " ++ node.declname
    );

rule IdentifierType =
    list(node.names, item, " ");

rule Compound =
    "{" ++
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
    "}";

rule branch_Compound =
    " " ++ format(node);

rule Return =
    "return" ++
    optional(
        node.expr,
        " " ++ format(node.expr)
    ) ++
    ";";

rule Constant =
    node.value;

rule ID =
    node.name;

rule BinaryOp =
    group(
        "(" ++
        format(node.left) ++
        " " ++
        node.op ++
        nest(
            4,
            softline() ++ format(node.right)
        ) ++
        ")"
    );

rule Assignment =
    "(" ++ format(node, bare) ++ ")";

rule bare_Assignment =
    format(node.lvalue) ++
    " " ++
    node.op ++
    " " ++
    format(node.rvalue);

rule FuncCall =
    group(
        format(node.name) ++
        "(" ++
        optional(node.args, format(node.args)) ++
        ")"
    );

rule ExprList =
    nest(
        4,
        list(
            node.exprs,
            item,
            "," ++ softline()
        )
    );

rule bare_BinaryOp =
    group(
        format(node.left) ++
        " " ++
        node.op ++
        nest(
            4,
            softline() ++ format(node.right)
        )
    );

rule If =
    "if (" ++
    format(node.cond, bare) ++
    ")" ++
    format(node.iftrue, branch) ++
    optional(
        node.iffalse,
        format(node.iftrue, before_else) ++
        format(node.iffalse, else_branch)
    );

rule else_branch_If =
    " " ++ format(node);

rule else_branch_default =
    format(node, branch);

rule before_else_Compound =
    " else";

rule before_else_default =
    line() ++ "else";

rule While =
    "while (" ++
    format(node.cond, bare) ++
    ")" ++
    format(node.stmt, branch);

rule bare_UnaryOp =
    when(
        node.op, "p++",
        format(node.expr) ++ "++",
        when(
            node.op, "p--",
            format(node.expr) ++ "--",
            when(
                node.op, "sizeof",
                "sizeof " ++ format(node.expr),
                node.op ++ format(node.expr)
            )
        )
    );

rule UnaryOp =
    "(" ++ format(node, bare) ++ ")";

rule DeclList =
    list(node.decls, item, ", ");

rule For =
    "for (" ++
    optional(node.init, format(node.init, bare)) ++
    ";" ++
    optional(node.cond, " " ++ format(node.cond, bare)) ++
    ";" ++
    optional(node.next, " " ++ format(node.next, bare)) ++
    ")" ++
    format(node.stmt, branch);

rule branch_default =
    nest(4, line() ++ format(node, statement));

rule statement_Decl, statement_FuncCall =
    format(node) ++ ";";

rule statement_Assignment, statement_UnaryOp =
    format(node, bare) ++ ";";