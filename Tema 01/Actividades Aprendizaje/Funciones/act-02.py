# act-02.py
# Archivo de ejercicios de funciones
def EsMultiplo(numero1, numero2):
  """Función que devuelve True si numero1 es múltiplo de numero2 o viceversa"""
  if numero1 == 0 or numero2 == 0:
      return False
  return numero1 % numero2 == 0 or numero2 % numero1 == 0

while True:
    try:
        num1 = int(input("Introduce el primer número: "))
        num2 = int(input("Introduce el segundo número: "))

        print(EsMultiplo(num1, num2))
        break
    except ValueError:
        print("Por favor, introduce números enteros válidos.")