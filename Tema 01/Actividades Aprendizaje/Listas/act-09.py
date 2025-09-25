import random

listaTemperaturasMaximas = [random.randint(20, 40) for _ in range(5)]
listaTemperaturasMinimas = [random.randint(0, 20) for _ in range(5)]

print(f"Temperaturas medias: {[(max_temp + min_temp) / 2 for max_temp, min_temp in zip(listaTemperaturasMaximas, listaTemperaturasMinimas)]}")
print(f"Días con menor temperatura mínima: {[i for i, min_temp in enumerate(listaTemperaturasMinimas) if min_temp == min(listaTemperaturasMinimas)]}")

temperatura = float(input("Introduce una temperatura para buscar los días cuya temperatura máxima coincida: "))
existe = any([i for i, max_temp in enumerate(listaTemperaturasMaximas) if max_temp == temperatura])
if existe:
  print(f"La temperatura {temperatura}°C se encontró en los días: {[i for i, max_temp in enumerate(listaTemperaturasMaximas) if max_temp == temperatura]}")
else:
  print(f"La temperatura {temperatura}°C no se encontró en ningún día.")