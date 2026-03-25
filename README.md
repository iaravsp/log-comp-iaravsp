```ebnf

PROGRAM = { STATEMENT } ;
STATEMENT = ((IDENTIFIER, "=", EXPRESSION) | (PRINT, "(", EXPRESSION, ")") | ε), EOL ;
EXPRESSION = TERM, { ("+" | "-"), TERM } ;
TERM = FACTOR, { ("*" | "/"), FACTOR } ;
FACTOR = ("+" | "-"), FACTOR | "(", EXPRESSION, ")" | NUMBER ;
NUMBER = DIGIT, {DIGIT} ;
DIGIT = 0 | 1 | ... | 9 ;
IDENTIFIER = LETTER, {LETTER | DIGIT | "_"} ;
LETTER = a | b | ... | z | A | B | ... | Z ;

```
![Diagrama Sintático do Compilador](image.png) 

# log-comp-iaravsp

[![Compilation Status](https://compiler-tester.insper-comp.com.br/svg/iaravsp/log-comp-iaravsp)](https://compiler-tester.insper-comp.com.br/svg/iaravsp/log-comp-iaravsp)
