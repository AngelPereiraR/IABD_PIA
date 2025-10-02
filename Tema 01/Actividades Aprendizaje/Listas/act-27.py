pares = [(1, 2), (2, 3), (1, 3), (4, 2)]

contador = {}

for tupla in pares:
    for valor in tupla:
        if valor in contador:
            contador[valor] += 1
        else:
            contador[valor] = 1

print("Conteo de valores:")
for valor, cantidad in contador.items():
    print(f"'{valor}': {cantidad} veces")