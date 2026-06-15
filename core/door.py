from setting import *
import pygame
import math

class Door:
    def __init__(self, game, x, y):
        self.game = game
        self.x = x
        self.y = y
        self.state = "CLOSED" # CLOSED, OPENING, OPENED, CLOSING
        self.open_progress = 0.0
        self.speed = 0.05 # per frame
        self.trigger_distance = 1.5
        self.close_delay = 1000 # ms before closing
        self.close_timer = 0
        
        # визуал
        self.color = WALL_COLORS['W']
        self.frame = 0
        
    def update(self):
        dx = self.game.player.x - self.x
        dy = self.game.player.y - self.y
        dist = math.hypot(dx, dy)
        
        # Логика открытия/закрытия
        if self.state == "CLOSED":
            if dist < self.trigger_distance:
                self.state = "OPENING"
        
        elif self.state == "OPENING":
            self.open_progress += self.speed
            if self.open_progress >= 1.0:
                self.open_progress = 1.0
                self.state = "OPEN"
                self.close_timer = pygame.time.get_ticks() + self.close_delay
        
        elif self.state == "OPEN":
            if dist > self.trigger_distance * 1.5:
                if pygame.time.get_ticks() > self.close_timer:
                    self.state = "CLOSING"
        
        elif self.state == "CLOSING":
            self.open_progress -= self.speed
            if self.open_progress <= 0.0:
                self.open_progress = 0.0
                self.state = "CLOSED"
    def is_wall(self):
        """Возвращает True, если дверь действует как стена"""
        return self.state == "CLOSED" or self.state == "CLOSING"
    
    def get_texture_offset(self):
        """Возвращает смещение текстуры для анимации"""
        if self.state == "OPENING":
            return self.open_progress
        elif self.state == "CLOSING":
            return self.open_progress
        elif self.state == "OPEN":
            return 1.0
        else:
            return 0.0
