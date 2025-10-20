# act-03.py
# POO - Excepciones - ejercicio 3

def introducir_nombre():
    while True:
        try:
            nombre = input("Introduce tu nombre: ")
            if nombre == "" or nombre.isdigit():
                raise ValueError("El nombre no puede estar vacío y debe contener letras.")
            print(f"Nombre ingresado: {nombre}")
            break
        except ValueError as e:
            print(e)

def main():
    introducir_nombre()


if __name__ == "__main__":
    main()
