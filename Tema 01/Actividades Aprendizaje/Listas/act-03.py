listaNotas = []

for i in range(5):
  nota = float(input(f"Introduce la nota {i + 1} (entre 0 y 10): "))
  while nota < 0 or nota > 10:
    print("Nota inválida. Debe estar entre 0 y 10.")
    nota = float(input(f"Introduce la nota {i + 1} (entre 0 y 10): "))
  listaNotas.append(nota)
  
print(f"Lista de notas: {listaNotas}")
print(f"Media: {sum(listaNotas) / len(listaNotas)}")
print(f"Nota más alta: {max(listaNotas)}")
print(f"Nota más baja: {min(listaNotas)}")