import random

listaNumeros = []

for i in range(10):
  listaNumeros.append(int(random.random() * 100))
  
print(f"Números generados: {listaNumeros}")
  
listaNumeros.sort()

print(f"Números ordenados: {listaNumeros}")