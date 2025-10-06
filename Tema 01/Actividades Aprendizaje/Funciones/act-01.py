# act-01.py
# Archivo de ejercicios de funciones
def EscribirCentrado(texto):
  """Función que escribe un texto centrado en una línea de 80 caracteres, subrayando con '='"""
  longitud = len(texto)
  if(longitud >= 80):
    print(texto)
    return
  elif(longitud % 2 != 0):
    texto += '='
    longitud += 1
  espacios = (80 - longitud) // 2
  print(' ' * espacios + texto + ' ' * espacios)
  print(' ' * espacios + '=' * longitud + ' ' * espacios)
  
EscribirCentrado("Hola Mundo")