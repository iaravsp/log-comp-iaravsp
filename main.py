import sys

class Node:
    def __init__(self, value, children):
        self.value = value
        self.children = children
    def evaluate(self):
        pass

class IntVal(Node):
    def __init__(self, value, children):
        super().__init__(value, [])
    def evaluate(self):
        return self.value

class UnOp(Node):
    def __init__(self, value, children):
        super().__init__(value, children)
    def evaluate(self):
        res = self.children[0].evaluate()
        if self.value == '-': 
            return -res
        return res

class BinOp(Node):
    def __init__(self, value, children):
        super().__init__(value, children)
    def evaluate(self):
        filho1_result  = self.children[0].evaluate()
        filho2_result  = self.children[1].evaluate()
        if self.value == '+': 
            return filho1_result + filho2_result
        if self.value == '-':
            return filho1_result - filho2_result
        if self.value == '*': 
            return filho1_result * filho2_result
        if self.value == '/': 
            return filho1_result // filho2_result
        if self.value == '^':
            return filho1_result ^ filho2_result
        if self.value == '**':
            return filho1_result ** filho2_result
        raise ValueError(f"[Semantic] Operador inválido {self.value}")

class Token:
     def __init__(self, tipo, valor):
        self.type: str = tipo
        self.value: int = valor

# análise léxica 
class Lexer:
    def __init__(self, source: str):
        self.source = source #código de entrada
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
        elif self.source[self.position] == '*':
            self.next = Token('MULT', '*')
            self.position +=1
        elif self.source[self.position] == '/':
            self.next = Token('DIV', '/')
            self.position +=1
        elif self.source[self.position] == '(':
            self.next = Token('OPEN_PAR', '(')
            self.position +=1
        elif self.source[self.position] == ')':
            self.next = Token('CLOSE_PAR', ')')
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
        resultado = Parser.parse_term()

        while Parser.lexer.next.type == "PLUS" or Parser.lexer.next.type == "MINUS" or Parser.lexer.next.type == "XOR" :
            operador = '+' if Parser.lexer.next.type == "PLUS" else ('-' if Parser.lexer.next.type == "MINUS" else "^")
            Parser.lexer.select_next()
            proximo_term = Parser.parse_term()
            resultado = BinOp(operador, [resultado, proximo_term])
        return resultado

    @staticmethod
    def run(code: str):
        Parser.lexer = Lexer(code)
        Parser.lexer.select_next()
        pars = Parser.parse_expression()
        if Parser.lexer.next.type != 'EOF':
            raise ValueError(f"[Parser] Unexpected token {Parser.lexer.next.value}")
        return pars
    
    @staticmethod
    def parse_term():
        resultado = Parser.parse_factor()
        while Parser.lexer.next.type == "MULT" or Parser.lexer.next.type == "DIV":
            operador = '*' if Parser.lexer.next.type == "MULT" else '/'
            Parser.lexer.select_next()
            proximo_factor = Parser.parse_factor()
            resultado = BinOp(operador, [resultado, proximo_factor]) 
        return resultado
    @staticmethod
    def parse_factor():
        if Parser.lexer.next.type == 'INT':
            resultado = Parser.lexer.next.value
            Parser.lexer.select_next()
            resultado = IntVal(resultado, [])
            return resultado
        elif Parser.lexer.next.type == 'MINUS' or Parser.lexer.next.type == 'PLUS':
            sinal = Parser.lexer.next.type
            Parser.lexer.select_next()
            resultado = Parser.parse_factor()
            resultado = UnOp('-' if sinal == 'MINUS' else '+', [resultado])
            return resultado
        elif Parser.lexer.next.type == 'OPEN_PAR':
            Parser.lexer.select_next()
            expr = Parser.parse_expression()
            if Parser.lexer.next.type != 'CLOSE_PAR':
                raise ValueError(f"[Parser] Expected ')'")
            Parser.lexer.select_next()
            return expr
        else:
            raise ValueError(f"[Parser] Unexpected token {Parser.lexer.next.value}")

def main():
    entrada = sys.argv[1]
    print(Parser.run(entrada).evaluate())

if __name__ == "__main__":
    main()
    