import math
import pygame
# Game setting
pygame.init()
info = pygame.display.Info()
WIDTH = info.current_w
HEIGHT = info.current_h
RES = (WIDTH, HEIGHT)
GRID_W = 32
GRID_H = 18
CELL_W, CELL_H = WIDTH // GRID_W, HEIGHT // GRID_H
HALF_WIDTH = WIDTH // 2
HALF_HEIGHT = HEIGHT // 2
MASTER_VOLUME = 0.5
FPS = 300
TILE = 100 # Коэффициент масштабирования

# Players settings
PLAYER_POS = (1.5, 5)
PLAYER_ANGLE = 0
PLAYER_SPEED = 0.004
PLAYER_ROT_SPEED = 0.002
PLAYER_SIZE_SCALE = 0.2 # Коллизия игрока внутри клетки

# Mouse control
MOUSE_SENSITIVITY = 0.002
MOUSE_MAX_REL = 40 # Ограничение резкого рывка
MOUSE_BORDER_LEFT = 100
MOUSE_BORDER_RIGHT = WIDTH - 100

# Raycasting
FOV = math.pi / 3 # 60 degrees
HALF_FOV = FOV / 2
NUM_RAYS = WIDTH // 2
SCALE = math.ceil(WIDTH // NUM_RAYS)
HALF_NUM_RAYS = NUM_RAYS // 2
DELTA_ANGLE = FOV / NUM_RAYS # шаг угла меж лучами
SCREEN_DIST = WIDTH // 2 / math.tan(HALF_FOV) # Масштабирование мира 
MAX_DEPTH = 20
# Цвета стен
WALL_COLORS = {
    '1': (200, 200, 200),  # белый/серый (стандарт)
    'R': (200, 150, 150),  # пастельно-красный
    'B': (150, 150, 200),  # пастельно-синий
    'G': (150, 200, 150),  # пастельно-зелёный
    'Y': (200, 200, 150),  # пастельно-жёлтый
    'P': (200, 150, 200),  # пастельно-пурпурный
    'O': (200, 180, 150),  # пастельно-оранжевый
    'C': (150, 200, 200),  # пастельно-голубой
    'W': (180, 160, 140),  # пастельно-деревянный
    'S': (160, 160, 160),  # пастельно-каменный
    'M': (170, 170, 190),  # пастельно-металлик
}

# Текстуры
TEXTURE_SIZE = 128
TEXTURES_PATH = "resources/textures/"
USE_TEXTURES = True
TEXTURE_NAMES = ['W', 'R', 'B', 'G', 'Y', 'P', 'O', 'C', 'S', 'M', "D", "^"]


# === КОНВЕРТЕР КООРДИНАТ СЕТКИ ===
def grid_to_pixel(col, row, mod='topleft'):
    """
    Преобразует координаты сетки (32×18) в пиксельные координаты экрана.
    
    Параметры:
        col, row - координаты в сетке (0-31, 0-17)
        mod - точка привязки:
            'topleft' - верхний левый угол (по умолчанию)
            'center' - центр клетки
            'midtop' - середина верхней границы
            'midbottom' - середина нижней границы
            'midleft' - середина левой границы
            'midright' - середина правой границы
            'topright' - правый верхний угол
            'bottomleft' - левый нижний угол
            'bottomright' - правый нижний угол
    
    Возвращает:
        (x, y) - координаты в пикселях
    """
    x = col * CELL_W
    y = row * CELL_H
    
    if mod == 'topleft':
        return (x, y)
    elif mod == 'center':
        return (x + CELL_W // 2, y + CELL_H // 2)
    elif mod == 'midtop':
        return (x + CELL_W // 2, y)
    elif mod == 'midbottom':
        return (x + CELL_W // 2, y + CELL_H)
    elif mod == 'midleft':
        return (x, y + CELL_H // 2)
    elif mod == 'midright':
        return (x + CELL_W, y + CELL_H // 2)
    elif mod == 'topright':
        return (x + CELL_W, y)
    elif mod == 'bottomleft':
        return (x, y + CELL_H)
    elif mod == 'bottomright':
        return (x + CELL_W, y + CELL_H)
    else:
        return (x, y)
