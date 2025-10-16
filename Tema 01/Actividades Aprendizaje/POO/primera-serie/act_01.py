# act-01.py
# POO - primera serie - ejercicio 1

class Persona:
    """Clase que representa a una persona con atributos nombre, edad y DNI."""
    nombre = ""
    edad = 0
    DNI = ""

    def __init__(self, nombre = "", edad = 0, DNI = ""):
        """Constructor de la clase Persona."""
        self.nombre = nombre
        self.edad = edad
        self.DNI = DNI
        
    def getNombre(self):
        """Devuelve el nombre de la persona."""
        return self.nombre
    
    def getEdad(self):
        """Devuelve la edad de la persona."""
        return self.edad
    
    def getDNI(self):
        """Devuelve el DNI de la persona."""
        return self.DNI

    def setNombre(self, nombre):
        """Establece el nombre de la persona."""
        self.nombre = nombre

    def setEdad(self, edad):
        """Establece la edad de la persona."""
        self.edad = edad

    def setDNI(self, DNI):
        """Establece el DNI de la persona."""
        self.DNI = DNI
        
    def mostrar(self):
        """Muestra la información de la persona."""
        print(f"Nombre: {self.nombre}")
        print(f"Edad: {self.edad}")
        print(f"DNI: {self.DNI}")
        
    def esMayorDeEdad(self):
        """Devuelve True si la persona es mayor de edad (18 años o más), False en caso contrario."""
        return self.edad >= 18

def main():
    
    persona = Persona()
    
    persona.setNombre("Juan")
    persona.setEdad(20)
    persona.setDNI("12345678A")
    
    persona.mostrar()

    if persona.esMayorDeEdad():
        print("La persona es mayor de edad.")
    else:
        print("La persona es menor de edad.")

if __name__ == "__main__":
    main()
