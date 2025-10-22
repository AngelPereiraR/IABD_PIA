import pygame
import random
import time 
import json
import os

# --- 1. CONFIGURACIÓN INICIAL DE PYGAME Y CONSTANTES ---
pygame.init()

# Constantes de la ventana y el juego
WIDTH, HEIGHT = 1200, 900 
SQUARE_SIZE = 30
GRID_ROWS, GRID_COLS = 10, 10
GRID_WIDTH_PX = GRID_COLS * SQUARE_SIZE
STATS_FILE = "battleship_stats.json" # Nombre del archivo de guardado

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
GAME_OVER_Y = 680

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
SHIP_DEFINITIONS = {
    "Portaaviones": 5,
    "Acorazado": 4,
    "Crucero": 3,
    "Submarino": 3,
    "Destructor": 2
}

# --- FUNCIONES DE PERSISTENCIA DE DATOS ---

def get_default_stats():
    """Devuelve la estructura base de estadísticas."""
    return {
        'EASY': {'player_wins': 0, 'ai_wins': 0, 'player_score': 0, 'ai_score': 0},
        'NORMAL': {'player_wins': 0, 'ai_wins': 0, 'player_score': 0, 'ai_score': 0},
        'HARD': {'player_wins': 0, 'ai_wins': 0, 'player_score': 0, 'ai_score': 0},
    }

def load_stats():
    """Carga las estadísticas desde el archivo JSON o devuelve las predeterminadas."""
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, 'r') as f:
                stats = json.load(f)
                # Asegura que el archivo cargado tenga todas las claves de dificultad
                default_stats = get_default_stats()
                for key in default_stats:
                    if key not in stats:
                        stats[key] = default_stats[key]
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

# --- LÓGICA DE LA IA (Sin cambios sustanciales en la estrategia) ---

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

def ai_take_turn(player_grid, player_ships, difficulty, ai_target_queue, last_hit):
    r, c = None, None
    hit, message, sunk_points = False, "", 0

    if difficulty == 'HARD' or (difficulty == 'NORMAL' and random.random() < 0.5 and ai_target_queue):
        if ai_target_queue:
            r, c = ai_target_queue.pop(0) 
        
        if r is None or (player_grid[r][c] != WATER and player_grid[r][c] != SHIP): 
            r, c = random_shot(player_grid)
    else:
        r, c = random_shot(player_grid)
    
    if r is not None and c is not None:
        hit, message, sunk_points = take_shot(player_grid, player_ships, r, c)
    else:
        hit, message, sunk_points = False, "La IA no pudo encontrar un objetivo.", 0

    # Actualizar la cola de objetivos y el último acierto
    new_last_hit = last_hit
    if hit:
        new_last_hit = (r, c)
        
        if sunk_points == 0: 
            if difficulty != 'EASY':
                new_neighbors = get_valid_neighbors(player_grid, r, c)
                for nr, nc in new_neighbors:
                    if (nr, nc) not in ai_target_queue:
                        ai_target_queue.append((nr, nc))
        
        elif sunk_points > 0 and difficulty in ['NORMAL', 'HARD']:
            ai_target_queue = []
            new_last_hit = None 

    return hit, message, sunk_points, ai_target_queue, new_last_hit

# --- PANTALLA DE SELECCIÓN DE DIFICULTAD (Modificada para estadísticas y centrado) ---

def draw_stats_table(screen, font, stats):
    """Dibuja la tabla de estadísticas totales, centrada."""
    y_start = 450
    small_font = pygame.font.Font(None, 24)
    
    draw_text(screen, "MARCADOR GLOBAL", font, BLACK, WIDTH // 2, y_start)
    y_current = y_start + 40

    # Definir las posiciones X (centradas). 
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
    for difficulty in ['EASY', 'NORMAL', 'HARD']:
        data = stats.get(difficulty, {'player_wins': 0, 'ai_wins': 0, 'player_score': 0, 'ai_score': 0})
        
        diff_text = difficulty.capitalize()
        
        draw_text(screen, diff_text, small_font, BLACK, x_pos[0], y_current)
        draw_text(screen, str(data['player_wins']), small_font, GREEN, x_pos[1], y_current)
        draw_text(screen, str(data['ai_wins']), small_font, RED, x_pos[2], y_current)
        draw_text(screen, str(data['player_score']), small_font, BLUE, x_pos[3], y_current)
        draw_text(screen, str(data['ai_score']), small_font, BLUE, x_pos[4], y_current)
        y_current += 25


def difficulty_menu(screen, font, stats):
    """Muestra el menú de selección de dificultad y espera la elección."""
    running = True
    
    buttons = {
        "FÁCIL": (WIDTH // 2, 200, 200, 50, 'EASY'),
        "NORMAL": (WIDTH // 2, 280, 200, 50, 'NORMAL'),
        "DIFÍCIL": (WIDTH // 2, 360, 200, 50, 'HARD')
    }
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None 
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = event.pos
                for _, (cx, cy, w, h, mode) in buttons.items():
                    rect = pygame.Rect(cx - w // 2, cy - h // 2, w, h)
                    if rect.collidepoint(mouse_x, mouse_y):
                        return mode
                        
        screen.fill(WHITE)
        draw_text(screen, "SELECCIONA LA DIFICULTAD", font, BLACK, WIDTH // 2, 100)
        
        # Dibujar botones
        for text, (cx, cy, w, h, mode) in buttons.items():
            rect = pygame.Rect(cx - w // 2, cy - h // 2, w, h)
            
            color = GREY
            if rect.collidepoint(pygame.mouse.get_pos()):
                color = DARK_RED
            
            pygame.draw.rect(screen, color, rect)
            draw_text(screen, text, font, WHITE, cx, cy)
            
        # Dibujar la tabla de estadísticas
        draw_stats_table(screen, font, stats)

        pygame.display.update()
        pygame.time.Clock().tick(30)
    
    return None

# --- BUCLE PRINCIPAL DEL JUEGO (Modificado para puntuación y victoria) ---

def game_loop(screen, difficulty_mode, stats):
    pygame.display.set_caption(f"Hundir la Flota - Modo: {difficulty_mode}")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 36)
    small_font = pygame.font.Font(None, 24)

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
    
    current_player_score = 0
    current_ai_score = 0

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # Guardar antes de salir
                if game_over:
                    save_stats(stats)
                return None 
            
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                # Guardar antes de volver al menú
                if game_over:
                    save_stats(stats)
                return True 
            
            # --- Manejo de Clicks (Turno del Jugador) ---
            if event.type == pygame.MOUSEBUTTONDOWN and not game_over:
                if player_turn:
                    mouse_pos = pygame.mouse.get_pos()
                    grid_row, grid_col = get_grid_coords_from_mouse(mouse_pos, GRID_OFFSET_X_AI, GRID_OFFSET_Y_AI)
                    
                    if grid_row is not None:
                        if ai_grid[grid_row][grid_col] == WATER or ai_grid[grid_row][grid_col] == SHIP:
                            
                            hit, message, sunk_points = take_shot(ai_grid, ai_ships, grid_row, grid_col)
                            game_message = f"Jugador: {message}"
                            
                            if sunk_points > 0:
                                current_player_score += sunk_points
                                
                            if check_win(ai_ships):
                                game_over = True
                                winner_message = "¡Has ganado! ¡Hundiste toda la flota enemiga!"
                                # Actualizar estadísticas globales
                                stats[difficulty_mode]['player_wins'] += 1
                                stats[difficulty_mode]['player_score'] += current_player_score
                                stats[difficulty_mode]['ai_score'] += current_ai_score
                            
                            player_turn = False 
                        else:
                            game_message = "Jugador: Ya has disparado aquí."
            
            # --- Reiniciar Juego (con R) ---
            if game_over and event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                # Guardar antes de reiniciar
                save_stats(stats)
                return True 

        # --- Lógica del Turno de la IA ---
        if not player_turn and not game_over:
            time.sleep(0.8)

            hit, message, sunk_points, ai_target_queue, last_hit_coord = ai_take_turn(
                player_grid, player_ships, difficulty_mode, ai_target_queue, last_hit_coord
            )
            
            game_message = f"IA ({difficulty_mode}): {message}"
            
            if sunk_points > 0:
                current_ai_score += sunk_points
                
            if check_win(player_ships):
                game_over = True
                winner_message = "¡La IA ha ganado! ¡Tu flota ha sido hundida!"
                # Actualizar estadísticas globales
                stats[difficulty_mode]['ai_wins'] += 1
                stats[difficulty_mode]['player_score'] += current_player_score
                stats[difficulty_mode]['ai_score'] += current_ai_score

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
        draw_text(screen, game_message, font, BLACK, WIDTH // 2, 50)

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

    app_running = True
    while app_running:
        
        # 2. Mostrar menú de dificultad y pasar las estadísticas
        selected_difficulty = difficulty_menu(screen, font_large, game_stats)
        
        if selected_difficulty is None:
            app_running = False
        
        elif selected_difficulty:
            # 3. Iniciar el juego
            result = game_loop(screen, selected_difficulty, game_stats)
            
            if result is None:
                app_running = False

    # 4. Guardar las estadísticas finales al salir de la aplicación
    save_stats(game_stats)
    pygame.quit()