# act-13.py
# POO - segunda serie - ejercicio 13

class Casa:
    def __init__(self, direccion, habitaciones):
        self.direccion = direccion
        self.habitaciones = habitaciones

    def agregar_habitacion(self, habitacion):
        self.habitaciones.append(habitacion)

    def eliminar_habitacion(self, habitacion):
        self.habitaciones.remove(habitacion)
        
    def __del__(self):
        while len(self.habitaciones) > 0:
            self.habitaciones.pop()
        del self
        print("Casa eliminada")

class Habitacion:
    def __init__(self, nombre, area):
        self.nombre = nombre
        self.area = area

def main():
    casa = Casa("Calle Falsa 123", [])
    habitacion1 = Habitacion("Dormitorio", 20)
    habitacion2 = Habitacion("Sala", 30)

    casa.agregar_habitacion(habitacion1)
    casa.agregar_habitacion(habitacion2)
    print(f"Casa en {casa.direccion} con {len(casa.habitaciones)} habitaciones.")
    
    casa.eliminar_habitacion(habitacion1)
    print(f"Casa en {casa.direccion} con {len(casa.habitaciones)} habitaciones.")
    del casa

if __name__ == "__main__":
    main()
