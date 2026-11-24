Calc: expressions=ExprLine+ ;

ExprLine: expr=Expr EOL ;

Expr: left=Expr op=("+" | "-") EOL? right=Term {left}
    | Term
    ;

Term: left=Term op=("*" | "/") EOL? right=Factor {left}
    | Factor
    ;

Factor: "(" expr=Expr ")"
      | number=Number
      ;

terminals

Number: /[0-9]+/ ;
EOL: /[\r\n]+/ ;