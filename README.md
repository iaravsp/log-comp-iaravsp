```ebnf

PROGRAM = { STATEMENT } ;

STATEMENT = ( ( IDENTIFIER, "=", EXPRESSION ) | ( "print", "(", EXPRESSION, ")" ) | ε ), "\n" ;

EXPRESSION = TERM, { ("+" | "-"), TERM } ;

TERM = FACTOR, { ("*" | "/"), FACTOR } ;

FACTOR = ( ( "+" | "-" ), FACTOR ) | "(", EXPRESSION, ")" | NUMBER | IDENTIFIER ;

NUMBER = DIGIT, { DIGIT } ;

IDENTIFIER = LETTER, { LETTER | DIGIT | "_" } ;

LETTER = ( "a" | "..." | "z" | "A" | "..." | "Z" ) ;

DIGIT = ( "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9" ) ;

```
![Diagrama Sintático do Compilador](image.png) 

# log-comp-iaravsp

[![Compilation Status](https://compiler-tester.insper-comp.com.br/svg/iaravsp/log-comp-iaravsp)](https://compiler-tester.insper-comp.com.br/svg/iaravsp/log-comp-iaravsp)
