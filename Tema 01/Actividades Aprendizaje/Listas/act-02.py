listaCadenas = []

for i in range(5):
  cadena = input(f"Introduce la cadena {i + 1}: ")
  listaCadenas.append(cadena)

nuevaLista = listaCadenas.copy()
nuevaLista.reverse()

for cadena in nuevaLista:
  print(cadena)