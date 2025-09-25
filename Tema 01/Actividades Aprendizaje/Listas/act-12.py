marco = []

for i in range(5):
  marco.append([])
  for j in range(15):
    if(i == 0 or i == 4 or j == 0 or j == 14):
      marco[i].append(1)
    else:
      marco[i].append(0)

print("Matriz:")
for fila in marco:
  print(fila)

