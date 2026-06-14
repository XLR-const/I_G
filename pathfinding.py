# pathfinding.py

import math
from setting import *

class PathFinder:
    def __init__(self, game):
        self.game = game
    
    def a_star(self, start, goal, max_distance=5):
        """
        Итеративная версия A* поиска пути
        start = (x, y) - координаты НПС
        goal = (x, y) - координаты цели (игрок)
        """
        
        # Шаг 0: подготовка
        start_cell = (int(start[0]), int(start[1]))
        goal_cell = (int(goal[0]), int(goal[1]))
        
        
        manhattan_dist = abs(start_cell[0] - goal_cell[0]) + abs(start_cell[1] - goal_cell[1])
        if manhattan_dist > max_distance:
            return []  # не ищем путь далеко
        if start_cell == goal_cell:
            return [start_cell]
        
        if self.game.map.is_wall(goal_cell[0], goal_cell[1]):
            return []
        
        # Шаг 1: открытые и закрытые клетки
        open_set = {}  # словарь {pos: node} для быстрого поиска
        closed_set = set()
        
        start_node = {
            'pos': start_cell,
            'g': 0,
            'f': self.heuristic(start_cell, goal_cell),
            'parent': None
        }
        
        open_set[start_cell] = start_node
        
        # Основной цикл
        max_iterations = 1000  # защита от бесконечного цикла
        iterations = 0
        
        while open_set and iterations < max_iterations:
            iterations += 1
            
            # Находим узел с минимальным f
            current = min(open_set.values(), key=lambda node: node['f'])
            
            # Проверка достижения цели
            if current['pos'] == goal_cell:
                # Восстанавливаем путь
                path = []
                node = current
                while node is not None:
                    path.append(node['pos'])
                    node = node['parent']
                path.reverse()
                return path
            
            # Удаляем current из open_set
            del open_set[current['pos']]
            closed_set.add(current['pos'])
            
            # Соседи
            neighbors = [
                (current['pos'][0] + 1, current['pos'][1]),  # право
                (current['pos'][0] - 1, current['pos'][1]),  # лево
                (current['pos'][0], current['pos'][1] + 1),  # низ
                (current['pos'][0], current['pos'][1] - 1)   # верх
            ]
            
            for neighbor in neighbors:
                # Проверка границ
                if not (0 <= neighbor[0] < self.game.map.width and 
                        0 <= neighbor[1] < self.game.map.height):
                    continue
                
                # Проверка стены
                if self.game.map.is_wall(neighbor[0], neighbor[1]):
                    continue
                
                # Проверка закрытого множества
                if neighbor in closed_set:
                    continue
                
                # Расчёт g
                new_g = current['g'] + 1
                
                # Если сосед уже в open_set
                if neighbor in open_set:
                    neighbor_node = open_set[neighbor]
                    if new_g < neighbor_node['g']:
                        neighbor_node['g'] = new_g
                        neighbor_node['f'] = new_g + self.heuristic(neighbor, goal_cell)
                        neighbor_node['parent'] = current
                else:
                    # Создаём новый узел
                    new_node = {
                        'pos': neighbor,
                        'g': new_g,
                        'f': new_g + self.heuristic(neighbor, goal_cell),
                        'parent': current
                    }
                    open_set[neighbor] = new_node
        
        # Не нашли путь
        return []
    
    def heuristic(self, a, b):
        """Манхэттенская дистанция"""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])