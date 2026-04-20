
import pygame
from setting import *
class Map:
    text_map = [
        ['1', '1', '1', '1', '1', '1', '1', '1', '1', '1'],
        ['1', '_', '_', '_', '_', '_', '_', '_', '_', '1'],
        ['1', '_', '_', '_', '_', '_', '_', '1', '_', '1'],
        ['1', '_', '_', '_', '_', '_', '_', '_', '_', '1'],
        ['1', '_', '_', '1', '_', '_', '_', '_', '_', '1'],
        ['1', '_', '_', '_', '_', '_', '_', '_', '_', '1'],
        ['1', '_', '_', '_', '_', '_', '_', '_', '_', '1'],
        ['1', '_', '2', '_', '_', '_', '_', '_', '_', '1'],
        ['1', '_', '_', '_', '_', '_', '_', '_', '_', '1'],
        ['1', '_', '_', '_', '_', '_', '_', '_', '_', '1'],
        ['1', '_', '_', '_', '_', '_', '_', '1', '_', '1'],
        ['1', '_', '_', '_', '_', '_', '_', '_', '_', '1'],
        ['1', '_', '_', '1', '_', '2', '_', '_', '_', '1'],
        ['1', '_', '_', '_', '_', '_', '_', '_', '_', '1'],
        ['1', '2', '_', '_', '_', '_', '_', '_', '_', '1'],
        ['1', '_', '_', '_', '_', '_', '_', '_', '_', '1'],
        ['1', '_', '_', '_', '_', '_', '_', '_', '_', '1'],
        ['1', '1', '1', '1', '1', '1', '1', '1', '1', '1']
    ]
    
    def __init__(self, game):
        self.game = game
        self.npc_positions = []
        self.world_map = {}
        self.get_map()
        self.width = len(self.text_map[0])
        self.height = len(self.text_map)

    def get_map(self):
        for j, row in enumerate(self.text_map):
            for i, char in enumerate(row):
                if char == '1':
                    self.world_map[(i, j)] = char # Сохраняем координаты стен
                if char == '2':
                    self.npc_positions.append((i, j))

    def draw(self): 
        for pos in self.world_map:
            pygame.draw.rect(self.game.screen, 'gray', 
                             (pos[0] * TILE, pos[1] * TILE, TILE, TILE), 2)
    
    def is_wall(self, x, y):
        return (int(x), int(y)) in self.world_map
    