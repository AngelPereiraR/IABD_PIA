# act-02.py
# POO - primera serie - ejercicio 2

from act_01 import Persona

class Cuenta:
    titular = Persona()

    def __init__(self, titular, saldo = 0.0):
        self.titular = titular
        self.saldo = saldo

    def getTitular(self):
        return self.titular
    
    def getSaldo(self):
        return self.saldo

    def setTitular(self, titular):
        self.titular = titular
    
    def ingresar(self, cantidad):
        if cantidad > 0:
            self.saldo += cantidad
        else:
            print("La cantidad a ingresar debe ser positiva.")
            
    def retirar(self, cantidad):
        if cantidad > 0:
            self.saldo -= cantidad
        else:
            print("La cantidad a retirar debe ser positiva.")
            
    def mostrar(self):
        print(f"Titular: {self.titular.getNombre()}")
        print(f"Edad: {self.titular.getEdad()}")
        print(f"DNI: {self.titular.getDNI()}")
        print(f"Saldo: {self.saldo}")

def main():
    cuenta = Cuenta(Persona("Ana", 30, "87654321B"), 100.0)
    
    cuenta.ingresar(20)
    cuenta.retirar(40)
    
    cuenta.mostrar()

if __name__ == "__main__":
    main()
