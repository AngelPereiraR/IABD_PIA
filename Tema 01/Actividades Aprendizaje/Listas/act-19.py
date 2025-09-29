def encontrarMaximo(lista):
    if len(lista) == 1:
        return lista[0]
    else:
        maximoResto = encontrarMaximo(lista[1:])
        return lista[0] if lista[0] > maximoResto else maximoResto
      
print(encontrarMaximo([7, 2, 10, 3]))