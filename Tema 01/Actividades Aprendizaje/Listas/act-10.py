import random

listaBi = []

for i in range(5):
  listaBi.append([])
  for j in range(5):
    listaBi[i].append(int(random.random() * 10))
  
sumaFilas = [sum(fila) for fila in listaBi]  
sumaColumnas = [sum(listaBi[i][j] for i in range(5)) for j in range(5)]

print("Matriz:")
for fila in listaBi:
  print(fila)

print(f"Suma de filas: {sumaFilas}")
print(f"Suma de columnas: {sumaColumnas}")