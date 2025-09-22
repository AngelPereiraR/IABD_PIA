cadena = input("Introduce una cadena de caracteres: ")
while(True):
  caracter = input("Introduce un caracter: ")
  
  if(len(caracter) == 1):
    break
  
cadena = cadena.replace(cadena[0], caracter)

print(cadena)