# act-15.py
# Archivo de ejercicios de funciones
def LongitudCola(cola):
    """Función que devuelve la longitud de una cola representada como una lista"""
    return len(cola)

def EstaVaciaCola(cola):
    """Función que devuelve True si la cola está vacía"""
    return len(cola) == 0

def EstaLlenaCola(cola, capacidad):
    """Función que devuelve True si la cola está llena dado su capacidad máxima"""
    return len(cola) >= capacidad

def AddCola(cola, elemento, capacidad):
    """Función que añade un elemento a la cola si no está llena"""
    if EstaLlenaCola(cola, capacidad):
        print("Error: La cola está llena. No se puede añadir el elemento.")
        return False
    cola.append(elemento)
    return True

def SacarDeLaCola(cola):
    """Función que saca y devuelve el elemento superior de la cola si no está vacía"""
    if EstaVaciaCola(cola):
        print("Error: La cola está vacía. No se puede sacar ningún elemento.")
        return None
    return cola.pop(0)

def EscribirCola(cola):
    """Función que imprime los elementos de la cola"""
    if EstaVaciaCola(cola):
        print("La cola está vacía.")
    else:
        print("Elementos de la cola (de delante a atrás):")
        for elemento in cola:
            print(elemento)
            
def main():
    cola = []
    capacidad = 0
    while True:
        try:
            capacidad = int(input("Introduce la capacidad máxima de la cola: "))
            if capacidad <= 0:
                raise ValueError("La capacidad debe ser un número positivo.")
            break
        except ValueError as e:
            print(f"Error: {e}")
            
    while True:
        print("---- Menú ----")
        print("1. Añadir elemento a la cola")
        print("2. Sacar elemento de la cola")
        print("3. Ver longitud de la cola")
        print("4. Mostrar cola")
        print("5. Salir")
        
        opcion = input("Elige una opción (1-5): ")
        if opcion == '1':
            elemento = input("Introduce el elemento a añadir: ")
            if AddCola(cola, elemento, capacidad):
                print(f"Elemento '{elemento}' añadido a la cola.")
        elif opcion == '2':
            elemento = SacarDeLaCola(cola)
            if elemento is not None:
                print(f"Elemento '{elemento}' sacado de la cola.")
        elif opcion == '3':
            longitud = LongitudCola(cola)
            print(f"La longitud de la cola es: {longitud}")
        elif opcion == '4':
            EscribirCola(cola)
        elif opcion == '5':
            print("Saliendo del programa...")
            break
        else:
            print("Opción no válida. Por favor, elige una opción del 1 al 5.")
            
main()