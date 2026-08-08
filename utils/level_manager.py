import json
import os
import pygame
import math
import numpy as np
from setting import *
from core.map import Map
from core.player import Player
from core.npc import NPC
from core.weapon import Weapon
from config.game_data import NPC_CONFIG, WEAPON_CONFIG, SYMBOLS_CONFIG, ACTS_SEQUENCE
from core.item import *


class LevelManager:
    """Менеджер загрузки уровней с поддержкой системы эпизодов/актов"""
    
    def __init__(self, game):
        self.game = game
        
        # Индексы для новой системы актов
        self.current_act_index = 0      # Порядковый номер акта в листе ACTS_SEQUENCE
        self.current_level = 1          # Номер уровня внутри текущего акта
        self.acts_sequence = ACTS_SEQUENCE
        
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
        char_to_id = {}
        current_id = 1
        for symbol, config in SYMBOLS_CONFIG.items():
            if config.get('type') in ('wall', 'door'):
                char_to_id[symbol] = current_id
                current_id += 1
        return char_to_id

    def get_current_act_name(self):
        """Безопасно возвращает имя текущего акта из конфига"""
        if 0 <= self.current_act_index < len(ACTS_SEQUENCE):
            return ACTS_SEQUENCE[self.current_act_index]
        return None

    def load_level(self, level_num):
        """Загружает уровень из JSON с учетом текущего акта"""
        act_name = self.get_current_act_name()
        if not act_name:
            print("Ошибка: Текущий акт не найден в ACTS_SEQUENCE!")
            return False
            
        print(f"\n{'=' * 60}")
        print(f"ЗАГРУЗКА: АКТ '{act_name}' -> УРОВЕНЬ {level_num}")
        print(f"{'=' * 60}")
        
        # 🔥 НОВЫЙ ДИНАМИЧЕСКИЙ ПУТЬ К ПАПКЕ АКТА:
        file_path = f"{self.levels_folder}/{act_name}/level_{level_num}.json"
        
        if not os.path.exists(file_path):
            print(f"Ошибка: файл {file_path} не найден!")
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
        
        # Загрузка предметов (Аптечки, Броня, Ключи, Декор)
        for x, y, item_type, amount, weapon_name, ammo in self.map.item_positions:
            if item_type == 'health':
                item = HealthItem(self.game, x, y, amount)
            elif item_type == 'armor':
                item = ArmorItem(self.game, x, y, amount)
            elif item_type == 'weapon':
                item = WeaponItem(self.game, x, y, weapon_name, ammo)
            elif item_type == 'key':
                from core.item import KeyItem
                key_color = str(amount).strip().lower()
                item = KeyItem(self.game, x, y, key_color=key_color)
            elif item_type == 'decor':
                from core.item import DecorItem
                decor_name = str(amount).strip().lower()
                item = DecorItem(self.game, x, y, decor_name=decor_name, height_scale=ammo)
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
            self.player.armor = 0
            self.player.angle = 0
            self.exit_pos = self.map.exit_pos
            self.player.keys_inventory = []
        else:
            print("ОШИБКА: Нет спавна игрока на карте (символ 'S')")
            return False
            
        self.inventory = []
        start_weapons = level_data.get('inventory', ['KNIFE'])
        if not start_weapons:
            start_weapons = ['KNIFE']
            
        for weapon_name in start_weapons:
            if weapon_name in WEAPON_CONFIG:
                weapon = Weapon(self.game, weapon_name)
                self.inventory.append(weapon)
                
        if not self.inventory:
            if 'KNIFE' in WEAPON_CONFIG:
                self.inventory.append(Weapon(self.game, 'KNIFE'))
            else:
                first_weapon_name = list(WEAPON_CONFIG.keys())[0]
                self.inventory.append(Weapon(self.game, first_weapon_name))
                
        self.current_weapon_index = 0
        if len(self.inventory) > 0:
            active_weapon = self.inventory[0]
            self.weapon = active_weapon 
            self.game.weapon = active_weapon 
            if hasattr(self.game, 'player') and self.game.player is not None:
                self.game.player.weapon = active_weapon
            if hasattr(self.game.player, 'inventory'):
                self.game.player.inventory = self.inventory
        else:
            self.game.weapon = None
            if hasattr(self.game, 'player') and self.game.player is not None:
                self.game.player.weapon = None
                
        # Спавн обычных NPC по вашей стандартной схеме
        self.npcs = []
        for npc_x, npc_y, npc_type in self.map.npc_positions:
            if npc_type in NPC_CONFIG:
                x, y = npc_x + 0.5, npc_y + 0.5
                npc = NPC(self.game, npc_type, pos=(x, y))
                self.npcs.append(npc)
                
        for npc in self.npcs:
            try:
                npc.generate_waypoints_auto(4)
                if npc.waypoints:
                    npc.state = "PATROL"
                else:
                    npc.state = "IDLE"
            except Exception as e:
                print(f"Ошибка waypoints для {npc.name}: {e}")
                npc.waypoints = []
                npc.state = "IDLE"
                
        # Оптимизация Numba
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
            self.game.raycasting.door_id = char_to_id.get('D', -1)
            
        string_grid = level_data['map']
        height = len(string_grid)
        width = max(len(row) for row in string_grid) if height > 0 else 0
        numeric_grid = np.zeros((height, width), dtype=np.int32)
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
        self.map.door_states = door_states
        
        print(f"Уровень {level_num} акта '{act_name}' загружен: {len(self.npcs)} NPC")
        return True

    def next_level(self):
        """Умный переход на следующий уровень или следующий акт"""
        self.level_time = (pygame.time.get_ticks() - self.level_start_time) // 1000
        
        # Получаем имя текущего акта перед расчетами
        act_name = self.get_current_act_name()
        
        # Проверяем, существует ли СЛЕДУЮЩИЙ уровень внутри текущего акта
        next_lvl_num = self.current_level + 1
        next_level_path = f"{self.levels_folder}/{act_name}/level_{next_lvl_num}.json"
        
        if os.path.exists(next_level_path):
            # Если файл есть, просто шагаем на следующий уровень в этом же акте
            self.current_level = next_lvl_num
            # Сохраняем прогресс (передаем сквозной ID уровня для сейв-системы, например 100 * акт + уровень)
            self.game.save_system.save(self.current_level, self.total_kills, self.level_time)
            self.game.ui_manager.current_state = self.game.ui_manager.states['LEVEL_END']
        else:
            # Иначе — текущий акт полностью пройден! Пытаемся переключиться на следующий акт
            next_act_idx = self.current_act_index + 1
            
            if next_act_idx < len(ACTS_SEQUENCE):
                # Если в списке еще есть акты, переключаемся на начало нового акта
                self.current_act_index = next_act_idx
                self.current_level = 1
                
                self.game.save_system.save(self.current_level, self.total_kills, self.level_time)
                self.game.ui_manager.current_state = self.game.ui_manager.states['LEVEL_END']
                print(f"[УРОВЕНЬ] Переход на АКТ: '{ACTS_SEQUENCE[self.current_act_index]}'")
            else:
                # Если акты закончились — игра полностью пройдена! Выходим в главное меню
                print("[ИГРА] Поздравляем! Все акты из ACTS_SEQUENCE успешно пройдены!")
                self.game.ui_manager.current_state = self.game.ui_manager.states['MENU']

    def check_exit(self):
        if self.exit_pos is None or self.player is None:
            return
        player_cell = (int(self.player.x), int(self.player.y))
        exit_cell = (int(self.exit_pos[0]), int(self.exit_pos[1]))
        
        if player_cell == exit_cell:
            self.next_level()

    def reset_game(self):
        """Полный сброс игры на самый первый уровень самого первого акта"""
        self.game.save_system.delete()
        self.total_kills = 0
        self.level_time = 0
        
        # Сбрасываем на начальную точку по вашему листу актов
        self.current_act_index = 0
        self.current_level = 1
        
        if hasattr(self.game, 'items') and self.game.items:
            self.game.items.clear()
        if hasattr(self, 'items') and self.items:
            self.items.clear()
        if hasattr(self.game, 'npcs') and self.game.npcs:
            self.game.npcs.clear()
        if hasattr(self.game, 'particles') and self.game.particles:
            self.game.particles.clear()
        if hasattr(self, 'inventory') and self.inventory:
            self.inventory.clear()
        if hasattr(self.game, 'inventory') and self.game.inventory:
            self.game.inventory.clear()
        if hasattr(self.game, 'object_handler') and hasattr(self.game.object_handler, 'sprite_list'):
            self.game.object_handler.sprite_list.clear()
            
        self.game.items = []
        self.game.npcs = []
        self.game.particles = []
        self.game.inventory = []
        self.game.player = None
        
        # Загружаем первый уровень первого акта
        self.load_level(self.current_level)

    def game_over(self):
        pygame.quit()