# act-04.py
# POO - Excepciones - ejercicio 4

def abrir_archivo(intentos = 3):
    while intentos > 0:
        try:
            nombre_archivo = input("Introduce el nombre del archivo: ")
            archivo = open(nombre_archivo, "r")
            print("Archivo abierto con éxito.")
            return archivo
        except FileNotFoundError:
            print("Error: Archivo no encontrado.")
            intentos -= 1
            if intentos == 0:
                print("Se han agotado los intentos.")
                return None

def main():
    abrir_archivo()


if __name__ == "__main__":
    main()
