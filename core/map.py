import pygame
from setting import *
from core.door import Door
from config.game_data import SYMBOLS_CONFIG, NPC_CONFIG, WEAPON_CONFIG


class Map:
    """Класс карты

    Attributes:
        game: Объект игры
        text_map: Текстовая карта (массив строк)
        doors: Список дверей
        world_map: Словарь стен {(x, y): symbol}
        npc_positions: Список позиций NPC [(x, y, symbol)]
        weapon_positions: Список позиций оружия [(x, y, symbol)]
        exit_pos: Координаты выхода (x, y)
        player_spawn_pos: Координаты спавна игрока (x, y)
        width: Ширина карты в клетках
        height: Высота карты в клетках
    """

    def __init__(self, game, map_data=None):
        """Инициализирует карту

        Args:
            game: Объект игры
            map_data: Текстовая карта
        """
        self.game = game
        self.text_map = map_data if map_data else []
        self.doors = []
        self.world_map = {}
        self.npc_positions = []
        self.weapon_positions = []
        self.item_positions = []
        self.exit_pos = None
        self.player_spawn_pos = None

        if self.text_map:
            self.parse_map()

        self.width = len(self.text_map[0]) if self.text_map else 0
        self.height = len(self.text_map) if self.text_map else 0

    def parse_map(self):
        """Разбирает текстовую карту по символам из конфига"""
        self.npc_positions = []
        self.weapon_positions = []
        self.item_positions = []
        self.exit_pos = None
        self.player_spawn_pos = None
        self.doors = []
        self.world_map = {}

        for j, row in enumerate(self.text_map):
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
                    elif symbol_type == 'item':
                        item_type = SYMBOLS_CONFIG[char].get('item_type')
                        amount = SYMBOLS_CONFIG[char].get('amount', 0)
                        self.item_positions.append((i, j, item_type, amount))

                elif char in NPC_CONFIG:
                    self.npc_positions.append((i, j, char))

                elif char in WEAPON_CONFIG:
                    self.weapon_positions.append((i, j, char))

    def is_wall(self, x, y):
        """Проверяет, является ли клетка стеной

        Args:
            x: Координата X клетки
            y: Координата Y клетки

        Returns:
            bool: True если стена
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
            x: Координата X клетки
            y: Координата Y клетки

        Returns:
            bool: True если проходимо
        """
        return not self.is_wall(x, y)

    def get_exit_pos(self):
        """Возвращает позицию выхода

        Returns:
            tuple: Координаты выхода (x, y) или None
        """
        return self.exit_pos
