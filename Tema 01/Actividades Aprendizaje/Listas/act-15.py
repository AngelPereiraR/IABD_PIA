lista = []
while True:
  try:
    print(f"{'*'*10} Menú {'*'*10}")
    print("1. Añadir número a la lista.")
    print("2. Añadir número de la lista en una posición.")
    print("3. Longitud de la lista.")
    print("4. Eliminar el último número.")
    print("5. Eliminar un número.")
    print("6. Contar números.")
    print("7. Posiciones de un número.")
    print("8. Mostrar lista.")
    print("9. Salir.")
    opcion = int(input("Elige una opción (1-9): "))
    
    if opcion == 1:
      numero = int(input("Introduce un número para añadir a la lista: "))
      lista.append(numero)
      print(f"Número {numero} añadido a la lista.")
    elif opcion == 2:
      numero = int(input("Introduce un número para añadir a la lista: "))
      posicion = int(input(f"Introduce la posición (1 a {len(lista) + 1}) donde quieres añadir el número: "))
      if posicion < 1 or posicion > len(lista) + 1:
        print("Posición no válida.")
      else:
        lista.insert(posicion - 1, numero)
        print(f"Número {numero} añadido en la posición {posicion}.")
    elif opcion == 3:
      print(f"La longitud de la lista es: {len(lista)}")
    elif opcion == 4:
      if lista:
        eliminado = lista.pop()
        print(f"Número {eliminado} eliminado de la lista.")
      else:
        print("La lista está vacía.")
    elif opcion == 5:
      numero = int(input("Introduce el número que quieres eliminar de la lista: "))
      if numero in lista:
        lista.remove(numero)
        print(f"Número {numero} eliminado de la lista.")
      else:
        print(f"El número {numero} no está en la lista.")
    elif opcion == 6:
      numero = int(input("Introduce el número que quieres contar en la lista: "))
      contador = lista.count(numero)
      print(f"El número {numero} aparece {contador} veces en la lista.")
    elif opcion == 7:
      numero = int(input("Introduce el número del que quieres conocer las posiciones en la lista: "))
      posiciones = [i for i, x in enumerate(lista) if x == numero]
      if posiciones:
        print(f"El número {numero} está en las posiciones: {posiciones}")
      else:
        print(f"El número {numero} no está en la lista.")
    elif opcion == 8:
      print(f"Lista actual: {lista}")
    elif opcion == 9:
      print("Saliendo del programa.")
      break
  except ValueError:
    print("Por favor, introduce un valor válido.")
    continue