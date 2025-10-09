# act-01.py
# Ejercicio de diccionarios 1

def main():
    while True:
        try:
            valor = int(input("Introduce un número entero: "))
            diccionario = {num: num**2 for num in range(1, valor + 1)}
            print(diccionario)
            break
        except ValueError:
            print("Entrada no válida. Por favor, introduce un número entero.")
            continue

if __name__ == "__main__":
    main()
