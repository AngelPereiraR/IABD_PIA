meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
diasMes = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

mes = 0
while mes < 1 or mes > 12:
  try:
    mes = int(input("Introduce un número de mes (1-12): "))
    if mes < 1 or mes > 12:
      print("Número de mes inválido. Debe estar entre 1 y 12.")
  except ValueError:
    print("Por favor, introduce un número válido.")
    
print(f"El mes de {meses[mes - 1]} tiene {diasMes[mes - 1]} días.")