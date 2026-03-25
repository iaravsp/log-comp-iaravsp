import sys
import re

class PrePro:
    @staticmethod
    def filter(code: str):
        padrao_comentario = r"--.*"
        return re.sub(padrao_comentario, '', code)

class SymbolTable:
    def __init__(self):
        self.table = {}
    def get_value(self, name):
        if name not in self.table.keys():
            raise ValueError("[Semantic] - A variável não foi definida")
        return self.table[name]
    def set_value(self, name, value):
        self.table[name] = Variable(value)
        
class Variable:
    def __init__(self, value):
        self.value = value 

class Node:
    def __init__(self, value, children):
        self.value = value
        self.children = children
    def evaluate(self, st: SymbolTable):
        pass

class Identifier(Node):
    def __init__(self, value, children):
        super().__init__(value,[])
    def evaluate(self, st: SymbolTable):
        return st.get_value(self.value).value
    
class Assignment(Node):
    def __init__(self, value, children):
        super().__init__(value,children)
    def evaluate(self, st: SymbolTable):
        filho1  = self.children[0].value
        filho2  = self.children[1].evaluate(st)
        st.set_value(filho1, filho2)

class Print(Node):
    def __init__(self, value, children):
        super().__init__(value,children)
    def evaluate(self, st: SymbolTable):
        print(self.children[0].evaluate(st))

class IntVal(Node):
    def __init__(self, value, children):
        super().__init__(value, [])
    def evaluate(self, st: SymbolTable):
        return self.value

class UnOp(Node):
    def __init__(self, value, children):
        super().__init__(value, children)
    def evaluate(self, st: SymbolTable):
        res = self.children[0].evaluate(st)
        if self.value == '-': 
            return -res
        return res

class BinOp(Node):
    def __init__(self, value, children):
        super().__init__(value, children)
    def evaluate(self, st: SymbolTable):
        filho1_result  = self.children[0].evaluate(st)
        filho2_result  = self.children[1].evaluate(st)
        if self.value == '+': 
            return filho1_result + filho2_result
        if self.value == '-':
            return filho1_result - filho2_result
        if self.value == '*': 
            return filho1_result * filho2_result
        if self.value == '/': 
            if filho2_result == 0:
                raise ValueError("[Semantic] divisão por zero não permitida")
            return filho1_result // filho2_result
        if self.value == '^':
            return filho1_result ^ filho2_result
        if self.value == '**':
            return filho1_result ** filho2_result
        raise ValueError(f"[Semantic] Operador inválido {self.value}")

class NoOp(Node):
    def __init__(self, value=None, children=None):
        super().__init__(None, [])
    def evaluate(self, st: SymbolTable):
        pass

class Token:
     def __init__(self, tipo, valor):
        self.type: str = tipo
        self.value: int = valor

PALAVRAS_RESERVADAS = ["print"]
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
        elif self.source[self.position] == '\n':
            self.next = Token('END', '\n')
            self.position +=1
        elif self.source[self.position] == '=':
            self.next = Token('ASSIGN', '=')
            self.position +=1

        elif self.source[self.position].isalpha():
            palavra_lida = str(self.source[self.position])
            self.position += 1
            
            while self.position < len(self.source) and (self.source[self.position].isalnum() or self.source[self.position] == '_'):
                palavra_lida = palavra_lida + self.source[self.position]
                self.position += 1
                
            if palavra_lida in PALAVRAS_RESERVADAS:
                tipo_token = palavra_lida.upper()
                self.next = Token(tipo_token, palavra_lida)
            else:
                self.next = Token('IDEN', palavra_lida)

        elif self.source[self.position].isdigit():
            digito = str(self.source[self.position])
            self.position +=1
            while  self.position < len(self.source) and self.source[self.position].isdigit():
                digito = digito + self.source[self.position]
                self.position +=1
            self.next = Token('INT', int(digito))
        else:
            raise ValueError(f"[Lexer] Invalid Symbol {self.source[self.position]}")

class Block(Node):
    def __init__(self, value, children):
        super().__init__(value, children)

    def evaluate(self, st: SymbolTable):
        for filho in self.children:
            filho.evaluate(st)

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
        elif Parser.lexer.next.type == 'IDEN':
            resultado = Parser.lexer.next.value
            Parser.lexer.select_next()
            resultado = Identifier(resultado, [])
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
    @staticmethod
    def parse_program():
        comandos = []
        while Parser.lexer.next.type != 'EOF':
            no = Parser.parse_statement()
            comandos.append(no)
            
            if Parser.lexer.next.type == 'END': 
                Parser.lexer.select_next()
            elif Parser.lexer.next.type != 'EOF':
                raise ValueError(f"[Parser] Unexpected token {Parser.lexer.next.value}")
        return Block(None, comandos)

    @staticmethod
    def run(code: str):
        Parser.lexer = Lexer(code)
        Parser.lexer.select_next()
        return Parser.parse_program()

    @staticmethod
    def parse_statement():
        if Parser.lexer.next.type == 'IDEN':
            no_id = Identifier(Parser.lexer.next.value, [])
            Parser.lexer.select_next()
            if Parser.lexer.next.type == 'ASSIGN':
                Parser.lexer.select_next()
                expression = Parser.parse_expression()
                return Assignment(None, [no_id, expression])
            else:
                raise ValueError("[Parser] Esperado '=' após identificador")
        elif Parser.lexer.next.type == 'PRINT':
            Parser.lexer.select_next()
            if Parser.lexer.next.type == 'OPEN_PAR':
                Parser.lexer.select_next()
                expression = Parser.parse_expression()
                if Parser.lexer.next.type == 'CLOSE_PAR':
                    Parser.lexer.select_next()
                    return Print(None, [expression])
                else:
                    raise ValueError("[Parser] Esperado ')'")
            else:
                raise ValueError("[Parser] Esperado '(' ")
        else:
            return NoOp()

def main():
    nome_arquivo = sys.argv[1]
    arquivo = open(nome_arquivo, "r")
    entrada = arquivo.read() + "\n"
    entrada_prepro = PrePro.filter(entrada)
    st = SymbolTable()
    Parser.run(entrada_prepro).evaluate(st)

if __name__ == "__main__":
    main()
    