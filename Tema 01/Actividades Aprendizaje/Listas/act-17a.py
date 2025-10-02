import random as rd

numRandom = rd.randint(30, 40)

numeros = [rd.randint(1, 30) for _ in range(numRandom)]

sinDuplicados = list(set(numeros))

print(f"Números generados ({numRandom}): {numeros}")
print(f"Números sin duplicados: {sinDuplicados}")