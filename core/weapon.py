import pygame
import math
from random import uniform
from setting import *
from config.game_data import WEAPON_CONFIG
from core.particle import Particle

class Weapon:
    def __init__(self, game, weapon_name):
        self.game = game
        self.weapon_name = weapon_name
        
        # Читаем параметры из конфига
        config = WEAPON_CONFIG.get(weapon_name, {})
        self.name = config.get('name', weapon_name)
        self.damage = config.get('damage', 10)
        self.reload_time = config.get('reload_time', 150)
        self.is_continuous = config.get('continuous', False)
        self.ammo_start = config.get('ammo_start', 0)
        self.sprite_path = config.get('sprite', f'resources/weapons/{weapon_name}.png')
        self.sound_path = config.get('sound', f'resources/weapons/{weapon_name}_shot.wav')
        
        self.reloading = False
        self.ammo = self.ammo_start
        self.last_shot_time = 0
        self.recoil = 0
        
        # Звуки
        self.sound = pygame.mixer.Sound(self.sound_path)
        self.sound.set_volume(0.2)
        self.sound_empty_ammo = pygame.mixer.Sound('resources/weapons/empty.wav')
        self.sound_empty_ammo.set_volume(0.2)
        
        # Спрайт
        self.sprite = None
        self._load_sprite()

    def _load_sprite(self):
        try:
            original = pygame.image.load(self.sprite_path).convert_alpha()
            if self.name == "Pistol":
                scale = 0.3
            elif self.name == "Shotgun":
                scale = 1.0
            elif self.name in ["Machine Gun", "Plasma Gun"]:
                scale = 4.0
            else:
                scale = 1.0
            new_w = int(original.get_width() * scale)
            new_h = int(original.get_height() * scale)
            self.sprite = pygame.transform.scale(original, (new_w, new_h))
        except Exception as e:
            print(f"Ошибка загрузки спрайта {self.name}: {e}")
            self.sprite = None

    def update_animation(self):
        if self.reloading:
            self.elapsed = pygame.time.get_ticks() - self.last_shot_time
            if self.elapsed < self.reload_time:
                self.recoil = math.sin(self.elapsed / self.reload_time * math.pi) * 50
            else:
                self.reloading = False
                self.recoil = 0
        else:
            self.elapsed = 9999

    def fire(self):
        if self.reloading or self.ammo <= 0:
            if self.ammo <= 0:
                self.sound_empty_ammo.play()
            return None

        self.reloading = True
        self.last_shot_time = pygame.time.get_ticks()
        self.sound.play()
        self.ammo -= 1

        hit_x, hit_y, dist, side = self._get_hit_pos()

        for npc in self.game.npcs:
            if not npc.alive:
                continue

            dx = npc.x - self.game.player.x
            dy = npc.y - self.game.player.y
            dist_npc = math.hypot(dx, dy)

            theta = math.atan2(dy, dx)
            delta = theta - self.game.player.angle
            delta = (delta + math.pi) % math.tau - math.pi

            view_width = 0.3 / dist_npc

            if abs(delta) < view_width and dist_npc < dist and math.cos(delta) > 0:
                npc.get_damage(self.damage)

        for _ in range(10):
            p_x = hit_x + uniform(-0.02, 0.02)
            p_y = hit_y + uniform(-0.02, 0.02)
            self.game.particles.append(Particle(self.game, (p_x, p_y), (255, 200, 50), uniform(0.001, 0.005)))

        return hit_x, hit_y, dist, side

    def _get_hit_pos(self):
        ox, oy = self.game.player.x, self.game.player.y
        x_map, y_map = int(ox), int(oy)

        angle = self.game.player.angle
        sin_a = math.sin(angle)
        cos_a = math.cos(angle)

        delta_dist_x = abs(1 / cos_a) if cos_a != 0 else 1e30
        delta_dist_y = abs(1 / sin_a) if sin_a != 0 else 1e30

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

        side = 0
        while True:
            if side_dist_x < side_dist_y:
                side_dist_x += delta_dist_x
                x_map += step_x
                side = 0
            else:
                side_dist_y += delta_dist_y
                y_map += step_y
                side = 1

            if (x_map, y_map) in self.game.map.world_map:
                break

        if side == 0:
            dist = side_dist_x - delta_dist_x
        else:
            dist = side_dist_y - delta_dist_y

        hit_x = ox + dist * cos_a
        hit_y = oy + dist * sin_a

        return hit_x, hit_y, dist, side

    def draw(self):
        pass


class Pistol(Weapon):
    def __init__(self, game):
        super().__init__(game, 'Pistol')

    def draw(self):
        self.update_animation()

        if self.sprite is None:
            self._draw_fallback()
            return

        center_x = (GRID_W // 2) * CELL_W - 0.5 * CELL_W
        bottom_y = HEIGHT + int(80 * (CELL_H / 60)) + self.recoil * 2.0
        recoil_offset = 1 * self.recoil

        sprite_rect = self.sprite.get_rect(midbottom=(center_x, bottom_y + recoil_offset))
        self.game.screen.blit(self.sprite, sprite_rect)

        if self.reloading and self.elapsed < 50:
            flash_x = 16 * CELL_W
            flash_y = 12 * CELL_H + recoil_offset
            pygame.draw.circle(self.game.screen, (255, 255, 100), (flash_x, flash_y), 50)
            pygame.draw.circle(self.game.screen, (255, 255, 255), (flash_x, flash_y), 20)

    def _draw_fallback(self):
        center_x = (GRID_W // 2) * CELL_W
        bottom_y = HEIGHT + int(80 * (CELL_H / 60)) + self.recoil * 2.0

        pygame.draw.polygon(self.game.screen, (35, 35, 35), [
            (center_x - 110, bottom_y), (center_x + 110, bottom_y),
            (center_x + 70, bottom_y - 350), (center_x - 70, bottom_y - 350)
        ])
        pygame.draw.polygon(self.game.screen, (55, 55, 55), [
            (center_x - 70, bottom_y - 280), (center_x + 70, bottom_y - 280),
            (center_x + 60, bottom_y - 350), (center_x - 60, bottom_y - 350)
        ])
        pygame.draw.rect(self.game.screen, (20, 20, 20), (center_x - 5, bottom_y - 365, 10, 15))
        pygame.draw.circle(self.game.screen, (10, 10, 10), (center_x, int(bottom_y - 330)), 12)

        if self.reloading and self.elapsed < 40:
            flash_y = bottom_y - 360
            pygame.draw.circle(self.game.screen, (255, 255, 100), (center_x, flash_y), 50)
            pygame.draw.circle(self.game.screen, (255, 255, 255), (center_x, flash_y), 20)


class Shotgun(Weapon):
    def __init__(self, game):
        super().__init__(game, 'Shotgun')

    def draw(self):
        self.update_animation()

        if self.sprite is None:
            self._draw_fallback()
            return

        center_x = (GRID_W // 2) * CELL_W + CELL_W * 0.2
        bottom_y = HEIGHT + int(80 * (CELL_H / 60)) + self.recoil * 2.0
        recoil_offset = 3.5 * self.recoil

        sprite_rect = self.sprite.get_rect(midbottom=(center_x, bottom_y + recoil_offset))
        self.game.screen.blit(self.sprite, sprite_rect)

        if self.reloading and self.elapsed < 50:
            flash_x = 16 * CELL_W
            flash_y = 12 * CELL_H + recoil_offset
            pygame.draw.circle(self.game.screen, (255, 140, 0), (flash_x, flash_y), 120)
            pygame.draw.circle(self.game.screen, (255, 255, 180), (flash_x, flash_y), 50)

    def _draw_fallback(self):
        center_x = (GRID_W // 2) * CELL_W
        bottom_y = HEIGHT + int(80 * (CELL_H / 60)) + self.recoil * 2.0

        pygame.draw.polygon(self.game.screen, (100, 50, 20), [
            (center_x - 220, bottom_y), (center_x + 220, bottom_y),
            (center_x + 170, bottom_y - 180), (center_x - 170, bottom_y - 180)
        ])
        pygame.draw.polygon(self.game.screen, (50, 50, 50), [
            (center_x - 90, bottom_y - 200), (center_x, bottom_y - 200),
            (center_x, bottom_y - 400), (center_x - 75, bottom_y - 400)
        ])
        pygame.draw.polygon(self.game.screen, (60, 60, 60), [
            (center_x, bottom_y - 200), (center_x + 90, bottom_y - 200),
            (center_x + 75, bottom_y - 400), (center_x, bottom_y - 400)
        ])

        if self.reloading and self.elapsed < 50:
            flash_y = bottom_y - 410
            pygame.draw.circle(self.game.screen, (255, 140, 0), (center_x, flash_y), 120)
            pygame.draw.circle(self.game.screen, (255, 255, 180), (center_x, flash_y), 50)


class MachineGun(Weapon):
    def __init__(self, game):
        super().__init__(game, 'Machine Gun')

    def draw(self):
        self.update_animation()

        if self.sprite is None:
            self._draw_fallback()
            return

        center_x = (GRID_W // 2) * CELL_W + CELL_W
        bottom_y = HEIGHT + int(80 * (CELL_H / 60)) + self.recoil * 2.0 - CELL_H
        recoil_offset = 1.5 * self.recoil

        sprite_rect = self.sprite.get_rect(midbottom=(center_x, bottom_y - recoil_offset))
        self.game.screen.blit(self.sprite, sprite_rect)

        if self.reloading and self.elapsed < 40:
            flash_x = 17 * CELL_W
            flash_y = 12 * CELL_H + recoil_offset
            pygame.draw.circle(self.game.screen, (255, 200, 50), (flash_x, flash_y), 80)
            pygame.draw.circle(self.game.screen, (255, 255, 255), (flash_x, flash_y), 30)

    def _draw_fallback(self):
        center_x = (GRID_W // 2) * CELL_W
        bottom_y = HEIGHT + int(120 * (CELL_H / 60)) + self.recoil
        shake = math.sin(pygame.time.get_ticks() * 0.3) * 6 if self.reloading else 0
        cx = center_x + shake

        pygame.draw.polygon(self.game.screen, (30, 30, 30), [
            (cx - 180, bottom_y), (cx + 180, bottom_y),
            (cx + 140, bottom_y - 180), (cx - 140, bottom_y - 180)
        ])

        if self.reloading and self.elapsed < 40:
            flash_y = bottom_y - 440
            pygame.draw.circle(self.game.screen, (255, 200, 50), (cx, flash_y), 80)
            pygame.draw.circle(self.game.screen, (255, 255, 255), (cx, flash_y), 30)


class PlasmaGun(Weapon):
    def __init__(self, game):
        super().__init__(game, 'Plasma Gun')

    def draw(self):
        self.update_animation()

        if self.sprite is None:
            return

        center_x = (GRID_W // 2) * CELL_W + CELL_W * 5
        offset_y = -40
        bottom_y = HEIGHT + offset_y + self.recoil * 2.0 - CELL_H
        recoil_offset = 2.5 * self.recoil

        sprite_rect = self.sprite.get_rect(center=(center_x, bottom_y + recoil_offset))
        self.game.screen.blit(self.sprite, sprite_rect)

        if self.reloading and self.elapsed < 100:
            flash_x = 18 * CELL_W
            flash_y = 13 * CELL_H + recoil_offset
            pygame.draw.circle(self.game.screen, (200, 0, 255), (flash_x, flash_y), 70)
            pygame.draw.circle(self.game.screen, (255, 100, 255), (flash_x, flash_y), 30)
