"""Класс карты с поддержкой трёх слоёв: стены, пол, потолок

Содержит класс Map для хранения и парсинга игровой карты.
"""

import pygame
from setting import *
from core.door import Door
from config.game_data import SYMBOLS_CONFIG, NPC_CONFIG, WEAPON_CONFIG


class Map:
    """Класс карты с 3 слоями: стены, пол, потолок

    Основной класс для хранения данных карты. Поддерживает:
    - Слой стен (world_map) - существующая логика
    - Слой пола (floor_layer) - высота пола в каждой клетке
    - Слой потолка (ceiling_layer) - высота потолка в каждой клетке

    Attributes:
        game: Объект игры
        world_map: Словарь стен {(x, y): symbol} - существующее поле
        floor_layer: Словарь высот пола {(x, y): height} - новая структура
        ceiling_layer: Словарь высот потолка {(x, y): height} - новая структура
        floor_textures: Словарь текстур пола {(x, y): texture_path} - для будущего
        ceiling_textures: Словарь текстур потолка {(x, y): texture_path} - для будущего
        doors: Список дверей
        npc_positions: Список позиций NPC [(x, y, symbol)]
        weapon_positions: Список позиций оружия [(x, y, symbol)]
        exit_pos: Координаты выхода (x, y)
        player_spawn_pos: Координаты спавна игрока (x, y)
        map_data: Текстовая карта стен (для парсинга)
        floor_data: Текстовая карта высот пола (для парсинга)
        ceiling_data: Текстовая карта высот потолка (для парсинга)
        width: Ширина карты в клетках
        height: Высота карты в клетках
    """

    def __init__(self, game, map_data=None, floor_data=None, ceiling_data=None):
        """Инициализирует карту с тремя слоями

        Args:
            game: Объект игры
            map_data: Текстовая карта стен (массив строк)
            floor_data: Текстовая карта высот пола (массив строк с цифрами)
            ceiling_data: Текстовая карта высот потолка (массив строк с цифрами)
        """
        self.game = game

        # Основной слой стен (существующее поле)
        self.world_map = {}

        # Новые слои для высот
        self.floor_layer = {}
        self.ceiling_layer = {}

        # Текстуры для пола и потолка (задел на будущее)
        self.floor_textures = {}
        self.ceiling_textures = {}

        # Объекты на карте
        self.doors = []
        self.npc_positions = []
        self.weapon_positions = []
        self.exit_pos = None
        self.player_spawn_pos = None

        # Сохраняем текстовые данные для парсинга
        self.map_data = map_data if map_data else []
        self.floor_data = floor_data if floor_data else []
        self.ceiling_data = ceiling_data if ceiling_data else []

        # Парсим карту
        if self.map_data:
            self.parse_map()

        # Размеры карты
        self.width = len(self.map_data[0]) if self.map_data else 0
        self.height = len(self.map_data) if self.map_data else 0

    def parse_map(self):
        """Разбирает текстовые слои карты в словари

        Парсит три слоя:
        1. Стены (world_map) - из map_data по SYMBOLS_CONFIG
        2. Пол (floor_layer) - из floor_data (цифры = высота)
        3. Потолок (ceiling_layer) - из ceiling_data (цифры = высота)

        Также собирает:
        - Двери
        - Позиции NPC
        - Позиции оружия
        - Выход
        - Спавн игрока
        """
        # Очищаем старые данные
        self.npc_positions = []
        self.weapon_positions = []
        self.exit_pos = None
        self.player_spawn_pos = None
        self.doors = []
        self.world_map = {}

        # ============================================================
        # ПАРСИМ СЛОЙ СТЕН
        # ============================================================
        for j, row in enumerate(self.map_data):
            for i, char in enumerate(row):
                if char == '_' or char == '.':
                    continue

                if char in SYMBOLS_CONFIG:
                    symbol_type = SYMBOLS_CONFIG[char]['type']

                    if symbol_type == 'wall':
                        self.world_map[(i, j)] = char
                    elif symbol_type == 'door':
                        door = Door(self.game, i + 0.5, j + 0.5)
                        self.doors.append(door)
                    elif symbol_type == 'exit':
                        self.exit_pos = (i + 0.5, j + 0.5)
                    elif symbol_type == 'player_spawn':
                        self.player_spawn_pos = (i + 0.5, j + 0.5)

                elif char in NPC_CONFIG:
                    self.npc_positions.append((i, j, char))

                elif char in WEAPON_CONFIG:
                    self.weapon_positions.append((i, j, char))

        # ============================================================
        # ПАРСИМ СЛОЙ ПОЛА
        # ============================================================
        if self.floor_data and len(self.floor_data) == len(self.map_data):
            for j, row in enumerate(self.floor_data):
                for i, char in enumerate(row):
                    if char.isdigit():
                        self.floor_layer[(i, j)] = int(char)
                    elif char == '.':
                        self.floor_layer[(i, j)] = 0

        # ============================================================
        # ПАРСИМ СЛОЙ ПОТОЛКА
        # ============================================================
        if self.ceiling_data and len(self.ceiling_data) == len(self.map_data):
            for j, row in enumerate(self.ceiling_data):
                for i, char in enumerate(row):
                    if char.isdigit():
                        self.ceiling_layer[(i, j)] = int(char)
                    elif char == '.':
                        self.ceiling_layer[(i, j)] = 3  # дефолтная высота

        # ============================================================
        # ЗАПОЛНЯЕМ ПРОПУСКИ В ВЫСОТАХ
        # ============================================================
        # Если нет данных о высотах - задаём дефолтные
        if not self.floor_layer:
            for (x, y) in self.world_map.keys():
                self.floor_layer[(x, y)] = 0
                self.ceiling_layer[(x, y)] = 3

    def get_floor_height(self, x, y):
        """Возвращает высоту пола в клетке

        Args:
            x: Координата X клетки (целое число)
            y: Координата Y клетки (целое число)

        Returns:
            float: Высота пола в клетке (по умолчанию 0)
        """
        return self.floor_layer.get((int(x), int(y)), 0)

    def get_ceiling_height(self, x, y):
        """Возвращает высоту потолка в клетке

        Args:
            x: Координата X клетки (целое число)
            y: Координата Y клетки (целое число)

        Returns:
            float: Высота потолка в клетке (по умолчанию 3)
        """
        return self.ceiling_layer.get((int(x), int(y)), 3)

    def is_wall(self, x, y):
        """Проверяет, является ли клетка стеной

        Args:
            x: Координата X клетки (целое или дробное)
            y: Координата Y клетки (целое или дробное)

        Returns:
            bool: True если стена, False если проходимо
        """
        if (int(x), int(y)) in self.world_map:
            return True

        for door in self.doors:
            if int(door.x) == int(x) and int(door.y) == int(y):
                return door.is_wall()

        return False

    def is_walkable(self, x, y):
        """Проверяет, может ли NPC пройти через клетку

        Args:
            x: Координата X клетки (целое или дробное)
            y: Координата Y клетки (целое или дробное)

        Returns:
            bool: True если проходимо, False если стена
        """
        return not self.is_wall(x, y)

    def get_exit_pos(self):
        """Возвращает позицию выхода с уровня

        Returns:
            tuple: Координаты выхода (x, y) или None если выхода нет
        """
        return self.exit_pos
