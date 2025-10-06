# act-14.py
# Archivo de ejercicios de funciones
def LongitudPila(pila):
    """Función que devuelve la longitud de una pila representada como una lista"""
    return len(pila)

def EstaVaciaPila(pila):
    """Función que devuelve True si la pila está vacía"""
    return len(pila) == 0

def EstaLlenaPila(pila, capacidad):
    """Función que devuelve True si la pila está llena dado su capacidad máxima"""
    return len(pila) >= capacidad

def AddPila(pila, elemento, capacidad):
    """Función que añade un elemento a la pila si no está llena"""
    if EstaLlenaPila(pila, capacidad):
        print("Error: La pila está llena. No se puede añadir el elemento.")
        return False
    pila.append(elemento)
    return True

def SacarDeLaPila(pila):
    """Función que saca y devuelve el elemento superior de la pila si no está vacía"""
    if EstaVaciaPila(pila):
        print("Error: La pila está vacía. No se puede sacar ningún elemento.")
        return None
    return pila.pop()

def EscribirPila(pila):
    """Función que imprime los elementos de la pila"""
    if EstaVaciaPila(pila):
        print("La pila está vacía.")
    else:
        print("Elementos de la pila (de arriba a abajo):")
        for elemento in reversed(pila):
            print(elemento)
            
def main():
    pila = []
    capacidad = 0
    while True:
        try:
            capacidad = int(input("Introduce la capacidad máxima de la pila: "))
            if capacidad <= 0:
                raise ValueError("La capacidad debe ser un número positivo.")
            break
        except ValueError as e:
            print(f"Error: {e}")
            
    while True:
        print("---- Menú ----")
        print("1. Añadir elemento a la pila")
        print("2. Sacar elemento de la pila")
        print("3. Ver longitud de la pila")
        print("4. Mostrar pila")
        print("5. Salir")
        
        opcion = input("Elige una opción (1-5): ")
        if opcion == '1':
            elemento = input("Introduce el elemento a añadir: ")
            if AddPila(pila, elemento, capacidad):
                print(f"Elemento '{elemento}' añadido a la pila.")
        elif opcion == '2':
            elemento = SacarDeLaPila(pila)
            if elemento is not None:
                print(f"Elemento '{elemento}' sacado de la pila.")
        elif opcion == '3':
            longitud = LongitudPila(pila)
            print(f"La longitud de la pila es: {longitud}")
        elif opcion == '4':
            EscribirPila(pila)
        elif opcion == '5':
            print("Saliendo del programa...")
            break
        else:
            print("Opción no válida. Por favor, elige una opción del 1 al 5.")
            
main()