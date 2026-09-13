Json: value=JsonValue ;

JsonValue: JsonString
         | JsonNumber
         | JsonBool
         | JsonNull
         | JsonObject
         | JsonArray
         ;

JsonObject: "{" (members=JsonMember ("," members=JsonMember)*)? "}" ;

JsonMember: key=JsonString ":" value=JsonValue ;

JsonArray: "[" (values=JsonValue ("," values=JsonValue)*)? "]" ;

JsonBool: "true" | "false" ;

JsonNull: "null" ;

terminals
JsonString: /"([^"\\]|\\.)*"/ ;
JsonNumber: /-?[0-9]+(\.[0-9]+)?([eE][+-]?[0-9]+)?/ ;