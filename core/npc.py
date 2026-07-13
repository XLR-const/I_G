import os
import math
from random import uniform
import pygame
from setting import *
from config.game_data import NPC_CONFIG
from core.particle import Particle


class NPCAnimator:
    """Компонент для автоматической загрузки, расчета 8 ракурсов и эффектов NPC"""
    
    # Глобальный кэш, чтобы загружать 34 спрайта с диска только один раз для каждого типа врага
    SPRITE_CACHE = {}

    def __init__(self, npc):
        self.npc = npc
        self.game = npc.game
        
        # Контейнеры графики
        self.sprites = {}
        self.current_image = None
        self.sprite_width = 0
        self.sprite_height = 0
        self.sprite_ratio = 1.0
        self.move_direction = "front"
        
        # Таймеры для смены ног при ходьбе (анимация 1-2-3)
        self.walk_timer = 0
        self.walk_frame = 1  # Текущий кадр ноги: 1, 2 или 3
        
        # Таймеры для линейной анимации смерти
        self.death_timer = 0
        self.death_frame = 1
        self.max_death_frames = 0

        # Автоматически инициализируем сборку ресурсов из папки
        self._initialize_resources()

    def _load_and_scale_file(self, filename, scale, fallback_color=(0, 0, 0), fallback_sprite=None):
        """Безопасно загружает одиночный спрайт с диска в ОРИГИНАЛЬНОМ качестве"""
        path = os.path.join(self.npc.folder_path, filename)
        try:
            if os.path.exists(path):
                # Просто загружаем и оптимизируем, ничего не сжимая!
                return pygame.image.load(path).convert_alpha()
        except Exception as e:
            print(f"[Аниматор] Ошибка чтения файла {filename}: {e}")
            
        if fallback_sprite:
            return fallback_sprite
            
        surface = pygame.Surface((50, 80), pygame.SRCALPHA)
        surface.fill(fallback_color)
        return surface

    
    def _initialize_resources(self):
        """Проверяет кэш и собирает полную 8-ракурсную колоду спрайтов NPC в исходном качестве"""
        name = self.npc.name

        if name not in NPCAnimator.SPRITE_CACHE:
            cached_sprites = {}
            directions = ["front", "front_left", "front_right", "left", "right", "back", "back_left", "back_right"]

            # 1. Загружаем 32 спрайта ходьбы (MOVE, кадры 1, 2, 3, 4)
            for direction in directions:
                for frame in range(1, 5):
                    key = f"move_{direction}_{frame}"
                    filename = f"{name}_move_{direction}_{frame}.png"
                    cached_sprites[key] = self._load_and_scale_file(filename, 1.0, (150, 150, 150))

            # 2. Боевая стойка и Выстрел (ATTACK и SHOOT)
            fallback_idle = cached_sprites.get("move_front_1")
            cached_sprites["attack_front_0"] = self._load_and_scale_file(f"{name}_attack_front_0.png", 1.0, (200, 50, 50), fallback_idle)
            cached_sprites["shoot_front_0"] = self._load_and_scale_file(f"{name}_shoot_front_0.png", 1.0, (255, 200, 0), fallback_idle)

            # 3. Обычная смерть (DIE)
            die_frame = 1
            while True:
                filename = f"{name}_die_front_{die_frame}.png"
                path = os.path.join(self.npc.folder_path, filename)
                if os.path.exists(path):
                    cached_sprites[f"die_front_{die_frame}"] = self._load_and_scale_file(filename, 1.0, (50, 50, 50))
                    die_frame += 1
                else: break
            cached_sprites["max_death_frames"] = die_frame - 1

            # 4. Экстремальная смерть (X_DIE)
            x_die_frame = 1
            while True:
                filename = f"{name}_x_die_front_{x_die_frame}.png"
                path = os.path.join(self.npc.folder_path, filename)
                if os.path.exists(path):
                    cached_sprites[f"x_die_front_{x_die_frame}"] = self._load_and_scale_file(filename, 1.0, (100, 0, 0))
                    x_die_frame += 1
                else: break
            cached_sprites["max_x_death_frames"] = x_die_frame - 1
            
            NPCAnimator.SPRITE_CACHE[name] = cached_sprites

        # Привязываем ссылки
        self.sprites = NPCAnimator.SPRITE_CACHE[name]
        self.max_death_frames = self.sprites.get("max_death_frames", 0)
        self.current_image = self.sprites.get("move_front_1")
        self._update_sizes()



    def _update_sizes(self):
        """Синхронизирует текущие размеры текстуры для корректного Z-буфера рендерера"""
        if self.current_image:
            self.sprite_width, self.sprite_height = self.current_image.get_size()
            self.sprite_ratio = self.sprite_width / self.sprite_height

    def _calculate_direction(self):
        """Определяет, каким из 8 ракурсов NPC повернут к камере игрока"""
        # 1. Вычисляем вектор собственного движения/взгляда NPC
        dx_move = self.npc.x - self.npc.last_x
        dy_move = self.npc.y - self.npc.last_y

        if dx_move != 0 or dy_move != 0:
            npc_angle = math.atan2(dy_move, dx_move)
        else:
            # Если стоит, по умолчанию считает, что смотрит на игрока
            npc_angle = math.atan2(self.game.player.y - self.npc.y, self.game.player.x - self.npc.x)

        # 2. Вычисляем честный вектор от ИГРОКА к NPC (камера взгляда)
        view_angle = math.atan2(self.npc.y - self.game.player.y, self.npc.x - self.game.player.x)

        # Находим относительный угол между направлением взгляда игрока и лицом NPC
        rel_angle = view_angle - npc_angle
        rel_angle = math.atan2(math.sin(rel_angle), math.cos(rel_angle))
        
        # Переводим в градусы (0 - 360)
        rel_angle_deg = math.degrees(rel_angle) % 360

        # 3. Делим окружность на 8 секторов по 45 градусов вокруг центральных осей
        if 22.5 <= rel_angle_deg < 67.5:
            self.move_direction = "back_left"
        elif 67.5 <= rel_angle_deg < 112.5:
            self.move_direction = "left"
        elif 112.5 <= rel_angle_deg < 157.5:
            self.move_direction = "front_left"
        elif 157.5 <= rel_angle_deg < 202.5:
            self.move_direction = "front"
        elif 202.5 <= rel_angle_deg < 247.5:
            self.move_direction = "front_right"
        elif 247.5 <= rel_angle_deg < 292.5:
            self.move_direction = "right"
        elif 292.5 <= rel_angle_deg < 337.5:
            self.move_direction = "back_right"
        else:
            self.move_direction = "back"

        # Фиксируем текущие координаты NPC для вектора следующего кадра
        self.npc.last_x = self.npc.x
        self.npc.last_y = self.npc.y

    def update(self):
        """Основной цикл аниматора: поддерживает 4 кадра ходьбы и 2 вида смерти"""
        now = pygame.time.get_ticks()

        # 1. ОБРАБОТКА ПОКАДРОВОЙ СМЕРТИ (Обычная или X-Death)
        if self.npc.state == "DEAD":
            # Определяем, какую смерть играть (берём тип из параметров NPC)
            d_type = getattr(self.npc, 'death_type', 'die')
            max_frames = self.max_death_frames if d_type == 'die' else self.sprites.get("max_x_death_frames", 0)
            
            if self.death_frame < max_frames:
                if now - self.death_timer > self.npc.death_speed:
                    self.death_timer = now
                    self.death_frame += 1
            
            # Замораживаем последний кадр трупа на полу
            key = f"{d_type}_front_{self.death_frame}"
            self.current_image = self.sprites.get(key, self.current_image)
            self._update_sizes()
            return

        # 2. РАСЧЕТ РАКУРСА ДЛЯ ЖИВЫХ СОСТОЯНИЙ
        self._calculate_direction()

        # 3. АНИМАЦИЯ ХОДЬБЫ (Крутим ноги 1 -> 2 -> 3 -> 4 -> 1)
        if self.npc.state in ("PATROL", "CHASE"):
            if now - self.walk_timer > self.npc.animation_speed:
                self.walk_timer = now
                self.walk_frame += 1
                if self.walk_frame > 4:  # ТЕПЕРЬ ТУТ ЦИКЛ ДО 4 КАДРОВ!
                    self.walk_frame = 1
            
            key = f"move_{self.move_direction}_{self.walk_frame}"
            self.current_image = self.sprites.get(key)
        
        # 4. БОЕВАЯ СТОЙКА (ATTACK)
        elif self.npc.state == "ATTACK":
            self.walk_frame = 1
            self.current_image = self.sprites.get("attack_front_0", self.sprites.get("move_front_1"))
        
        # 5. СТРЕЛЬБА / ВСПЫШКА ОГНЯ (SHOOT)
        elif self.npc.state == "SHOOT":
            self.current_image = self.sprites.get("shoot_front_0", self.sprites.get("move_front_1"))
        
        # 6. ОЖИДАНИЕ (IDLE)
        else:
            self.walk_frame = 1
            # ИСПРАВЛЕНИЕ: Если NPC просто стоит, берём первый кадр ходьбы (нога выпрямлена)
            key = f"move_{self.move_direction}_1"
            self.current_image = self.sprites.get(key)

        self._update_sizes()


    def get_processed_image(self, proj_width, proj_height):
        """Накладывает маску HURT_FLASH и масштабирует спрайт под 3D-проекцию"""
        if not self.current_image:
            return None

        # Создаем чистую копию кадра
        img = self.current_image.copy()

        # Эффект получения урона (окрашивание в красный цвет)
        if self.npc.hurt_flash > 0:
            red_surface = pygame.Surface(img.get_size())
            red_surface.fill((255, 0, 0))
            img.blit(red_surface, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

        # Честно масштабируем под размеры экрана
        return pygame.transform.scale(img, (proj_width, proj_height))

import importlib.util
import types

class NPC:
    """Универсальный монолитный класс для всех NPC в игре (мозг и физика)"""

    def __init__(self, game, npc_type, pos=(8.5, 7.5)):
        self.game = game
        self.npc_type = npc_type

        # 1. Читаем базовые числовые параметры из глобального config/game_data.py
        config = NPC_CONFIG.get(npc_type, {})
        self.name = config.get('name', 'unknown')
        self.speed = config.get('speed', 0.3)
        self.hp = config.get('hp', 100)
        self.max_hp = self.hp
        self.damage = config.get('damage', 10)
        self.shoot_range = config.get('shoot_range', 5.0)
        self.shoot_delay = config.get('shoot_delay', 800)

        # Физические параметры хитбокса и активации
        self.radius = config.get('radius', 0.35)
        self.size = 0.3
        self.x, self.y = pos
        self.alive = True
        self.active = True
        self.activation_distance = 25

        # Локальные таймеры FSM-состояний
        self.state = "IDLE"
        self.state_timer = 0
        self.last_shot = 0
        self.shoot_flash = 0
        self.hurt_flash = 0

        # Вектор движения для 8-ракурсной математики
        self.last_x = self.x
        self.last_y = self.y

        # Настройки по умолчанию для текстового конфига папки
        self.scale = 0.1
        self.animation_speed = 150
        self.death_speed = 120

        # Ссылка на локальную папку ресурсов монстра
        self.folder_path = os.path.join('resources', 'npc', self.name)

        # Читаем локальный config.txt монстра, если он существует
        config_file = os.path.join(self.folder_path, 'config.txt')
        if os.path.exists(config_file):
            self._parse_local_txt_config(config_file)

        # 2. Подключаем локальные звуки из папки монстра
        sound_volume = config.get('sound_volume', 0.2)
        shot_sound_path = os.path.join(self.folder_path, 'shot.wav')
        if os.path.exists(shot_sound_path):
            self.shoot_sound = pygame.mixer.Sound(shot_sound_path)
        else:
            self.shoot_sound = pygame.mixer.Sound('resources/npc/npc_rifle.wav')
        self.shoot_sound.set_volume(sound_volume)

        # Пытаемся загрузить локальный звук смерти
        death_sound_path = os.path.join(self.folder_path, 'death.wav')
        if os.path.exists(death_sound_path):
            self.death_sound = pygame.mixer.Sound(death_sound_path)
        else:
            self.death_sound = None

        # 3. ПОДКЛЮЧАЕМ НАШ FSM-АНИМАТОР (Он заберет кэш и 34 спрайта)
        self.animator = NPCAnimator(self)

        # Прокидываем мостик совместимости свойств для глобального рендерера игры
        self.image = self.animator.current_image
        self.sprite_width = self.animator.sprite_width
        self.sprite_height = self.animator.sprite_height
        self.sprite_ratio = self.animator.sprite_ratio
        self.move_direction = self.animator.move_direction

        # Патрулирование и навигация A*
        self.waypoints = []
        self.current_waypoint = 0
        self.idle_duration = 500
        self.path = []
        self.last_path_update = 0
        self.current_target_index = 0
        self._last_los_check = 0
        self._cached_los = True

        # 4. МАГИЯ ДИНАМИЧЕСКИХ СКРИПТОВ ЛОГИКИ (logic.py)
        # Если в папке монстра лежит logic.py — намертво привязываем его функции к методам self!
        logic_file = os.path.join(self.folder_path, 'logic.py')
        if os.path.exists(logic_file):
            try:
                spec = importlib.util.spec_from_file_location("npc_custom_logic", logic_file)
                custom_logic = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(custom_logic)
                
                # Подменяем стандартный метод атаки на кастомный из logic.py с сохранением self
                if hasattr(custom_logic, 'perform_attack'):
                    self.perform_attack = types.MethodType(custom_logic.perform_attack, self)
                
                # Подменяем стандартный метод логики обновлений (если нужен уникальный ИИ)
                if hasattr(custom_logic, 'custom_update'):
                    self.custom_update = types.MethodType(custom_logic.custom_update, self)
            except Exception as e:
                print(f"[NPC] Ошибка загрузки скрипта логики для {self.name}: {e}")

    def _parse_local_txt_config(self, filepath):
        """Парсит локальный config.txt внутри папки NPC с железной защитой от комментариев"""
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'): 
                    continue
                
                if '=' in line:
                    key, val = line.split('=', 1)
                    key = key.strip()
                    val = val.strip()
                    
                    # ПРАВИЛЬНО: Отрезаем комментарий и берем первый элемент [0] строки
                    if '#' in val:
                        val = val.split('#', 1)[0].strip()

                    # Перевод в числа теперь отработает идеально
                    if key == 'scale': self.scale = float(val)
                    elif key == 'animation_speed': self.animation_speed = int(val)
                    elif key == 'death_speed': self.death_speed = int(val)
                    elif key == 'radius': self.radius = float(val)
                    elif key == 'shoot_range': self.shoot_range = float(val)
                    elif key == 'shoot_delay': self.shoot_delay = int(val)




    def get_damage(self, damage):
        """Вызывается при попадании пули игрока в NPC"""
        if not self.alive:
            return

        self.hp -= damage
        self.hurt_flash = 8
        
        # Если монстр еще жив, переводим в стейт ступора от боли
        if self.hp > 0:
            self.state = "HURT"
            self.state_timer = pygame.time.get_ticks() + 300
        else:
            self.alive = False
            self.state = "DEAD"
            self.game.level_manager.total_kills += 1
            
            # НОВОЕ: Если урон избыточен (здоровье ушло глубоко в минус),
            # включаем экстремальную смерть 'x_die', иначе обычную 'die'
            if self.hp <= -30:
                self.death_type = "x_die"
            else:
                self.death_type = "die"
            
            if self.death_sound:
                self.death_sound.play()

            # Для X-Death спавним в два раза больше брызг крови!
            p_count = 40 if self.death_type == "x_die" else 20
            for _ in range(p_count):
                self.game.particles.append(Particle(
                    self.game,
                    (self.x + uniform(-0.2, 0.2), self.y + uniform(-0.2, 0.2)),
                    (150, 0, 0), uniform(0.002, 0.006)
                ))


    def perform_attack(self):
        """Стандартный метод атаки по умолчанию (стрельба пулями)"""
        now = pygame.time.get_ticks()
        if now - self.last_shot >= self.shoot_delay:
            self.last_shot = now
            
            # Включаем новое состояние вспышки выстрела SHOOT
            self.state = "SHOOT"
            self.shoot_flash = 4  # Длительность отображения кадра со вспышкой
            self.shoot_sound.play()
            
            # Наносим урон игроку
            self.game.player.take_damage(self.damage)

            # Спавним искры выстрела из ствола
            for _ in range(8):
                self.game.particles.append(Particle(
                    self.game,
                    (self.x + uniform(-0.1, 0.1), self.y + uniform(-0.1, 0.1)),
                    (255, 200, 50),
                    uniform(0.003, 0.005)
                ))

    def update(self):
        """Кадровое обновление NPC"""
        # Если монстр умер, мы НЕ делаем return! Мы продолжаем обновлять 
        # аниматор, чтобы труп линейно упал на пол и остался лежать вечно
        if self.state == "DEAD":
            self.animator.update()
            self.image = self.animator.current_image
            self.sprite_width = self.animator.sprite_width
            self.sprite_height = self.animator.sprite_height
            self.sprite_ratio = self.animator.sprite_ratio
            return

        # Отсечка по глобальной дистанции активации ИИ
        dist = math.hypot(self.game.player.x - self.x, self.game.player.y - self.y)
        if dist > self.activation_distance:
            return

        dt = self.game.delta_time
        if dt > 0.033:
            dt = 0.033

        # Уменьшаем таймеры эффектов
        if self.hurt_flash > 0: self.hurt_flash -= 1
        if self.shoot_flash > 0: self.shoot_flash -= 1

        # ЕСЛИ ЕСТЬ КАСТОМНАЯ СУПЕР-ЛОГИКА ИИ ИЗ СКРИПТА logic.py — ВЫПОЛНЯЕМ ЕЁ
        if hasattr(self, 'custom_update'):
            self.custom_update(dt)
        else:
            # Иначе крутим стандартный конечный автомат поведения
            self.update_state(dt)

        # Синхронизируем состояние с 8-ракурсным аниматором
        self.animator.update()

        # Транслируем актуальные размеры и картинку наружу для рендерера игры
        self.image = self.animator.current_image
        self.sprite_width = self.animator.sprite_width
        self.sprite_height = self.animator.sprite_height
        self.sprite_ratio = self.animator.sprite_ratio
        self.move_direction = self.animator.move_direction

    def has_line_of_sight(self):
        """Проверяет, видит ли NPC игрока по прямой линии (с кэшированием)"""
        now = pygame.time.get_ticks()
        if now - self._last_los_check < 150:
            return self._cached_los
        self._last_los_check = now

        x1, y1 = int(self.x), int(self.y)
        x2, y2 = int(self.game.player.x), int(self.game.player.y)

        if math.hypot(x2 - x1, y2 - y1) > self.activation_distance:
            self._cached_los = False
            return False

        dx, dy = abs(x2 - x1), abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy

        x, y = x1, y1
        while (x, y) != (x2, y2):
            if self.game.map.is_wall(x, y):
                self._cached_los = False
                return False
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

        self._cached_los = True
        return True

    def try_move(self, dx, dy):
        """Перемещает NPC с мягким скольжением вдоль стен на основе радиуса коллизии"""
        if self.state == "DEAD":
            return
        new_x, new_y = self.x + dx, self.y + dy

        for offset_x, offset_y in [(-self.radius, self.radius), (self.radius, self.radius),
                                   (-self.radius, -self.radius), (self.radius, -self.radius)]:
            if self.game.map.is_wall(int(new_x + offset_x), int(self.y + offset_y)):
                new_x = self.x
            if self.game.map.is_wall(int(self.x + offset_x), int(new_y + offset_y)):
                new_y = self.y

        self.x, self.y = new_x, new_y

    def generate_waypoints_auto(self, num_points=4):
        """Автоматически находит свободные клетки вокруг NPC для патрулирования"""
        waypoints = []
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]

        for dx, dy in directions:
            for dist in range(2, 6):
                check_x = int(self.x) + dx * dist
                check_y = int(self.y) + dy * dist
                if 0 <= check_x < self.game.level_manager.map.width and 0 <= check_y < self.game.level_manager.map.height:
                    try:
                        if not self.game.level_manager.map.is_wall(check_x, check_y):
                            waypoints.append((check_x + 0.5, check_y + 0.5))
                            break
                    except:
                        pass

        max_attempts, attempts = 100, 0
        while len(waypoints) < num_points and attempts < max_attempts:
            attempts += 1
            rand_x, rand_y = self.x + uniform(-3, 3), self.y + uniform(-3, 3)
            if 1 < rand_x < self.game.level_manager.map.width - 1 and 1 < rand_y < self.game.level_manager.map.height - 1:
                try:
                    if not self.game.level_manager.map.is_wall(int(rand_x), int(rand_y)):
                        waypoints.append((rand_x, rand_y))
                except:
                    pass

        self.waypoints = waypoints[:num_points]

    def update_state(self, dt):
        """Конечный автомат поведения ИИ"""
        if self.hp <= 0:
            if self.state != "DEAD":
                self.state = "DEAD"
                self.alive = False
            return

        dist_to_player = math.hypot(self.x - self.game.player.x, self.y - self.game.player.y)
        can_see = self.has_line_of_sight()

        # 1. ОБРАБОТКА ВЫХОДА ИЗ СТУПОРА ОТ БОЛИ
        if self.state == "HURT":
            if pygame.time.get_ticks() > self.state_timer:
                self.state = "CHASE" if can_see else ("PATROL" if self.waypoints else "IDLE")
            return

        # 2. ОБРАБОТКА МГНОВЕННОГО ВЫХОДА ИЗ СОСТОЯНИЯ ВЫСТРЕЛА
        if self.state == "SHOOT":
            # После кадра вспышки сразу возвращаемся целиться в ATTACK
            if self.shoot_flash <= 0:
                self.state = "ATTACK"
            return

        # 3. АНАЛИЗ ВИДИМОСТИ ИГРОКА ДЛЯ ЖИВЫХ СОСТОЯНИЙ
        if can_see:
            if dist_to_player <= self.shoot_range:
                self.state = "ATTACK"
            else:
                if self.state != "CHASE":
                    self.state = "CHASE"
        else:
            # Если потеряли игрока из виду — возвращаемся к мирным делам
            if self.state in ("ATTACK", "CHASE"):
                if self.waypoints:
                    self.state = "PATROL"
                    self.current_waypoint = 0
                else:
                    self.state = "IDLE"
                    self.state_timer = pygame.time.get_ticks() + self.idle_duration

        # 4. ЛОГИКА СОСТОЯНИЯ ОЖИДАНИЯ (IDLE)
        if self.state == "IDLE":
            if self.state_timer and pygame.time.get_ticks() > self.state_timer:
                if self.waypoints:
                    self.state = "PATROL"
                    self.current_waypoint = 0

        # 5. ЛОГИКА ПАТРУЛИРОВАНИЯ (PATROL)
        elif self.state == "PATROL":
            if not self.waypoints:
                self.state = "IDLE"
                return

            target_x, target_y = self.waypoints[self.current_waypoint]
            dx, dy = target_x - self.x, target_y - self.y
            dist = math.hypot(dx, dy)

            if dist < 0.2:
                self.current_waypoint = (self.current_waypoint + 1) % len(self.waypoints)
            elif dist > 0.01:
                self.try_move((dx / dist) * self.speed * dt, (dy / dist) * self.speed * dt)

        # 6. ЛОГИКА ПРЕСЛЕДОВАНИЯ (CHASE)
        elif self.state == "CHASE":
            now = pygame.time.get_ticks()
            # Обновляем A* путь каждые 200 миллисекунд
            if now - self.last_path_update >= 200:
                self.last_path_update = now
                path = self.game.pathfinder.a_star((self.x, self.y), (self.game.player.x, self.game.player.y))
                if path:
                    self.path = [(x + 0.5, y + 0.5) for x, y in path]
                    self.current_target_index = 0

            # Идем строго по точкам A* пути
            if self.path and self.current_target_index < len(self.path):
                target_x, target_y = self.path[self.current_target_index]
                dx, dy = target_x - self.x, target_y - self.y
                dist = math.hypot(dx, dy)

                if dist < 0.6:
                    self.current_target_index += 1
                elif dist > 0.01:
                    self.try_move((dx / dist) * self.speed * dt, (dy / dist) * self.speed * dt)
            else:
                # Если путь потерян, идем напрямую на игрока
                dx, dy = self.game.player.x - self.x, self.game.player.y - self.y
                dist = math.hypot(dx, dy)
                if dist > 0.01:
                    self.try_move((dx / dist) * self.speed * dt, (dy / dist) * self.speed * dt)

            if dist_to_player <= self.shoot_range and self.has_line_of_sight():
                self.state = "ATTACK"

        # 7. ЛОГИКА БОЕВОЙ СТОЙКИ ПРИЦЕЛИВАНИЯ (ATTACK)
        elif self.state == "ATTACK":
            if self.has_line_of_sight():
                # Вызываем атаку. Благодаря types.MethodType здесь автоматически 
                # сработает либо perform_attack, либо кастомная атака из logic.py!
                self.perform_attack()
            
            if dist_to_player > self.shoot_range or not self.has_line_of_sight():
                self.state = "CHASE"

    def draw(self):
        """Отрисовывает 8-ракурсный спрайт NPC в 3D мире с учетом Z-буфера стен"""
        # Труп продолжает рисоваться на полу (метод не отсекается по alive)
        dx = self.x - self.game.player.x
        dy = self.y - self.game.player.y
        dist = math.hypot(dx, dy)
        
        # Защита от деления на ноль при подходе в упор
        if dist < 0.2: 
            return

        # Находим угол между игроком и NPC
        theta = math.atan2(dy, dx)
        delta = theta - self.game.player.angle
        delta = (delta + math.pi) % math.tau - math.pi
        
        # Отсекаем объекты, которые физически находятся за пределами FOV камеры
        if abs(delta) > HALF_FOV: 
            return

        # Плоская дистанция (защита от эффекта "рыбьего глаза")
        dist_flat = dist * math.cos(delta)
        if dist_flat < 0.2: 
            return

        # Вычисляем высоту и ширину 3D проекции на основе размеров спрайта
        proj_height = int(SCREEN_DIST / dist_flat)
        proj_width = int(proj_height * self.sprite_ratio)

        # Ограничиваем максимальный размер вблизи для оптимизации FPS
        if proj_height > HEIGHT * 2:
            proj_height = HEIGHT * 2
            proj_width = int(proj_height * self.sprite_ratio)

        # Запрашиваем у аниматора готовую, отмасштабированную картинку нужного ракурса и цвета
        img = self.animator.get_processed_image(proj_width, proj_height)
        if img is None: 
            return

        # Находим координаты центра и левой границы спрайта на экране
        center_x = (HALF_NUM_RAYS + delta / DELTA_ANGLE) * SCALE
        start_x = int(center_x - proj_width // 2)

        # Пополосный рендеринг спрайта с шагом SCALE пикселей
        for x in range(start_x, start_x + proj_width, SCALE):
            ray_idx = int(x // SCALE)
            
            # Проверяем, попадает ли вертикальная полоса в границы экрана
            if 0 <= ray_idx < NUM_RAYS:
                # Сверяемся с Z-буфером: если монстр ближе, чем стена за ним — рисуем полосу
                if dist_flat < self.game.raycasting.z_buffer[ray_idx]:
                    sub_x = int(x - start_x)
                    
                    if 0 <= sub_x < proj_width:
                        # Блитим (рисуем) вырезанную полоску спрайта на экран
                        self.game.screen.blit(
                            img, 
                            (x, HALF_HEIGHT - proj_height // 2), 
                            (sub_x, 0, SCALE, proj_height)
                        )

