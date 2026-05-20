import sys
import re

class PrePro:
    @staticmethod
    def filter(code: str):
        padrao_comentario = r"--.*"
        return re.sub(padrao_comentario, '', code)

class SymbolTable:
    def __init__(self, parent=None):
        self.table = {}
        self._offset = 0
        self.parent = parent 

    def get_value(self, name):
        if name in self.table:
            return self.table[name]
        if self.parent is not None:
            return self.parent.get_value(name)
        raise ValueError(f"[Semantic] - A variável '{name}' não foi definida")

    def set_value(self, name, value):
        if name in self.table:
            if self.table[name].is_func:
                raise ValueError(f"[Semantic] '{name}' é uma função, não pode ser atribuída")
            if self.table[name].type != value.type:
                raise ValueError(f"[Semantic] Erro de tipo. Esperado {self.table[name].type}, recebido {value.type}")
            self.table[name].value = value.value
            return
        if self.parent is not None:
            self.parent.set_value(name, value)
            return
        raise ValueError(f"[Semantic] - A variável '{name}' não foi declarada")

    def create_variable(self, name, value, type, is_func=False):
        if name in self.table:
            raise ValueError(f"[Semantic] - A variável '{name}' já foi definida")
        self._offset += 4
        self.table[name] = Variable(value, type, self._offset, is_func=is_func)


class Variable:
    def __init__(self, value, type, shift=0, is_func=False):
        self.value = value
        self.type = type
        self.shift = shift
        self.is_func = is_func


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
    def new_id():
        Node.id += 1
        return Node.id

    def __init__(self, value, children):
        self.value = value
        self.children = children
        self.id = Node.new_id()

    def evaluate(self, st: SymbolTable):
        pass

    def generate(self, st: SymbolTable):
        pass


class Identifier(Node):
    def __init__(self, value, children):
        super().__init__(value, [])

    def evaluate(self, st: SymbolTable):
        return st.get_value(self.value)

    def generate(self, st: SymbolTable):
        var = st.get_value(self.value)
        Code.append(f"mov eax, [ebp-{var.shift}]")


class Assignment(Node):
    def __init__(self, value, children):
        super().__init__(value, children)

    def evaluate(self, st: SymbolTable):
        nome = self.children[0].value
        resultado_var = self.children[1].evaluate(st)
        st.set_value(nome, resultado_var)

    def generate(self, st: SymbolTable):
        nome = self.children[0].value
        self.children[1].generate(st)
        var = st.get_value(nome)
        Code.append(f"mov [ebp-{var.shift}], eax ; {nome} = expr")


class Print(Node):
    def __init__(self, value, children):
        super().__init__(value, children)

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
        return Variable(self.value, 'number')

    def generate(self, st: SymbolTable):
        Code.append(f"mov eax, {self.value}")


class BoolVal(Node):
    def __init__(self, value, children):
        super().__init__(value, [])

    def evaluate(self, st: SymbolTable):
        return Variable(self.value, 'boolean')

    def generate(self, st: SymbolTable):
        val = 1 if self.value == 'true' else 0
        Code.append(f"mov eax, {val}")


class StringVal(Node):
    def __init__(self, value, children):
        super().__init__(value, [])

    def evaluate(self, st: SymbolTable):
        return Variable(self.value, 'string')

    def generate(self, st: SymbolTable):
        pass


class VarDec(Node):
    def __init__(self, value, children):
        super().__init__(value, children)

    def evaluate(self, st):
        nome_variavel = self.children[0].value
        tipo_variavel = self.value
        if len(self.children) == 1:
            valor_padrao = 0
            if tipo_variavel == "string": valor_padrao = ""
            if tipo_variavel == "boolean": valor_padrao = False
            st.create_variable(nome_variavel, valor_padrao, tipo_variavel, is_func=False)
        elif len(self.children) == 2:
            filho2 = self.children[1].evaluate(st)
            if filho2.type != tipo_variavel:
                raise ValueError(f"[Semantic] Erro na declaração. Variável '{nome_variavel}' é do tipo '{tipo_variavel}', mas recebeu '{filho2.type}'.")
            st.create_variable(nome_variavel, filho2.value, tipo_variavel, is_func=False)

    def generate(self, st: SymbolTable):
        nome_variavel = self.children[0].value
        tipo_variavel = self.value
        valor_padrao = 0
        if tipo_variavel == "string": valor_padrao = ""
        if tipo_variavel == "boolean": valor_padrao = False
        st.create_variable(nome_variavel, valor_padrao, tipo_variavel, is_func=False)
        var = st.get_value(nome_variavel)
        Code.append(f"sub esp, 4 ; var {nome_variavel} [{'-'+str(var.shift)}]")
        if len(self.children) == 2:
            self.children[1].generate(st)
            Code.append(f"mov [ebp-{var.shift}], eax ; {nome_variavel} = expr")


class UnOp(Node):
    def __init__(self, value, children):
        super().__init__(value, children)

    def evaluate(self, st: SymbolTable):
        res_var = self.children[0].evaluate(st)
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


class BinOp(Node):
    def __init__(self, value, children):
        super().__init__(value, children)

    def generate(self, st: SymbolTable):
        self.children[0].generate(st)
        Code.append("push eax")
        self.children[1].generate(st)
        Code.append("pop ecx")
        if self.value == '+':
            Code.append("add eax, ecx")
        elif self.value == '-':
            Code.append("sub ecx, eax")
            Code.append("mov eax, ecx")
        elif self.value == '*':
            Code.append("imul ecx")
        elif self.value == '/':
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
        filho1_result = self.children[0].evaluate(st)
        filho2_result = self.children[1].evaluate(st)

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

        if self.value == '..':
            return Variable(str(filho1_result.value) + str(filho2_result.value), 'string')

        raise ValueError(f"[Semantic] Operador inválido {self.value}")


class NoOp(Node):
    def __init__(self, value=None, children=None):
        super().__init__(None, [])

    def evaluate(self, st: SymbolTable):
        pass

    def generate(self, st: SymbolTable):
        pass


class Return(Node):
    def __init__(self, value, children):
        super().__init__(value, children)

    def evaluate(self, st: SymbolTable):
        return self.children[0].evaluate(st)

    def generate(self, st: SymbolTable):
        pass


class FuncDec(Node):
    def __init__(self, value, children):
        super().__init__(value, children)

    def evaluate(self, st: SymbolTable):
        nome = self.children[0].value
        tipo_retorno = self.value
        
        root_st = st
        while root_st.parent is not None:
            root_st = root_st.parent
            
        root_st.create_variable(nome, self, tipo_retorno if tipo_retorno else 'void', is_func=True)

    def generate(self, st: SymbolTable):
        pass


class FuncCall(Node):
    def __init__(self, value, children):
        super().__init__(value, children)

    def evaluate(self, st: SymbolTable):
        nome = self.value

        func_var = st.get_value(nome)
        if not func_var.is_func:
            raise ValueError(f"[Semantic] '{nome}' não é uma função")

        func_dec = func_var.value
        params = func_dec.children[1:-1]
        args   = self.children

        if len(params) != len(args):
            raise ValueError(
                f"[Semantic] Função '{nome}' espera {len(params)} argumento(s), "
                f"mas recebeu {len(args)}"
            )

        root_st = st
        while root_st.parent is not None:
            root_st = root_st.parent
            
        local_st = SymbolTable(parent=root_st)

        for param, arg_node in zip(params, args):
            param_nome = param.children[0].value
            param_tipo = param.value
            arg_val = arg_node.evaluate(st)
            if arg_val.type != param_tipo:
                raise ValueError(
                    f"[Semantic] Argumento '{param_nome}' da função '{nome}' "
                    f"esperado '{param_tipo}', mas recebeu '{arg_val.type}'"
                )
            local_st.create_variable(param_nome, arg_val.value, param_tipo, is_func=False)

        corpo = func_dec.children[-1]
        resultado = corpo.evaluate(local_st)

        tipo_retorno = func_var.type
        if tipo_retorno == 'void':
            return None
        if resultado is None:
            raise ValueError(f"[Semantic] Função '{nome}' deveria retornar '{tipo_retorno}', mas não retornou nada")
        if resultado.type != tipo_retorno:
            raise ValueError(
                f"[Semantic] Função '{nome}' deveria retornar '{tipo_retorno}', "
                f"mas retornou '{resultado.type}'"
            )
        return resultado

    def generate(self, st: SymbolTable):
        pass 


class If(Node):
    def evaluate(self, st: SymbolTable):
        if self.children[0].evaluate(st).value:
            result = self.children[1].evaluate(st)
            if result is not None:
                return result
        elif len(self.children) == 3:
            result = self.children[2].evaluate(st)
            if result is not None:
                return result

    def generate(self, st: SymbolTable):
        uid = self.id
        self.children[0].generate(st)
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
            result = self.children[1].evaluate(st)
            if result is not None:
                return result

    def generate(self, st: SymbolTable):
        uid = self.id
        Code.append(f"loop_{uid}:")
        self.children[0].generate(st)
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


class Block(Node):
    def __init__(self, value, children):
        super().__init__(value, children)

    def evaluate(self, st: SymbolTable):
        for filho in self.children:
            if isinstance(filho, Return):
                return filho.evaluate(st)
            elif isinstance(filho, Block):
                inner_st = SymbolTable(parent=st)
                result = filho.evaluate(inner_st)
                if result is not None:
                    return result
            else:
                result = filho.evaluate(st)
                if result is not None:
                    return result
        return None

    def generate(self, st: SymbolTable):
        for filho in self.children:
            filho.generate(st)


class Token:
    def __init__(self, tipo, valor):
        self.type: str = tipo
        self.value = valor


PALAVRAS_RESERVADAS = ["print", "if", "then", "else", "while", "do", "end", "read", "and", "or", "not", "local", "true", "false","string", "number", "boolean", "function", "return" ]
class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.position = 0
        self.next = None

    def select_next(self):
        while self.position < len(self.source) and self.source[self.position] == ' ':
            self.position += 1
        if self.position >= len(self.source):
            self.next = Token('EOF', '')
            self.position += 1
            return
        ch = self.source[self.position]
        if ch == '+':
            self.next = Token('PLUS', '+'); self.position += 1
        elif ch == '-':
            self.next = Token('MINUS', '-'); self.position += 1
        elif ch == '^':
            self.next = Token('XOR', '^'); self.position += 1
        elif ch == '*':
            self.next = Token('MULT', '*'); self.position += 1
        elif ch == '/':
            self.next = Token('DIV', '/'); self.position += 1
        elif ch == '(':
            self.next = Token('OPEN_PAR', '('); self.position += 1
        elif ch == ')':
            self.next = Token('CLOSE_PAR', ')'); self.position += 1
        elif ch == ',':
            self.next = Token('COMMA', ','); self.position += 1   
        elif ch == '\n':
            self.next = Token('END', '\n'); self.position += 1
        elif ch == '=':
            if self.position + 1 < len(self.source) and self.source[self.position + 1] == '=':
                self.next = Token('EQ', '=='); self.position += 2
            else:
                self.next = Token('ASSIGN', '='); self.position += 1
        elif ch == '>':
            self.next = Token('GT', '>'); self.position += 1
        elif ch == '<':
            self.next = Token('LT', '<'); self.position += 1
        elif ch == '.':
            self.position += 1
            if self.position < len(self.source) and self.source[self.position] == '.':
                self.next = Token('CONCAT', '..'); self.position += 1
            else:
                raise ValueError(f"[Lexer] Caractere inválido: '.'")
        elif ch.isdigit():
            num_str = ''
            while self.position < len(self.source) and self.source[self.position].isdigit():
                num_str += self.source[self.position]
                self.position += 1
            self.next = Token('INT', int(num_str))
        elif ch.isalpha() or ch == '_':
            palavra_lida = ''
            while self.position < len(self.source) and (self.source[self.position].isalnum() or self.source[self.position] == '_'):
                palavra_lida += self.source[self.position]
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
                elif palavra_lida == "function":
                    tipo_token = "FUNC"       
                elif palavra_lida == "return":
                    tipo_token = "RETURN"  
                else:
                    tipo_token = palavra_lida.upper()
                self.next = Token(tipo_token, palavra_lida)
            else:
                self.next = Token('IDEN', palavra_lida)
        elif ch == '"' or ch == "'":
            tipo_aspas = ch
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
            raise ValueError(f"[Lexer] Caractere inválido: '{ch}'")


class Parser:
    lexer = None

    @staticmethod
    def parse_expression():
        resultado = Parser.parse_term()
        while Parser.lexer.next.type in ("PLUS", "MINUS", "XOR", "CONCAT"):
            if Parser.lexer.next.type == "PLUS":
                operador = '+'
            elif Parser.lexer.next.type == "MINUS":
                operador = '-'
            elif Parser.lexer.next.type == "XOR":
                operador = '^'
            else:
                operador = '..'
            Parser.lexer.select_next()
            proximo_term = Parser.parse_term()
            resultado = BinOp(operador, [resultado, proximo_term])
        return resultado

    @staticmethod
    def parse_term():
        resultado = Parser.parse_factor()
        while Parser.lexer.next.type in ("MULT", "DIV"):
            operador = '*' if Parser.lexer.next.type == "MULT" else '/'
            Parser.lexer.select_next()
            resultado = BinOp(operador, [resultado, Parser.parse_factor()])
        return resultado

    @staticmethod
    def parse_factor():
        tok = Parser.lexer.next
        if tok.type == 'INT':
            val = tok.value
            Parser.lexer.select_next()
            return IntVal(val, [])
        elif tok.type == 'STR':
            val = tok.value
            Parser.lexer.select_next()
            return StringVal(val, [])
        elif tok.type == 'BOOL':
            val = tok.value
            Parser.lexer.select_next()
            return BoolVal(val, [])
        elif tok.type == 'IDEN':
            nome = tok.value
            Parser.lexer.select_next()
            if Parser.lexer.next.type == 'OPEN_PAR':
                Parser.lexer.select_next() 
                args = []
                if Parser.lexer.next.type != 'CLOSE_PAR':
                    args.append(Parser.parse_bool_expression())
                    while Parser.lexer.next.type == 'COMMA':
                        Parser.lexer.select_next()
                        args.append(Parser.parse_bool_expression())
                if Parser.lexer.next.type != 'CLOSE_PAR':
                    raise ValueError("[Parser] Esperado ')' na chamada de função")
                Parser.lexer.select_next()
                return FuncCall(nome, args)
            return Identifier(nome, [])
        elif tok.type in ('MINUS', 'PLUS'):
            sinal = tok.type
            Parser.lexer.select_next()
            return UnOp('-' if sinal == 'MINUS' else '+', [Parser.parse_factor()])
        elif tok.type == 'OPEN_PAR':
            Parser.lexer.select_next()
            expr = Parser.parse_bool_expression()
            if Parser.lexer.next.type != 'CLOSE_PAR':
                raise ValueError("[Parser] Expected ')'")
            Parser.lexer.select_next()
            return expr
        elif tok.type == 'READ':
            Parser.lexer.select_next()
            if Parser.lexer.next.type != 'OPEN_PAR': raise ValueError("[Parser] Esperado '(' após read")
            Parser.lexer.select_next()
            if Parser.lexer.next.type != 'CLOSE_PAR': raise ValueError("[Parser] Esperado ')' após read")
            Parser.lexer.select_next()
            return Read(None, [])
        elif tok.type == 'NOT':
            Parser.lexer.select_next()
            return UnOp('not', [Parser.parse_factor()])
        else:
            raise ValueError(f"[Parser] Unexpected token '{tok.value}' (tipo={tok.type})")


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
        if Parser.lexer.next.type in ('EQ', 'GT', 'LT'):
            op = Parser.lexer.next.value
            Parser.lexer.select_next()
            return BinOp(op, [node_left, Parser.parse_expression()])
        return node_left


    @staticmethod
    def parse_func_declaration():
        Parser.lexer.select_next()  
        if Parser.lexer.next.type != 'IDEN':
            raise ValueError("[Parser] Esperado nome de função após 'function'")
        nome_func = Parser.lexer.next.value
        Parser.lexer.select_next()

        if Parser.lexer.next.type != 'OPEN_PAR':
            raise ValueError("[Parser] Esperado '(' na declaração de função")
        Parser.lexer.select_next()

        params = []
        if Parser.lexer.next.type != 'CLOSE_PAR':
            if Parser.lexer.next.type != 'IDEN':
                raise ValueError("[Parser] Esperado identificador no parâmetro")
            param_nome = Parser.lexer.next.value
            Parser.lexer.select_next()
            if Parser.lexer.next.type != 'TYPE':
                raise ValueError("[Parser] Esperado tipo do parâmetro")
            param_tipo = Parser.lexer.next.value
            Parser.lexer.select_next()
            params.append(VarDec(param_tipo, [Identifier(param_nome, [])]))
            while Parser.lexer.next.type == 'COMMA':
                Parser.lexer.select_next()
                if Parser.lexer.next.type != 'IDEN':
                    raise ValueError("[Parser] Esperado identificador no parâmetro")
                param_nome = Parser.lexer.next.value
                Parser.lexer.select_next()
                if Parser.lexer.next.type != 'TYPE':
                    raise ValueError("[Parser] Esperado tipo do parâmetr")
                param_tipo = Parser.lexer.next.value
                Parser.lexer.select_next()
                params.append(VarDec(param_tipo, [Identifier(param_nome, [])]))

        if Parser.lexer.next.type != 'CLOSE_PAR':
            raise ValueError("[Parser] Esperado ')' na declaração de função")
        Parser.lexer.select_next()
        tipo_retorno = None
        if Parser.lexer.next.type == 'TYPE':
            tipo_retorno = Parser.lexer.next.value
            Parser.lexer.select_next()
        if Parser.lexer.next.type != 'END':
            raise ValueError("[Parser] Esperado '\\n' após assinatura da função")
        Parser.lexer.select_next()
        comandos_corpo = []
        while Parser.lexer.next.type not in ('EOF', 'CLOSE_BRA'):
            if Parser.lexer.next.type == 'END':
                Parser.lexer.select_next()
                continue
            no = Parser.parse_statement()
            comandos_corpo.append(no)
            if Parser.lexer.next.type == 'END':
                Parser.lexer.select_next()
            elif Parser.lexer.next.type not in ('EOF', 'CLOSE_BRA'):
                raise ValueError(f"[Parser] Token inesperado no corpo da função: {Parser.lexer.next.type}")
        corpo = Block(None, comandos_corpo)

        if Parser.lexer.next.type != 'CLOSE_BRA':
            raise ValueError("[Parser] Esperado 'end' ao final da função")
        Parser.lexer.select_next()

        children = [Identifier(nome_func, [])] + params + [corpo]
        return FuncDec(tipo_retorno, children)

    @staticmethod
    def parse_program():
        comandos = []
        while Parser.lexer.next.type != 'EOF':
            if Parser.lexer.next.type == 'END':
                Parser.lexer.select_next()
                continue
            if Parser.lexer.next.type == 'FUNC':
                no = Parser.parse_func_declaration()
            else:
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
        while Parser.lexer.next.type not in ('EOF', 'CLOSE_BRA', 'ELSE'):
            if Parser.lexer.next.type == 'END':
                Parser.lexer.select_next()
                continue
            no = Parser.parse_statement()
            comandos.append(no)
            if Parser.lexer.next.type == 'END':
                Parser.lexer.select_next()
            elif Parser.lexer.next.type not in ('EOF', 'CLOSE_BRA', 'ELSE'):
                raise ValueError(f"[Parser] Token inesperado no bloco: {Parser.lexer.next.type}")
        return Block(None, comandos)

    @staticmethod
    def parse_var_declaration():
        Parser.lexer.select_next()
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


    @staticmethod
    def parse_statement():
        tok = Parser.lexer.next

        if tok.type == 'IF':
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
                if Parser.lexer.next.type != 'CLOSE_BRA': raise ValueError("[Parser] Esperado 'end' após else")
                Parser.lexer.select_next()
                return If(None, [condicao, bloco_then, bloco_else])
            if Parser.lexer.next.type != 'CLOSE_BRA': raise ValueError("[Parser] Esperado 'end'")
            Parser.lexer.select_next()
            return If(None, [condicao, bloco_then])

        elif tok.type == 'WHILE':
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

        elif tok.type == 'IDEN':
            nome = tok.value
            Parser.lexer.select_next()
            if Parser.lexer.next.type == 'OPEN_PAR':
                Parser.lexer.select_next() 
                args = []
                if Parser.lexer.next.type != 'CLOSE_PAR':
                    args.append(Parser.parse_bool_expression())
                    while Parser.lexer.next.type == 'COMMA':
                        Parser.lexer.select_next()
                        args.append(Parser.parse_bool_expression())
                if Parser.lexer.next.type != 'CLOSE_PAR':
                    raise ValueError("[Parser] Esperado ')' na chamada de função")
                Parser.lexer.select_next()
                return FuncCall(nome, args)
            elif Parser.lexer.next.type == 'ASSIGN':
                Parser.lexer.select_next()
                expression = Parser.parse_bool_expression()
                return Assignment(None, [Identifier(nome, []), expression])
            else:
                raise ValueError(f"[Parser] Esperado '=' ou '(' após identificador '{nome}'")

        elif tok.type == 'PRINT':
            Parser.lexer.select_next()
            if Parser.lexer.next.type != 'OPEN_PAR': raise ValueError("[Parser] Esperado '('")
            Parser.lexer.select_next()
            expression = Parser.parse_bool_expression()
            if Parser.lexer.next.type != 'CLOSE_PAR': raise ValueError("[Parser] Esperado ')'")
            Parser.lexer.select_next()
            return Print(None, [expression])

        elif tok.type == 'OPEN_BRA':
            Parser.lexer.select_next()
            if Parser.lexer.next.type == 'END': Parser.lexer.select_next()
            bloco = Parser.parse_block()
            if Parser.lexer.next.type != 'CLOSE_BRA': raise ValueError("[Parser] Esperado 'end'")
            Parser.lexer.select_next()
            return bloco

        elif tok.type == 'VAR':
            return Parser.parse_var_declaration()
        elif tok.type == 'RETURN':
            Parser.lexer.select_next()
            expression = Parser.parse_bool_expression()
            return Return(None, [expression])

        else:
            return NoOp()


def main():
    nome_arquivo = sys.argv[1]
    with open(nome_arquivo, "r") as f:
        entrada = f.read() + "\n"
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

    asm_filename = nome_arquivo.rsplit('.', 1)[0] + '.asm'
    Code.dump(asm_filename)

if __name__ == "__main__":
    main()