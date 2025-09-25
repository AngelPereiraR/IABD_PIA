palabra = input("Introduce una palabra: ")

palabra = palabra.lower()

esPalindromo = True

for index in range(int(len(palabra) / 2 - 1)):
    if(palabra[index] == palabra[-index - 1]):
        esPalindromo = True
    else:
        esPalindromo = False
        
if(esPalindromo):
    print("La palabra es un palíndromo.")
else:
    print("La palabra NO es un palíndromo.")