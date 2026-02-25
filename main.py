import sys
def main ():
    if len(sys.argv) < 2:
        return
    entrada = sys.argv[1]

    numeros = '0123456789'
    operadores = ['+', '-']
    itens = []

    i = 0
    while i < len(entrada):
        if entrada[i] == ' ':
            i += 1
            continue
        elif entrada[i] in numeros:
            num = ''    
            while i < len(entrada) and entrada[i] in numeros:
                num += entrada[i]
                i+=1
            itens.append(num)
            continue

        elif entrada[i] in operadores:
            itens.append(entrada[i])
            i+=1    
        else:
            raise Exception()
        
    # print(itens)

    resultado = int(itens[0])
    j=1
    while j < len(itens):

        op = itens[j]
        if op not in operadores:
            raise Exception()
        
        if j+1 >= len(itens):
            raise Exception()
        
        proximo = int(itens[j+1])

        if op == '+':
            resultado += proximo
        elif op == '-':
            resultado -= proximo

        j+=2
    
    print(resultado)

if __name__ == "__main__":
    main()