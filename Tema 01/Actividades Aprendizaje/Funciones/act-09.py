# act-09.py
# Archivo de ejercicios de funciones
def MCDEuclides(a, b):
  """Función que calcula el máximo común divisor (MCD) de dos números usando el algoritmo de Euclides"""
  while b:
      a, b = b, a % b
  return a
  
def main():
  while True:
    try:
      num1 = int(input("Introduce el primer número: "))
      num2 = int(input("Introduce el segundo número: "))
      if num1 <= 0 or num2 <= 0:
          print("Por favor, introduce números enteros positivos.")
      else:
          print(f"El MCD de {num1} y {num2} es {MCDEuclides(num1, num2)}")
      break
    except ValueError:
        print("Por favor, introduce números enteros válidos.")
        
main()