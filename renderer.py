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
        x, y = grid_to_pixel(0, 0)
        # Получаем текущее значение FPS
        fps = str(int(self.game.clock.get_fps()))
        # Создаем поверхность с текстом
        fps_render = self.game.font.render(fps, True, (0, 255, 0)) # Зеленый цвет
        # Рисуем
        self.game.screen.blit(fps_render, (x, y))
    
    def draw_crosshair(self):
        pygame.draw.circle(self.game.screen, 'red', (WIDTH // 2, HEIGHT // 2), 4, 1)
        
    def draw_interface(self):
        hp = self.game.player.hp
        current_weapon = self.game.weapon.name
        ammo = self.game.weapon.ammo
        health_bar_lpos = grid_to_pixel(1, 16)
        health_bar_width = 6 * CELL_W
        health_bar_height = 1 * CELL_H
        health_bar_width_progressive = (hp / 100) * health_bar_width
        weapon_name_pos = grid_to_pixel(25, 15)
        weapon_ammo_pos = grid_to_pixel(25, 16)
        
        font = pygame.font.Font(None, 64)
        text_weapon_surface = font.render(current_weapon, True, (255, 255, 255))
        font = pygame.font.Font(None, 50)
        text_ammo_surface = font.render(str(ammo), True, (255, 200, 255))
        
        pygame.draw.rect(self.game.screen, (200, 50, 50), 
                         (health_bar_lpos[0], health_bar_lpos[1], health_bar_width, health_bar_height))
        pygame.draw.rect(self.game.screen, (50, 240, 0), 
                         (health_bar_lpos[0], health_bar_lpos[1],  health_bar_width_progressive, health_bar_height))        
        self.game.screen.blit(text_weapon_surface, weapon_name_pos)
        self.game.screen.blit(text_ammo_surface, weapon_ammo_pos)


    def draw_line_of_cells(self):
        """Рисует линии сетки"""
        thickness = 2 
        
        COLOR_OUTER = (255, 0, 0)
        COLOR_CELL = (100, 100, 100)
        COLOR_CENTER = (0, 255, 0)
        
        
        for i in range(GRID_W + 1):
            # Вертикальные линии
            x = i * CELL_W
            pygame.draw.line(self.game.screen, COLOR_CELL, (x, 0), (x, HEIGHT), 1)
            if i < GRID_W:
                font = pygame.font.Font(None, int(CELL_H * 0.3))
                text = font.render(str(i), True, (50, 50, 50))
                self.game.screen.blit(text, (x + 5, 5))
        
        for i in range(GRID_H + 1):
            # Горизонтальные линии
            y = i * CELL_H
            pygame.draw.line(self.game.screen, COLOR_CELL, (0, y), (WIDTH, y), 1)
            if i < GRID_H:
                font = pygame.font.Font(None, int(CELL_H * 0.3))
                text = font.render(str(i), True, (50, 50, 50))
                self.game.screen.blit(text, (5, y + 5))
        
        center_x = WIDTH // 2
        center_y = HEIGHT // 2
        pygame.draw.circle(self.game.screen, COLOR_CENTER, (center_x, center_y), 15, 0)
