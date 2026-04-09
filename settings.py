import math

# Размер окна
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

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
TILE_SIZE = 64

# Параметры игрока
PLAYER_SPEED = 0.03
MOUSE_SENSE = 0.005

# Параметры рейкастинга
FOV = math.pi / 3  # 60 градусов
HEIGHT_COEF = 250

# Оружие
SHOOT_DISTANCE = 10
SHOT_COOLDOWN = 10
CROSSHAIR_SIZE = 10
