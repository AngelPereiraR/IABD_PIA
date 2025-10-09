# act-04.py
# Ejercicio de diccionarios 4

def main():
    alumnosNotas = {}
    while True:
        try:
            numAlumnos = int(input("Introduce el número de alumnos: "))
            if numAlumnos <= 0:
                print("El número de alumnos debe ser un entero positivo.")
                continue
            break
        except ValueError:
            print("Entrada no válida. Por favor, introduce un número entero positivo.")

    for _ in range(numAlumnos):
        nombre = input("Introduce el nombre del alumno: ")
        if(nombre in alumnosNotas):
            print("El alumno ya existe. Introduce un nombre diferente.")
            continue
        notas = []
        
        while True:
            try:
                nota = int(input(f"Introduce una nota para {nombre} (o número negativo para terminar): "))
                if nota < 0:
                    break
                notas.append(nota)
            except ValueError:
                print("Entrada no válida. Por favor, introduce un número entero no negativo.")

    print("Notas media de los alumnos:")
    for alumno, notas in alumnosNotas.items():
        if notas:
            media = sum(notas) / len(notas)
            print(f"{alumno}: {media:.2f}")
        else:
            print(f"{alumno}: No hay notas disponibles para calcular la media.")

if __name__ == "__main__":
    main()
