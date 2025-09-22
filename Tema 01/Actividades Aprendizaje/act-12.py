cadena = input("Introduce una cadena de caracteres: ")
subcadena = input("Introduce una subcadena de caracteres: ")

contiene = True

for index in range(len(subcadena)):
  if(cadena[index] != subcadena[index]):
    contiene = False
    break
    
if(contiene):
  print("La cadena comienza por la subcadena.")
else:
  print("La cadena NO comienza por la subcadena.")