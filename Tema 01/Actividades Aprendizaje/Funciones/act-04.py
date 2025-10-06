# act-04.py
# Archivo de ejercicios de funciones
def ConvertirEspaciado(texto):
    """Función que añade un espacio entre cada carácter del texto a excepción de los espacios ya existentes"""
    return '"' + ' '.join(texto.replace(" ", "")) + ' "'

def main():
    print(ConvertirEspaciado("Hola"))
    print(ConvertirEspaciado("Hola que tal"))
    
main()