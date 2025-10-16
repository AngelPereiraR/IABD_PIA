# act-07.py
# POO - segunda serie - ejercicio 7

class Coche:
    def __init__(self):
        self.marca = "Desconocida"
        self.modelo = "Desconocido"
        self.anio = 0
        self.velocidad = 0

def main():
    coche1 = Coche()
    
    print(f"Coche 1: {coche1.marca}, {coche1.modelo}, {coche1.anio}, Velocidad: {coche1.velocidad_actual()} km/h")


if __name__ == "__main__":
    main()
