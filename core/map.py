import pygame
from setting import *
from core.door import Door
from config.game_data import SYMBOLS_CONFIG, NPC_CONFIG, WEAPON_CONFIG


class Map:
    def __init__(self, game, map_data=None):
        self.game = game
        self.text_map = map_data if map_data else []
        self.doors = []
        self.world_map = {}
        self.npc_positions = []
        self.weapon_positions = []
        self.exit_pos = None
        self.player_spawn_pos = None
        
        if self.text_map:
            self.parse_map()
        
        self.width = len(self.text_map[0]) if self.text_map else 0
        self.height = len(self.text_map) if self.text_map else 0

    def parse_map(self):
        self.npc_positions = []
        self.weapon_positions = []
        self.exit_pos = None
        self.player_spawn_pos = None
        self.doors = []
        self.world_map = {}
        
        for j, row in enumerate(self.text_map):
            for i, char in enumerate(row):
                # Пропускаем пустые клетки
                if char == '_' or char == '.':
                    continue
                
                # Проверяем символ в SYMBOLS_CONFIG
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
                
                # Проверяем NPC_CONFIG
                elif char in NPC_CONFIG:
                    self.npc_positions.append((i, j, char))
                
                # Проверяем WEAPON_CONFIG
                elif char in WEAPON_CONFIG:
                    self.weapon_positions.append((i, j, char))

    def is_wall(self, x, y):
        if (int(x), int(y)) in self.world_map:
            return True
        
        for door in self.doors:
            if int(door.x) == int(x) and int(door.y) == int(y):
                return door.is_wall()
        
        return False

    def is_walkable(self, x, y):
        return not self.is_wall(x, y)

    def get_exit_pos(self):
        return self.exit_pos
