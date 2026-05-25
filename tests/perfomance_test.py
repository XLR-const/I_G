import pygame
import time
import sys
import math
sys.path.append('.')

from setting import *
from npc import Solder

def test_npc_performance():
    """Тест: сколько NPC можно держать без лагов"""
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    
    # Создаём фейковую игру
    class FakeGame:
        def __init__(self):
            self.delta_time = 16
            self.screen = screen
            self.player = type('Player', (), {'x': 5, 'y': 5, 'hp': 100})()
            self.npcs = []
            self.particles = []
            self.total_kills = 0
            
            # Фейковая карта
            class FakeMap:
                def is_wall(self, x, y):
                    return False
                doors = []
            self.map = FakeMap()
            
            # Фейковый pathfinder
            class FakePathFinder:
                def a_star(self, start, goal):
                    return []  # пустой путь
            self.pathfinder = FakePathFinder()
    
    # Тестируем разное количество NPC
    for count in [5, 10, 15, 20, 30]:
        game = FakeGame()
        game.npcs = []
        
        for i in range(count):
            npc = Solder(game, (i % 10 + 1, i // 10 + 1))
            npc.alive = True
            npc.hp = 100
            game.npcs.append(npc)
        
        start = time.time()
        frames = 0
        while time.time() - start < 1:
            for npc in game.npcs:
                npc.update()
            frames += 1
        elapsed = time.time() - start
        
        print(f"{count} NPC: {frames} кадров за {elapsed:.1f} сек (~{frames} FPS)")
        if frames < 30:
            print(f"  ⚠️ Рекомендуемый лимит: {count}")
            break

def test_pathfinding_performance():
    """Тест: производительность A* поиска пути"""
    from pathfinding import PathFinder
    
    class FakeGame:
        def __init__(self, size):
            class FakeMap:
                def __init__(self, s):
                    self.width = s
                    self.height = s
                def is_wall(self, x, y):
                    return x <= 0 or y <= 0 or x >= self.width-1 or y >= self.height-1
            self.map = FakeMap(size)
    
    for size in [32, 64, 100]:
        game = FakeGame(size)
        pf = PathFinder(game)
        
        start = time.time()
        searches = 0
        while time.time() - start < 1:
            pf.a_star((size//2, size//2), (size-2, size-2))
            searches += 1
        elapsed = time.time() - start
        
        print(f"Карта {size}x{size}: {searches} поисков/сек")
        if searches < 10:
            print(f"  ⚠️ Рекомендуемый размер: {size//2}")
            break

if __name__ == "__main__":
    print("=== ТЕСТ 1: NPC ПРОИЗВОДИТЕЛЬНОСТЬ ===")
    test_npc_performance()
    print("\n=== ТЕСТ 2: A* ПОИСК ПУТИ ===")
    test_pathfinding_performance()