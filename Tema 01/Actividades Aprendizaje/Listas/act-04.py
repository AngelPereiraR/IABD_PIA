lista = []

while True:
  try:
    numero = int(input("Introduce un número (introduce un número negativo para salir): "))
    if numero < 0:
      break
    lista.append(numero)
  except ValueError:
    print("Por favor, introduce un número válido.")

print(f"Lista de números: {lista}")