equipos = []
resultados = []

for i in range(15):
  equipoLocal = input(f"Introduce el nombre del equipo local para el partido {i+1}: ")
  equipoVisitante = input(f"Introduce el nombre del equipo visitante para el partido {i+1}: ")
  equipos.append([equipoLocal, equipoVisitante])
  
  try:
    golesLocal = int(input(f"Introduce los goles del equipo local ({equipoLocal}): "))
    golesVisitante = int(input(f"Introduce los goles del equipo visitante ({equipoVisitante}): "))
    if golesLocal < 0 or golesVisitante < 0:
      raise ValueError
  except ValueError:
    print("Por favor, introduce valores válidos para los goles.")
    continue

  resultados.append([golesLocal, golesVisitante])
  
print("\nResultados de los partidos:")
for i in range(len(equipos)):
  equipoLocal, equipoVisitante = equipos[i]
  golesLocal, golesVisitante = resultados[i]
  resultadoQuiniela = 0
  if(golesLocal < golesVisitante):
    resultadoQuiniela = 2
  elif(golesLocal > golesVisitante):
    resultadoQuiniela = 1
  else:
    resultadoQuiniela = "X"
  print(f"Partido {i+1}: {equipoLocal} vs {equipoVisitante} - Resultado: {resultadoQuiniela}")