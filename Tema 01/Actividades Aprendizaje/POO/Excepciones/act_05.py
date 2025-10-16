# act-05.py
# POO - Excepciones - ejercicio 5

def Calcular_mcd(numerador, denominador):
    """Función que calcula el máximo común divisor (MCD) de dos números enteros positivos."""
    while denominador != 0:
        numerador, denominador = denominador, numerador % denominador
    return numerador
            
def Escribir_fracción(numerador, denominador):
    """Función que escribe una fracción en la forma 'numerador/denominador'."""
    print(f"La fracción simplificada es: {numerador}/{denominador}")

def Simplificar_fracción(numerador, denominador):
    """Función que simplifica una fracción dada su numerador y denominador."""
    if denominador == 0:
        raise ValueError("El denominador no puede ser cero.")
    mcd = Calcular_mcd(abs(numerador), abs(denominador))
    return Escribir_fracción(numerador // mcd, denominador // mcd)

def Leer_fracción():
    """Función que lee una fracción del usuario y la devuelve como una tupla (numerador, denominador)."""
    while True:
        try:
            fraccion = input("Introduce una fracción en la forma 'numerador/denominador': ")
            numerador, denominador = map(int, fraccion.split('/'))
            if denominador == 0:
                print("El denominador no puede ser cero. Inténtalo de nuevo.")
                continue
            return (numerador, denominador)
        except ValueError:
            print("Entrada inválida. Asegúrate de introducir la fracción en el formato correcto.")
    
def Sumar_fracciones(n1, d1, n2, d2):
    """Función que suma dos fracciones y devuelve el resultado simplificado."""
    numerador = n1 * d2 + n2 * d1
    denominador = d1 * d2
    return Simplificar_fracción(numerador, denominador)

def Restar_fracciones(n1, d1, n2, d2):
    """Función que resta dos fracciones y devuelve el resultado simplificado."""
    numerador = n1 * d2 - n2 * d1
    denominador = d1 * d2
    return Simplificar_fracción(numerador, denominador)

def Multiplicar_fracciones(n1, d1, n2, d2):
    """Función que multiplica dos fracciones y devuelve el resultado simplificado."""
    numerador = n1 * n2
    denominador = d1 * d2
    return Simplificar_fracción(numerador, denominador)

def Dividir_fracciones(n1, d1, n2, d2):
    """Función que divide dos fracciones y devuelve el resultado simplificado."""
    if n2 == 0:
        raise ValueError("No se puede dividir por una fracción con numerador cero.")
    numerador = n1 * d2
    denominador = d1 * n2
    return Simplificar_fracción(numerador, denominador)

def main():
    print("Operaciones con fracciones:")
    print("1. Sumar")
    print("2. Restar")
    print("3. Multiplicar")
    print("4. Dividir")
    
    while True:
        try:
            opcion = int(input("Selecciona una operación (1-4): "))
            if opcion not in [1, 2, 3, 4]:
                print("Opción inválida. Inténtalo de nuevo.")
                continue
            
            print("Introduce la primera fracción:")
            n1, d1 = Leer_fracción()
            print("Introduce la segunda fracción:")
            n2, d2 = Leer_fracción()
            
            if opcion == 1:
                Sumar_fracciones(n1, d1, n2, d2)
            elif opcion == 2:
                Restar_fracciones(n1, d1, n2, d2)
            elif opcion == 3:
                Multiplicar_fracciones(n1, d1, n2, d2)
            elif opcion == 4:
                Dividir_fracciones(n1, d1, n2, d2)
            break
        except ValueError as e:
            print(f"Error: {e}")
            
main()