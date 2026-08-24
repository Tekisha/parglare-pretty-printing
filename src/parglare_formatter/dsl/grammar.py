"""
DSL grammar for declaratively defining formatting rules.

DSL syntax (example):

    rule binary_op(node) =
        format(node.left) ++ text(" + ") ++ format(node.right);

    rule block(node) =
        text("{") ++
        nest(2, line() ++ list(node.stmts, format(item))) ++
        line() ++ text("}");

Notes on grammar structure (see the project's introductory chapter):
  - All regex terminals (Ident, StringLiteral, IntLiteral) are defined
    in the `terminals` block at the end, not inline in the productions.
  - Whitespace is not manually inserted via WS terminals in the
    productions - parglare's default `ws` parameter (" \t\n\r" by
    default) in the Parser constructor is sufficient for this DSL,
    since there's no need for special comment handling at this stage.
    If needed later, a separate LAYOUT rule can be added without
    modifying this grammar.
  - DocExpr uses `{left}` disambiguation for the '++' operator (left
    associative concatenation), which is parglare's standard syntax
    for resolving a shift/reduce conflict on a recursive rule.
  - Arguments like `node.left` (accessing an AST node's attribute) are
    modeled via a dedicated `AttrPath: Ident ("." Ident)*` rule so the
    DSL can reference nested AST node fields without special syntax
    for it.
  - Named matches (name=, params=, body=, left=, right=) are used
    wherever they reduce the need for manually writing actions - see
    dsl_parser.py.
"""

DSL_GRAMMAR = r"""
RuleFile: RuleDecl+ ;

RuleDecl: "rule" name=Ident "(" params=ParamList? ")" "=" body=DocExpr ";" ;

ParamList: Ident ("," Ident)* ;

DocExpr: left=DocExpr "++" right=DocTerm  {left}
       | DocTerm
       ;

DocTerm: "text" "(" StringLiteral ")"
       | "line" "(" ")"
       | "softline" "(" ")"
       | "nest" "(" IntLiteral "," DocExpr ")"
       | "group" "(" DocExpr ")"
       | "align" "(" DocExpr ")"
       | "format" "(" AttrPath ")"
       | "list" "(" AttrPath "," DocExpr ")"
       | "item"
       | AttrPath
       ;

AttrPath: Ident (Dot Ident)* ;

terminals

Dot: "." ;
Ident: /[a-zA-Z_][a-zA-Z0-9_]*/ ;
StringLiteral: /"(\\.|[^"\\])*"/ ;
IntLiteral: /[0-9]+/ ;
"""