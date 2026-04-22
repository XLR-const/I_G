import math
from setting import *

class PathFinder:
    def __init__(self, game):
        self.game = game
     
    def a_star(self, start, goal):
        """
        start = (x, y) - координаты НПС
        goal = (x, y) - координаты цели то есть игрока
        """
        
        #==ШАГ 0 подготовка
        start_cell = (int(start[0]), int(start[1]))
        goal_cell = (int(goal[0]), int(goal[1]))
        
        if start_cell == goal_cell:
            return [start_cell]
        
        if self.game.map.is_wall(goal_cell[0], goal_cell[1]):
            return []
        
        #==ШАГ 1 список открытых и закрытых клеток
        open_set = [] # клетки которые нужно проверить
        closed_set = set() # клетки которые уже проверены
        """Клетка это:
        {
            'pos': (x, y),
            'g': сколько шагов инт от старта,
            'parent': откуда пришли}"""
        start_node = {
            'pos': start_cell,
            'g': 0,
            'parent': None
        }
        
        open_set.append(start_node)
        # вспомагательный словарь
        open_dict = {start_cell: start_node}
        
        #==ШАГ 2 основной цикл
        """f = g + h 
        где h - расстояние до клетки от текущей
        по манхетеннской формуле"""
        while open_set:
            # Находим лучшую клетку
            best_node = None
            best_f = float('inf')
            
            for node in open_set:
                h = abs(node['pos'][0] - goal_cell[0]) + abs(node['pos'][1] - goal_cell[1])
                f = node['g'] + h
                
                if f < best_f:
                    best_f = f
                    best_node = node
            current = best_node
            
            # Проверка
            if current['pos'] == goal_cell:
                # восстанавливаем путь
                path = []
                node = current
                while node is not None:
                    path.append(node['pos'])
                    node = node['parent']
                path.reverse()
                return path
            # Не дошли пока
            open_set.remove(current)
            del open_dict[current['pos']]
            closed_set.add(current['pos'])
            
            # работаем с соседями
            neighbors = [
                (current['pos'][0] + 1, current['pos'][1]),  # право
                (current['pos'][0] - 1, current['pos'][1]),  # лево
                (current['pos'][0], current['pos'][1] + 1),  # низ
                (current['pos'][0], current['pos'][1] - 1)  # верх
            ]
            
            for neighbor in neighbors:
                if neighbor in closed_set:
                    continue
                
                # Если стена
                if self.game.map.is_wall(neighbor[0], neighbor[1]):
                    continue
                
                # Контроль границ
                width = self.game.map.width
                height = self.game.map.height
                if not (0 <= neighbor[0] < width and 0 <= neighbor[1] < height):
                    continue
                
                new_g = current['g'] + 1
                
                if neighbor in open_dict:
                    neighbor_node = open_dict[neighbor]
                    # если путь короче
                    if new_g < neighbor_node['g']:
                        neighbor_node['g'] = new_g
                        neighbor_node['parent'] = current
                        
                else:
                    # новый узел - сосед
                    new_node = {
                        'pos': neighbor,
                        'g': new_g,
                        'parent': current
                    }
                    
                    open_set.append(new_node)
                    open_dict[neighbor] = new_node
        # если ниче не нашли то увы че
        return []
     
    
    
    
    def heuristic(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
    
