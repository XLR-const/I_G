from setting import *
from math import sin, cos
import pygame

class RayCasting:
    def __init__(self, game):
        self.game = game
    
    def ray_cast(self):
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