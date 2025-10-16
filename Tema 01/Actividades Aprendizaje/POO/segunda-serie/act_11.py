# act-11.py
# POO - segunda serie - ejercicio 11

class Vehiculo:
    def __init__(self):
        self.tipo = ""
        
class Conductor:
    def __init__(self, nombre, vehiculo):
        self.nombre = nombre
        self.vehiculo = vehiculo

def main():
    vehiculo1 = Vehiculo()
    vehiculo1.tipo = "Coche"
    conductor1 = Conductor("Juan", vehiculo1)

    print(f"Conductor: {conductor1.nombre}, Vehículo: {conductor1.vehiculo.tipo}")


if __name__ == "__main__":
    main()
