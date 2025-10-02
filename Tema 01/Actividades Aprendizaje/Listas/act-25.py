listaDeListaCadenas = [["Hola", "mundo"], ["esto", "es", "una", "prueba"], ["Python", "es", "genial"]]

def concatenarElementosFila(lista, fila, posicion=0):
    if fila < 0 or fila >= len(lista):
        return ""
    if posicion >= len(lista[fila]):
        return ""
    else:
        return lista[fila][posicion] + " " + concatenarElementosFila(lista, fila, posicion + 1)
      
print(concatenarElementosFila(listaDeListaCadenas, 1))
print(concatenarElementosFila(listaDeListaCadenas, 0))