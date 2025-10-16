# act-16.py
# POO - segunda serie - ejercicio 16

class Figura:
    def area(self):
        pass
    
class Cuadrado(Figura):
    def __init__(self, lado):
        self.lado = lado

    def area(self):
        return self.lado * self.lado

class Circulo(Figura):
    def __init__(self, radio):
        self.radio = radio

    def area(self):
        import math
        return math.pi * self.radio * self.radio
    
class Triangulo(Figura):
    def __init__(self, base, altura):
        self.base = base
        self.altura = altura

    def area(self):
        return 0.5 * self.base * self.altura

def main():
    figuras = [
        Cuadrado(4),
        Circulo(3),
        Triangulo(4, 5)
    ]
    
    for figura in figuras:
        print(f"Área de la figura: {figura.area():.2f}")


if __name__ == "__main__":
    main()
