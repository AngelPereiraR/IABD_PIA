contrasena = input("Introduce la contraseña: ")

if(len(contrasena) >= 8 and any(c.isupper() for c in contrasena) and any(c.isdigit() for c in contrasena)):
  print("Contraseña válida.")
else:
  print("Contraseña inválida. Debe tener al menos 8 caracteres, una mayúscula y un número.")