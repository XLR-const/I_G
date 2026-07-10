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
COLORS = {
    # Стены (фон клетки)
    'wall': (60, 60, 70),        # тёмно-серый
    'floor': (20, 20, 25),       # чёрный
    'start': (100, 80, 0),       # тёмно-жёлтый
    'exit': (0, 80, 0),          # тёмно-зелёный
    'door': (100, 60, 0),        # тёмно-оранжевый
    'npc': (100, 0, 0),          # тёмно-красный
    'boss': (80, 0, 100),        # тёмно-фиолетовый

    # Текст
    'text': (240, 240, 240),     # белый
    'text_dim': (120, 120, 120), # серый

    # Сетка и выделение
    'grid': (80, 80, 90),        # полупрозрачная сетка
    'grid_dim': (40, 40, 50),    # тёмная сетка
    'selection': (255, 255, 255, 128),  # ярко-белое выделение
    'selection_border': (255, 255, 255, 255),  # рамка выделения

    # Фон редактора
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
    'h': (200, 0, 0),
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

