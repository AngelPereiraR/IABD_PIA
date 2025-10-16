# act-09.py
# POO - segunda serie - ejercicio 9

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
            
    def __repr__(self):
        return (f"Coche(marca={self.marca}, modelo={self.modelo}, "
                f"anio={self.anio}, velocidad={self.velocidad})")
        
    def __str__(self):
        return (f"{self.marca} {self.modelo} ({self.anio}) - "
                f"Velocidad actual: {self.velocidad} km/h")

def main():
    lista_coches = [
        Coche("Toyota", "Corolla", 2020),
        Coche("Honda", "Civic", 2019),
        Coche("Ford", "Mustang", 2021)
    ]

    for coche in lista_coches:
        print(coche.__repr__())
        print(coche.__str__())


if __name__ == "__main__":
    main()
