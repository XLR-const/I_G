import os
import math
from random import uniform
import pygame
from setting import *
from config.game_data import WEAPON_CONFIG
from core.particle import Particle


class Weapon:
    """Класс оружия с автозагрузкой из папок и монотонной покадровой анимацией"""

    def __init__(self, game, weapon_name):
        self.game = game
        self.weapon_name = weapon_name

        # Читаем конфигурацию из game_data.py
        config = WEAPON_CONFIG.get(weapon_name, {})
        self.name = config.get('name', weapon_name)
        self.slot = config.get('slot', 4)
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

        # Контейнеры для анимации (хранят ТОЛЬКО чистые pygame.Surface)
        self.idle_frames = []
        self.fire_frames = []
        self.current_frames = []
        
        # Текущий отображаемый спрайт для HUD интерфейса
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
        """Загружает всё из папки оружия с гарантированным порядком кадров от A до Z"""
        if not os.path.exists(self.folder_path):
            print(f"[Оружие] Папка не найдена: {self.folder_path}")
            return

        # 1. Парсим config.txt
        config_file = os.path.join(self.folder_path, 'config.txt')
        if os.path.exists(config_file):
            self._parse_txt_config(config_file)

        # 2. Строго перебираем алфавит от A до Z
        # Для буквы A мы проверим файлы от A1 до A9, чтобы собрать анимацию покоя
        for i in range(26):
            letter = chr(65 + i)  # 65 = 'A', 66 = 'B' и т.д.
            
            if letter == 'A':
                # АНИМАЦИЯ ПОКОЯ: Ищем файлы вида PLASA1.png, PLASA2.png ... PLASA9.png
                for num in range(1, 10):
                    filename = f"{self.sprite_prefix}A{num}.png"
                    img_path = os.path.join(self.folder_path, filename)
                    
                    if os.path.exists(img_path):
                        try:
                            sprite = pygame.image.load(img_path).convert_alpha()
                            w, h = sprite.get_size()
                            sprite = pygame.transform.scale(sprite, (int(w * self.scale), int(h * self.scale)))
                            self.idle_frames.append(sprite)
                        except Exception as e:
                            print(f"[Оружие] Ошибка чтения кадра покоя {filename}: {e}")
                
                # Если анимированных кадров нет, ищем старый добрый одиночный дефолт PLASA0.png
                if not self.idle_frames:
                    filename = f"{self.sprite_prefix}A0.png"
                    img_path = os.path.join(self.folder_path, filename)
                    if os.path.exists(img_path):
                        sprite = pygame.image.load(img_path).convert_alpha()
                        w, h = sprite.get_size()
                        sprite = pygame.transform.scale(sprite, (int(w * self.scale), int(h * self.scale)))
                        self.idle_frames.append(sprite)
            else:
                # АНИМАЦИЯ ВЫСТРЕЛА: Оставляем старый стандарт (PLASB0.png, PLASC0.png)
                filename = f"{self.sprite_prefix}{letter}0.png"
                img_path = os.path.join(self.folder_path, filename)
                
                if os.path.exists(img_path):
                    try:
                        sprite = pygame.image.load(img_path).convert_alpha()
                        w, h = sprite.get_size()
                        sprite = pygame.transform.scale(sprite, (int(w * self.scale), int(h * self.scale)))
                        self.fire_frames.append(sprite)
                    except Exception as e:
                        print(f"[Оружие] Ошибка чтения кадра выстрела {filename}: {e}")

        # Защита от пустых анимаций
        if not self.fire_frames:
            self.fire_frames = self.idle_frames[:] if self.idle_frames else []
        if not self.idle_frames:
            fallback = pygame.Surface((100, 100))
            fallback.fill((200, 0, 0))
            self.idle_frames = [fallback]
            self.fire_frames = [fallback]

        self.current_frames = self.idle_frames
        self.sprite = self.idle_frames[0] if self.idle_frames else None

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
        """Обновляет кадры анимации по таймеру (поддерживает циклическую анимацию покоя)"""
        now = pygame.time.get_ticks()

        if self.reloading:
            # Анимация выстрела (останавливается, когда доходит до конца списка)
            if now - self.last_shot_time > self.animation_speed:
                self.last_shot_time = now
                self.frame_index += 1

                if self.frame_index >= len(self.current_frames):
                    self.reloading = False
                    self.current_frames = self.idle_frames
                    self.frame_index = 0
                
                if self.current_frames and self.frame_index < len(self.current_frames):
                    self.sprite = self.current_frames[self.frame_index]
        else:
            # АНИМАЦИЯ ПОКОЯ (Мерцание колбы плазмагана)
            # Если у оружия больше 1 кадра в стойке покое — крутим их по кругу бесконечно!
            if len(self.idle_frames) > 1:
                # Скорость мерцания молнии в колбе (60 мс — будет очень динамично)
                idle_speed = 60 
                
                if now - self.last_shot_time > idle_speed:
                    self.last_shot_time = now
                    # Увеличиваем индекс кадра
                    self.frame_index += 1
                    # Зацикливаем индекс: если дошли до конца, сбрасываем в 0
                    self.frame_index %= len(self.idle_frames)
                    
                    self.sprite = self.idle_frames[self.frame_index]
            else:
                # Если кадр всего один (как у автомата или кольта) — просто всегда держим его
                self.frame_index = 0
                self.sprite = self.idle_frames[0]


    def fire(self):
        """Выполняет выстрел с использованием честного луча DDA"""
        if self.reloading or self.ammo <= 0:
            if self.ammo <= 0:
                self.sound_empty_ammo.play()
            return None

        self.reloading = True
        self.last_shot_time = pygame.time.get_ticks()
        
        # Переключаемся на непрерывную ленту выстрела
        self.current_frames = self.fire_frames
        self.frame_index = 0
        if self.fire_frames:
            self.sprite = self.fire_frames[0]  # Гарантированно берем ПЕРВЫЙ кадр выстрела (вспышку)

        self.sound.play()
        self.ammo -= 1

        # Запускаем луч выстрела (DDA)
        hit_x, hit_y, dist, side = self._get_hit_pos()

        # Спавним искры или кровь в точке попадания
        particle_color = (200, 0, 0) if side == -1 else (255, 200, 50)
        
        for _ in range(10):
            p_x = hit_x + uniform(-0.02, 0.02)
            p_y = hit_y + uniform(-0.02, 0.02)
            self.game.particles.append(
                Particle(self.game, (p_x, p_y), particle_color, uniform(0.001, 0.005))
            )

        return hit_x, hit_y, dist, side

    def _get_hit_pos(self):
        """Улучшенный DDA алгоритм: считает точку попадания пули с учетом стен и врагов"""
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
        dist = 0
        steps = 0
        max_steps = int(max_dist * 10)
        npc_hit = None

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

            # Проверка на врага
            for npc in self.game.npcs:
                if npc.alive and int(npc.x) == x_map and int(npc.y) == y_map:
                    npc_hit = npc
                    break
            
            if npc_hit:
                break

            # Проверка на стену через числовую матрицу
            if 0 <= x_map < self.game.map.numeric_grid.shape[1] and 0 <= y_map < self.game.map.numeric_grid.shape[0]:
                cell_value = self.game.map.numeric_grid[y_map, x_map]
                if cell_value > 0:
                    door_id = getattr(self.game.raycasting, 'door_id', -1)
                    if cell_value == door_id:
                        door_offset = self.game.map.door_states[y_map, x_map]
                        if door_offset < 0.8:
                            break
                    else:
                        break

        if side == 0:
            dist = side_dist_x - delta_dist_x
        else:
            dist = side_dist_y - delta_dist_y

        hit_x = ox + dist * cos_a
        hit_y = oy + dist * sin_a

        if npc_hit:
            npc_hit.get_damage(self.damage)
            return hit_x, hit_y, dist, -1

        return hit_x, hit_y, dist, side

    def draw(self):
        """Рисует оружие на экране с точным вычислением букв отдачи и покачиванием на основе движения"""
        self.update_animation()

        if self.sprite is None:
            return

        # Получаем чистый размер картинки pygame.Surface
        sw, sh = self.sprite.get_size()

        # 1. БАЗОВАЯ ПОЗИЦИЯ (Центр низа экрана с учетом сдвигов из config.txt)
        x = WIDTH // 2 - sw // 2 + self.offset_x
        y = HEIGHT - sh + self.offset_y

        # ============================================================
        # МЕХАНИКА ПОКАЧИВАНИЯ ОРУЖИЯ (WEAPON BOBBING НА ОСНОВЕ СКОРОСТИ)
        # ============================================================
        # Заставляем пушку качаться, только если игрок НЕ стреляет
        if not self.reloading:
            # Получаем текущее время
            time_ms = pygame.time.get_ticks()

            # Проверяем, двигается ли игрок на самом деле.
            # Если в вашем классе Player переменная скорости называется по-другому, 
            # мы используем универсальную проверку: нажимаются ли клавиши ходьбы.
            # Но чтобы это работало ВЕЗДЕ, мы вынесем опрос кнопок напрямую через pygame
            keys = pygame.key.get_pressed()
            is_moving = (keys[pygame.K_w] or keys[pygame.K_s] or keys[pygame.K_a] or keys[pygame.K_d] or
                         keys[pygame.K_UP] or keys[pygame.K_DOWN] or keys[pygame.K_LEFT] or keys[pygame.K_RIGHT])

            if is_moving:
                # Скорость покачивания (частота синусоиды)
                bob_speed = 0.001 
                
                # Амплитуда покачивания в пикселях (сделайте больше, если незаметно!)
                bob_amplitude_x = 25  # Сдвиг влево-вправо
                bob_amplitude_y = 15  # Сдвиг вверх-вниз

                # Математика классического Doom (рисует "восьмерку")
                bob_x = math.sin(time_ms * bob_speed) * bob_amplitude_x
                bob_y = abs(math.cos(time_ms * bob_speed * 2)) * bob_amplitude_y

                # Вносим коррективы в финальные координаты
                x += int(bob_x)
                y += int(bob_y)
        # ============================================================

        # 2. РАСЧЕТ ИНДИВИДУАЛЬНОЙ ОТДАЧИ КАДРОВ ПРИ ВЫСТРЕЛЕ
        if self.current_frames == self.fire_frames and self.frame_index < len(self.current_frames):
            letter = chr(66 + self.frame_index)
            if letter in self.frame_offsets:
                fx, fy = self.frame_offsets[letter]
                x += fx
                y += fy

        # Финальный вывод пушки на экран
        self.game.screen.blit(self.sprite, (x, y))

