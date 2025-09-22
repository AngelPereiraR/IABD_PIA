cadena = input("Introduce una cadena de caracteres: ")
while(True):
  caracter = input("Introduce un caracter: ")
  
  if(len(caracter) == 1):
    break

count = cadena.count(caracter)

print(f"El caracter {caracter} aparece {count} veces en la cadena.")