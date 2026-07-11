import json
import os
import pygame
import math
from setting import *
from core.map import Map
from core.player import Player
from core.npc import Solder, Kamikaze, Jaggernaut, Lightning, Boss
from core.weapon import Pistol, Shotgun, MachineGun, PlasmaGun
from config.game_data import NPC_CONFIG, WEAPON_CONFIG, SYMBOLS_CONFIG
from core.item import *
import numpy as np

class LevelManager:
    """Менеджер загрузки уровней

    Отвечает за загрузку уровней из JSON, создание всех игровых объектов,
    переход между уровнями и сброс игры.

    Attributes:
        game: Объект игры
        current_level: Текущий уровень
        total_kills: Общее количество убийств
        level_start_time: Время начала уровня
        level_time: Время прохождения уровня
        exit_pos: Позиция выхода
        player: Объект игрока
        map: Объект карты
        npcs: Список NPC
        items: Список предметов
        inventory: Инвентарь игрока
        weapon: Текущее оружие
        current_weapon_index: Индекс текущего оружия
        particles: Список частиц
        levels_folder: Папка с уровнями
    """

    def __init__(self, game):
        """Инициализирует менеджер уровней

        Args:
            game: Объект игры
        """
        self.game = game

        self.current_level = 1
        self.total_kills = 0
        self.level_start_time = 0
        self.level_time = 0
        self.exit_pos = None

        self.player = None
        self.map = None
        self.npcs = []
        self.items = []
        self.inventory = []
        self.weapon = None
        self.current_weapon_index = 0
        self.particles = []

        self.levels_folder = "resources/levels"
        
    @staticmethod
    def get_auto_char_to_id():
        """Автоматически создает словарь соответствия символов стен числовым ID"""
        char_to_id = {}
        current_id = 1
        
        for symbol, config in SYMBOLS_CONFIG.items():
            if config.get('type') in ('wall', 'door'):
                char_to_id[symbol] = current_id
                current_id += 1
                
        return char_to_id

    def load_level(self, level_num):
        """Загружает уровень из JSON

        Args:
            level_num: Номер уровня

        Returns:
            bool: True если загрузка успешна
        """
        print(f"\n{'=' * 60}")
        print(f"ЗАГРУЗКА УРОВНЯ {level_num}")
        print(f"{'=' * 60}")

        file_path = f"{self.levels_folder}/level_{level_num}.json"
        if not os.path.exists(file_path):
            print(f"Ошибка: уровень {file_path} не найден!")
            return False

        with open(file_path, 'r') as f:
            level_data = json.load(f)

        if hasattr(self.game, 'raycasting'):
            self.game.raycasting.texture_cache.clear()

        self.particles = []
        self.total_kills = 0
        self.npcs = []

        self.map = Map(self.game, level_data['map'])

        # Items
        for x, y, item_type, amount, weapon_name, ammo in self.map.item_positions:
            if item_type == 'health':
                item = HealthItem(self.game, x, y, amount)
            elif item_type == 'armor':
                item = ArmorItem(self.game, x, y, amount)
            elif item_type == 'weapon':
                item = WeaponItem(self.game, x, y, weapon_name, ammo)
            else:
                continue
            self.items.append(item)

        background = level_data.get('background', {})
        self.game.renderer.set_background(background)

        if self.map.player_spawn_pos:
            if self.player is None:
                self.player = Player(self.game)
            self.player.x, self.player.y = self.map.player_spawn_pos
            self.player.hp = 100
            self.player.angle = 0
            self.exit_pos = self.map.exit_pos
        else:
            print("ОШИБКА: Нет спавна игрока на карте (символ 'S')")
            return False

        self.inventory = []
        for weapon_name in level_data.get('inventory', ['Pistol']):
            config = WEAPON_CONFIG.get(weapon_name)
            if not config:
                continue

            class_name = config.get('class_name')
            if not class_name:
                continue

            weapon_class = globals().get(class_name)
            if not weapon_class:
                continue

            weapon = weapon_class(self.game)
            self.inventory.append(weapon)

        if not self.inventory:
            self.inventory = [Pistol(self.game)]

        self.current_weapon_index = 0
        self.weapon = self.inventory[0]

        self.npcs = []
        for npc_x, npc_y, npc_type in self.map.npc_positions:
            config = NPC_CONFIG.get(npc_type)
            if not config:
                continue

            class_name = config.get('class_name')
            if not class_name:
                continue

            npc_class = globals().get(class_name)
            if not npc_class:
                continue

            x, y = npc_x + 0.5, npc_y + 0.5
            npc = npc_class(self.game, pos=(x, y))
            self.npcs.append(npc)

        for npc in self.npcs:
            try:
                npc.generate_waypoints_auto(4)
                npc.state = "PATROL"
            except Exception as e:
                print(f"Ошибка waypoints для {npc.name}: {e}")
                npc.waypoints = []
                npc.state = "IDLE"

        # =================
        # АВТОМАТИЧЕСКАЯ ОПТИМИЗАЦИЯ NUMBA
        # =================
        char_to_id = {}
        id_to_char = {}
        current_id = 1
        
        for symbol, config in SYMBOLS_CONFIG.items():
            if config.get('type') in ('wall', 'door'):
                char_to_id[symbol] = current_id
                id_to_char[current_id] = symbol
                current_id += 1

        if hasattr(self.game, 'raycasting'):
            self.game.raycasting.id_to_char = id_to_char

        string_grid = level_data['map']
        height = len(string_grid)
        
        # Находим максимальную длину строки на карте, чтобы матрица была ровной
        width = max(len(row) for row in string_grid) if height > 0 else 0
        
        numeric_grid = np.zeros((height, width), dtype=np.int32)
        for y in range(height):
            # Проверяем реальную длину текущей строки
            current_row_len = len(string_grid[y])
            for x in range(width):
                # Если строка оказалась короче максимальной — считаем это пустотой (0)
                if x < current_row_len:
                    symbol = string_grid[y][x]
                    numeric_grid[y][x] = char_to_id.get(symbol, 0)
                else:
                    numeric_grid[y][x] = 0
                
        self.map.numeric_grid = numeric_grid
        # ============================================================

        
        print(f"Уровень {level_num} загружен: {len(self.npcs)} NPC, {len(self.inventory)} оружия")
        return True

    def next_level(self):
        """Переход на следующий уровень"""
        self.level_time = (pygame.time.get_ticks() - self.level_start_time) // 1000
        self.current_level += 1
        self.game.save_system.save(self.current_level, self.total_kills, self.level_time)
        next_level_path = f"{self.levels_folder}/level_{self.current_level}.json"
        if os.path.exists(next_level_path):
            self.game.ui_manager.current_state = self.game.ui_manager.states['LEVEL_END']
        else:
            self.game.ui_manager.current_state = self.game.ui_manager.states['MENU']

    def check_exit(self):
        """Проверяет, достиг ли игрок выхода"""
        if self.exit_pos is None or self.player is None:
            return

        player_cell = (int(self.player.x), int(self.player.y))
        exit_cell = (int(self.exit_pos[0]), int(self.exit_pos[1]))

        if player_cell == exit_cell:
            self.next_level()

    def reset_game(self):
        """Полный сброс игры (новый старт)"""
        self.game.save_system.delete()
        self.total_kills = 0
        self.level_time = 0
        self.current_level = 1
        self.load_level(self.current_level)

    def game_over(self):
        """Завершение игры"""
        pygame.quit()
