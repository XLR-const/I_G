import math
# Game setting
WIDTH = 1600
HEIGHT = 900
RES = (1920, 1080)
HALF_WIDTH = WIDTH // 2
HALF_HEIGHT = HEIGHT // 2
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
NUM_RAYS = WIDTH
SCALE = math.ceil(WIDTH // NUM_RAYS)
HALF_NUM_RAYS = NUM_RAYS // 2
DELTA_ANGLE = FOV / NUM_RAYS # шаг угла меж лучами
SCREEN_DIST = WIDTH // 2 / math.tan(HALF_FOV) # Масштабирование мира 
MAX_DEPTH = 20