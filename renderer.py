import pygame
from math import atan2, degrees
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
    
    def draw_compass(self):
        goal = self.game.map.exit_pos
        player = (self.game.player.x, self.game.player.y)
        d_x, d_y = goal[0] - player[0], goal[1] - player[1]
        angle_to_goal = math.degrees(atan2(d_y, d_x))
        # Параметры компаса
        compass_col = 11
        compass_row = 0
        compass_width = 10
        compass_height = 1
        # Координаты и размеры
        compass_x = compass_col * CELL_W
        compass_y = compass_row * CELL_H
        compass_w = compass_width * CELL_W
        compass_h = int(compass_height * CELL_H * 0.6)  # 60% высоты клетки
        # Рамка компаса
        pygame.draw.rect(self.game.screen, (30, 80, 30), 
                        (compass_x, compass_y, compass_w, compass_h))
        pygame.draw.rect(self.game.screen, (100, 100, 100), 
                        (compass_x, compass_y, compass_w, compass_h), 2)
        # Центр компаса (положение игрока)
        center_x = compass_x + compass_w // 2
        center_y = compass_y + compass_h // 2
        # Направление
        player_angle_deg = math.degrees(self.game.player.angle)
        # Настройка углов
        north_angle = 90
        east_angle = 0
        south_angle = 270
        west_angle = 180
        
        # Список направлений и их углов
        directions = [
            ('N', north_angle),
            ('NE', 45),
            ('E', east_angle),
            ('SE', 315),
            ('S', south_angle),
            ('SW', 225),
            ('W', west_angle),
            ('NW', 135),
            ('<!>', angle_to_goal)
        ]
        visible_range = 120
        pixels_per_degree = compass_w / visible_range
        font = pygame.font.Font(None, int(CELL_H * 0.4))
        for name, angle in directions:
            diff = angle - player_angle_deg
            while diff > 180:
                diff -= 360
            while diff < -180:
                diff += 360
            if abs(diff) <= visible_range // 2:
                # Позиция на компасе
                x = center_x + diff * pixels_per_degree
                intensity = 1.0 - (abs(diff) / (visible_range // 2)) * 0.7
                color_value = int(150 + 105 * intensity)
                color = (color_value, color_value, color_value)
                if len(name) == 1 and name != '<!>':
                    font_size = int(CELL_H * 0.45)
                    color = (255, 255, 255)
                elif name == '<!>':
                    font_size = int(CELL_H * 0.95)
                    color = 'yellow'
                else:
                    font_size = int(CELL_H * 0.3)
                    color = (180, 180, 180)
                
                font = pygame.font.Font(None, font_size)
                text = font.render(name, True, color)
                text_rect = text.get_rect(center=(x, center_y))
                self.game.screen.blit(text, text_rect)
        
        # Центральная метка
        triangle_points = [
            (center_x, center_y - 15),
            (center_x - 8, center_y + 5),
            (center_x + 8, center_y + 5)
        ]
        pygame.draw.polygon(self.game.screen, (255, 100, 0), triangle_points)
        for offset in [-20, 20]:
            pygame.draw.line(self.game.screen, (200, 200, 200),
                            (center_x + offset, center_y - 10),
                            (center_x + offset, center_y + 10), 2)

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
        self.draw_compass()


    def draw_line_of_cells(self):
        """Рисует линии сетки"""
        thickness = 2 
        
        COLOR_OUTER = (255, 0, 0)
        COLOR_CELL = (100, 100, 100)
        COLOR_CENTER = (255, 100, 0)
        
        
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
        #pygame.draw.circle(self.game.screen, COLOR_CENTER, (center_x, center_y), 15, 0)
        pygame.draw.line(self.game.screen, COLOR_CENTER, (center_x, center_y - CELL_H * 0.5), (center_x, center_y + CELL_H * 0.5), thickness)
        pygame.draw.line(self.game.screen, COLOR_CENTER, (center_x - CELL_W * 0.5, center_y), (center_x + CELL_W * 0.5, center_y), thickness)
        

