# act-04.py
# POO - segunda serie - ejercicio 4

class Coche:
    def __init__(self, marca, modelo, anio):
        self.marca = marca
        self.modelo = modelo
        self.anio = anio
        self.velocidad = 0
        
    def velocidad_actual(self):
        return self.velocidad

    def acelerar(self, incremento):
        self.velocidad += incremento

    def frenar(self, decremento):
        self.velocidad -= decremento
        if self.velocidad < 0:
            self.velocidad = 0

def main():
    coche = Coche("Toyota", "Corolla", 2020)
    coche.acelerar(50)
    print(f"Velocidad actual: {coche.velocidad_actual()} km/h")
    coche.frenar(20)
    print(f"Velocidad actual: {coche.velocidad_actual()} km/h")

if __name__ == "__main__":
    main()
