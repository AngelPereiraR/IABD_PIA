# act-03.py
# Archivo de ejercicios de funciones
def TemperaturaMedia(temp_max, temp_min):
  """Función que devuelve la temperatura media a partir de la temperatura máxima y mínima"""
  if temp_max < temp_min:
      raise ValueError("La temperatura máxima no puede ser menor que la mínima.")
  return (temp_max + temp_min) / 2
  
def main():
  dias = int(input("Introduce el número de días: "))
  try:
    for i in range(dias):
      temp_max = float(input(f"Introduce la temperatura máxima del día {i+1}: "))
      temp_min = float(input(f"Introduce la temperatura mínima del día {i+1}: "))
      print(f"La temperatura media del día {i+1} es: {TemperaturaMedia(temp_max, temp_min)}")
  except ValueError as e:
    print(f"Error: {e}")
    
main()