# act-07.py
# Archivo de ejercicios de funciones
def Login(nombre, contraseña, contadorIntentos=0):
  """Función que devuelve True si el nombre y la contraseña coinciden con los valores esperados"""
  return nombre == "usuario1" and contraseña == "asdasd", contadorIntentos + 1

def main():
    intentos = 0
    while intentos < 3:
        nombre = input("Introduce el nombre de usuario: ")
        contraseña = input("Introduce la contraseña: ")
        exito, intentos = Login(nombre, contraseña, intentos)
        if exito:
            print("Has iniciado sesión correctamente.")
            return
        else:
            print(f"Nombre o contraseña incorrectos. Intento {intentos} de 3.")
    print("Has superado el número máximo de intentos. Acceso bloqueado.")
    
main()