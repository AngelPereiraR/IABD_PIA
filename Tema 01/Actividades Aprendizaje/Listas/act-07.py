lista1 = []
lista2 = []

for i in range(5):
  try:
    lista1.append(int(input(f"Introduce el número {i + 1} para la lista 1: ")))
    lista2.append(int(input(f"Introduce el número {i + 1} para la lista 2: ")))
  except ValueError:
    print("Por favor, introduce un número válido.")

listaSuma = [lista1[i] + lista2[i] for i in range(5)]

print(f"Lista 1: {lista1}")
print(f"Lista 2: {lista2}")
print(f"Suma de listas: {listaSuma}")