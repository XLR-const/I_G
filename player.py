import math
import pygame

class Player:
    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.angle = angle
    
    def move(self, keys, speed):
        """Возвращает новые координаты (new_x, new_y) на основе нажатых клавиш"""
        new_x = self.x
        new_y = self.y
        
        if keys[pygame.K_w]:
            new_x += math.cos(self.angle) * speed
            new_y += math.sin(self.angle) * speed
        if keys[pygame.K_s]:
            new_x -= math.cos(self.angle) * speed
            new_y -= math.sin(self.angle) * speed
        if keys[pygame.K_a]:
            new_x += math.cos(self.angle - math.pi/2) * speed
            new_y += math.sin(self.angle - math.pi/2) * speed
        if keys[pygame.K_d]:
            new_x += math.cos(self.angle + math.pi/2) * speed
            new_y += math.sin(self.angle + math.pi/2) * speed
        
        return new_x, new_y
    
    def rotate(self, mouse_dx, sense):
        """Поворот игрока от движения мыши"""
        self.angle += mouse_dx * sense
    
    def apply_collision(self, new_x, new_y, world):
        """Проверяет коллизии и возвращает итоговые координаты"""
        # Проверка по X
        map_x = int(new_x)
        map_y = int(self.y)
        if 0 <= map_x < world.width and 0 <= map_y < world.height:
            if world.map[map_y][map_x] == 0:
                self.x = new_x
        
        # Проверка по Y
        map_x = int(self.x)
        map_y = int(new_y)
        if 0 <= map_x < world.width and 0 <= map_y < world.height:
            if world.map[map_y][map_x] == 0:
                self.y = new_y