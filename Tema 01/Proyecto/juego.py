import pygame
import random
import time 
import json
import os
import datetime

# --- CONFIGURACIÓN INICIAL DE PYGAME Y CONSTANTES ---
pygame.init()

# Constantes de la ventana y el juego
WIDTH, HEIGHT = 1200, 900 
SQUARE_SIZE = 30
GRID_ROWS, GRID_COLS = 10, 10
GRID_WIDTH_PX = GRID_COLS * SQUARE_SIZE
STATS_FILE = "battleship_stats.json" # Nombre del archivo de guardado
LOG_FILE = "battleship_log.txt" # Nombre del archivo de log

# Cálculo para centrar los dos tableros (300px cada uno) y el espacio intermedio
CENTRAL_SPACE = 100
TOTAL_GAME_WIDTH = (GRID_WIDTH_PX * 2) + CENTRAL_SPACE
INITIAL_OFFSET_X = (WIDTH - TOTAL_GAME_WIDTH) // 2

# Posiciones de las cuadrículas (Centradas)
GRID_OFFSET_X_PLAYER = INITIAL_OFFSET_X
GRID_OFFSET_Y_PLAYER = 100
GRID_OFFSET_X_AI = INITIAL_OFFSET_X + GRID_WIDTH_PX + CENTRAL_SPACE
GRID_OFFSET_Y_AI = 100

# Posición del Marcador (Tablas)
TABLE_Y_START = 450
TABLE_X_PLAYER = GRID_OFFSET_X_PLAYER
TABLE_X_AI = GRID_OFFSET_X_AI

# Posición del mensaje de Fin del Juego
GAME_OVER_Y = 780

# Colores
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 200)       
LIGHT_BLUE = (100, 100, 255) 
RED = (200, 0, 0)        
DARK_RED = (150, 0, 0) 
GREY = (100, 100, 100)   
GREEN = (0, 200, 0)      

# Estados de las casillas
WATER = 0
SHIP = 1
MISS = 2
HIT = 3

# Definición de los barcos
SHIP_DEFINITIONS_NORMAL = {
    "Portaaviones": 5,
    "Acorazado": 4,
    "Crucero": 3,
    "Submarino": 3,
    "Destructor": 2
}

SHIP_DEFINITIONS_RUSSIAN = {
    "Acorazado": 4,
    "Crucero 1": 3,
    "Crucero 2": 3,
    "Destructor 1": 2,
    "Destructor 2": 2,
    "Destructor 3": 2,
    "Submarino 1": 1,
    "Submarino 2": 1,
    "Submarino 3": 1,
    "Submarino 4": 1
}

# --- FUNCIONES DE PERSISTENCIA DE DATOS ---

def get_default_stats():
    """Devuelve la estructura base de estadísticas."""
    return {
        'NORMAL': {
            'EASY': {'player_wins': 0, 'ai_wins': 0, 'player_score': 0, 'ai_score': 0},
            'NORMAL': {'player_wins': 0, 'ai_wins': 0, 'player_score': 0, 'ai_score': 0},
            'HARD': {'player_wins': 0, 'ai_wins': 0, 'player_score': 0, 'ai_score': 0},
            'VERY HARD': {'player_wins': 0, 'ai_wins': 0, 'player_score': 0, 'ai_score': 0},
        },
        'RUSO': {
            'EASY': {'player_wins': 0, 'ai_wins': 0, 'player_score': 0, 'ai_score': 0},
            'NORMAL': {'player_wins': 0, 'ai_wins': 0, 'player_score': 0, 'ai_score': 0},
            'HARD': {'player_wins': 0, 'ai_wins': 0, 'player_score': 0, 'ai_score': 0},
            'VERY HARD': {'player_wins': 0, 'ai_wins': 0, 'player_score': 0, 'ai_score': 0},
        }
    }

def load_stats():
    """Carga las estadísticas desde el archivo JSON o devuelve las predeterminadas."""
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, 'r') as f:
                stats = json.load(f)
                # Asegura que el archivo cargado tenga todas las claves de ship_mode y dificultad
                default_stats = get_default_stats()
                for ship_mode in default_stats:
                    if ship_mode not in stats:
                        stats[ship_mode] = default_stats[ship_mode]
                    else:
                        for difficulty in default_stats[ship_mode]:
                            if difficulty not in stats[ship_mode]:
                                stats[ship_mode][difficulty] = default_stats[ship_mode][difficulty]
                return stats
        except (json.JSONDecodeError, IOError):
            # Si el archivo está corrupto o hay error de lectura, usamos las predeterminadas.
            print("Error al leer el archivo de estadísticas. Se usará el marcador inicial.")
            return get_default_stats()
    return get_default_stats()

def save_stats(stats):
    """Guarda las estadísticas actuales en el archivo JSON."""
    try:
        with open(STATS_FILE, 'w') as f:
            json.dump(stats, f, indent=4)
    except IOError:
        print("Error al guardar el archivo de estadísticas.")

def log_action(message):
    """Escribe una entrada en el archivo de log."""
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f"{datetime.datetime.now()}: {message}\n")
    except IOError:
        print("Error al escribir en el archivo de log.")


# --- CLASE PARA RASTREAR EL ESTADO DE CADA BARCO ---
class Barco:
    def __init__(self, name, length, positions):
        self.name = name
        self.length = length
        self.positions = positions 
        self.hits_taken = 0
        self.is_sunk = False

    def check_hit(self, row, col):
        if (row, col) in self.positions:
            self.hits_taken += 1
            if self.hits_taken == self.length:
                self.is_sunk = True
                return True, self.length # Devuelve longitud si está hundido
            return True, 0 # Devuelve 0 puntos si es un acierto pero no está hundido
        return False, 0

# --- FUNCIONES DE DIBUJO ---

def draw_text(screen, text, font, color, x, y):
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=(x, y))
    screen.blit(text_surface, text_rect)
    return text_rect 

def draw_grid(screen, grid, offset_x, offset_y, show_ships=False):
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            x = offset_x + col * SQUARE_SIZE
            y = offset_y + row * SQUARE_SIZE
            rect = pygame.Rect(x, y, SQUARE_SIZE, SQUARE_SIZE)
            
            color = LIGHT_BLUE 

            if grid[row][col] == SHIP:
                color = GREEN if show_ships else LIGHT_BLUE
            elif grid[row][col] == MISS:
                color = GREY
            elif grid[row][col] == HIT:
                color = RED
            elif grid[row][col] == WATER and show_ships:
                 color = BLUE

            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, BLACK, rect, 1)

def draw_ship_table(screen, ships, font, title, x_start, y_start):
    draw_text(screen, title, font, BLACK, x_start + 100, y_start)
    y_current = y_start + 30
    
    draw_text(screen, "BARCO", font, BLACK, x_start + 50, y_current)
    draw_text(screen, "ESTADO", font, BLACK, x_start + 150, y_current)
    y_current += 20

    for ship in ships:
        status_text = "HUNDIDO" if ship.is_sunk else "VIVO"
        status_color = RED if ship.is_sunk else GREEN
        
        draw_text(screen, ship.name, font, BLACK, x_start + 50, y_current)
        draw_text(screen, status_text, font, status_color, x_start + 150, y_current)
        y_current += 25

# --- LÓGICA DEL JUEGO Y UTILIDADES ---

def create_empty_grid():
    return [[WATER for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]

def place_ships_randomly(grid, ship_definitions):
    ships = []
    ship_names = list(ship_definitions.keys())
    
    for i, length in enumerate(ship_definitions.values()):
        name = ship_names[i]
        placed = False
        while not placed:
            row = random.randint(0, GRID_ROWS - 1)
            col = random.randint(0, GRID_COLS - 1)
            orientation = random.choice(['horizontal', 'vertical'])

            ship_positions = []
            valid = True

            for j in range(length):
                if orientation == 'horizontal':
                    r, c = row, col + j
                else:
                    r, c = row + j, col

                if not (0 <= r < GRID_ROWS and 0 <= c < GRID_COLS) or grid[r][c] == SHIP:
                    valid = False
                    break
                ship_positions.append((r, c))

            if valid:
                for r, c in ship_positions:
                    directions = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
                    for dr, dc in directions:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < GRID_ROWS and 0 <= nc < GRID_COLS and grid[nr][nc] == SHIP:
                            valid = False
                            break
                    if not valid:
                        break

            if valid:
                for r, c in ship_positions:
                    grid[r][c] = SHIP
                
                ships.append(Barco(name, length, ship_positions))
                placed = True
                
    return grid, ships

def get_grid_coords_from_mouse(pos, offset_x, offset_y):
    mouse_x, mouse_y = pos
    col = (mouse_x - offset_x) // SQUARE_SIZE
    row = (mouse_y - offset_y) // SQUARE_SIZE
    
    if 0 <= row < GRID_ROWS and 0 <= col < GRID_COLS:
        return row, col
    return None, None

def take_shot(grid, ships, row, col):
    """Procesa un disparo y devuelve (hit, message, sunk_points)"""
    if grid[row][col] == SHIP:
        grid[row][col] = HIT
        
        sunk_points = 0
        sunk_ship_name = None
        for ship in ships:
            is_hit, points = ship.check_hit(row, col)
            if is_hit:
                if points > 0:
                    sunk_points = points
                    sunk_ship_name = ship.name
                break
        
        if sunk_ship_name:
            return True, f"¡ACIERTO! ¡Has hundido el {sunk_ship_name}!", sunk_points 
        else:
            return True, "¡Acierto!", 0 
            
    elif grid[row][col] == WATER:
        grid[row][col] = MISS
        return False, "¡Agua!", 0
    else:
        return False, "Ya has disparado aquí.", 0

def check_win(ships):
    return all(ship.is_sunk for ship in ships)

# --- LÓGICA DE LA IA ---

def get_valid_neighbors(grid, r, c):
    neighbors = []
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    for dr, dc in directions:
        nr, nc = r + dr, c + dc
        if 0 <= nr < GRID_ROWS and 0 <= nc < GRID_COLS and (grid[nr][nc] == WATER or grid[nr][nc] == SHIP):
            neighbors.append((nr, nc))
    return neighbors

def random_shot(grid):
    valid_shots = []
    for r in range(GRID_ROWS):
        for c in range(GRID_COLS):
            if grid[r][c] == WATER or grid[r][c] == SHIP:
                valid_shots.append((r, c))
    
    if valid_shots:
        return random.choice(valid_shots)
    return None, None 

def ai_take_turn(player_grid, player_ships, difficulty, ai_target_queue, last_hit, consecutive_hits, current_direction):
    r, c = None, None
    hit, message, sunk_points = False, "", 0

    if difficulty == 'HARD' or (difficulty == 'NORMAL' and random.random() < 0.5 and ai_target_queue):
        if ai_target_queue:
            r, c = ai_target_queue.pop(0) 
        
        if r is None or (player_grid[r][c] != WATER and player_grid[r][c] != SHIP): 
            r, c = random_shot(player_grid)
    elif difficulty == 'VERY HARD':
        if ai_target_queue:
            r, c = ai_target_queue.pop(0)
        else:
            r, c = random_shot(player_grid)
    else:
        r, c = random_shot(player_grid)
    
    if r is not None and c is not None:
        hit, message, sunk_points = take_shot(player_grid, player_ships, r, c)
    else:
        hit, message, sunk_points = False, "La IA no pudo encontrar un objetivo.", 0

    # Actualizar la cola de objetivos y el último acierto
    new_last_hit = last_hit
    new_consecutive_hits = consecutive_hits
    new_current_direction = current_direction
    if hit:
        new_last_hit = (r, c)
        new_consecutive_hits += 1
        
        if sunk_points > 0:
            new_consecutive_hits = 0
            new_current_direction = None
            if difficulty in ['NORMAL', 'HARD', 'VERY HARD']:
                ai_target_queue = []
        
        else: 
            if difficulty == 'VERY HARD' and new_consecutive_hits >= 2:
                if new_current_direction is None and last_hit:
                    dr = r - last_hit[0]
                    dc = c - last_hit[1]
                    new_current_direction = (dr, dc)
                
                if new_current_direction:
                    nr = r + new_current_direction[0]
                    nc = c + new_current_direction[1]
                    if 0 <= nr < GRID_ROWS and 0 <= nc < GRID_COLS and (player_grid[nr][nc] == WATER or player_grid[nr][nc] == SHIP):
                        ai_target_queue.insert(0, (nr, nc))
            elif difficulty != 'EASY':
                new_neighbors = get_valid_neighbors(player_grid, r, c)
                for nr, nc in new_neighbors:
                    if (nr, nc) not in ai_target_queue:
                        ai_target_queue.append((nr, nc))
        
    else:
        new_consecutive_hits = 0
        new_current_direction = None

    return hit, message, sunk_points, ai_target_queue, new_last_hit, new_consecutive_hits, new_current_direction, r, c

# --- PANTALLA DE SELECCIÓN DE DIFICULTAD ---

def draw_stats_table(screen, font, stats, ship_mode):
    """Dibuja la tabla de estadísticas totales, centrada."""
    y_start = 600
    small_font = pygame.font.Font(None, 24)
    
    draw_text(screen, f"MARCADOR GLOBAL - BARCO {ship_mode}", font, BLACK, WIDTH // 2, y_start)
    y_current = y_start + 40

    # Definir las posiciones X. 
    x_pos_diff = WIDTH // 2 - 350    # DIFICULTAD (izquierda)
    x_pos_p_wins = WIDTH // 2 - 180  # VICTORIAS JUGADOR
    x_pos_ai_wins = WIDTH // 2 + 0   # VICTORIAS IA (centro)
    x_pos_p_score = WIDTH // 2 + 170 # PUNTOS JUGADOR
    x_pos_ai_score = WIDTH // 2 + 320 # PUNTOS IA (derecha)
    
    headers = ["DIFICULTAD", "VICTORIAS JUGADOR", "VICTORIAS IA", "PUNTOS JUGADOR", "PUNTOS IA"]
    x_pos = [x_pos_diff, x_pos_p_wins, x_pos_ai_wins, x_pos_p_score, x_pos_ai_score]
    
    # Encabezados
    for i, header in enumerate(headers):
        draw_text(screen, header, small_font, GREY, x_pos[i], y_current) 
    y_current += 20

    # Dibujar filas de datos
    for difficulty in ['EASY', 'NORMAL', 'HARD', 'VERY HARD']:
        data = stats[ship_mode].get(difficulty, {'player_wins': 0, 'ai_wins': 0, 'player_score': 0, 'ai_score': 0})
        
        diff_text = difficulty.replace('_', ' ').capitalize()
        
        draw_text(screen, diff_text, small_font, BLACK, x_pos[0], y_current)
        draw_text(screen, str(data['player_wins']), small_font, GREEN, x_pos[1], y_current)
        draw_text(screen, str(data['ai_wins']), small_font, RED, x_pos[2], y_current)
        draw_text(screen, str(data['player_score']), small_font, BLUE, x_pos[3], y_current)
        draw_text(screen, str(data['ai_score']), small_font, BLUE, x_pos[4], y_current)
        y_current += 25


def difficulty_menu(screen, font, stats, ship_mode):
    """Muestra el menú de selección de dificultad y espera la elección."""
    running = True
    
    buttons = {
        "FÁCIL": (WIDTH // 2, 200, 250, 75, 'EASY'),
        "NORMAL": (WIDTH // 2, 280, 250, 75, 'NORMAL'),
        "DIFÍCIL": (WIDTH // 2, 360, 250, 75, 'HARD'),
        "MUY DIFÍCIL": (WIDTH // 2, 440, 250, 75, 'VERY HARD'),
        "TOGGLE_SHIPS": (WIDTH // 2, 520, 500, 75, 'TOGGLE_SHIPS')
    }
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None, ship_mode 
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = event.pos
                for text, (cx, cy, w, h, mode) in buttons.items():
                    rect = pygame.Rect(cx - w // 2, cy - h // 2, w, h)
                    if rect.collidepoint(mouse_x, mouse_y):
                        if mode == 'TOGGLE_SHIPS':
                            ship_mode = 'RUSO' if ship_mode == 'NORMAL' else 'NORMAL'
                        else:
                            return mode, ship_mode
                        
        screen.fill(WHITE)
        draw_text(screen, "SELECCIONA LA DIFICULTAD", font, BLACK, WIDTH // 2, 100)
        
        # Dibujar botones
        for text, (cx, cy, w, h, mode) in buttons.items():
            rect = pygame.Rect(cx - w // 2, cy - h // 2, w, h)
            
            color = GREY
            if rect.collidepoint(pygame.mouse.get_pos()):
                color = DARK_RED
            
            pygame.draw.rect(screen, color, rect)
            if text == "TOGGLE_SHIPS":
                display_text = f"FORMATO BARCO: {ship_mode}"
            else:
                display_text = text
            draw_text(screen, display_text, font, WHITE, cx, cy)
            
        # Dibujar la tabla de estadísticas
        draw_stats_table(screen, font, stats, ship_mode)

        pygame.display.update()
        pygame.time.Clock().tick(30)
    
    return None, ship_mode

# --- BUCLE PRINCIPAL DEL JUEGO ---

def game_loop(screen, difficulty_mode, stats, ship_mode):
    pygame.display.set_caption(f"Hundir la Flota - Modo: {difficulty_mode}")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 36)
    small_font = pygame.font.Font(None, 24)

    # Elegir definición de barcos
    if ship_mode == 'NORMAL':
        SHIP_DEFINITIONS = SHIP_DEFINITIONS_NORMAL
    else:
        SHIP_DEFINITIONS = SHIP_DEFINITIONS_RUSSIAN

    # Loguear inicio de partida
    log_action(f"Partida iniciada: Dificultad: {difficulty_mode}, Modo barcos: {ship_mode}")

    # Inicialización
    player_grid_base = create_empty_grid()
    ai_grid_base = create_empty_grid()
    player_grid, player_ships = place_ships_randomly(player_grid_base, SHIP_DEFINITIONS)
    ai_grid, ai_ships = place_ships_randomly(ai_grid_base, SHIP_DEFINITIONS)

    # Variables de estado
    player_turn = True
    game_over = False
    winner_message = ""
    game_message = "Tu turno. ¡Dispara a la flota enemiga!"
    
    ai_target_queue = [] 
    last_hit_coord = None 
    consecutive_hits = 0
    current_direction = None
    
    current_player_score = 0
    current_ai_score = 0

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # Guardar antes de salir
                if game_over:
                    save_stats(stats)
                return 'quit' 
            
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                # Guardar antes de volver al menú
                if game_over:
                    save_stats(stats)
                return 'menu' 
            
            # --- Manejo de Clicks (Turno del Jugador) ---
            if event.type == pygame.MOUSEBUTTONDOWN and not game_over:
                if player_turn:
                    mouse_pos = pygame.mouse.get_pos()
                    grid_row, grid_col = get_grid_coords_from_mouse(mouse_pos, GRID_OFFSET_X_AI, GRID_OFFSET_Y_AI)
                    
                    if grid_row is not None:
                        if ai_grid[grid_row][grid_col] == WATER or ai_grid[grid_row][grid_col] == SHIP:
                            
                            hit, message, sunk_points = take_shot(ai_grid, ai_ships, grid_row, grid_col)
                            game_message = f"Jugador: {message}"
                            
                            # Determinar resultado para log
                            if not hit:
                                resultado = "Agua"
                            elif sunk_points > 0:
                                resultado = "Hundido"
                            else:
                                resultado = "Tocado"
                            log_action(f"Jugador: Disparo en ({grid_row}, {grid_col}) - {resultado}")
                            
                            if sunk_points > 0:
                                current_player_score += sunk_points
                                
                            if check_win(ai_ships):
                                game_over = True
                                winner_message = "¡Has ganado! ¡Hundiste toda la flota enemiga!"
                                # Actualizar estadísticas globales
                                stats[ship_mode][difficulty_mode]['player_wins'] += 1
                                stats[ship_mode][difficulty_mode]['player_score'] += current_player_score
                                stats[ship_mode][difficulty_mode]['ai_score'] += current_ai_score
                                # Log del resultado
                                log_action(f"Fin de partida: Ganador: Jugador, Puntuación Jugador: {current_player_score}, Puntuación IA: {current_ai_score}")
                            
                            player_turn = False 
                        else:
                            game_message = "Jugador: Ya has disparado aquí."
            
            # --- Reiniciar Juego (con R) ---
            if game_over and event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                # Guardar antes de reiniciar
                save_stats(stats)
                return 'restart' 

        # --- Lógica del Turno de la IA ---
        if not player_turn and not game_over:
            time.sleep(0.8)

            hit, message, sunk_points, ai_target_queue, last_hit_coord, consecutive_hits, current_direction, r, c = ai_take_turn(
                player_grid, player_ships, difficulty_mode, ai_target_queue, last_hit_coord, consecutive_hits, current_direction
            )
            
            game_message = f"IA ({difficulty_mode}): {message}"
            
            # Determinar resultado para log
            if not hit:
                resultado = "Agua"
            elif sunk_points > 0:
                resultado = "Hundido"
            else:
                resultado = "Tocado"
            log_action(f"IA ({difficulty_mode}): Disparo en ({r}, {c}) - {resultado}")
            
            if sunk_points > 0:
                current_ai_score += sunk_points
                
            if check_win(player_ships):
                game_over = True
                winner_message = "¡La IA ha ganado! ¡Tu flota ha sido hundida!"
                # Actualizar estadísticas globales
                stats[ship_mode][difficulty_mode]['ai_wins'] += 1
                stats[ship_mode][difficulty_mode]['player_score'] += current_player_score
                stats[ship_mode][difficulty_mode]['ai_score'] += current_ai_score
                # Log del resultado
                log_action(f"Fin de partida: Ganador: IA, Puntuación Jugador: {current_player_score}, Puntuación IA: {current_ai_score}")

            player_turn = True 

        # --- DIBUJAR EN LA PANTALLA ---
        screen.fill(WHITE)

        # Títulos de los tableros
        draw_text(screen, "TU FLOTA", font, BLACK, GRID_OFFSET_X_PLAYER + GRID_COLS * SQUARE_SIZE // 2, GRID_OFFSET_Y_PLAYER - 30)
        draw_text(screen, "FLOTA ENEMIGA (Haz click para disparar)", font, BLACK, GRID_OFFSET_X_AI + GRID_COLS * SQUARE_SIZE // 2, GRID_OFFSET_Y_AI - 30)

        # Puntuación actual del juego
        draw_text(screen, f"Puntuación Jugador: {current_player_score}", small_font, BLUE, GRID_OFFSET_X_PLAYER + 50, 420)
        draw_text(screen, f"Puntuación IA: {current_ai_score}", small_font, BLUE, GRID_OFFSET_X_AI + 50, 420)

        # Dibujar las cuadrículas
        draw_grid(screen, player_grid, GRID_OFFSET_X_PLAYER, GRID_OFFSET_Y_PLAYER, show_ships=True)
        draw_grid(screen, ai_grid, GRID_OFFSET_X_AI, GRID_OFFSET_Y_AI, show_ships=False)

        # Mensajes de estado
        draw_text(screen, game_message, font, BLACK, WIDTH // 2, 40)

        # Dibujar la tabla de barcos (Marcador)
        draw_ship_table(screen, player_ships, small_font, "ESTADO DE TU FLOTA", TABLE_X_PLAYER, TABLE_Y_START)
        draw_ship_table(screen, ai_ships, small_font, "ESTADO FLOTA ENEMIGA", TABLE_X_AI, TABLE_Y_START)

        # Mostrar mensaje de victoria/derrota 
        if game_over:
            draw_text(screen, winner_message, font, RED, WIDTH // 2, GAME_OVER_Y)
            draw_text(screen, "Presiona R para reiniciar o ESC para cambiar la dificultad", small_font, BLACK, WIDTH // 2, GAME_OVER_Y + 40)


        pygame.display.update()
        clock.tick(60)

    return True 

# --- BUCLE MAESTRO (Control de Flujo) ---

if __name__ == "__main__":
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    font_large = pygame.font.Font(None, 48)
    
    # 1. Cargar las estadísticas globales al inicio del juego
    game_stats = load_stats()
    ship_mode = 'NORMAL'  # Por defecto barcos normales

    app_running = True
    while app_running:
        
        # 2. Mostrar menú de dificultad y pasar las estadísticas y modo de barcos
        selected_difficulty, new_ship_mode = difficulty_menu(screen, font_large, game_stats, ship_mode)
        ship_mode = new_ship_mode
        
        if selected_difficulty is None:
            app_running = False
        
        elif selected_difficulty:
            # 3. Bucle para reiniciar con los mismos settings
            while True:
                result = game_loop(screen, selected_difficulty, game_stats, ship_mode)
                
                if result == 'quit':
                    app_running = False
                    break
                elif result == 'menu':
                    break  # Volver al menú de dificultad
                elif result == 'restart':
                    continue  # Reiniciar con los mismos settings

    # 4. Guardar las estadísticas finales al salir de la aplicación
    save_stats(game_stats)
    pygame.quit()