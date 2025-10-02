def sumar(lista):
    if len(lista) == 0:
        return 0
    else:
        return lista[0] + sumar(lista[1:])

print(sumar([1, 2, 3, 4]))