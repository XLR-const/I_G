from string import ascii_letters
import pygame
from setting import *
from door import Door
from npc import Tree

class Map:    
    def __init__(self, game, map_data=None, doors_data=None):
        self.game = game
        self.text_map = map_data if map_data else []
        self.doors = []
        self.world_map = {}
        self.npc_positions = []
        
        if self.text_map:
            self.parse_map(doors_data)
        if self.game.current_level == 2:
            Tree.init_spawn_points(self.game)
        
        self.width = len(self.text_map[0]) if self.text_map else 0
        self.height = len(self.text_map) if self.text_map else 0

    def parse_map(self, doors_data=None):
        """MANUAL:
        1 - basic wall(may WRS...)
        2 - solder
        3 - kamikaze
        4 - jaga
        5 - lightning
        ~ - fog"""
        self.npc_positions = []
        self.exit_pos = None
        for j, row in enumerate(self.text_map):
            for i, char in enumerate(row):
                if char == '1' or char in ascii_letters + '^' and char not in "ED":
                    self.world_map[(i, j)] = char # Сохраняем координаты стен
                
                # NPC
                if char == '2':
                    self.npc_positions.append((i, j, 'Solder'))
                if char == '3':
                    self.npc_positions.append((i, j, 'Kamikaze'))
                if char == '4':
                    self.npc_positions.append((i, j, 'Jaggernaut'))
                if char == '5':
                    self.npc_positions.append((i, j, 'Lightning'))
                if char == '/':
                    self.npc_positions.append((i, j, 'Tree'))
                if char == '~':
                    self.npc_positions.append((i, j, 'Fog'))

                if char == 'E':
                    self.exit_pos = (i + 0.5, j + 0.5)
                if char == 'D':
                    # Временно сохраняем позиции дверей из карты
                    if not hasattr(self, 'door_positions_from_map'):
                        self.door_positions_from_map = []
                    self.door_positions_from_map.append((i, j))
        
        # Создаём двери (приоритет у JSON, потом из карты)
        if doors_data:
            for door_pos in doors_data:
                door = Door(self.game, door_pos['x'] + 0.5, door_pos['y'] + 0.5)
                self.doors.append(door)
        elif hasattr(self, 'door_positions_from_map'):
            for x, y in self.door_positions_from_map:
                door = Door(self.game, x + 0.5, y + 0.5)
                self.doors.append(door)

    
    def is_wall(self, x, y):
        # Проверяем стены
        if (int(x), int(y)) in self.world_map:
            return True
        
        # Проверяем двери
        for door in self.doors:
            if int(door.x) == int(x) and int(door.y) == int(y):
                return door.is_wall()
        
        return False
    def get_exit_pos(self):
        return self.exit_pos
    