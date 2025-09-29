matriz = [[3, 5, 2, 8], [7, 9, 1, 4], [6, 8, 2, 5]]

def devolverTranspuesta(matriz):
    transpuesta = []
    for i in range(len(matriz[0])):
        nuevaFila = []
        for fila in matriz:
            nuevaFila.append(fila[i])
        transpuesta.append(nuevaFila)
    return transpuesta

print(devolverTranspuesta(matriz))