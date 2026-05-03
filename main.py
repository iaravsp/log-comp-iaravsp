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
        self._offset = 0     
    def get_value(self, name):
        if name not in self.table.keys():
            raise ValueError("[Semantic] - A variável não foi definida")
        return self.table[name]
    def set_value(self, name, value):
        if name not in self.table.keys():
            raise ValueError("[Semantic] - A variável não foi declarada")
        if self.table[name].type != value.type:
            raise ValueError(f"[Semantic] Erro de tipo. Esperado {self.table[name].type}, recebido {value.type}")
        self.table[name].value = value.value
    def create_variable(self, name, value, type):
        if name in self.table.keys():
            raise ValueError("[Semantic] - A variável já foi definida")
        self._offset += 4
        self.table[name] = Variable(value, type, self._offset)
        
class Variable:
    def __init__(self, value, type, shift=0):
        self.value = value 
        self.type = type
        self.shift = shift
        

class Code:
    instructions = []

    @staticmethod
    def append(code: str) -> None:
        Code.instructions.append(code)

    @staticmethod
    def dump(filename: str) -> None:
        header = """section .data
format_out: db "%d", 10, 0
format_in:  db "%d", 0
scan_int:   dd 0

section .text
extern printf
extern scanf
global _start
_start:
push ebp
mov ebp, esp
"""
        footer = """mov esp, ebp
pop ebp
mov eax, 1
xor ebx, ebx
int 0x80
"""
        with open(filename, 'w') as f:
            f.write(header)
            f.write("\n".join(Code.instructions))
            f.write("\n")
            f.write(footer)

class Node:
    id = 0

    @staticmethod
    def newId():
        Node.id += 1
        return Node.id

    def __init__(self, value, children):
        self.value = value
        self.children = children
        self.id = Node.newId()

    def evaluate(self, st: SymbolTable):
        pass

    def generate(self, st: SymbolTable):
        pass

class Identifier(Node):
    def __init__(self, value, children):
        super().__init__(value,[])
    def evaluate(self, st: SymbolTable):
        return st.get_value(self.value)
    def generate(self, st: SymbolTable):
        var = st.get_value(self.value)
        Code.append(f"mov eax, [ebp-{var.shift}]")
    
class Assignment(Node):
    def __init__(self, value, children):
        super().__init__(value,children)
    def evaluate(self, st: SymbolTable):
        nome = self.children[0].value
        resultado_var = self.children[1].evaluate(st)
        st.set_value(nome, resultado_var) #
    def generate(self, st: SymbolTable):
        nome = self.children[0].value
        self.children[1].generate(st)
        var = st.get_value(nome)
        Code.append(f"mov [ebp-{var.shift}], eax ; {nome} = expr")

class Print(Node):
    def __init__(self, value, children):
        super().__init__(value,children)
    def evaluate(self, st: SymbolTable):
        print(self.children[0].evaluate(st).value)
    def generate(self, st: SymbolTable):
        self.children[0].generate(st)
        Code.append("push eax")
        Code.append("push format_out")
        Code.append("call printf")
        Code.append("add esp, 8")

class IntVal(Node):
    def __init__(self, value, children):
        super().__init__(value, [])
    def evaluate(self, st: SymbolTable):
        return Variable(self.value,'number')
    def generate(self, st: SymbolTable):
        Code.append(f"mov eax, {self.value}")
    
class BoolVal(Node):
    def __init__(self, value, children):
        super().__init__(value, [])
    def evaluate(self, st: SymbolTable):
        return Variable(self.value,'boolean')
    def generate(self, st: SymbolTable):
        val = 1 if self.value == 'true' else 0
        Code.append(f"mov eax, {val}")

class StringVal (Node):
    def __init__(self, value, children):
        super().__init__(value, [])
    def evaluate(self, st: SymbolTable):
        return Variable(self.value,'string')
    def generate(self, st: SymbolTable):
        pass
    
class VarDec(Node):
    def __init__(self, value, children):
        super().__init__(value, children)
    def evaluate(self, st):     
        nome_variavel = self.children[0].value
        #pegamos o tipo da variável que está guardado no valor do próprio VarDec
        tipo_variavel = self.value
        if len(self.children) == 1:
            valor_padrao = 0
            if tipo_variavel == "string": valor_padrao = ""
            if tipo_variavel == "boolean": valor_padrao = False
            st.create_variable(nome_variavel, valor_padrao, tipo_variavel)
        elif len(self.children) == 2:
            filho2  = self.children[1].evaluate(st)
            if filho2.type != tipo_variavel:
                raise ValueError(f"[Semantic] Erro na declaração. Variável '{nome_variavel}' é do tipo '{tipo_variavel}', mas recebeu '{filho2.type}'.")
            st.create_variable(nome_variavel, filho2.value, tipo_variavel)
    def generate(self, st: SymbolTable):
        nome_variavel = self.children[0].value
        tipo_variavel = self.value
        # reserva 4 bytes na pilha cria_variable registra o shift
        valor_padrao = 0
        if tipo_variavel == "string": valor_padrao = ""
        if tipo_variavel == "boolean": valor_padrao = False
        st.create_variable(nome_variavel, valor_padrao, tipo_variavel)
        var = st.get_value(nome_variavel)
        Code.append(f"sub esp, 4 ; var {nome_variavel} [{'-'+str(var.shift)}]")
        if len(self.children) == 2:
            self.children[1].generate(st)
            Code.append(f"mov [ebp-{var.shift}], eax ; {nome_variavel} = expr")
        
    
    
class UnOp(Node):
    def __init__(self, value, children):
        super().__init__(value, children)
    def evaluate(self, st: SymbolTable):
        res_var = self.children[0].evaluate(st) # Variável resultante da avaliação do filho -> Var(value, type)
        if self.value in ['-', '+'] and res_var.type != 'number':
            raise ValueError("[Semantic] Operação inválida para o tipo do operando")
        else:
            if self.value == '-': 
                return Variable(-res_var.value, res_var.type)
            if self.value == '+': 
                return Variable(res_var.value, res_var.type)
        if self.value == 'not' and res_var.type != 'boolean':
            raise ValueError("[Semantic] Operação inválida para o tipo do operando")
        else:
            if self.value == 'not':
                return Variable(not res_var.value, 'boolean')
    def generate(self, st: SymbolTable):
        self.children[0].generate(st)
        if self.value == '-':
            Code.append("neg eax")
        elif self.value == 'not':
            Code.append("cmp eax, 0")
            Code.append("mov eax, 0")
            Code.append("mov ecx, 1")
            Code.append("cmove eax, ecx")
        # unop + não faz nada
        

class BinOp(Node):
    def __init__(self, value, children):
        super().__init__(value, children)
    def generate(self, st: SymbolTable):
        self.children[0].generate(st)   # resultado em EAX
        Code.append("push eax")
        self.children[1].generate(st)    # resultado em EAX
        Code.append("pop ecx")        # ecx = filho1, eax = filho2
        if self.value == '+':
            Code.append("add eax, ecx")
        elif self.value == '-':
            # filho1 - filho2  ->  ecx - eax
            Code.append("sub ecx, eax")
            Code.append("mov eax, ecx")
        elif self.value == '*':
            Code.append("imul ecx")
        elif self.value == '/':
            # filho1 / filho2  ->  ecx / eax
            Code.append("mov edx, ecx")
            Code.append("mov ecx, eax")
            Code.append("mov eax, edx")
            Code.append("cdq")
            Code.append("idiv ecx")
        elif self.value in ['==', '<', '>']:
            Code.append("cmp ecx, eax")
            Code.append("mov eax, 0")
            Code.append("mov ecx, 1")
            if self.value == '==':
                Code.append("cmove eax, ecx")
            elif self.value == '<':
                Code.append("cmovl eax, ecx")
            elif self.value == '>':
                Code.append("cmovg eax, ecx")
        elif self.value == 'and':
            # ecx AND eax (ambos 0/1)
            Code.append("and eax, ecx")
            Code.append("cmp eax, 0")
            Code.append("mov eax, 0")
            Code.append("mov ecx, 1")
            Code.append("cmovne eax, ecx")
        elif self.value == 'or':
            Code.append("or eax, ecx")
            Code.append("cmp eax, 0")
            Code.append("mov eax, 0")
            Code.append("mov ecx, 1")
            Code.append("cmovne eax, ecx")
    def evaluate(self, st: SymbolTable):
        filho1_result  = self.children[0].evaluate(st)
        filho2_result  = self.children[1].evaluate(st)
        
        if self.value in ['+', '-', '*', '/', '^', '**', '>', '<']:
            if filho1_result.type != 'number' or filho2_result.type != 'number':
                raise ValueError(f"[Semantic] Operação '{self.value}' exige que ambos sejam 'number'. Recebeu {filho1_result.type} e {filho2_result.type}.")
            
            if self.value == '+': return Variable(filho1_result.value + filho2_result.value, 'number')
            if self.value == '-': return Variable(filho1_result.value - filho2_result.value, 'number')
            if self.value == '*': return Variable(filho1_result.value * filho2_result.value, 'number')
            if self.value == '/': 
                if filho2_result.value == 0: raise ValueError("[Semantic] Divisão por zero não permitida")
                return Variable(filho1_result.value // filho2_result.value, 'number')
            if self.value == '^': return Variable(filho1_result.value ^ filho2_result.value, 'number')
            if self.value == '**': return Variable(filho1_result.value ** filho2_result.value, 'number')
            
            if self.value == '>': return Variable(filho1_result.value > filho2_result.value, 'boolean')
            if self.value == '<': return Variable(filho1_result.value < filho2_result.value, 'boolean')

        if self.value == '==':

            return Variable(filho1_result.value == filho2_result.value, 'boolean')

        if self.value in ['or', 'and']:
            if filho1_result.type != 'boolean' or filho2_result.type != 'boolean':
                raise ValueError(f"[Semantic] Operação '{self.value}' exige 'boolean'. Recebeu {filho1_result.type} e {filho2_result.type}.")
            if self.value == 'or': return Variable(filho1_result.value or filho2_result.value, 'boolean')
            if self.value == 'and': return Variable(filho1_result.value and filho2_result.value, 'boolean')

        if  self.value == '..':
            return Variable(str(filho1_result.value) + str(filho2_result.value), 'string')
            
        raise ValueError(f"[Semantic] Operador inválido {self.value}")

class NoOp(Node):
    def __init__(self, value=None, children=None):
        super().__init__(None, [])
    def evaluate(self, st: SymbolTable):
        pass
    def generate(self, st: SymbolTable):
        pass

class If(Node):
    def evaluate(self, st: SymbolTable):
        if self.children[0].evaluate(st).value:
            self.children[1].evaluate(st)
        elif len(self.children) == 3:
            self.children[2].evaluate(st)
    def generate(self, st: SymbolTable):
        uid = self.id
        self.children[0].generate(st)          # condição em EAX
        Code.append(f"cmp eax, 0")
        if len(self.children) == 3:
            Code.append(f"je else_{uid}")
            self.children[1].generate(st)
            Code.append(f"jmp exit_{uid}")
            Code.append(f"else_{uid}:")
            self.children[2].generate(st)
        else:
            Code.append(f"je exit_{uid}")
            self.children[1].generate(st)
        Code.append(f"exit_{uid}:")

class While(Node):
    def evaluate(self, st: SymbolTable):
        while self.children[0].evaluate(st).value:
            self.children[1].evaluate(st)
    def generate(self, st: SymbolTable):
        uid = self.id
        Code.append(f"loop_{uid}:")
        self.children[0].generate(st)          # condição em EAX
        Code.append(f"cmp eax, 0")
        Code.append(f"je exit_{uid}")
        self.children[1].generate(st)
        Code.append(f"jmp loop_{uid}")
        Code.append(f"exit_{uid}:")

class Read(Node):
    def evaluate(self, st: SymbolTable):
        return Variable(int(input()), 'number')
    def generate(self, st: SymbolTable):
        Code.append("push scan_int")
        Code.append("push format_in")
        Code.append("call scanf")
        Code.append("add esp, 8")
        Code.append("mov eax, dword [scan_int]")
    



class Token:
     def __init__(self, tipo, valor):
        self.type: str = tipo
        self.value: int = valor

PALAVRAS_RESERVADAS = ["print", "if", "then", "else", "while", "do", "end", "read", "and", "or", "not", "local","true","false", "string","number","boolean"]
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
            if self.position + 1 < len(self.source) and self.source[self.position + 1] == '=':
                self.next = Token('EQ', '==')
                self.position += 2
            else:
                self.next = Token('ASSIGN', '=')
                self.position += 1
        elif self.source[self.position] == '>':
            self.next = Token('GT', '>')
            self.position += 1
        elif self.source[self.position] == '<':
            self.next = Token('LT', '<')
            self.position += 1
        elif self.source[self.position] == '.':
            self.position += 1
            if self.source[self.position] == '.':
                self.next = Token('CONCAT', '..')
                self.position += 1
            else:
                raise ValueError(f"[Lexer] Caractere inválido: '{self.source[self.position-1]}'")
        elif self.source[self.position].isdigit(): 
            num_str = ''
            while self.position < len(self.source) and self.source[self.position].isdigit():
                num_str += self.source[self.position]
                self.position += 1
            self.next = Token('INT', int(num_str))
        elif self.source[self.position].isalpha():
            palavra_lida = str(self.source[self.position])
            self.position += 1
            
            while self.position < len(self.source) and (self.source[self.position].isalnum() or self.source[self.position] == '_'):
                palavra_lida = palavra_lida + self.source[self.position]
                self.position += 1
                
            if palavra_lida in PALAVRAS_RESERVADAS:
                if palavra_lida == "then":
                    tipo_token = "OPEN_IF_BRA"
                elif palavra_lida == "do":
                    tipo_token = "OPEN_BRA"
                elif palavra_lida == "end":
                    tipo_token = "CLOSE_BRA"
                elif palavra_lida in ["string", "number", "boolean"]:
                    tipo_token = "TYPE"
                elif palavra_lida in ["true", "false"]:
                    tipo_token = "BOOL"
                elif palavra_lida == "local":
                    tipo_token = "VAR"
                else:
                    tipo_token = palavra_lida.upper()
                    
                self.next = Token(tipo_token, palavra_lida)
            else:
                self.next = Token('IDEN', palavra_lida)
        elif self.source[self.position] == '"' or self.source[self.position] == "'":
            tipo_aspas = self.source[self.position] #p/ eu ver se são aspas simples ou duplas
            self.position += 1
            string_lida = ''
            while self.position < len(self.source) and self.source[self.position] != tipo_aspas:
                string_lida += self.source[self.position]
                self.position += 1
            if self.position >= len(self.source):
                raise ValueError(f"[Lexer] String não fechada: '{string_lida}'")
            self.position += 1

            self.next = Token('STR', string_lida)

        else:
            raise ValueError(f"[Lexer] Caractere inválido: '{self.source[self.position]}'")

class Block(Node):
    def __init__(self, value, children):
        super().__init__(value, children)

    def evaluate(self, st: SymbolTable):
        for filho in self.children:
            filho.evaluate(st)

    def generate(self, st: SymbolTable):
        for filho in self.children:
            filho.generate(st)

class Parser():
    lexer = None

    @staticmethod
    def parse_expression():
        resultado = Parser.parse_term()

        while Parser.lexer.next.type == "PLUS" or Parser.lexer.next.type == "MINUS" or Parser.lexer.next.type == "XOR"  or Parser.lexer.next.type == "CONCAT":
            operador = '+' if Parser.lexer.next.type == "PLUS" else ('-' if Parser.lexer.next.type == "MINUS" else "^")
            operador = '..' if Parser.lexer.next.type == "CONCAT" else operador
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
        elif Parser.lexer.next.type == 'STR':
            resultado = Parser.lexer.next.value
            Parser.lexer.select_next()
            resultado = StringVal(resultado, [])
            return resultado
        elif Parser.lexer.next.type == 'BOOL':
            resultado = Parser.lexer.next.value
            Parser.lexer.select_next()
            resultado = BoolVal(resultado, [])
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
            expr = Parser.parse_bool_expression() 
            if Parser.lexer.next.type != 'CLOSE_PAR':
                raise ValueError(f"[Parser] Expected ')'")
            Parser.lexer.select_next()
            return expr
        elif Parser.lexer.next.type == 'READ':
            Parser.lexer.select_next()
            if Parser.lexer.next.type != 'OPEN_PAR': raise ValueError("[Parser] Esperado '(' após read")
            Parser.lexer.select_next()
            if Parser.lexer.next.type != 'CLOSE_PAR': raise ValueError("[Parser] Esperado ')' após read")
            Parser.lexer.select_next()
            return Read(None, [])
        elif Parser.lexer.next.type == 'NOT':
            Parser.lexer.select_next()
            resultado = Parser.parse_factor()
            return UnOp('not', [resultado])
        else:
            raise ValueError(f"[Parser] Unexpected token {Parser.lexer.next.value}")
    @staticmethod
    def parse_program():
        comandos = []
        while Parser.lexer.next.type != 'EOF':
            if Parser.lexer.next.type == 'END':
                Parser.lexer.select_next()
                continue
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
    def parse_block():
        comandos = []
        while Parser.lexer.next.type not in ['EOF', 'CLOSE_BRA', 'ELSE']:
            if Parser.lexer.next.type == 'END':
                Parser.lexer.select_next()
                continue
            no = Parser.parse_statement()
            comandos.append(no)
            
            if Parser.lexer.next.type == 'END':
                Parser.lexer.select_next()
            elif Parser.lexer.next.type not in ['EOF', 'CLOSE_BRA', 'ELSE']:
                raise ValueError(f"[Parser] Token inesperado no bloco: {Parser.lexer.next.type}")
        return Block(None, comandos)
    

    @staticmethod
    def parse_statement():
        if Parser.lexer.next.type == 'IF':
            Parser.lexer.select_next()
        
            if Parser.lexer.next.type != 'OPEN_PAR': raise ValueError("[Parser] Esperado '('")
            Parser.lexer.select_next()
            condicao = Parser.parse_bool_expression()
            if Parser.lexer.next.type != 'CLOSE_PAR': raise ValueError("[Parser] Esperado ')'")
            Parser.lexer.select_next()
            
            if Parser.lexer.next.type != 'OPEN_IF_BRA': raise ValueError("[Parser] Esperado 'then'")
            Parser.lexer.select_next()
            if Parser.lexer.next.type == 'END': Parser.lexer.select_next()
            
            bloco_then = Parser.parse_block()
            
            if Parser.lexer.next.type == 'ELSE':
                Parser.lexer.select_next()
                if Parser.lexer.next.type == 'END': Parser.lexer.select_next()
                bloco_else = Parser.parse_block()
                
                if Parser.lexer.next.type != 'CLOSE_BRA': raise ValueError("[Parser] Esperado 'end' apos else")
                Parser.lexer.select_next()
                return If(None, [condicao, bloco_then, bloco_else])
            
            if Parser.lexer.next.type != 'CLOSE_BRA': raise ValueError("[Parser] Esperado 'end'")
            Parser.lexer.select_next()
            return If(None, [condicao, bloco_then])

        elif Parser.lexer.next.type == 'WHILE':
            Parser.lexer.select_next()
            

            if Parser.lexer.next.type != 'OPEN_PAR': raise ValueError("[Parser] Esperado '('")
            Parser.lexer.select_next()
            condicao = Parser.parse_bool_expression()
            if Parser.lexer.next.type != 'CLOSE_PAR': raise ValueError("[Parser] Esperado ')'")
            Parser.lexer.select_next()
            
            if Parser.lexer.next.type != 'OPEN_BRA': raise ValueError("[Parser] Esperado 'do'")
            Parser.lexer.select_next()
            if Parser.lexer.next.type == 'END': Parser.lexer.select_next()
            
            bloco = Parser.parse_block()

            if Parser.lexer.next.type != 'CLOSE_BRA': raise ValueError("[Parser] Esperado 'end'")
            Parser.lexer.select_next()
            return While(None, [condicao, bloco])
            
        elif Parser.lexer.next.type == 'IDEN':
            no_id = Identifier(Parser.lexer.next.value, [])
            Parser.lexer.select_next()
            if Parser.lexer.next.type == 'ASSIGN':
                Parser.lexer.select_next()
            
                expression = Parser.parse_bool_expression()
                return Assignment(None, [no_id, expression])
            else:
                raise ValueError("[Parser] Esperado '=' após identificador")
                
        elif Parser.lexer.next.type == 'PRINT':
            Parser.lexer.select_next()
            if Parser.lexer.next.type == 'OPEN_PAR':
                Parser.lexer.select_next()
     
                expression = Parser.parse_bool_expression()
                if Parser.lexer.next.type == 'CLOSE_PAR':
                    Parser.lexer.select_next()
                    return Print(None, [expression])
                else:
                    raise ValueError("[Parser] Esperado ')'")
            else:
                raise ValueError("[Parser] Esperado '(' ")
            
        elif Parser.lexer.next.type == 'OPEN_BRA':
            Parser.lexer.select_next()
            if Parser.lexer.next.type == 'END': Parser.lexer.select_next()
            bloco = Parser.parse_block()
            if Parser.lexer.next.type != 'CLOSE_BRA': raise ValueError("[Parser] Esperado 'end'")
            Parser.lexer.select_next()
            return bloco
        elif Parser.lexer.next.type == 'VAR':
            Parser.lexer.select_next() #consumi o 'local'
            if Parser.lexer.next.type != 'IDEN': 
                raise ValueError("[Parser] Esperado identificador após 'local'")
            nome_variavel = Parser.lexer.next.value
            Parser.lexer.select_next()
            if Parser.lexer.next.type != 'TYPE':
                raise ValueError("[Parser] Esperado tipo após nome da variável")
            tipo_variavel = Parser.lexer.next.value
            Parser.lexer.select_next()
            if Parser.lexer.next.type == 'ASSIGN':
                Parser.lexer.select_next()
                expression = Parser.parse_bool_expression()
                return VarDec(tipo_variavel, [Identifier(nome_variavel, []), expression])
            return VarDec(tipo_variavel, [Identifier(nome_variavel, [])])
        else:
            return NoOp()
        
    @staticmethod
    def parse_bool_expression():
        resultado = Parser.parse_bool_term()
        while Parser.lexer.next.type == 'OR':
            Parser.lexer.select_next()
            resultado = BinOp('or', [resultado, Parser.parse_bool_term()])
        return resultado

    @staticmethod
    def parse_bool_term():
        resultado = Parser.parse_rel_expression()
        while Parser.lexer.next.type == 'AND':
            Parser.lexer.select_next()
            resultado = BinOp('and', [resultado, Parser.parse_rel_expression()])
        return resultado

    @staticmethod
    def parse_rel_expression():
        node_left = Parser.parse_expression()
        if Parser.lexer.next.type in ['EQ', 'GT', 'LT']:
            op = Parser.lexer.next.value
            Parser.lexer.select_next()
            node_right = Parser.parse_expression()
            return BinOp(op, [node_left, node_right])
        return node_left

def main():
    nome_arquivo = sys.argv[1]
    arquivo = open(nome_arquivo, "r")
    entrada = arquivo.read() + "\n"
    entrada_prepro = PrePro.filter(entrada)

    #fase semântica (evaluate) 
    st_eval = SymbolTable()
    ast = Parser.run(entrada_prepro)
    ast.evaluate(st_eval)

    #fase de geração de código (generate)
    Code.instructions = []  
    Node.id = 0             
    st_gen = SymbolTable()
    Parser.run(entrada_prepro).generate(st_gen)

    #escreve o .asm com mesmo prefixo do arquivo de entrada
    asm_filename = nome_arquivo.rsplit('.', 1)[0] + '.asm'
    Code.dump(asm_filename)

if __name__ == "__main__":
    main()