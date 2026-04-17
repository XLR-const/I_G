import pygame
import math
from setting import *
from random import uniform
from weapon import Particle

class NPC:
    def __init__(self, game, pos=(8.5, 7.5)):
        self.game = game
        self.x, self.y = pos[0] + 0.5, pos[1] + 0.5
        self.alive = True
        self.size = 0.3
        self.hp = 100
        self.color = (245, 100, 0)
        
        # СПРАЙТЫ
        self.image = pygame.image.load('resources/npc/solder.png').convert_alpha()
        self.sprite_width, self.sprite_height = self.image.get_size()
        self.sprite_ratio = self.sprite_width / self.sprite_height
        
    def get_damage(self, damage):
        if self.alive:
            self.hp -= damage
            if self.hp <= 0:
                self.alive = False
                self.color = (50, 50, 50)
                
            for _ in range(15):
                dx = self.game.player.x - self.x
                dy = self.game.player.y - self.y
                dist = math.hypot(dx, dy)
                
                # Точка появления: чуть ближе к игроку от центра NPC
                p_x = self.x + (dx / dist) * 0.1 + uniform(-0.1, 0.1)
                p_y = self.y + (dy / dist) * 0.1 + uniform(-0.1, 0.1)
                self.game.particles.append(Particle(self.game, (p_x, p_y), (200, 0, 0), uniform(0.002, 0.005)))
    
    def update(self):
        if not self.alive:
            return self.check_hit()
    
    def check_hit(self):
        pass
    
    def draw(self):
        if not self.alive:
            # Add other dead sprite
            return

        dx = self.x - self.game.player.x
        dy = self.y - self.game.player.y
        distance = math.hypot(dx, dy)
        
        theta = math.atan2(dy, dx)
        delta = theta - self.game.player.angle
        delta = (delta + math.pi) % math.tau - math.pi
        
        # Если NPC за спиной — не рисуем
        if math.cos(delta) <= 0 or distance < 0.2:
            return

        # Убираем рыбий глаз и считаем проекцию
        dist_flat = distance * math.cos(delta)
        # Защита от 0
        if dist_flat < 0.2:
            return
        
        proj_height = int(SCREEN_DIST / (dist_flat + 0.0001))
        if proj_height > HEIGHT * 2:
            proj_height = HEIGHT * 2
        proj_width = int(proj_height * self.sprite_ratio)
        
        # Позиция центра на экране
        center_x = (HALF_NUM_RAYS + delta / DELTA_ANGLE) * SCALE
        
        # Collision render
        """
        # Определяем границы NPC на экране
        start_x = int(center_x - proj_height // 2)
        end_x = int(center_x + proj_height // 2)

        # РИСУЕМ ПОЛОСКАМИ
        # Проходим по всем экранным координатам, которые занимает NPC
        for screen_x in range(start_x, end_x, SCALE):
            ray_idx = int(screen_x // SCALE)
            
            # Проверяем, попадает ли полоска в экран
            if 0 <= ray_idx < NUM_RAYS:
                # ГЛАВНОЕ: сравниваем дистанцию этой полоски с Z-буфером стены
                if dist_flat < self.game.raycasting.z_buffer[ray_idx]:
                    # Рисуем вертикальную линию (одну полоску спрайта)
                    pygame.draw.line(self.game.screen, self.color,
                                 (screen_x, HALF_HEIGHT - proj_height // 2),
                                 (screen_x, HALF_HEIGHT + proj_height // 2),
                                 SCALE)
        """

        # SPRITE RENDER
        img = pygame.transform.scale(self.image, (proj_width, proj_height))
        
        # Отрисовка полосками для Z-буфера
        start_x = int(center_x - proj_width // 2)
        for x in range(start_x, start_x + proj_width, SCALE):
            ray_idx = int(x // SCALE)
            if 0 <= ray_idx < NUM_RAYS:
                if dist_flat < self.game.raycasting.z_buffer[ray_idx]:
                    # Вырезаем нужную вертикальную полоску из отмасштабированной картинки
                    # area = (x_внутри_картинки, y_внутри_картинки, ширина_полоски, высота)
                    sub_x = int((x - start_x))
                    if 0 <= sub_x < proj_width:
                        self.game.screen.blit(img, (x, HALF_HEIGHT - proj_height // 2), 
                                              (sub_x, 0, SCALE, proj_height))
        
        