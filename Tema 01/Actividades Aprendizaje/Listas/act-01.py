import random

listaNumeros = []

for i in range(10):
  listaNumeros.append(int(random.random() * 10))

for index in range(len(listaNumeros)):
  print(f"Número {index + 1}: {listaNumeros[index]}. Cuadrado: {listaNumeros[index]**2}. Cubo: {listaNumeros[index]**3}")