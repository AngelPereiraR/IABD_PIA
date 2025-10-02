lista = [3, 5, 2, 7, 9]

def encontrarParParecido(lista):
    if len(lista) < 2:
        return None  # No hay suficientes elementos para formar un par
    else:
      copiaLista = lista.copy()
      numMin = min(copiaLista)
      copiaLista.remove(numMin)
      segundoNumMin = min(copiaLista)

      return (numMin, segundoNumMin)

def encontrarParDiferente(lista):
    if len(lista) < 2:
        return None  # No hay suficientes elementos para formar un par
    else:
      numMin = min(lista)
      numMax = max(lista)

      return (numMin, numMax)

print(encontrarParParecido(lista))
print(encontrarParDiferente(lista))