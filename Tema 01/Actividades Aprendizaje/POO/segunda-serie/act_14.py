# act-14.py
# POO - segunda serie - ejercicio 14

class Trabajador:
    def __init__(self, nombre, salario):
        self.nombre = nombre
        self.salario = salario
        
    def devolver_salario(self):
        return self.salario
        
class Docente(Trabajador):
    def __init__(self, nombre, salario):
        super().__init__(nombre, salario)
        
    def devolver_salario(self):
        return self.salario * 1.10  # Incremento del 10%
    
class PAS(Trabajador):
    def __init__(self, nombre, salario):
        super().__init__(nombre, salario)
        
    def devolver_salario(self):
        return self.salario * 1.05  # Incremento del 5%

def main():
    trabajador1 = Docente("Juan", 3000)
    trabajador2 = PAS("Maria", 2500)

    print(f"Salario {trabajador1.nombre}: {trabajador1.devolver_salario():.2f}")
    print(f"Salario {trabajador2.nombre}: {trabajador2.devolver_salario():.2f}")


if __name__ == "__main__":
    main()
