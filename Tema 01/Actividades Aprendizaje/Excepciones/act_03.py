# act-03.py
# POO - Excepciones - ejercicio 3

def introducir_nombre():
    while True:
        try:
            nombre = input("Introduce tu nombre: ")
            if not nombre.isalpha():
                raise ValueError("El nombre debe contener solo letras.")
            print(f"Nombre ingresado: {nombre}")
            break
        except ValueError as e:
            print(e)

def main():
    introducir_nombre()


if __name__ == "__main__":
    main()
