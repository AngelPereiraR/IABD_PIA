# act-10.py
# POO - segunda serie - ejercicio 10

class Coche:
    def __init__(self, marca, modelo, anio):
        self.marca = marca
        self.modelo = modelo
        self.anio = anio
        self._velocidad = 0

    def get_velocidad(self):
        return self._velocidad
    
    def set_velocidad(self, nueva_velocidad):
        if nueva_velocidad >= 0 and nueva_velocidad <= 200:
            self._velocidad = nueva_velocidad
        else:
            print("La velocidad no puede ser negativa o superior a 200.")
            
class CuentaBancaria:
    __saldo = 0.0
    __titular = ""

    def __init__(self, titular, saldo_inicial=0.0):
        self.__titular = titular
        self.__saldo = saldo_inicial

    def get_saldo(self):
        return self.__saldo

    def depositar(self, cantidad):
        if cantidad > 0:
            self.__saldo += cantidad
        else:
            print("La cantidad a depositar debe ser positiva.")
            
    def retirar(self, cantidad):
        if cantidad > 0 and cantidad <= self.__saldo:
            self.__saldo -= cantidad
        else:
            print("Cantidad inválida para retirar.")
            
    def get_titular(self):
        return self.__titular
    
    def set_titular(self, nuevo_titular):
        self.__titular = nuevo_titular

def main():
    coche = Coche("Toyota", "Corolla", 2020)
    coche.set_velocidad(100)
    print(coche.get_velocidad())
    coche.set_velocidad(250)
    print(coche.get_velocidad())

    cuenta = CuentaBancaria("Juan Perez", 1000.0)
    print(cuenta.get_titular())
    print(cuenta.get_saldo())
    cuenta.depositar(500.0)
    print(cuenta.get_saldo())
    cuenta.retirar(100.0)
    print(cuenta.get_saldo())


if __name__ == "__main__":
    main()
