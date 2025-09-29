marco = []
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
  marco.append([])
  for j in range(columnas):
    if(i == 0 or i == filas - 1 or j == 0 or j == columnas - 1):
      marco[i].append(1)
    else:
      marco[i].append(0)

print("Matriz:")
for fila in marco:
  print(fila)

