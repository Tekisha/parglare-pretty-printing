Calc: expressions=ExprLine+ ;

ExprLine: expr=Expr EOL ;

Expr: left=Expr op=("+" | "-") right=Term {left}
    | Term
    ;

Term: left=Term op=("*" | "/") right=Factor {left}
    | Factor
    ;

Factor: "(" Expr ")"
      | number=Number
      ;

terminals

Number: /[0-9]+/ ;
EOL: /[\r\n]+/ ;