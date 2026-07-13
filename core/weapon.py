import os
import math
from random import uniform
import pygame
from setting import *
from config.game_data import WEAPON_CONFIG
from core.particle import Particle


class Weapon:
    """Класс оружия с автозагрузкой из папок"""

    def __init__(self, game, weapon_name):
        self.game = game
        self.weapon_name = weapon_name

        # Читаем конфигурацию из game_data.py
        config = WEAPON_CONFIG.get(weapon_name, {})
        self.name = config.get('name', weapon_name)
        self.damage = config.get('damage', 10)
        self.reload_time = config.get('reload_time', 150)
        self.is_continuous = config.get('continuous', False)
        self.ammo_start = config.get('ammo_start', 0)
        self.max_distance = config.get('max_distance', 5)

        # Параметры для спрайт-листов
        self.folder_name = config.get('folder_name', None)
        self.sprite_prefix = config.get('sprite_prefix', None)

        # Внутренние состояния
        self.reloading = False
        self.ammo = self.ammo_start
        self.last_shot_time = 0
        self.frame_index = 0

        # Параметры из config.txt
        self.scale = 3.0
        self.offset_x = 0
        self.offset_y = 0
        self.animation_speed = 60
        self.frame_offsets = {}

        # Контейнеры для анимации
        self.idle_frames = []
        self.fire_frames = []
        self.current_frames = []
        
        # Свойство self.sprite теперь хранит чистый pygame.Surface для HUD
        self.sprite = None

        # Звук
        self.sound_empty_ammo = pygame.mixer.Sound('resources/weapons/empty.wav')
        self.sound_empty_ammo.set_volume(0.2)
        self.sound = self.sound_empty_ammo

        # Загружаем данные из папки
        if self.folder_name and self.sprite_prefix:
            self.folder_path = os.path.join('resources', 'weapons', self.folder_name)
            self._load_weapon_data()

    def _load_weapon_data(self):
        """Загружает всё из папки оружия"""
        if not os.path.exists(self.folder_path):
            print(f"[Оружие] Папка не найдена: {self.folder_path}")
            return

        # 1. Парсим config.txt
        config_file = os.path.join(self.folder_path, 'config.txt')
        if os.path.exists(config_file):
            self._parse_txt_config(config_file)

        # 2. Загружаем кадры
        files = sorted(os.listdir(self.folder_path))
        for file in files:
            if file.startswith(self.sprite_prefix) and file.endswith('.png'):
                img_path = os.path.join(self.folder_path, file)
                sprite = pygame.image.load(img_path).convert_alpha()

                w, h = sprite.get_size()
                sprite = pygame.transform.scale(sprite, (int(w * self.scale), int(h * self.scale)))

                frame_letter = file[len(self.sprite_prefix)]
                # Сохраняем картинку вместе с её буквой в кортеж
                if frame_letter == 'A':
                    self.idle_frames.append((sprite, frame_letter))
                else:
                    self.fire_frames.append((sprite, frame_letter))

        # Защита от пустых анимаций
        if not self.fire_frames:
            self.fire_frames = self.idle_frames[:] if self.idle_frames else []
        if not self.idle_frames:
            fallback = pygame.Surface((100, 100))
            fallback.fill((200, 0, 0))
            self.idle_frames = [(fallback, 'A')]
            self.fire_frames = [(fallback, 'A')]

        self.current_frames = self.idle_frames
        # Записываем чистую картинку первого кадра для HUD интерфейса
        self.sprite = self.idle_frames[0][0] if self.idle_frames else None

        # 3. Загружаем звук
        sound_path = os.path.join(self.folder_path, 'shot.wav')
        if os.path.exists(sound_path):
            try:
                self.sound = pygame.mixer.Sound(sound_path)
                self.sound.set_volume(0.2)
            except Exception as e:
                print(f"[Оружие] Ошибка загрузки звука: {e}")
                self.sound = self.sound_empty_ammo
        else:
            self.sound = self.sound_empty_ammo

    def _parse_txt_config(self, filepath):
        """Парсит config.txt"""
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
                        letter = key.split('_')[1]
                        x_shift, y_shift = map(int, val.split(','))
                        self.frame_offsets[letter] = (x_shift, y_shift)

    def update_animation(self):
        """Обновляет анимацию"""
        if self.reloading:
            now = pygame.time.get_ticks()
            if now - self.last_shot_time > self.animation_speed:
                self.last_shot_time = now
                self.frame_index += 1

                if self.frame_index >= len(self.current_frames):
                    self.reloading = False
                    self.current_frames = self.idle_frames
                    self.frame_index = 0
                    
                # Обновляем текстуру для HUD (берем только картинку из кортежа)
                if self.current_frames and self.frame_index < len(self.current_frames):
                    self.sprite = self.current_frames[self.frame_index][0]

    def fire(self):
        """Выстрел"""
        if self.reloading or self.ammo <= 0:
            if self.ammo <= 0:
                self.sound_empty_ammo.play()
            return None

        self.reloading = True
        self.last_shot_time = pygame.time.get_ticks()
        self.current_frames = self.fire_frames
        self.frame_index = 0
        
        # Переключаем картинку HUD на первый кадр вспышки выстрела
        if self.fire_frames:
            self.sprite = self.fire_frames[0][0]

        self.sound.play()
        self.ammo -= 1

        hit_x, hit_y, dist, side = self._get_hit_pos()

        # Попадания в NPC
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

        # Частицы
        for _ in range(10):
            p_x = hit_x + uniform(-0.02, 0.02)
            p_y = hit_y + uniform(-0.02, 0.02)
            self.game.particles.append(
                Particle(self.game, (p_x, p_y), (255, 200, 50), uniform(0.001, 0.005))
            )

        return hit_x, hit_y, dist, side

    def _get_hit_pos(self):
        """DDA с ограничением по дистанции"""
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
        """Рисует оружие на экране"""
        self.update_animation()

        if self.sprite is None:
            return

        # self.sprite теперь всегда хранит чистую картинку pygame.Surface
        sw, sh = self.sprite.get_size()

        # Базовая позиция по центру низа экрана
        x = WIDTH // 2 - sw // 2 + self.offset_x
        y = HEIGHT - sh + self.offset_y

        # Рассчитываем покадровое смещение отдачи
        if self.current_frames and self.frame_index < len(self.current_frames):
            # Извлекаем букву кадра напрямую из кортежа текущего кадра
            letter = self.current_frames[self.frame_index][1]
            
            if letter in self.frame_offsets:
                fx, fy = self.frame_offsets[letter]
                x += fx
                y += fy

        self.game.screen.blit(self.sprite, (x, y))
