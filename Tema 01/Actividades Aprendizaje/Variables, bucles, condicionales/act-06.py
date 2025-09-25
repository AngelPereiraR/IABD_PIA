cadena = input("Introduce una cadena de caracteres: ")

if(len(cadena) > 10):
  cadena = cadena.upper()
else:
  cadena = cadena.lower()
  
print(cadena)