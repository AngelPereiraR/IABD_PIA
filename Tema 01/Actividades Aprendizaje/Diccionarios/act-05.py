# act-05.py
# Ejercicio de diccionarios 5

def anadir_modificar(agenda):
    nombre = input("Introduce el nombre: ")
    if(nombre in agenda):
        print(f"El número de {nombre} es {agenda[nombre]}")
        while True:
            opcion = input("¿Quieres modificarlo? (s/n): ").lower()
            if opcion == 's':
                nuevo_numero = input(f"Introduce el nuevo número para {nombre}: ")
                agenda[nombre] = nuevo_numero
                print(f"Número de {nombre} modificado a {nuevo_numero}.")
                break
            elif opcion == 'n':
                print("No se ha realizado ninguna modificación.")
                break
            else:
                print("Opción no válida. Por favor, responde con 's' o 'n'.")
    else:
        numero = input(f"Introduce el número para {nombre}: ")
        agenda[nombre] = numero
        print(f"Contacto {nombre} añadido con el número {numero}.")
                
def buscar(agenda):
    cadena = input("Introduce la cadena por la que empiezan los nombres a buscar: ")
    encontrados = {nombre: numero for nombre, numero in agenda.items() if nombre.startswith(cadena)}
    if encontrados:
        print("Nombres encontrados:")
        for nombre, numero in encontrados.items():
            print(f"{nombre}: {numero}")
    else:
        print("No se han encontrado nombres que empiecen por esa cadena.")
            
def borrar(agenda):
    nombre = input("Introduce el nombre a borrar: ")
    if nombre in agenda:
        while True:
            opcion = input(f"¿Estás seguro de que quieres borrar a {nombre}? (s/n): ").lower()
            if opcion == 's':
                del agenda[nombre]
                print(f"{nombre} ha sido borrado de la agenda.")
                break
            elif opcion == 'n':
                print("No se ha realizado ninguna eliminación.")
                break
            else:
                print("Opción no válida. Por favor, responde con 's' o 'n'.")
    else:
        print(f"{nombre} no se encuentra en la agenda.")

def main():
    agenda = {}
    while True:
        print("\nMenú:")
        print("1. Añadir o modificar un contacto")
        print("2. Buscar contactos por nombre")
        print("3. Borrar un contacto")
        print("4. Salir")
        opcion = input("Elige una opción (1-4): ")
        
        if opcion == '1':
            anadir_modificar(agenda)
        elif opcion == '2':
            buscar(agenda)
        elif opcion == '3':
            borrar(agenda)
        elif opcion == '4':
            print("Saliendo del programa.")
            break
        else:
            print("Opción no válida. Por favor, elige una opción del 1 al 4.")

if __name__ == "__main__":
    main()
