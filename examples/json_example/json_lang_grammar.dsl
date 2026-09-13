Json: value=JsonValue ;

JsonValue: JsonString
         | JsonNumber
         | JsonBool
         | JsonNull
         | JsonObject
         | JsonArray
         ;

JsonObject: "{" members=JsonMember*[Comma] "}" ;

JsonMember: key=JsonString ":" value=JsonValue ;

JsonArray: "[" values=JsonValue*[Comma] "]" ;

JsonBool: "true" | "false" ;

JsonNull: "null" ;

terminals
Comma: "," ;
JsonString: /"([^"\\]|\\.)*"/ ;
JsonNumber: /-?[0-9]+(\.[0-9]+)?([eE][+-]?[0-9]+)?/ ;