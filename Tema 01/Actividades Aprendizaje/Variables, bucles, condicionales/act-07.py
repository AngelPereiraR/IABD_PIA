numero = int(input("Introduce un número: "))

if(numero < 0):
  print("El número es menor que 0.")
elif(numero <= 10):
  print("El número está entre 0 y 10.")
else:
  print("El número es mayor que 10.")