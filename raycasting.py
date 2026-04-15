from setting import *
from math import sin, cos
import pygame

class RayCasting:
    def __init__(self, game):
        self.game = game
    
    def ray_cast_native(self):
        ox, oy = self.game.player.x, self.game.player.y
        for i in range(NUM_RAYS):
            ray_angle = self.game.player.angle - HALF_FOV + i * DELTA_ANGLE
            
            sin_a = math.sin(ray_angle)
            cos_a = math.cos(ray_angle)
            
            # Полет луча
            for depth in range(1, MAX_DEPTH * 10):
                dist = depth / 10 # Шаг по 0.1 клетки
                
                # текущее координаты конца луча
                x = ox + dist * cos_a
                y = oy + dist * sin_a
                
                # проверка на попадание в стену
                if (int(x), int(y)) in self.game.map.world_map:
                    #pygame.draw.line(self.game.screen, 'white',
                    #                 (100 * ox, 100 * oy),
                    #                (100 * x, 100 * y), 1)

                    break
                dist *=  cos(self.game.player.angle - ray_angle) # Рыбий глаз
                
                # Рассчет высоты проекции стены
                proj_height = SCREEN_DIST / (dist + 0.0001)
                
                # Рисовка полоски стены по лучу i
                color = [255 / (1 + dist ** 2 * 0.1)] * 3 # Глубина цвета
                pygame.draw.rect(self.game.screen, color,
                                 (i * (WIDTH // NUM_RAYS), HALF_HEIGHT - proj_height // 2, 
                                WIDTH // NUM_RAYS, proj_height))
    
    # Внедрение алгоритма DDA            
    def ray_cast(self):
        ox, oy = self.game.player.x, self.game.player.y
        x_map, y_map = int(ox), int(oy)

        for i in range(NUM_RAYS):
            ray_angle = self.game.player.angle - HALF_FOV + i * DELTA_ANGLE
            sin_a = math.sin(ray_angle)
            cos_a = math.cos(ray_angle)

            # 1. Рассчет изменения пролета луча через одну клетку по диагонали на X и Y
            # Если cos_a равен 0, дистанция бесконечна (1e30)
            delta_dist_x = abs(1 / cos_a) if cos_a != 0 else 1e30
            delta_dist_y = abs(1 / sin_a) if sin_a != 0 else 1e30

            # 2. Чекаем к какой линии сетки ближе находится наблюдатель,
            # который находится где то внутри клетки, и считаем это расстояние
            if cos_a < 0:
                step_x = -1
                side_dist_x = (ox - x_map) * delta_dist_x
            else:
                step_x = 1
                side_dist_x = (x_map + 1.0 - ox) * delta_dist_x

            if sin_a < 0:
                step_y = -1
                side_dist_y = (oy - y_map) * delta_dist_y
            else:
                step_y = 1
                side_dist_y = (y_map + 1.0 - oy) * delta_dist_y

            # 3. Цикл DDA: прыгаем по клеткам, пока не найдем стену
            wall_hit = False
            while not wall_hit:
                # Выбираем, куда прыгнуть: к следующей линии X или к следующей Y
                if side_dist_x < side_dist_y: # Вертикаль ближе
                    side_dist_x += delta_dist_x
                    x_map += step_x
                    side = 0 # Ударились в вертикальную стену
                else:
                    side_dist_y += delta_dist_y
                    y_map += step_y
                    side = 1 # Ударились в горизонтальную стену
                
                # Проверяем, есть ли стена в этой клетке
                if (x_map, y_map) in self.game.map.world_map:
                    wall_hit = True

            # 4. Считаем финальную дистанцию до стены
            if side == 0: # Вертикаль
                dist = side_dist_x - delta_dist_x
            else:
                dist = side_dist_y - delta_dist_y

            # 5. Убираем "эффект рыбьего глаза" (фикс дисторсии)
            dist *= math.cos(self.game.player.angle - ray_angle)

            # 6. Проекция
            proj_height = SCREEN_DIST / (dist + 0.0001)
            
            # Делаем стены разного оттенка в зависимости от стороны (X или Y)
            color = (200, 200, 200) if side == 0 else (150, 150, 150)
            # Дополнительное затенение от дистанции
            color = [c / (1 + dist * dist * 0.01) for c in color]

            # Фикс прорисовки стен - зубчики
            # Рассчитываем параметры один раз
            w = SCALE
            h = int(proj_height)
            x = int(i * SCALE)
            y = int(HALF_HEIGHT - h // 2)

            # Ограничиваем высоту, чтобы не было "зубьев" при взгляде в упор
            if h > HEIGHT * 2: # даем запас, но не бесконечность
                h = HEIGHT * 2
                y = int(HALF_HEIGHT - h // 2)

            pygame.draw.rect(self.game.screen, color, (x, y, w, h))
            #pygame.draw.line(self.game.screen, color, (x, y), (x, y + h), w)
            # Сбрасываем координаты сетки для следующего луча!
            x_map, y_map = int(ox), int(oy)
