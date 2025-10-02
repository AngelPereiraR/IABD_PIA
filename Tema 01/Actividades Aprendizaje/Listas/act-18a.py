listaPalabras = []

def contarPalabras(lista):
    contador = {}
    for palabra in lista:
        if palabra in contador:
            contador[palabra] += 1
        else:
            contador[palabra] = 1
    return contador
  
def modificarLista(lista, palabra, nuevaPalabra):
    return [nuevaPalabra if p == palabra else p for p in lista]
  
def eliminarPalabra(lista, palabra):
    return [p for p in lista if p != palabra]
  
def mostrarLista(lista):
    print("Lista actual:", lista)
    print("Conteo de palabras:", contarPalabras(lista))
    
while True:
    print(f"{'*'*10} Menú {'*'*10}")
    print("1. Añadir palabra a la lista.")
    print("2. Modificar palabra en la lista.")
    print("3. Eliminar palabra de la lista.")
    print("4. Mostrar lista y conteo de palabras.")
    print("5. Salir.")
    
    try:
        opcion = int(input("Elige una opción (1-5): "))
        
        if opcion == 1:
            palabra = input("Introduce una palabra para añadir a la lista: ")
            listaPalabras.append(palabra)
            print(f"Palabra '{palabra}' añadida a la lista.")
        
        elif opcion == 2:
            palabra = input("Introduce la palabra que quieres modificar: ")
            if palabra in listaPalabras:
                nuevaPalabra = input(f"Introduce la nueva palabra para reemplazar '{palabra}': ")
                listaPalabras = modificarLista(listaPalabras, palabra, nuevaPalabra)
                print(f"Palabra '{palabra}' modificada a '{nuevaPalabra}'.")
            else:
                print(f"La palabra '{palabra}' no está en la lista.")
        
        elif opcion == 3:
            palabra = input("Introduce la palabra que quieres eliminar de la lista: ")
            if palabra in listaPalabras:
                listaPalabras = eliminarPalabra(listaPalabras, palabra)
                print(f"Palabra '{palabra}' eliminada de la lista.")
            else:
                print(f"La palabra '{palabra}' no está en la lista.")
        
        elif opcion == 4:
            mostrarLista(listaPalabras)
        
        elif opcion == 5:
            print("Saliendo del programa.")
            break
        
        else:
            print("Opción no válida. Por favor, elige una opción entre 1 y 5.")
    
    except ValueError:
        print("Por favor, introduce un valor válido.")