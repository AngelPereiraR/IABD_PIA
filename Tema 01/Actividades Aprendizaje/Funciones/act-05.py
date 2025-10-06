# act-05.py
# Archivo de ejercicios de funciones
def calcularMinMax(lista):
  """Función que devuelve el valor mínimo y máximo de una lista"""
  if not lista:
      return None, None
  return max(lista), min(lista)

def main():
  numeros = []
  
  while True:
    entrada = input("Introduce un número (o 'fin' para terminar): ")
    if entrada.lower() == 'fin':
        break
    try:
        numero = float(entrada)
        numeros.append(numero)
    except ValueError:
        print("Por favor, introduce un número válido.")

  maximo, minimo = calcularMinMax(numeros)
  if maximo is not None and minimo is not None:
      print(f"El valor máximo es: {maximo}")
      print(f"El valor mínimo es: {minimo}")

main()