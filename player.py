import pygame
from math import sin, cos, pi
from setting import *
class Player():
    def __init__(self, game):
        self.game = game
        self.x, self.y = PLAYER_POS
        self.angle = PLAYER_ANGLE
        
    def mouse_control(self):
        mx, my = pygame.mouse.get_rel()
        self.angle += mx * MOUSE_SENSITIVITY
        pygame.mouse.set_pos([WIDTH//2, HEIGHT//2])
        
    def movement(self):
        keys = pygame.key.get_pressed()
        sin_a = sin(self.angle)
        cos_a = cos(self.angle)
        dx, dy = 0, 0
        speed = PLAYER_SPEED * self.game.delta_time
        
        if keys[pygame.K_w]:
            dx += speed * cos_a
            dy += speed * sin_a
        if keys[pygame.K_s]:
            dx -= speed * cos_a
            dy -= speed * sin_a
        if keys[pygame.K_a]:
            dx += speed * sin_a # тригоном преобраз 90
            dy -= speed * cos_a
        if keys[pygame.K_d]:
            dx -= speed * sin_a
            dy += speed * cos_a
        self.x += dx
        self.y += dy
        
    def update(self):
        Player.mouse_control(self)
        Player.movement(self)
    
    def draw(self):
        # Временно
        pygame.draw.circle(self.game.screen, 'red', (self.x * TILE, self.y * TILE), 15)
        pygame.draw.line(self.game.screen, 'yellow', 
             (self.x * TILE, self.y * TILE), 
             (self.x * TILE + WIDTH * math.cos(self.angle), 
              self.y * TILE + WIDTH * math.sin(self.angle)), 2)