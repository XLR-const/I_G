"""Конфигурация редактора карт"""

import os
import pygame

# Размеры окна
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800

# Размер клетки в пикселях (будет пересчитываться под размер карты)
DEFAULT_CELL_SIZE = 20
MIN_CELL_SIZE = 8
MAX_CELL_SIZE = 60

# Шрифты (создаются один раз)
pygame.init()
FONT_SMALL = pygame.font.Font(None, 14)
FONT_MEDIUM = pygame.font.Font(None, 18)
FONT_LARGE = pygame.font.Font(None, 24)

# Цветовая схема
"""Конфигурация редактора карт"""

import os
import pygame

# Размеры окна
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800

# Размер клетки
DEFAULT_CELL_SIZE = 20
MIN_CELL_SIZE = 6
MAX_CELL_SIZE = 80

# Шрифты
FONT_PATH = os.path.join("resources", "fonts", "Roboto-Regular.ttf")
FONT_BOLD_PATH = os.path.join("resources", "fonts", "Roboto-Bold.ttf")

# Если шрифтов нет — используем системные
try:
    FONT_SMALL = pygame.font.Font(FONT_PATH, 14)
    FONT_MEDIUM = pygame.font.Font(FONT_PATH, 18)
    FONT_LARGE = pygame.font.Font(FONT_PATH, 24)
    FONT_BOLD = pygame.font.Font(FONT_BOLD_PATH, 18)
except:
    # Fallback на системные
    FONT_SMALL = pygame.font.SysFont("Arial", 14, bold=False)
    FONT_MEDIUM = pygame.font.SysFont("Arial", 18, bold=False)
    FONT_LARGE = pygame.font.SysFont("Arial", 24, bold=False)
    FONT_BOLD = pygame.font.SysFont("Arial", 18, bold=True)

# Цвета
COLORS = {
    'wall': (60, 60, 70),
    'floor': (20, 20, 25),
    'start': (100, 80, 0),
    'exit': (0, 80, 0),
    'door': (100, 60, 0),
    'npc': (100, 0, 0),
    'boss': (80, 0, 100),
    'text': (240, 240, 240),
    'text_dim': (160, 160, 170),
    'grid': (80, 80, 90),
    'grid_dim': (40, 40, 50),
    'selection': (255, 255, 255, 128),
    'selection_border': (255, 255, 255, 255),
    'background': (30, 30, 35),
    'panel_bg': (45, 45, 50),
    'panel_border': (80, 80, 90),
    'toolbar_bg': (40, 40, 45),
    'info_bg': (35, 35, 40),
}


# Типы объектов и их цвета
OBJECT_TYPES = {
    'wall': ['M', 'C', 'L', 'R', 'B', 'G', 'W', 'I'],
    'floor': ['_'],
    'start': ['S'],
    'exit': ['N'],
    'door': ['D'],
    'npc': ['2', '3', '4', '5'],
    'boss': ['6'],
}

# Для каждого символа — цвет фона
SYMBOL_COLORS = {
    'M': COLORS['wall'],
    'C': COLORS['wall'],
    'L': COLORS['wall'],
    'R': COLORS['wall'],
    'B': COLORS['wall'],
    'G': COLORS['wall'],
    'W': COLORS['wall'],
    'I': COLORS['wall'],
    '_': COLORS['floor'],
    'S': COLORS['start'],
    'N': COLORS['exit'],
    'D': COLORS['door'],
    '2': COLORS['npc'],
    '3': COLORS['npc'],
    '4': COLORS['npc'],
    '5': COLORS['npc'],
    '6': COLORS['boss'],
}

# Пути к ресурсам (относительно корня проекта)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESOURCES_DIR = os.path.join(ROOT_DIR, 'resources')
TEXTURES_DIR = os.path.join(RESOURCES_DIR, 'textures')
NPC_DIR = os.path.join(RESOURCES_DIR, 'npc')
LEVELS_DIR = os.path.join(RESOURCES_DIR, 'levels')
BACKUP_DIR = os.path.join(LEVELS_DIR, 'levels_backup')

# Пути к конфигам
GAME_DATA_PATH = os.path.join(ROOT_DIR, 'config', 'game_data.py')

