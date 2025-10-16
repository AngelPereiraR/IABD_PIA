# act-15.py
# POO - segunda serie - ejercicio 15
        
class Terrestre:
    def __init__(self):
        self.tipo_terrestre = ""

class Acuatico:
    def __init__(self):
        self.tipo_acuatico = ""

class Anfibio(Terrestre, Acuatico):
    def __init__(self):
        Terrestre.__init__(self)
        Acuatico.__init__(self)
        self.nombre = ""
        self.edad = 0

def main():
    anfibio = Anfibio()
    anfibio.nombre = "Rana"
    anfibio.edad = 5
    anfibio.tipo_terrestre = "Sapo"
    anfibio.tipo_acuatico = "Rana de agua dulce"

    print(f"Nombre: {anfibio.nombre}")
    print(f"Edad: {anfibio.edad}")
    print(f"Tipo Terrestre: {anfibio.tipo_terrestre}")
    print(f"Tipo Acuático: {anfibio.tipo_acuatico}")


if __name__ == "__main__":
    main()
