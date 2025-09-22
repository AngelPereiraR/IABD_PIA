edad = int(input("Introduce tu edad: "))

if(edad < 12):
  categoria = "Niño"
elif(edad <= 18):
  categoria = "Adolescente"
else:
  categoria = "Adulto"
  
print(f"Te encuentras en la categoría {categoria}")