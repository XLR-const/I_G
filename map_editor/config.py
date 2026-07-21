"""Конфигурация редактора карт — полностью автоматическая"""

import os
import pygame
from config.game_data import SYMBOLS_CONFIG, NPC_CONFIG

# ============================================================
# РАЗМЕРЫ
# ============================================================
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
DEFAULT_CELL_SIZE = 20
MIN_CELL_SIZE = 6
MAX_CELL_SIZE = 80

# ============================================================
# БАЗОВЫЕ ЦВЕТА (только для фона и интерфейса)
# ============================================================
COLORS = {
    'background': (30, 30, 35),
    'text': (240, 240, 240),
    'text_dim': (160, 160, 170),
    'grid': (80, 80, 90),
    'selection': (255, 255, 255, 128),
    'panel_bg': (45, 45, 50),
    'panel_border': (80, 80, 90),
    'info_bg': (35, 35, 40),
}

# ============================================================
# АВТОМАТИЧЕСКИЕ ЦВЕТА (fallback, если нет текстуры)
# ============================================================
def generate_symbol_colors():
    """Генерирует цвета для всех объектов из конфигов"""
    colors = {}
    
    # 1. Стены — серые
    for symbol, config in SYMBOLS_CONFIG.items():
        if config.get('type') == 'wall':
            colors[symbol] = (60, 60, 70)
    
    # 2. Пол — тёмный
    colors['_'] = (20, 20, 25)
    
    # 3. Спавн — жёлтый
    colors['S'] = (100, 80, 0)
    
    # 4. Выход — зелёный
    colors['E'] = (0, 100, 0)
    
    # 5. Двери — серые
    for symbol, config in SYMBOLS_CONFIG.items():
        if config.get('type') == 'door':
            door_type = config.get('door_type', 'normal')
            if door_type == 'secret':
                colors[symbol] = (100, 80, 60)
            elif door_type == 'key_red':
                colors[symbol] = (200, 50, 50)
            elif door_type == 'key_blue':
                colors[symbol] = (50, 100, 200)
            elif door_type == 'key_yellow':
                colors[symbol] = (200, 200, 50)
            else:
                colors[symbol] = (100, 100, 100)
    
    # 6. Предметы
    item_colors = {
        'health': (200, 0, 0),
        'armor': (0, 100, 200),
        'key_red': (200, 0, 0),
        'key_blue': (0, 100, 200),
        'key_yellow': (200, 200, 0),
    }
    
    for symbol, config in SYMBOLS_CONFIG.items():
        if config.get('type') == 'item':
            item_type = config.get('item_type')
            if item_type in item_colors:
                colors[symbol] = item_colors[item_type]
            elif config.get('weapon_name'):
                colors[symbol] = (200, 200, 0)  # Оружие — жёлтое
            else:
                colors[symbol] = (150, 150, 150)
    
    # 7. NPC
    npc_colors = {
        '2': (200, 50, 50),
        '3': (200, 100, 0),
        '4': (150, 50, 200),
        '5': (50, 200, 200),
        '6': (200, 0, 200),
    }
    
    for symbol in NPC_CONFIG.keys():
        colors[symbol] = npc_colors.get(symbol, (200, 100, 100))
    
    return colors

SYMBOL_COLORS = generate_symbol_colors()

# ============================================================
# ПУТИ
# ============================================================
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESOURCES_DIR = os.path.join(ROOT_DIR, 'resources')
TEXTURES_DIR = os.path.join(RESOURCES_DIR, 'textures')
NPC_DIR = os.path.join(RESOURCES_DIR, 'npc')
LEVELS_DIR = os.path.join(RESOURCES_DIR, 'levels')
BACKUP_DIR = os.path.join(LEVELS_DIR, 'levels_backup')
GAME_DATA_PATH = os.path.join(ROOT_DIR, 'config', 'game_data.py')