# act-02.py
# Ejercicio de diccionarios 2

def main():
    cadena = input("Introduce una cadena de texto: ")
    diccionario = {}
    for char in cadena:
        if char in diccionario:
            diccionario[char] += 1
        else:
            diccionario[char] = 1
    print(diccionario)

if __name__ == "__main__":
    main()
