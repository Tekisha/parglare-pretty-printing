"""
dsl_grammar.py

Gramatika DSL-a za deklarativno definisanje formatting pravila.

Sintaksa DSL-a (primer):

    rule binary_op(node) =
        format(node.left) ++ text(" + ") ++ format(node.right);

    rule block(node) =
        text("{") ++
        nest(2, line() ++ list(node.stmts, format(item))) ++
        line() ++ text("}");

Napomene o strukturi gramatike (v. uvodno poglavlje projekta):
  - Svi regex terminali (Ident, StringLiteral, IntLiteral) su definisani
    u `terminals` bloku na kraju, ne inline u produkcijama.
  - Whitespace se ne umece rucno WS terminalima u produkcijama - parglare-ov
    default `ws` parametar (podrazumevano " \t\n\r") u Parser konstruktoru
    je dovoljan za ovaj DSL, jer nema potrebe za posebnim tretiranjem
    komentara u ovoj fazi. Ako bude potrebno kasnije, dodaje se posebno
    LAYOUT pravilo bez izmene ove gramatike.
  - DocExpr koristi `{left}` disambiguation za operator '++' (levo
    asocijativna konkatenacija), sto je parglare-ova standardna sintaksa
    za resavanje shift/reduce konflikta nad rekurzivnim pravilom.
  - Argumenti poput `node.left` (pristup atributu AST cvora) modelovani su
    kroz posebno pravilo `AttrPath: Ident ("." Ident)*` da bi DSL mogao da
    referencira ugnjezdena polja AST cvora bez posebne sintakse za to.
  - Named matches (name=, params=, body=, left=, right=) se koriste gde
    god to smanjuje potrebu za rucnim pisanjem akcija - v. dsl_parser.py.
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