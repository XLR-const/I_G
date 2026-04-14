import math
# Game setting
WIDTH = 1600
HEIGHT = 900
FPS = 60
TILE = 100

# Players settings
PLAYER_POS = (1.5, 5)
PLAYER_ANGLE = 0
PLAYER_SPEED = 0.004
PLAYER_ROT_SPEED = 0.002
PLAYER_SIZE_SCALE = 60 # Коллизия игрока

# Mouse control
MOUSE_SENSITIVITY = 0.0004
MOUSE_MAX_REL = 40 # Ограничение резкого рывка
MOUSE_BORDER_LEFT = 100
MOUSE_BORDER_RIGHT = WIDTH - 100