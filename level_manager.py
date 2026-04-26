import json
import os
from setting import *

class LevelManager:
    def __init__(self, game):
        self.game = game
        self.current_level = 1
        self.levels_folder = "resources/levels"
        
        if not os.path.exists(self.levels_folder):
            os.makedirs(self.levels_folder)
            
    def load_level(self, level_num):
        file_path = f"{self.levels_folder}/level_{level_num}.json"
        if not os.path.exists(file_path):
            print(f"Ошибка: уровень {file_path} не найден!")
            return False
        
        with open(file_path, 'r') as f:
            level_data = json.load(f)
            
        # парсинг джисона
        map_data = level_data['map'] # матрица-лвл
        player_start = tuple(level_data['player_start']) # x, y
        npc_spawns = level_data.get('npcs', [])
        doors = level_data.get('doors', [])
        exit_pos = tuple(level_data.get('exit', (-1, -1)))
        inventory = level_data.get('inventory', [])
        starting_ammo = level_data.get('starting_ammo', 0)
        
        return {
            'map_data': map_data,
            'player_start': player_start,
            'npcs': npc_spawns,
            'doors': doors,
            'exit': exit_pos,
            'inventory': inventory,
            'starting_ammo': starting_ammo
        }
        
    def save_level(self, level_num, map_data, player_start, npcs, doors, exit_pos):
        """Сохраняет уровень в JSON (для создания новых уровней)"""
        level_data = {
            'map': map_data,
            'player_start': list(player_start),
            'npcs': npcs,
            'doors': doors,
            'exit': list(exit_pos)
        }
        
        file_path = f"{self.levels_folder}/level_{level_num:02d}.json"
        with open(file_path, 'w') as f:
            json.dump(level_data, f, indent=4)
        
        print(f"Уровень сохранён: {file_path}")
      