# act-12.py
# POO - segunda serie - ejercicio 12

class Curso:
    def __init__(self, nombre, duracion, estudiantes):
        self.nombre = nombre
        self.duracion = duracion
        self.estudiantes = estudiantes

    def agregar_alumno(self, alumno):
        self.estudiantes.append(alumno)

    def eliminar_alumno(self, alumno):
        self.estudiantes.remove(alumno)
        
class Estudiante:
    def __init__(self, nombre, edad):
        self.nombre = nombre
        self.edad = edad


def main():
    estudiante1 = Estudiante("Ana", 22)
    estudiante2 = Estudiante("Luis", 23)

    curso1 = Curso("Programación", 30, [estudiante1, estudiante2])
    curso1.agregar_alumno(Estudiante("Pedro", 24))
    
    curso2 = Curso("Matemáticas", 40, [])
    curso2.agregar_alumno(estudiante1)
    curso2.agregar_alumno(estudiante2)
    curso2.eliminar_alumno(estudiante1)

    for curso in [curso1, curso2]:
        print(f"Curso: {curso.nombre}, Duración: {curso.duracion} horas")
        for estudiante in curso.estudiantes:
            print(f" - Estudiante: {estudiante.nombre}, Edad: {estudiante.edad}")
        print()


if __name__ == "__main__":
    main()
