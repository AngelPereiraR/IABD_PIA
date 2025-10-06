# act-06.py
# Archivo de ejercicios de funciones
def calcularAreaPerimetroCircunferencia(radio):
  """Función que calcula el área y el perímetro de una circunferencia dado su radio"""
  import math
  area = math.pi * radio ** 2
  perimetro = 2 * math.pi * radio
  return area, perimetro

def main():
  while True:
    try:
      radio = float(input("Introduce el radio de la circunferencia: "))
      if radio < 0:
          raise ValueError("El radio no puede ser negativo.")
      area, perimetro = calcularAreaPerimetroCircunferencia(radio)
      print(f"El área de la circunferencia es: {area:.2f}")
      print(f"El perímetro de la circunferencia es: {perimetro:.2f}")
      break
    except ValueError as e:
      print(f"Error: {e}")
    

main()