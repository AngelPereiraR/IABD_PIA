def filtrarPalabrasLargas(lista):
    if len(lista) == 0:
        return []
    else:
        cabeza = lista[0]
        cola = lista[1:]
        if len(cabeza) > 5:
            return [cabeza] + filtrarPalabrasLargas(cola)
        else:
            return filtrarPalabrasLargas(cola)

print(filtrarPalabrasLargas(['hola', 'javascript', 'clase', 'expresiones']))