import math
import pygame

# Game settings
pygame.init()
info = pygame.display.Info()

WIDTH = info.current_w
HEIGHT = info.current_h
RES = (WIDTH, HEIGHT)

GRID_W = 32
GRID_H = 18
CELL_W = WIDTH // GRID_W
CELL_H = HEIGHT // GRID_H

HALF_WIDTH = WIDTH // 2
HALF_HEIGHT = HEIGHT // 2

MASTER_VOLUME = 0.5
FPS = 300
TILE = 100

# Player settings
PLAYER_POS = (1.5, 5)
PLAYER_ANGLE = 0
PLAYER_SPEED = 0.008
PLAYER_ROT_SPEED = 0.002
PLAYER_SIZE_SCALE = 0.2

# Mouse control
MOUSE_SENSITIVITY = 0.002
MOUSE_MAX_REL = 40
MOUSE_BORDER_LEFT = 100
MOUSE_BORDER_RIGHT = WIDTH - 100

# Raycasting
FOV = math.pi / 3
HALF_FOV = FOV / 2
NUM_RAYS = WIDTH // 2
SCALE = math.ceil(WIDTH // NUM_RAYS)
HALF_NUM_RAYS = NUM_RAYS // 2
DELTA_ANGLE = FOV / NUM_RAYS
SCREEN_DIST = (WIDTH // 2) / math.tan(HALF_FOV)
MAX_DEPTH = 20

# Wall colors (fallback when textures are disabled)
WALL_COLORS = {
    '1': (200, 200, 200),
    'R': (200, 150, 150),
    'B': (150, 150, 200),
    'G': (150, 200, 150),
    'Y': (200, 200, 150),
    'P': (200, 150, 200),
    'O': (200, 180, 150),
    'C': (150, 200, 200),
    'W': (180, 160, 140),
    'S': (160, 160, 160),
    'M': (170, 170, 190),
}

# Textures
TEXTURE_SIZE = 128
TEXTURES_PATH = "resources/textures/"
USE_TEXTURES = True
TEXTURE_NAMES = ['W', 'R', 'B', 'G', 'Y', 'P', 'O', 'C', 'S', 'M', "D", "^", "L"]


def grid_to_pixel(col, row, mod='topleft'):
    """Преобразует координаты сетки в пиксельные координаты экрана

    Args:
        col: Номер колонки в сетке (0-31)
        row: Номер строки в сетке (0-17)
        mod: Точка привязки (topleft, center, midtop, midbottom,
            midleft, midright, topright, bottomleft, bottomright)

    Returns:
        tuple: Координаты (x, y) в пикселях
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
