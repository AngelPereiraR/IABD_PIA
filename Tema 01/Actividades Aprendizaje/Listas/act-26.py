listaDeListaCadenas = [["Hola", "mundo"], ["esto", "es", "una", "prueba"], ["Python", "es", "genial"]]

def buscarPosicionPalabra(lista, palabra, fila=0, columna=0):
    if fila >= len(lista):
        return (-1, -1)
    if columna >= len(lista[fila]):
        return buscarPosicionPalabra(lista, palabra, fila + 1, 0)
    if lista[fila][columna] == palabra:
        return (fila, columna)
    return buscarPosicionPalabra(lista, palabra, fila, columna + 1)

print(buscarPosicionPalabra(listaDeListaCadenas, "prueba"))
print(buscarPosicionPalabra(listaDeListaCadenas, "Python"))
print(buscarPosicionPalabra(listaDeListaCadenas, "Java"))