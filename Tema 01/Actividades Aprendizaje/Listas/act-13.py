nombres = []
kms = []

while True:
  nombre = input("Introduce el nombre del conductor (o * para terminar): ")
  nombres.append(nombre)
  if nombre == "*":
    break
  for diaSemana in [0, 1, 2, 3, 4, 5, 6]:
    while True:
      try:
        km = float(input(f"Introduce los kilómetros recorridos el día {diaSemana + 1} de la semana: "))
        if km < 0:
          raise ValueError
        if len(kms) <= diaSemana:
          kms.append([])
        kms[diaSemana].append(km)
        break
      except ValueError:
        print("Por favor, introduce un número válido (no negativo).")

for i in range(len(nombres) - 1):
  total_km = sum(kms[dia][i] for dia in range(len(kms)) if i < len(kms[dia]))
  print(f"El conductor {nombres[i]} ha recorrido un total de {total_km} km en la semana.")