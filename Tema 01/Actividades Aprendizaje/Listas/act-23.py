lista = [3, 5, 2, 7, 9]

def encontrarParMasParecido(lista):
    if len(lista) < 2:
        return None  # No hay suficientes elementos para formar un par
    else:
        lista.sort()
        parMasParecido = (lista[0], lista[1])
        menorDiferencia = abs(lista[0] - lista[1])

        for i in range(1, len(lista) - 1):
            diferencia = abs(lista[i] - lista[i + 1])
            if diferencia < menorDiferencia:
                menorDiferencia = diferencia
                parMasParecido = (lista[i], lista[i + 1])

        return parMasParecido

def encontrarParDiferente(lista):
    if len(lista) < 2:
        return None  # No hay suficientes elementos para formar un par
    else:
      numMin = min(lista)
      numMax = max(lista)

      return (numMin, numMax)

print(encontrarParMasParecido(lista))
print(encontrarParDiferente(lista))