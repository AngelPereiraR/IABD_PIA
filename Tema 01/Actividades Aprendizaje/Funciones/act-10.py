# act-10.py
# Archivo de ejercicios de funciones
def calcularSegundos(horas, minutos, segundos):
    """Función que convierte horas, minutos y segundos a segundos"""
    return horas * 3600 + minutos * 60 + segundos
  
def calcularHorasMinutosSegundos(totalSegundos):
    """Función que convierte segundos a horas, minutos y segundos"""
    horas = totalSegundos // 3600
    minutos = (totalSegundos % 3600) // 60
    segundos = totalSegundos % 60
    return horas, minutos, segundos
  
def main():
    while True:
        print("Menú:")
        print("1. Convertir horas, minutos y segundos a segundos")
        print("2. Convertir segundos a horas, minutos y segundos")
        print("3. Salir")
        opcion = input("Elige una opción (1-3): ")
        
        if opcion == '1':
            horas = int(input("Introduce las horas: "))
            minutos = int(input("Introduce los minutos: "))
            segundos = int(input("Introduce los segundos: "))
            totalSegundos = calcularSegundos(horas, minutos, segundos)
            print(f"Total en segundos: {totalSegundos}")
        
        elif opcion == '2':
            totalSegundos = int(input("Introduce el total de segundos: "))
            horas, minutos, segundos = calcularHorasMinutosSegundos(totalSegundos)
            print(f"{totalSegundos} segundos son {horas} horas, {minutos} minutos y {segundos} segundos")
        
        elif opcion == '3':
            print("Saliendo del programa.")
            break
        
        else:
            print("Opción no válida. Por favor, elige una opción del 1 al 3.")
        
        print()  # Línea en blanco para mejor legibilidad
        
main()