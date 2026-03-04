import sys

class Token:
     def __init__(self, tipo, valor):
        self.type: str = tipo
        self.value: int = valor

# análise léxica 
class Lexer:
    def __init__(self, source: str):
        self.source = source#código de entrada
        self.position = 0
        self.next = None

    def select_next(self):
        while self.position < len(self.source) and self.source[self.position] == ' ':
            self.position +=1
        if self.position >= len(self.source):
            self.next = Token('EOF','')
            self.position +=1
            return
        if self.source[self.position] == '+':
            self.next = Token('PLUS', '+')
            self.position +=1
        elif self.source[self.position] == '-': 
            self.next = Token('MINUS', '-')
            self.position +=1
        elif self.source[self.position] == '^': 
            self.next = Token('XOR', '^')
            self.position +=1
        elif self.source[self.position].isdigit():
            digito = str(self.source[self.position])
            self.position +=1
            while  self.position < len(self.source) and self.source[self.position].isdigit():
                digito = digito + self.source[self.position]
                self.position +=1
            self.next = Token('INT', int(digito))
        else:
            raise ValueError(f"[Lexer] Invalid Symbol {self.source[self.position]}")

class Parser():
    lexer = None

    @staticmethod
    def parse_expression():
        if Parser.lexer.next.type != 'INT':
            raise ValueError(f"[Parser] Unexpected token {Parser.lexer.next.value}")
        else: # é INT
            resultado = Parser.lexer.next.value
            Parser.lexer.select_next()

        while Parser.lexer.next.type == "PLUS" or Parser.lexer.next.type == "MINUS" or Parser.lexer.next.type == "XOR" :
            operador = '+' if Parser.lexer.next.type == "PLUS" else ('-' if Parser.lexer.next.type == "MINUS" else "^")
            Parser.lexer.select_next()
            if Parser.lexer.next.type != 'INT':
                raise ValueError(f"[Parser] Unexpected token {Parser.lexer.next.value}")
            if operador == "+":
                resultado += Parser.lexer.next.value
            elif operador == "-":
                resultado -= Parser.lexer.next.value
            elif operador == "^":
                resultado ^= Parser.lexer.next.value
            Parser.lexer.select_next()
        return resultado

    @staticmethod
    def run(code: str):
        Parser.lexer = Lexer(code)
        Parser.lexer.select_next()
        pars = Parser.parse_expression()
        if Parser.lexer.next.type != 'EOF':
            raise ValueError(f"[Parser] Unexpected token {Parser.lexer.next.value}")
        return pars

def main():
    entrada = sys.argv[1]
    print(Parser.run(entrada))

if __name__ == "__main__":
    main()
    