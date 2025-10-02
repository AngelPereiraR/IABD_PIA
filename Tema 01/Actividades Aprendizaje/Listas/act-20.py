def contarMayores(lista, umbral):
    if len(lista) == 0:
        return 0
    else:
        count = 1 if lista[0] > umbral else 0
        return count + contarMayores(lista[1:], umbral)
      
print(contarMayores([1, 5, 8, 12], 6))