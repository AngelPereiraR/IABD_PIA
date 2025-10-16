# act-01.py
# POO - Excepciones - ejercicio 1

def ingresar_numero():
    try:
        numero = float(input("Introduce un número: "))
        print(f"Número ingresado: {numero}")
    except ValueError:
        print("Error: No se pudo convertir la entrada a un número.")

def main():
    ingresar_numero()


if __name__ == "__main__":
    main()
