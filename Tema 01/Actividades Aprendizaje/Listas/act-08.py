nombres = []
edades = []

nombre = ""

while nombre != "*":
  nombre = input("Introduce un nombre para el alumno (o * para terminar): ")
  if nombre != "*":
    try:
      edad = int(input(f"Introduce la edad de {nombre}: "))
      nombres.append(nombre)
      edades.append(edad)
    except ValueError:
      print("Por favor, introduce un número válido para la edad.")
  else:
    break
  
posicionesMayoresEdad = []
edadMayor = -1
nombresMayores = []
for i in range(len(edades)):
  if edades[i] >= 18:
    posicionesMayoresEdad.append(i)
  if edades[i] > edadMayor:
    edadMayor = edades[i]
    nombresMayores = [nombres[i]]
  elif edades[i] == edadMayor:
    nombresMayores.append(nombres[i])

print(f"Nombres de alumnos mayores de edad: {[nombres[i] for i in posicionesMayoresEdad]}")
print(f"Nombre(s) del alumno/a mayor de edad: {nombresMayores}")