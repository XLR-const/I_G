import pygame
import math

# ========== КОНСТАНТЫ ==========
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
SENSE = 0.002


# Карта (1 - стена, 0 - пустота)
MAP = [
    [1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 1, 0, 0, 1, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 1, 1, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1],
]

MAP_WIDTH = len(MAP[0])
MAP_HEIGHT = len(MAP)
TILE_SIZE = 64  # для мини-карты (не используется в рейкастинге напрямую)

# Параметры игрока
PLAYER_SPEED = 0.05
FOV = math.pi / 3  # 60 градусов
HEIGHT_COEF = 250  # коэффициент высоты стен (подбери под свой вкус)

# ========== ФУНКЦИЯ РЕЙКАСТИНГА (DDA) ==========
def cast_ray(px, py, angle):
    """Возвращает расстояние до стены, попали ли, тип стены и координаты"""
    ray_dir_x = math.cos(angle)
    ray_dir_y = math.sin(angle)
    
    map_x = int(px)
    map_y = int(py)
    
    delta_dist_x = abs(1 / ray_dir_x) if ray_dir_x != 0 else 1e30
    delta_dist_y = abs(1 / ray_dir_y) if ray_dir_y != 0 else 1e30
    
    step_x = 1 if ray_dir_x > 0 else -1
    step_y = 1 if ray_dir_y > 0 else -1
    
    side_dist_x = (map_x + 1 - px) * delta_dist_x if ray_dir_x > 0 else (px - map_x) * delta_dist_x
    side_dist_y = (map_y + 1 - py) * delta_dist_y if ray_dir_y > 0 else (py - map_y) * delta_dist_y
    
    hit = False
    side = 0
    max_distance = 20
    distance = 0
    
    while not hit and distance < max_distance:
        if side_dist_x < side_dist_y:
            side_dist_x += delta_dist_x
            map_x += step_x
            side = 0
        else:
            side_dist_y += delta_dist_y
            map_y += step_y
            side = 1
        
        if map_x < 0 or map_x >= MAP_WIDTH or map_y < 0 or map_y >= MAP_HEIGHT:
            break
        
        if MAP[map_y][map_x] > 0:
            hit = True
            
            if side == 0:
                distance = (map_x - px + (1 - step_x) / 2) / ray_dir_x
            else:
                distance = (map_y - py + (1 - step_y) / 2) / ray_dir_y
            distance = abs(distance)
    
    if not hit:
        distance = 9999
    
    return distance, hit, side, (map_x, map_y)

# ========== ИНИЦИАЛИЗАЦИЯ ==========
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()
pygame.display.set_caption("Raycasting Demo")
pygame.mouse.set_visible(False)
pygame.event.set_grab(True)

# Игрок
player_x = 1.5
player_y = 1.5
player_angle = 0

# ========== ГЛАВНЫЙ ЦИКЛ ==========
running = True
while running:
    # Обработка событий
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
    
    # Управление с клавиатуры (WASD)
    keys = pygame.key.get_pressed()
    
    new_x = player_x
    new_y = player_y
    
    if keys[pygame.K_w]:
        new_x += math.cos(player_angle) * PLAYER_SPEED
        new_y += math.sin(player_angle) * PLAYER_SPEED
    if keys[pygame.K_s]:
        new_x -= math.cos(player_angle) * PLAYER_SPEED
        new_y -= math.sin(player_angle) * PLAYER_SPEED
    if keys[pygame.K_a]:
        new_x += math.cos(player_angle - math.pi/2) * PLAYER_SPEED
        new_y += math.sin(player_angle - math.pi/2) * PLAYER_SPEED
    if keys[pygame.K_d]:
        new_x += math.cos(player_angle + math.pi/2) * PLAYER_SPEED
        new_y += math.sin(player_angle + math.pi/2) * PLAYER_SPEED
    
    # Простые коллизии
    map_x = int(new_x)
    map_y = int(player_y)
    if 0 <= map_x < MAP_WIDTH and 0 <= map_y < MAP_HEIGHT:
        if MAP[map_y][map_x] == 0:
            player_x = new_x
    
    map_x = int(player_x)
    map_y = int(new_y)
    if 0 <= map_x < MAP_WIDTH and 0 <= map_y < MAP_HEIGHT:
        if MAP[map_y][map_x] == 0:
            player_y = new_y
    
    # Поворот мышью
    mouse_dx = pygame.mouse.get_rel()[0]
    player_angle += mouse_dx * SENSE
    
    # Заливка экрана (небо и пол)
    screen.fill((50, 50, 100))  # небо голубое
    pygame.draw.rect(screen, (50, 50, 50), (0, SCREEN_HEIGHT//2, SCREEN_WIDTH, SCREEN_HEIGHT//2))  # пол тёмный
    
    # ========== РЕЙКАСТИНГ ==========
    for ray_num in range(SCREEN_WIDTH):
        # Угол текущего луча
        ray_angle = player_angle - FOV/2 + (ray_num / SCREEN_WIDTH) * FOV
        
        # Пускаем луч
        dist, hit, side, hit_pos = cast_ray(player_x, player_y, ray_angle)
        
        if hit:
            # Коррекция "рыбий глаз"
            fish_fix = math.cos(ray_angle - player_angle)
            dist = dist * fish_fix
            
            # Защита от деления на ноль
            ray_size = dist + 0.0001
            
            # Высота стены
            wall_height = int(HEIGHT_COEF / ray_size)
            if wall_height > SCREEN_HEIGHT:
                wall_height = SCREEN_HEIGHT
            
            y_start = SCREEN_HEIGHT//2 - wall_height//2
            if y_start < 0:
                y_start = 0
            y_end = SCREEN_HEIGHT//2 + wall_height//2
            if y_end > SCREEN_HEIGHT:
                y_end = SCREEN_HEIGHT
            
            # Затемнение по расстоянию
            brightness = 255 / (1 + dist * dist * 0.3)
            if brightness < 40:
                brightness = 40
            color_val = int(brightness)
            
            # Разные оттенки для вертикальных и горизонтальных стен
            if side == 0:
                color = (color_val // 2, color_val // 3, color_val // 2)
            else:
                color = (color_val, color_val // 2, color_val // 2)
            
            # Рисуем вертикальную полоску
            pygame.draw.line(screen, color, (ray_num, y_start), (ray_num, y_end))
    
    # Отладочная информация
    font = pygame.font.Font(None, 24)
    text = font.render(f"X: {player_x:.2f} Y: {player_y:.2f} Angle: {int(math.degrees(player_angle))} deg", True, (255, 255, 255))
    screen.blit(text, (10, 10))
    
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()