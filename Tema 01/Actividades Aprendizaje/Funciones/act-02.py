# act-02.py
# Archivo de ejercicios de funciones
def EsMultiplo(numero1, numero2):
  """Función que devuelve True si numero1 es múltiplo de numero2"""
  if numero1 == 0 or numero2 == 0:
      return False
  return numero1 % numero2 == 0 or numero2 % numero1 == 0

print(EsMultiplo(4, 2))
print(EsMultiplo(2, 4))