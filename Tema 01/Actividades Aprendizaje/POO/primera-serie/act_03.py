# act-03.py
# POO - primera serie - ejercicio 3

from act_01 import Persona
from act_02 import Cuenta

class CuentaJoven(Cuenta):
    def __init__(self, titular, saldo=0.0, bonificacion=0.0):
        super().__init__(titular, saldo)
        self.bonificacion = bonificacion

    def es_titular_valido(self):
        return 18 <= self.titular.getEdad() < 25

    def retirar(self, cantidad):
        if self.es_titular_valido():
            super().retirar(cantidad)
        else:
            print("El titular no es válido para realizar retiros.")

    def mostrar(self):
        super().mostrar()
        print(f"Bonificación: {self.bonificacion}%")

def main():
    titular = Persona("Carlos", 22, "11223344C")
    cuenta_joven = CuentaJoven(titular, 150.0, 10.0)
    
    print("Información de la cuenta joven:")
    cuenta_joven.mostrar()
    
    print("\nIntentando retirar 50...")
    cuenta_joven.retirar(50)
    cuenta_joven.mostrar()
    
    print("\nCambiando la edad del titular a 26...")
    titular.setEdad(26)
    
    print("Intentando retirar 50 nuevamente...")
    cuenta_joven.retirar(50)
    cuenta_joven.mostrar()


if __name__ == "__main__":
    main()
