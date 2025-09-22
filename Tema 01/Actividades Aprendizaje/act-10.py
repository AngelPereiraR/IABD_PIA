accion = ""
a = 0
b = 0

while(True):
  print("---- Calculadora simple ----")
  
  while(True):
    accion = input("Introduce la acción a realizar (+, -, *, /) o 'salir' para terminar: ")
  
    if(accion == "salir"):
      print("Saliendo de la calculadora...")
      break
    elif(accion in ['+', '-', '*', '/']):
      break
    
  if(accion == "salir"):
    break
  
  while(True):
    try:
      a = float(input("Introduce el primer número: "))
      b = float(input("Introduce el segundo número: "))
    
      if(accion == "+"):
        print(f"{a} + {b} = {a + b}")
      elif(accion == "-"):
        print(f"{a} - {b} = {a - b}")
      elif(accion == "*"):
        print(f"{a} * {b} = {a * b}")
      elif(accion == "/"):
        if b != 0:
          print(f"{a} / {b} = {a / b}")
        else:
          print("Error: División por cero no permitida.")
      break
    except:
      print("Error: Los valores introducidos deben ser numéricos.")