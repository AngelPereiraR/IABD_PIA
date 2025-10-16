# act-06.py
# POO - segunda serie - ejercicio 6

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
            
    def __eq__(self, value):
        if isinstance(value, Coche):
            return (self.marca == value.marca and
                    self.modelo == value.modelo)


def main():
    coche1 = Coche("Toyota", "Corolla", 2020)
    coche2 = Coche("Toyota", "Corolla", 2020)

    print(f"¿Son iguales? {coche1 == coche2}")


if __name__ == "__main__":
    main()
