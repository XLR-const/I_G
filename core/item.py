"""Класс предмета на полу"""

import pygame
import math
from setting import *
from config.game_data import SYMBOLS_CONFIG


class Item:
    def __init__(self, game, x, y, item_type, amount=0):
        self.game = game
        self.x = x + 0.5
        self.y = y + 0.5
        self.item_type = item_type
        self.amount = amount
        self.alive = True

        self.sprite = None
        self._load_sprite()

    def _load_sprite(self):
        for symbol, config in SYMBOLS_CONFIG.items():
            if config.get('type') == 'item':
                if config.get('item_type') == self.item_type:
                    sprite_path = config.get('sprite')
                    if sprite_path:
                        try:
                            self.sprite = pygame.image.load(sprite_path).convert_alpha()
                            self.sprite = pygame.transform.scale(self.sprite, (32, 32))
                            return
                        except:
                            pass
                    break
        # Заглушка
        self.sprite = pygame.Surface((32, 32))
        self.sprite.fill((200, 0, 0))
        pygame.draw.rect(self.sprite, (255, 255, 255), (8, 14, 16, 4))
        pygame.draw.rect(self.sprite, (255, 255, 255), (14, 8, 4, 16))

    def pick_up(self, player):
        if not self.alive:
            return False

        if self.item_type == 'health':
            old_hp = player.hp
            player.hp = min(100, player.hp + self.amount)
            healed = player.hp - old_hp

            if healed > 0:
                self.alive = False
                print(f"[Предмет] +{healed} HP")
                return True

        return False

    def update(self, player):
        if self.alive:
            dx = player.x - self.x
            dy = player.y - self.y
            if math.hypot(dx, dy) < 0.5:
                self.pick_up(player)

    def draw(self):
        if not self.alive or self.sprite is None:
            return

        dx = self.x - self.game.player.x
        dy = self.y - self.game.player.y
        dist = math.hypot(dx, dy)

        if dist < 0.1:
            return

        theta = math.atan2(dy, dx)
        delta = theta - self.game.player.angle
        delta = (delta + math.pi) % math.tau - math.pi

        # Немного расширяем FOV для проверки, чтобы края спрайта не исчезали внезапно
        if abs(delta) > HALF_FOV + 0.5:
            return

        # Плоская дистанция (для корректного Z-буфера)
        dist_flat = dist * math.cos(delta)
        if dist_flat < 0.1:
            return

        # 1. Расчёт размеров БЕЗ искусственного занижения вблизи
        # Коэффициент 0.3-0.4 подбирайте под высоту ваших стен
        proj_height = int(SCREEN_DIST / dist_flat * 0.35) 
        if proj_height < 2:  # Защита от нулевого размера для pygame.transform
            return

        proj_width = int(proj_height * (self.sprite.get_width() / self.sprite.get_height()))

        # Позиционирование на экране
        center_x = (HALF_NUM_RAYS + delta / DELTA_ANGLE) * SCALE
        screen_x = int(center_x - proj_width // 2)
        
        # 2. ИСПРАВЛЕНИЕ: Привязка к полу (вычисляем Y от линии пола)
        # Если в игре стены занимают всю высоту экрана, то HALF_HEIGHT — это середина стены.
        # Спрайт высотой proj_height опускаем вниз.
        screen_y = int(HALF_HEIGHT + (SCREEN_DIST / dist_flat * 0.5) - proj_height)

        # Масштабируем спрайт под нужные размеры для вырезания полос
        scaled_sprite = pygame.transform.scale(self.sprite, (proj_width, proj_height))

        # 3. ИСПРАВЛЕНИЕ: Пополосный рендеринг с проверкой Z-буфера для каждого луча
        for col in range(proj_width):
            x_pos = screen_x + col
            
            # Проверяем, попадает ли вертикальная полоса в экран
            if 0 <= x_pos < WIDTH:
                ray_idx = int(x_pos // SCALE)
                
                if 0 <= ray_idx < NUM_RAYS:
                    # Проверяем Z-буфер конкретно для этого луча
                    if dist_flat < self.game.raycasting.z_buffer[ray_idx]:
                        # Вырезаем вертикальную полоску из отмасштабированного спрайта
                        sub_surface = scaled_sprite.subsurface(col, 0, 1, proj_height)
                        # Блитуем полоску на экран
                        self.game.screen.blit(sub_surface, (x_pos, screen_y))

