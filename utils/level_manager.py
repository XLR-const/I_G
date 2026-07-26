import json
import os
import pygame
import math
from setting import *
from core.map import Map
from core.player import Player
from core.npc import NPC
from core.weapon import Weapon
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
        self.items = []

        self.map = Map(self.game, level_data['map'])

        # Items
        for x, y, item_type, amount, weapon_name, ammo in self.map.item_positions:
            if item_type == 'health':
                item = HealthItem(self.game, x, y, amount)
            elif item_type == 'armor':
                item = ArmorItem(self.game, x, y, amount)
            elif item_type == 'weapon':
                item = WeaponItem(self.game, x, y, weapon_name, ammo)
                
            # 🔥 ЧИСТОЕ ДОБАВЛЕНИЕ КЛЮЧА ПО ТВОЕМУ ШАБЛОНУ:
            elif item_type == 'key':
                from core.item import KeyItem
                # Берем цвет ключа ('red', 'blue' или 'yellow') напрямую из переменной amount
                key_color = str(amount).strip().lower()
                # Создаем объект ключа точно так же, как аптечку или броню
                item = KeyItem(self.game, x, y, key_color=key_color)
            
            elif item_type == 'decor':
                from core.item import DecorItem
                # Передаем в decor_name то, как ты упаковываешь имя предмета на карте
                decor_name = str(amount).strip().lower()
                item = DecorItem(self.game, x, y, decor_name=decor_name, height_scale=ammo)
                
            else:
                continue
                
            # Складываем в твой родной список предметов уровня
            self.items.append(item)


        background = level_data.get('background', {})
        self.game.renderer.set_background(background)

        if self.map.player_spawn_pos:
            if self.player is None:
                self.player = Player(self.game)
            self.player.x, self.player.y = self.map.player_spawn_pos
            self.player.hp = 100
            self.player.armor = 0
            self.player.angle = 0
            self.exit_pos = self.map.exit_pos
            self.player.keys_inventory = []
        else:
            print("ОШИБКА: Нет спавна игрока на карте (символ 'S')")
            return False

        self.inventory = []
        
        # Читаем инвентарь из JSON. Если ключа нет — по умолчанию выдаем список с 'Colt'
        start_weapons = level_data.get('inventory', ['KNIFE'])
        
        # Защита на случай, если в JSON ключ 'inventory' есть, но он записан как пустой массив []
        if not start_weapons:
            start_weapons = ['KNIFE']
        
        for weapon_name in start_weapons:
            # Проверяем, существует ли вообще такая пушка в нашем WEAPON_CONFIG
            if weapon_name in WEAPON_CONFIG:
                # Создаем пушку через наш единый универсальный класс Weapon
                weapon = Weapon(self.game, weapon_name)
                self.inventory.append(weapon)

        # Финальная защита: если инвентарь все еще пуст (например, 'Colt' удален из WEAPON_CONFIG)
        if not self.inventory:
            if 'KNIFE' in WEAPON_CONFIG:
                self.inventory.append(Weapon(self.game, 'KNIFE'))
            else:
                # Берем первую попавшуюся пушку из конфига, чтобы игра никогда не падала
                first_weapon_name = list(WEAPON_CONFIG.keys())[0]
                self.inventory.append(Weapon(self.game, first_weapon_name))

        # Делаем активным самое первое оружие из списка инвентаря
        self.current_weapon_index = 0
        
        if len(self.inventory) > 0:
            active_weapon = self.inventory[0]
            
            # Записываем оружие в менеджер уровней
            self.weapon = active_weapon 
            
            # Записываем оружие в главный класс игры
            self.game.weapon = active_weapon 
            
            # Записываем оружие напрямую в объект игрока
            if hasattr(self.game, 'player') and self.game.player is not None:
                self.game.player.weapon = active_weapon
                
                # Если у игрока есть свой массив инвентаря, синхронизируем и его
                if hasattr(self.game.player, 'inventory'):
                    self.game.player.inventory = self.inventory
        else:
            self.game.weapon = None
            if hasattr(self.game, 'player') and self.game.player is not None:
                self.game.player.weapon = None

        self.npcs = []
        for npc_x, npc_y, npc_type in self.map.npc_positions:
            # Проверяем, существует ли вообще такой тип врага в нашем NPC_CONFIG
            if npc_type in NPC_CONFIG:
                # Центрируем врага на клетке (npc_x + 0.5, npc_y + 0.5)
                x, y = npc_x + 0.5, npc_y + 0.5
                
                # Создаем пушку... то есть врага через наш единый универсальный класс NPC!
                # Передаем ему объект игры, символ типа ('2', '7' и т.д.) и позицию
                npc = NPC(self.game, npc_type, pos=(x, y))
                self.npcs.append(npc)

        # Автоматическая генерация путей патрулирования для всех заспавненных NPC
        for npc in self.npcs:
            try:
                # Бот сам ищет свободные клетки вокруг себя
                npc.generate_waypoints_auto(4)
                
                # Если точки нашлись, переводим его в мирный стейт ходьбы по комнатам
                if npc.waypoints:
                    npc.state = "PATROL"
                else:
                    npc.state = "IDLE"
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
            # Передаем ID двери в рейкастинг (например, число 10)
            self.game.raycasting.door_id = char_to_id.get('D', -1)

        string_grid = level_data['map']
        height = len(string_grid)
        width = max(len(row) for row in string_grid) if height > 0 else 0
        
        numeric_grid = np.zeros((height, width), dtype=np.int32)
        # Создаем матрицу float32 для плавного открытия дверей
        door_states = np.zeros((height, width), dtype=np.float32)
        
        for y in range(height):
            current_row_len = len(string_grid[y])
            for x in range(width):
                if x < current_row_len:
                    symbol = string_grid[y][x]
                    numeric_grid[y][x] = char_to_id.get(symbol, 0)
                else:
                    numeric_grid[y][x] = 0
                
        self.map.numeric_grid = numeric_grid
        # Сохраняем пустую матрицу состояний в карту
        self.map.door_states = door_states
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
        
        # ============================================================
        # 🔥 УЛЬТИМАТИВНЫЙ ФИКС: ЖЁСТКАЯ ОЧИСТКА ОЗУ ЧЕРЕЗ .CLEAR()
        # ============================================================
        # Очищаем списки через .clear(), чтобы уничтожить двойников во всех модулях игры!
        if hasattr(self.game, 'items') and self.game.items: self.game.items.clear()
        if hasattr(self, 'items') and self.items: self.items.clear()
        if hasattr(self.game, 'npcs') and self.game.npcs: self.game.npcs.clear()
        if hasattr(self.game, 'particles') and self.game.particles: self.game.particles.clear()
        
        # Очищаем инвентарь левел-менеджера, чтобы пушки не накладывались друг на друга
        if hasattr(self, 'inventory') and self.inventory: self.inventory.clear()
        if hasattr(self.game, 'inventory') and self.game.inventory: self.game.inventory.clear()
        
        # Если у тебя есть object_handler (отрисовщик), принудительно вычищаем спрайты и оттуда:
        if hasattr(self.game, 'object_handler') and hasattr(self.game.object_handler, 'sprite_list'):
            self.game.object_handler.sprite_list.clear()
            
        self.game.items = []
        self.game.npcs = []
        self.game.particles = []
        self.game.inventory = []
        self.game.player = None
        # ============================================================
        
        self.load_level(self.current_level)


    def game_over(self):
        """Завершение игры"""
        pygame.quit()
