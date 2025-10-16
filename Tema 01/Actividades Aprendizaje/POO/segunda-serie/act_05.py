# act-05.py
# POO - segunda serie - ejercicio 5

from act_04 import Coche

def main():
    coche01 = Coche("Toyota", "Corolla", 2020)
    coche02 = Coche("Toyota", "Corolla", 2020)
    
    print(f"¿Son iguales? {coche01 is coche02}")
    
    coche02.acelerar(100)
    print(f"¿Son iguales? {coche01 is coche02}")


if __name__ == "__main__":
    main()
