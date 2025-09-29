diagonal = []
filas = -1
columnas = -1

while True:
  try:
    filas = int(input("Introduce el número de filas: "))
    if(filas < 1):
      raise ValueError
    columnas = int(input("Introduce el número de columnas: "))
    if(columnas < 1):
      raise ValueError
    break
  except ValueError:
    print("Introduce valores numéricos positivos.")

for i in range(filas):
  diagonal.append([])
  for j in range(columnas):
    if i == j:
      diagonal[i].append(1)
    else:
      diagonal[i].append(0)


print("Matriz:")
for fila in diagonal:
  print(fila)
