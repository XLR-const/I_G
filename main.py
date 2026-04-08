import pygame
import math
from settings import *
from player import Player
from world import World
from raycast import cast_ray

# Инициализация Pygame
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()
pygame.display.set_caption("Raycasting Demo")
pygame.mouse.set_visible(False)
pygame.event.set_grab(True)

# Создание объектов
player = Player(1.5, 1.5, 0)
world = World(MAP)

# Главный цикл
running = True
while running:
    # Обработка событий
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
    
    # Управление с клавиатуры
    keys = pygame.key.get_pressed()
    new_x, new_y = player.move(keys, PLAYER_SPEED)
    player.apply_collision(new_x, new_y, world)
    
    # Поворот мышью
    mouse_dx = pygame.mouse.get_rel()[0]
    player.rotate(mouse_dx, MOUSE_SENSE)
    
    # Отрисовка неба и пола
    screen.fill((50, 50, 100))  # небо голубое
    pygame.draw.rect(screen, (50, 50, 50), (0, SCREEN_HEIGHT//2, SCREEN_WIDTH, SCREEN_HEIGHT//2))  # пол тёмный
    
    # ========== РЕЙКАСТИНГ ==========
    for ray_num in range(SCREEN_WIDTH):
        # Угол текущего луча
        ray_angle = player.angle - FOV/2 + (ray_num / SCREEN_WIDTH) * FOV
        
        # Пускаем луч
        dist, hit, side, _ = cast_ray(player.x, player.y, ray_angle, world.map)
        
        if hit:
            # Коррекция "рыбий глаз"
            fish_fix = math.cos(ray_angle - player.angle)
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
    text = font.render(f"X: {player.x:.2f} Y: {player.y:.2f} Angle: {int(math.degrees(player.angle))} deg", True, (255, 255, 255))
    screen.blit(text, (10, 10))
    
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()