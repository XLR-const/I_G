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
pygame.init()
FONT_SMALL = pygame.font.Font(None, 14)
FONT_MEDIUM = pygame.font.Font(None, 18)
FONT_LARGE = pygame.font.Font(None, 24)

# Цвета
COLORS = {
    'wall': (60, 60, 70),
    'floor': (20, 20, 25),
    'start': (100, 80, 0),
    'exit': (0, 100, 0),      # зелёный для выхода
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

# Типы объектов и их символы в карте
OBJECT_TYPES = {
    'wall': ['M', 'C', 'L', 'R', 'B', 'G', 'W', 'I'],
    'floor': ['_'],
    'start': ['S'],
    'exit': ['E'],           # Выход в карте — символ E
    'door': ['D'],
    'npc': ['2', '3', '4', '5'],
    'boss': ['6'],
}

# Для каждого символа — цвет фона в редакторе
# N — это текстура выхода в игре, но в редакторе это просто стена
SYMBOL_COLORS = {
    # Стены
    'M': COLORS['wall'],
    'C': COLORS['wall'],
    'L': COLORS['wall'],
    'R': COLORS['wall'],
    'B': COLORS['wall'],
    'G': COLORS['wall'],
    'W': COLORS['wall'],
    'I': COLORS['wall'],
    'N': COLORS['wall'],
    # Пол
    '_': COLORS['floor'],
    # Объекты
    'S': COLORS['start'],
    'E': COLORS['wall'],      # Выход — зелёный
    'D': COLORS['door'],
    # NPC
    '2': COLORS['npc'],
    '3': COLORS['npc'],
    '4': COLORS['npc'],
    '5': COLORS['npc'],
    '6': COLORS['boss'],
}

# Пути к ресурсам
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESOURCES_DIR = os.path.join(ROOT_DIR, 'resources')
TEXTURES_DIR = os.path.join(RESOURCES_DIR, 'textures')
NPC_DIR = os.path.join(RESOURCES_DIR, 'npc')
LEVELS_DIR = os.path.join(RESOURCES_DIR, 'levels')
BACKUP_DIR = os.path.join(LEVELS_DIR, 'levels_backup')

GAME_DATA_PATH = os.path.join(ROOT_DIR, 'config', 'game_data.py')
