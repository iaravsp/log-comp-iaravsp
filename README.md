```ebnf

PROGRAM = { STATEMENT } ;

STATEMENT = ( "iden", "=", BOOLEXPRESSION
          | "if", "(", BOOLEXPRESSION, ")", "then", { STATEMENT }, ( "end" | "else", { STATEMENT }, "end" )
          | "local", "iden", "type", [ "=", BOOLEXPRESSION ]
          | "while", "(", BOOLEXPRESSION, ")", "do", { STATEMENT }, "end"
          | "print", "(", BOOLEXPRESSION, ")"
          | BLOCK ), "EOL" ;

BLOCK = "do", { STATEMENT }, "end" ;

BOOLEXPRESSION = BOOLTERM, { "or", BOOLTERM } ;

BOOLTERM = RELEXPRESSION, { "and", RELEXPRESSION } ;

RELEXPRESSION = EXPRESSION, [ ("==" | "<" | ">"), EXPRESSION ] ;

EXPRESSION = TERM, { ("+" | "-" | ".."), TERM } ;

TERM = FACTOR, { ("*" | "/"), FACTOR } ;

FACTOR = "int" | "string_val" | "bool_val" | "iden" 
       | ("+" | "-" | "not"), FACTOR 
       | "(", BOOLEXPRESSION, ")" 
       | "read", "(", ")" ;

```
![Diagrama Sintático do Compilador](image.png) 

# log-comp-iaravsp

[![Compilation Status](https://compiler-tester.insper-comp.com.br/svg/iaravsp/log-comp-iaravsp)](https://compiler-tester.insper-comp.com.br/svg/iaravsp/log-comp-iaravsp)
