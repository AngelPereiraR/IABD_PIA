# act-03.py
# Ejercicio de diccionarios 3

def main():
    frutasPrecio = {'manzana': 3, 'banana': 5, 'naranja': 2, 'pera': 4}
    
    while True:
        fruta = input("Introduce el nombre de una fruta (o 'salir' para terminar): ").lower()
        if fruta == 'salir':
            print("Programa terminado.")
            break
        elif fruta in frutasPrecio:
            print(f"El precio de la {fruta} es {frutasPrecio[fruta]} unidades monetarias.")
        else:
            print("Fruta no disponible. Intenta con otra.")

if __name__ == "__main__":
    main()
