# Hundir la Flota

## Descripción

Este es un juego de "Hundir la Flota" (Battleship) implementado en Python utilizando la biblioteca Pygame. El juego permite jugar contra uno o más rivales controlados por el ordenador, con diferentes niveles de dificultad. Incluye características como estadísticas persistentes, logs de acciones y modos de barcos alternativos.

## Características

- **Modos de barcos**: Normal (barcos estándar) o Ruso (barcos más pequeños y numerosos).
- **Múltiples rivales**: Juega contra 1, 2 o 3 rivales controlados por el ordenador simultáneamente.
- **Dificultades**: Fácil, Normal, Difícil y Muy Difícil, con estrategias de IA cada vez más avanzadas.
- **Interfaz gráfica**: Visualización de tableros, botones para cambiar entre rivales, mensajes en tiempo real.
- **Estadísticas**: Seguimiento de victorias, derrotas y puntuaciones por modo y dificultad.
- **Logs**: Registro de todas las acciones en un archivo CSV para análisis posterior.
- **Reinicio rápido**: Opción para reiniciar la partida con los mismos ajustes.

## Requisitos

- Python 3.6 o superior
- Pygame 2.0 o superior

## Instalación

1. Asegúrate de tener Python instalado. Puedes descargarlo desde [python.org](https://www.python.org/).

2. Instala Pygame ejecutando el siguiente comando en tu terminal:

   ```
   pip install pygame
   ```

3. Descarga o clona este repositorio en tu máquina local.

## Cómo ejecutar

1. Navega al directorio del proyecto:

   ```
   cd ruta/al/directorio/del/proyecto
   ```

2. Ejecuta el juego:
   ```
   python juego.py
   ```

## Instrucciones de juego

1. **Menú de dificultad**:

   - Selecciona la dificultad deseada (Fácil, Normal, Difícil, Muy Difícil).
   - Elige el formato de barcos (Normal o Ruso) haciendo clic en "FORMATO BARCO".
   - Selecciona el número de rivales (1-3) haciendo clic en "RIVALES" para ciclar entre opciones.
   - Una vez configurado, selecciona una dificultad para comenzar.

2. **Colocación de barcos**:

   - Los barcos se colocan automáticamente al inicio de cada partida.

3. **Juego**:

   - Es tu turno: Haz clic en el tablero del rival actual para disparar.
   - Usa los botones numerados arriba del tablero enemigo para cambiar entre rivales.
   - El objetivo es hundir toda la flota enemiga antes de que ellos hundan la tuya.
   - Las IAs atacan al jugador o entre sí, pero solo si aún tienen barcos vivos.

4. **Fin de partida**:
   - Cuando ganes o pierdas, aparecerá un mensaje.
   - Presiona 'R' para reiniciar con los mismos ajustes o 'ESC' para volver al menú.

## Controles

- **Ratón**: Hacer clic para disparar o seleccionar opciones.
- **Teclado**:
  - 'ESC': Volver al menú de dificultad.
  - 'R': Reiniciar partida (solo al final).

## Archivos importantes

- `juego.py`: Archivo principal del juego.
- `battleship_stats.json`: Archivo de estadísticas persistentes.
- `battleship_log.csv`: Log de acciones de todas las partidas.

## Desarrollo

Este proyecto fue desarrollado como parte de un curso de especialización en IABD (Inteligencia Artificial y Big Data) en el módulo PIA (Programación de Inteligencia Artificial).
