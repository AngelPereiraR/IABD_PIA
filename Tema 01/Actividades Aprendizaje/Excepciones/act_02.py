# act-02.py
# POO - Excepciones - ejercicio 2

def ingresar_edad():
    try:
        edad = int(input("Introduce tu edad: "))
        if edad < 0:
            raise ValueError("La edad no puede ser negativa.")
    except ValueError as e:
        edad = 18
        
    print(f"Edad asignada: {edad}")

def main():
    ingresar_edad()


if __name__ == "__main__":
    main()
