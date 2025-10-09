# act-11.py
# Archivo de ejercicios de funciones
def LeerFecha():
    """Función que lee una fecha en formato dd/mm/aaaa y la devuelve como una tupla (dd, mm, aaaa)"""
    fecha = input("Introduce una fecha (dd/mm/aaaa): ")
    dia, mes, anio = map(int, fecha.split('/'))
    return dia, mes, anio

def EsBisiesto(anio):
    """Función que devuelve True si el año es bisiesto"""
    return (anio % 4 == 0 and anio % 100 != 0) or (anio % 400 == 0)

def DiasDelMes(mes, anio):
    """Función que devuelve el número de días de un mes dado y el año (considerando años bisiestos)"""
    if mes in [1, 3, 5, 7, 8, 10, 12]:
        return 31
    elif mes in [4, 6, 9, 11]:
        return 30
    elif mes == 2:
        return 29 if EsBisiesto(anio) else 28
    else:
        raise ValueError("Mes inválido")
    
def Calcular_Dia_Juliano(dia, mes, anio):
    """Función que calcula el día juliano a partir de una fecha dada"""
    dia_juliano = dia
    for m in range(1, mes):
        dia_juliano += DiasDelMes(m, anio)
    return dia_juliano

def main():
    try:
        dia, mes, anio = LeerFecha()
        if mes < 1 or mes > 12:
            raise ValueError("Mes inválido")
        if dia < 1 or dia > DiasDelMes(mes, anio):
            raise ValueError("Día inválido para el mes y año dados")
        dia_juliano = Calcular_Dia_Juliano(dia, mes, anio)
        print(f"La fecha {dia}/{mes}/{anio} corresponde al día juliano {dia_juliano}.")
    except ValueError as e:
        print(f"Error: {e}")
        
main()