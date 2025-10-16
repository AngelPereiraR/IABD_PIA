# act-08.py
# POO - segunda serie - ejercicio 8

class Coche:
    def __init__(self):
        self.marca = "Desconocida"
        self.modelo = "Desconocido"
        self.anio = 0
        self.velocidad = 0

    def acelerar(self, incremento):
        self.velocidad += incremento

    def frenar(self, decremento):
        self.velocidad -= decremento

    def velocidad_actual(self):
        return self.velocidad
    
    def __hash__(self):
        return hash((self.marca, self.modelo, self.anio))
    
    def __eq__(self, value):
        if isinstance(value, Coche):
            return (self.__hash__() == value.__hash__())

def main():
    coche1 = Coche()
    coche1.marca = "Toyota"
    coche1.modelo = "Corolla"
    coche1.anio = 2020
    coche1.acelerar(50)

    print(f"Coche 1: {coche1.marca}, {coche1.modelo}, {coche1.anio}, Velocidad: {coche1.velocidad_actual()} km/h")
    
    coche2 = Coche()
    coche2.marca = "Toyota"
    coche2.modelo = "Corolla"
    coche2.anio = 2020
    coche2.acelerar(50)

    print(f"Coche 2: {coche2.marca}, {coche2.modelo}, {coche2.anio}, Velocidad: {coche2.velocidad_actual()} km/h")
    
    coche3 = Coche()
    coche3.marca = "Honda"
    coche3.modelo = "Civic"
    coche3.anio = 2020
    coche3.acelerar(50)

    print(f"Coche 3: {coche3.marca}, {coche3.modelo}, {coche3.anio}, Velocidad: {coche3.velocidad_actual()} km/h")

    diccionario = {coche1: "Ana", coche2: "Luis", coche3: "Carlos"}

    print(diccionario)

if __name__ == "__main__":
    main()
