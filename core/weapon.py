import os
import math
from random import uniform
import pygame
from setting import *
from config.game_data import WEAPON_CONFIG
from core.particle import Particle


class Weapon:
    """Базовый класс для оружия с поддержкой обратной совместимости и автозагрузки"""

    def __init__(self, game, weapon_name):
        self.game = game
        self.weapon_name = weapon_name

        # Читаем базовую конфигурацию из game_data.py
        config = WEAPON_CONFIG.get(weapon_name, {})
        self.name = config.get('name', weapon_name)
        self.damage = config.get('damage', 10)
        self.reload_time = config.get('reload_time', 150)
        self.is_continuous = config.get('continuous', False)
        self.ammo_start = config.get('ammo_start', 0)
        self.max_distance = config.get('max_distance', 5)

        # Новые параметры автоматизации для спрайт-листов
        self.folder_name = config.get('folder_name', None)
        self.sprite_prefix = config.get('sprite_prefix', None)

        # Внутренние состояния
        self.reloading = False
        self.ammo = self.ammo_start
        self.last_shot_time = 0
        self.recoil = 0
        self.elapsed = 9999

        # Параметры по умолчанию для настройки новых пушек из config.txt
        self.scale = 3.0
        self.offset_x = 0
        self.offset_y = 0
        self.animation_speed = 60
        self.frame_offsets = {}  # Тряска конкретных кадров при отдаче

        # Контейнеры для покадровой анимации новых пушек
        self.idle_frames = []
        self.fire_frames = []
        self.reload_frames = []
        self.current_frames = []
        self.frame_index = 0

        # Общие базовые звуки
        self.sound_empty_ammo = pygame.mixer.Sound('resources/weapons/empty.wav')
        self.sound_empty_ammo.set_volume(0.2)

        # Проверяем, какой режим загрузки использовать:
        if self.folder_name and self.sprite_prefix:
            # Система для новых пушек с папками и конфигами
            self.is_new_system = True
            self.folder_path = os.path.join('resources', 'weapons', self.folder_name)
            self._load_new_weapon_data()
        else:
            # Старая система с хардкодом одной картинки
            self.is_new_system = False
            self.sprite_path = config.get('sprite', f'resources/weapons/{weapon_name}.png')
            self.sound_path = config.get('sound', f'resources/weapons/{weapon_name}_shot.wav')
            
            try:
                self.sound = pygame.mixer.Sound(self.sound_path)
                self.sound.set_volume(0.2)
            except Exception as e:
                print(f"Ошибка загрузки звука {self.name}: {e}")
                self.sound = self.sound_empty_ammo
                
            self.sprite = None
            self._load_sprite()

    def _load_sprite(self):
        """Загрузка одиночного спрайта для старых пушек"""
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

    def _load_new_weapon_data(self):
        """Автоматическая сборка новой пушки из её персональной папки"""
        if not os.path.exists(self.folder_path):
            print(f"[Оружие] Папка не найдена: {self.folder_path}")
            return

        # 1. Парсим config.txt этой пушки
        config_file = os.path.join(self.folder_path, 'config.txt')
        if os.path.exists(config_file):
            self._parse_txt_config(config_file)

        # 2. Сканируем папку и распределяем кадры (Doom-номенклатура)
        files = sorted(os.listdir(self.folder_path))
        for file in files:
            if file.startswith(self.sprite_prefix) and file.endswith('.png'):
                img_path = os.path.join(self.folder_path, file)
                sprite = pygame.image.load(img_path).convert_alpha()
                
                # Масштабируем по коэффициенту из config.txt
                w, h = sprite.get_size()
                sprite = pygame.transform.scale(sprite, (int(w * self.scale), int(h * self.scale)))

                # Разбираем кадры по буквам после префикса (Например: AK47A0 -> буква A)
                frame_letter = file[len(self.sprite_prefix)]
                if frame_letter == 'A':
                    self.idle_frames.append((sprite, frame_letter))
                elif frame_letter in ('B', 'C', 'D'):
                    self.fire_frames.append((sprite, frame_letter))
                else:
                    self.reload_frames.append((sprite, frame_letter))

        # Защита на случай неполных анимаций в скачанном паке
        if not self.fire_frames:
            self.fire_frames = self.idle_frames
        if not self.reload_frames:
            self.reload_frames = self.idle_frames
            
        self.current_frames = self.idle_frames

        # 3. Загружаем динамический звук выстрела из папки пушки
        sound_path = os.path.join(self.folder_path, 'shot.wav')
        if os.path.exists(sound_path):
            try:
                self.sound = pygame.mixer.Sound(sound_path)
                self.sound.set_volume(0.2)
            except Exception as e:
                print(f"[Оружие] Ошибка загрузки звука выстрела: {e}")
                self.sound = self.sound_empty_ammo
        else:
            self.sound = self.sound_empty_ammo

    def _parse_txt_config(self, filepath):
        """Парсер текстового конфига 'ключ = значение'"""
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, val = line.split('=', 1)
                    key = key.strip()
                    val = val.strip()

                    if key == 'scale':
                        self.scale = float(val)
                    elif key == 'offset_x':
                        self.offset_x = int(val)
                    elif key == 'offset_y':
                        self.offset_y = int(val)
                    elif key == 'animation_speed':
                        self.animation_speed = int(val)
                    elif key.startswith('frame_'):
                        # Парсим индивидуальные покадровые сдвиги (например: frame_B = 5, -20)
                        letter = key.split('_')[1]
                        x_shift, y_shift = map(int, val.split(','))
                        self.frame_offsets[letter] = (x_shift, y_shift)

    def update_animation(self):
        """Единый метод обновлений анимаций для старого и нового режимов"""
        if self.is_new_system:
            # Логика покадровой анимации новых пушек
            if self.reloading:
                now = pygame.time.get_ticks()
                if now - self.last_shot_time > self.animation_speed:
                    self.last_shot_time = now
                    self.frame_index += 1
                    
                    if self.frame_index >= len(self.current_frames):
                        self.reloading = False
                        self.current_frames = self.idle_frames
                        self.frame_index = 0
        else:
            # Ваша оригинальная логика отдачи через синус для старых пушек
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
        """Выполняет выстрел и обсчитывает попадания"""
        if self.reloading or self.ammo <= 0:
            if self.ammo <= 0:
                self.sound_empty_ammo.play()
            return None

        self.reloading = True
        self.last_shot_time = pygame.time.get_ticks()
        
        # Переключение стейта анимации для новых пушек при выстреле
        if self.is_new_system:
            self.current_frames = self.fire_frames
            self.frame_index = 0

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
            self.game.particles.append(
                Particle(self.game, (p_x, p_y), (255, 200, 50), uniform(0.001, 0.005))
            )

        return hit_x, hit_y, dist, side

    def _get_hit_pos(self):
        """DDA алгоритм попадания пули с ограничением по дистанции"""
        ox, oy = self.game.player.x, self.game.player.y
        x_map, y_map = int(ox), int(oy)
        angle = self.game.player.angle
        sin_a = math.sin(angle)
        cos_a = math.cos(angle)

        max_dist = self.max_distance

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
        steps = 0
        max_steps = int(max_dist * 10)

        while steps < max_steps:
            steps += 1
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
        """Универсальный отрисовщик: переключается на новую систему, если она активна"""
        self.update_animation()
        
        if self.is_new_system:
            if not self.current_frames:
                return
            sprite, letter = self.current_frames[self.frame_index]
            sw, sh = sprite.get_size()
            
            # Центрируем пушку по нижнему краю экрана с базовыми сдвигами из config.txt
            x = WIDTH // 2 - sw // 2 + self.offset_x
            y = HEIGHT - sh + self.offset_y
            
            # Добавляем покадровое смещение отдачи/тряски из config.txt
            if letter in self.frame_offsets:
                fx, fy = self.frame_offsets[letter]
                x += fx
                y += fy
                
            self.game.screen.blit(sprite, (x, y))


# ============================================================
# СТАРЫЕ КЛАССЫ ОРУЖИЯ (с обратной совместимостью)
# ============================================================

class Pistol(Weapon):
    def __init__(self, game):
        super().__init__(game, 'Pistol')

    def draw(self):
        if self.is_new_system:
            super().draw()
            return
            
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
            pygame.draw.circle(self.game.screen, (255, 255, 100), (center_x, bottom_y - 360), 50)


class Shotgun(Weapon):
    def __init__(self, game):
        super().__init__(game, 'Shotgun')

    def draw(self):
        if self.is_new_system:
            super().draw()
            return
            
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
            pygame.draw.circle(self.game.screen, (255, 140, 0), (center_x, bottom_y - 410), 120)


class MachineGun(Weapon):
    def __init__(self, game):
        super().__init__(game, 'Machine Gun')

    def draw(self):
        if self.is_new_system:
            super().draw()
            return
            
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
            pygame.draw.circle(self.game.screen, (255, 200, 50), (cx, bottom_y - 440), 80)


class PlasmaGun(Weapon):
    def __init__(self, game):
        super().__init__(game, 'Plasma Gun')

    def draw(self):
        if self.is_new_system:
            super().draw()
            return
            
        self.update_animation()
        if self.sprite is None:
            return
            
        center_x = (GRID_W // 2) * CELL_W + CELL_W * 5
        offset_y = -40
        bottom_y = HEIGHT + offset_y + self.recoil * 2.0 - CELL_H
        recoil_offset = 2.5 * self.recoil
        
        sprite_rect = self.sprite.get_rect(center=(center_x, bottom_y + recoil_offset))
        self.game.screen.blit(self.sprite, sprite_rect)


# ============================================================
# НОВЫЙ УНИВЕРСАЛЬНЫЙ КЛАСС (для калаша и любых других пушек)
# ============================================================

class NewWeapon(Weapon):
    """Класс для любого нового оружия с полностью автоматической data-driven логикой"""
    
    def __init__(self, game, weapon_name):
        super().__init__(game, weapon_name)

    def draw(self):
        # Перенаправляем в базовый draw, так как он умеет крутить покадровые листы
        super().draw()