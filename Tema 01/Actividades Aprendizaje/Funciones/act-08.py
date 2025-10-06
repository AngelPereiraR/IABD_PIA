# act-08.py
# Archivo de ejercicios de funciones
def calcularFactorial(n):
  """Función recursiva que calcula el factorial de un número n"""
  if n == 0:
    return 1
  else:
    return n * calcularFactorial(n-1)
  
def main():
  while True:
    try:
      numero = int(input("Introduce un número para calcular su factorial: "))
      if numero < 0:
        print("El factorial no está definido para números negativos.")
      else:
        print(f"El factorial de {numero} es {calcularFactorial(numero)}")
      break
    except ValueError:
      print("Por favor, introduce un número entero válido.")
    
main()