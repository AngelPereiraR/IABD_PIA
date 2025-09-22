cadena = input("Introduce una cadena de caracteres: ")
subcadena = input("Introduce una subcadena de caracteres: ")

contiene = int(cadena.find(subcadena))

if(contiene != -1):
  print("La cadena contiene la subcadena.")
else:
  print("La cadena NO contiene la subcadena.")