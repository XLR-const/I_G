import pygame
from setting import *
class Renderer:
    def __init__(self, game):
        self.game = game
    
    def draw_background(self):
        # Потолок (темно-серый)
        pygame.draw.rect(self.game.screen, WALL_COLORS['C'], (0, 0, WIDTH, HALF_HEIGHT))
        # Пол (чуть светлее)
        pygame.draw.rect(self.game.screen, (40, 40, 40), (0, HALF_HEIGHT, WIDTH, HEIGHT))

    def draw_fps(self):
        # Получаем текущее значение FPS
        fps = str(int(self.game.clock.get_fps()))
        # Создаем поверхность с текстом
        fps_render = self.game.font.render(fps, True, (0, 255, 0)) # Зеленый цвет
        # Рисуем в левом верхнем углу
        self.game.screen.blit(fps_render, (10, 10))
    
    def draw_crosshair(self):
        pygame.draw.circle(self.game.screen, 'red', (WIDTH // 2, HEIGHT // 2), 4, 1)
        
    def draw_interface(self):
        hp = self.game.player.hp
        current_weapon = self.game.weapon.name
        ammo = self.game.weapon.ammo
        length = WIDTH // 6
        h_length = (hp / 100) * length
        
        font = pygame.font.Font(None, 54)
        text_weapon_surface = font.render(current_weapon, True, (255, 255, 255))
        font = pygame.font.Font(None, 36)
        text_ammo_surface = font.render(str(ammo), True, (255, 200, 255))
        
        pygame.draw.rect(self.game.screen, (200, 50, 50), (WIDTH * 0 + 50, HEIGHT * 13 // 15, length, HEIGHT // 20))
        pygame.draw.rect(self.game.screen, (50, 240, 0), (WIDTH * 0 + 50, HEIGHT * 13 // 15,  h_length, HEIGHT // 20))        
        self.game.screen.blit(text_weapon_surface, (WIDTH - 400, HEIGHT * 13 // 15 - 25))
        self.game.screen.blit(text_ammo_surface, (WIDTH - 400, HEIGHT * 13 // 15 + 25))
