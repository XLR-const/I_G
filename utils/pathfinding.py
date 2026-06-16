"""A* поиск пути для NPC

Содержит класс PathFinder для поиска оптимального пути на карте.
"""

import math
from setting import *


class PathFinder:
    """Класс для поиска пути алгоритмом A*

    Attributes:
        game: Объект игры с доступом к карте
    """

    def __init__(self, game):
        """Инициализирует PathFinder

        Args:
            game: Объект игры
        """
        self.game = game

    def a_star(self, start, goal, max_distance=5):
        """Находит путь от старта к цели алгоритмом A*

        Args:
            start: Координаты старта (x, y) в пикселях
            goal: Координаты цели (x, y) в пикселях
            max_distance: Максимальное Манхэттенское расстояние для поиска

        Returns:
            list: Список клеток пути [(x1, y1), (x2, y2), ...]
                  или пустой список если путь не найден
        """
        start_cell = (int(start[0]), int(start[1]))
        goal_cell = (int(goal[0]), int(goal[1]))

        manhattan_dist = abs(start_cell[0] - goal_cell[0]) + abs(start_cell[1] - goal_cell[1])
        if manhattan_dist > max_distance:
            return []

        if start_cell == goal_cell:
            return [start_cell]

        if self.game.map.is_wall(goal_cell[0], goal_cell[1]):
            return []

        open_set = {}
        closed_set = set()

        start_node = {
            'pos': start_cell,
            'g': 0,
            'f': self._heuristic(start_cell, goal_cell),
            'parent': None
        }

        open_set[start_cell] = start_node

        max_iterations = 1000
        iterations = 0

        while open_set and iterations < max_iterations:
            iterations += 1

            current = min(open_set.values(), key=lambda node: node['f'])

            if current['pos'] == goal_cell:
                path = []
                node = current
                while node is not None:
                    path.append(node['pos'])
                    node = node['parent']
                path.reverse()
                return path

            del open_set[current['pos']]
            closed_set.add(current['pos'])

            neighbors = [
                (current['pos'][0] + 1, current['pos'][1]),
                (current['pos'][0] - 1, current['pos'][1]),
                (current['pos'][0], current['pos'][1] + 1),
                (current['pos'][0], current['pos'][1] - 1)
            ]

            for neighbor in neighbors:
                if not (0 <= neighbor[0] < self.game.map.width and
                        0 <= neighbor[1] < self.game.map.height):
                    continue

                if self.game.map.is_wall(neighbor[0], neighbor[1]):
                    continue

                if neighbor in closed_set:
                    continue

                new_g = current['g'] + 1

                if neighbor in open_set:
                    neighbor_node = open_set[neighbor]
                    if new_g < neighbor_node['g']:
                        neighbor_node['g'] = new_g
                        neighbor_node['f'] = new_g + self._heuristic(neighbor, goal_cell)
                        neighbor_node['parent'] = current
                else:
                    new_node = {
                        'pos': neighbor,
                        'g': new_g,
                        'f': new_g + self._heuristic(neighbor, goal_cell),
                        'parent': current
                    }
                    open_set[neighbor] = new_node

        return []

    def _heuristic(self, a, b):
        """Вычисляет Манхэттенское расстояние между двумя клетками

        Args:
            a: Координаты первой клетки (x, y)
            b: Координаты второй клетки (x, y)

        Returns:
            int: Манхэттенское расстояние
        """
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
