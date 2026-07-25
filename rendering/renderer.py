import pygame
import math
from setting import *
import os

class Renderer:
    """Класс для отрисовки фона, интерфейса и компаса

    Attributes:
        game: Объект игры
        ceiling_color: Цвет потолка
        floor_color: Цвет пола
        ceiling_texture: Текстура потолка
        floor_texture: Текстура пола
        nice_hp: Иконка здоровья (>80)
        average_hp: Иконка здоровья (50-80)
        bad_hp: Иконка здоровья (<50)
        hp_positions: Позиции иконок здоровья
    """

    def __init__(self, game):
        """Инициализирует рендерер

        Args:
            game: Объект игры
        """
        self.game = game
        self.ceiling_color = (50, 50, 80)
        self.floor_color = (30, 30, 40)
        self.ceiling_texture = None
        self.floor_texture = None
        self.notifications = []
        self.font_weapon = pygame.font.Font('resources/fonts/Fy.ttf', 48)
        self.font_ammo = pygame.font.Font('resources/fonts/Fy.ttf', 50)


        try:
            self.nice_hp = pygame.image.load('resources/player/nice_hp.png').convert_alpha()
            self.bad_hp = pygame.image.load('resources/player/bad_hp.png').convert_alpha()
            self.average_hp = pygame.image.load('resources/player/average_hp.png').convert_alpha()
            self.nice_hp = pygame.transform.scale(self.nice_hp, (CELL_W * 2, CELL_H * 2))
            self.bad_hp = pygame.transform.scale(self.bad_hp, (CELL_W * 2, CELL_H * 2))
            self.average_hp = pygame.transform.scale(self.average_hp, (CELL_W * 2, CELL_H * 2))
            self.hp_positions = tuple(grid_to_pixel(col, row) for col, row in ((1, 14), (3, 14), (5, 14)))
        except Exception:
            self.hp_positions = tuple(grid_to_pixel(col, row) for col, row in ((1, 14), (3, 14), (5, 14)))
        
        # --- ОПТИМИЗАЦИЯ ЗАГРУЗКИ КЛЮЧ-КАРТ ---
        self.key_sprites = {}
        key_types = ['red', 'blue', 'yellow']
        
        for k_color in key_types:
            path = f'resources/items/key_{k_color}.png'
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    # Масштабируем под размер ячейки сетки (CELL_W x CELL_H)
                    # Если ключи покажутся мелкими, можно сделать (int(CELL_W * 1.5), int(CELL_H * 1.5))
                    self.key_sprites[k_color] = pygame.transform.scale(img, (CELL_W, CELL_H))
                except Exception as e:
                    print(f"[Renderer] Ошибка загрузки ключа {k_color}: {e}")


    def set_background(self, background_data):
        """Устанавливает фон для текущего уровня из JSON

        Args:
            background_data: Словарь с параметрами фона
        """
        ceiling_texture_path = background_data.get('ceiling_texture')
        if ceiling_texture_path:
            try:
                self.ceiling_texture = pygame.image.load(ceiling_texture_path).convert()
                self.ceiling_texture = pygame.transform.scale(self.ceiling_texture, (WIDTH, HALF_HEIGHT))
            except Exception:
                self.ceiling_texture = None
        else:
            self.ceiling_texture = None

        floor_texture_path = background_data.get('floor_texture')
        if floor_texture_path:
            try:
                self.floor_texture = pygame.image.load(floor_texture_path).convert()
                self.floor_texture = pygame.transform.scale(self.floor_texture, (WIDTH, HALF_HEIGHT))
            except Exception:
                self.floor_texture = None
        else:
            self.floor_texture = None

        self.ceiling_color = background_data.get('ceiling_color', WALL_COLORS.get('C', (150, 200, 200)))
        self.floor_color = background_data.get('floor_color', (40, 40, 40))

    def load_level_textures(self):
        """Загружает текстуры пола и потолка для текущего уровня"""
        level_num = self.game.current_level
        textures = self.level_textures.get(level_num, self.level_textures[1])

        if textures['ceiling']:
            try:
                self.ceiling_texture = pygame.image.load(textures['ceiling']).convert()
                self.ceiling_texture = pygame.transform.scale(self.ceiling_texture, (WIDTH, HALF_HEIGHT))
            except Exception:
                self.ceiling_texture = None
        else:
            self.ceiling_texture = None

        if textures['floor']:
            try:
                self.floor_texture = pygame.image.load(textures['floor']).convert()
                self.floor_texture = pygame.transform.scale(self.floor_texture, (WIDTH, HALF_HEIGHT))
            except Exception:
                self.floor_texture = None
        else:
            self.floor_texture = None

        self.ceiling_color = textures['ceiling_color']
        self.floor_color = textures['floor_color']

    def draw_background(self):
        """Рисует потолок и пол с защитой от микрощелей на горизонте"""
        # 1. Потолок / Небо (рисуем на 5 пикселей НИЖЕ середины экрана)
        if self.ceiling_texture:
            self.game.screen.blit(self.ceiling_texture, (0, 0))
        else:
            pygame.draw.rect(self.game.screen, self.ceiling_color, (0, 0, WIDTH, HALF_HEIGHT + 5))

        # 2. Пол (рисуем на 5 пикселей ВЫШЕ середины экрана, чтобы перекрыть щели)
        if self.floor_texture:
            # Смещаем координату Y на 5 пикселей вверх
            self.game.screen.blit(self.floor_texture, (0, HALF_HEIGHT - 5))
        else:
            # Начинаем прямоугольник чуть выше (HALF_HEIGHT - 5), а высоту увеличиваем на 5
            pygame.draw.rect(self.game.screen, self.floor_color, (0, HALF_HEIGHT - 5, WIDTH, HALF_HEIGHT + 5))


    def draw_fps(self):
        """Рисует счётчик FPS"""
        x, y = grid_to_pixel(0, 0)
        fps = str(int(self.game.clock.get_fps()))
        fps_render = self.game.font.render(fps, True, (0, 255, 0))
        self.game.screen.blit(fps_render, (x, y))

    def draw_crosshair(self):
        """Рисует прицел"""
        pygame.draw.circle(self.game.screen, 'red', (WIDTH // 2, HEIGHT // 2), 4, 1)

    def draw_compass(self):
        """Рисует компас в Sci-Fi стиле с полигональной скошенной рамкой под стиль HUD"""
        goal = self.game.map.exit_pos
        if goal is None:
            return

        player = (self.game.player.x, self.game.player.y)
        d_x, d_y = goal[0] - player[0], goal[1] - player[1]
        angle_to_goal = math.degrees(math.atan2(d_y, d_x))

        # Исходные клетки из твоего конфига
        compass_col = 11
        compass_row = 0
        compass_width = 10
        compass_height = 1

        # Базовые пиксельные границы ячеек сетки
        x_start = compass_col * CELL_W
        y_start = compass_row * CELL_H
        w_total = compass_width * CELL_W
        h_total = int(compass_height * CELL_H * 0.6)
        x_end = x_start + w_total
        y_end = y_start + h_total

        # ==================================================================
        # 🔥 НОВАЯ Sci-Fi ПОЛИГОНАЛЬНАЯ РАМКА КОМПАСА (В СТИЛЕ РОМБОВ HUD)
        # ==================================================================
        # Делаем стильные скошенные углы по бокам, чтобы рамка выглядела агрессивно
        bevel = 15  # Размер скоса углов в пикселях
        compass_points = [
            (x_start + bevel, y_start),     # Верхний левый после скоса
            (x_end - bevel,   y_start),     # Верхний правый до скоса
            (x_end,           y_start + bevel), # Переход на боковину справа
            (x_end,           y_end),       # Нижний правый
            (x_start,         y_end),       # Нижний левый
            (x_start,         y_start + bevel)  # Переход на боковину слева
        ]
        
        # Рисуем полупрозрачную темную подложку компаса
        bg_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.polygon(bg_surface, (15, 20, 25, 160), compass_points)
        self.game.screen.blit(bg_surface, (0, 0))

        # Рисуем контур рамки фирменным неоново-бирюзовым цветом (0, 180, 255)
        pygame.draw.polygon(self.game.screen, (0, 180, 255), compass_points, 2)

        # Вычисляем математический центр панели для вывода делений
        center_x = x_start + w_total // 2
        center_y = y_start + h_total // 2
        player_angle_deg = math.degrees(self.game.player.angle)

        directions = [
            ('N', 90), ('NE', 45), ('E', 0), ('SE', 315),
            ('S', 270), ('SW', 225), ('W', 180), ('NW', 135),
            ('<!>', angle_to_goal)
        ]

        visible_range = 120
        pixels_per_degree = w_total / visible_range

        # Отрисовка направлений и меток
        for name, angle in directions:
            diff = angle - player_angle_deg
            while diff > 180:
                diff -= 360
            while diff < -180:
                diff += 360

            if abs(diff) <= visible_range // 2:
                x = center_x + diff * pixels_per_degree

                # Защита текста от вылета за скошенные края рамки
                if x_start + 10 <= x <= x_end - 10:
                    if len(name) == 1 and name != '<!>':
                        font_size = int(CELL_H * 0.45)
                        color = (255, 255, 255)
                    elif name == '<!>':
                        font_size = int(CELL_H * 0.95)
                        color = (0, 255, 255) # Метка выхода горит в цвет рамки
                    else:
                        font_size = int(CELL_H * 0.3)
                        color = (140, 160, 180)

                    font = pygame.font.Font(None, font_size)
                    text = font.render(name, True, color)
                    text_rect = text.get_rect(center=(x, center_y))
                    self.game.screen.blit(text, text_rect)

        # Главная стрелка направления (Стильный неоново-оранжевый треугольник)
        triangle_points = [
            (center_x,     center_y - 12),
            (center_x - 7, center_y + 6),
            (center_x + 7, center_y + 6)
        ]
        pygame.draw.polygon(self.game.screen, (255, 80, 0), triangle_points)

        # Боковые неоновые насечки шкалы
        for offset in [-20, 20]:
            pygame.draw.line(self.game.screen, (0, 150, 220),
                             (center_x + offset, center_y - 8),
                             (center_x + offset, center_y + 8), 2)


    def draw_health_sprite(self, center_x, center_y):
        """Рисует иконку здоровья строго по переданным координатам центра ячейки сетки"""
        hp = self.game.player.hp

        if hp >= 80:
            sprite = self.nice_hp
        elif 50 <= hp < 80:
            sprite = self.average_hp
        else:
            sprite = self.bad_hp

        # Идеальное центрирование спрайта головы на сетке
        fw, fh = sprite.get_size()
        pos = (center_x - fw // 2, center_y - fh // 2)

        try:
            self.game.screen.blit(sprite, pos)
        except Exception:
            pass


    def draw_interface(self):
        """Рисует Sci-Fi HUD в левом углу: неоновые цвета, вертикальное заполнение, привязка к сетке"""
        hp = max(0, min(100, self.game.player.hp))
        armor = max(0, min(100, self.game.player.armor))
        
        if self.game.weapon:
            current_weapon = self.game.weapon.name
            ammo = self.game.weapon.ammo
        else:
            current_weapon = "Fists"
            ammo = 0
        font_path = 'resources/fonts/Fy.ttf'

        # ==================================================================
        # 1. СЕТОЧНЫЕ КООРДИНАТЫ ДЛЯ ЦЕНТРАЛЬНОГО УЗЛА (ГОЛОВЫ)
        # ==================================================================
        cx, cy = grid_to_pixel(5, 15, 'center')
        cy += 8  # Опускаем панель ближе к нижнему краю экрана

        # ==================================================================
        # 2. МАТЕМАТИКА ЛЕВОЙ СТРЕЛКИ ЗДОРОВЬЯ (НЕОНОВОЕ КРЫЛО HP)
        # ==================================================================
        raw_hp_top_in  = grid_to_pixel(4, 14, 'midbottom')
        raw_hp_top_out = grid_to_pixel(3, 14, 'midbottom')
        raw_hp_mid_out = grid_to_pixel(1, 15, 'midright')
        raw_hp_bot_out = grid_to_pixel(3, 16, 'midtop')
        raw_hp_bot_in  = grid_to_pixel(4, 16, 'midtop')
        raw_hp_mid_in  = grid_to_pixel(2, 15, 'midright')

        p_hp_top_in  = (raw_hp_top_in[0],  raw_hp_top_in[1] - 10 + 8)
        p_hp_top_out = (raw_hp_top_out[0], raw_hp_top_out[1] - 10 + 8)
        p_hp_mid_out = (raw_hp_mid_out[0], cy)
        p_hp_bot_out = (raw_hp_bot_out[0], raw_hp_bot_out[1] + 10 + 8)
        p_hp_bot_in  = (raw_hp_bot_in[0],  raw_hp_bot_in[1] + 10 + 8)
        p_hp_mid_in  = (raw_hp_mid_in[0],  cy)

        bg_hp_points = [p_hp_top_in, p_hp_top_out, p_hp_mid_out, p_hp_bot_out, p_hp_bot_in, p_hp_mid_in]
        # Глубокий темный фон для контраста с неоном
        pygame.draw.polygon(self.game.screen, (24, 14, 16), bg_hp_points)
        
        if hp > 0:
            hp_ratio = hp / 100.0
            # 🔥 НОВЫЕ НЕОНОВЫЕ ЦВЕТА ЗДОРОВЬЯ
            # Кислотно-зеленый при нормальном ХП, неоново-алый при критическом
            hp_color = (255, 16, 92) if hp <= 35 else (0, 240, 160)
            
            total_height = p_hp_bot_in[1] - p_hp_top_in[1]
            cutoff_y = p_hp_bot_in[1] - int(total_height * hp_ratio)
            
            fill_hp_points = []
            for pt in bg_hp_points:
                if pt[1] >= cutoff_y:
                    fill_hp_points.append(pt)
                else:
                    fill_hp_points.append((pt[0], cutoff_y))
            
            pygame.draw.polygon(self.game.screen, hp_color, fill_hp_points)

        # ==================================================================
        # 3. МАТЕМАТИКА ПРАВОЙ СТРЕЛКИ БРОНИ (НЕОНОВОЕ КРЫЛО AP)
        # ==================================================================
        raw_ap_top_in  = grid_to_pixel(6, 14, 'midbottom')
        raw_ap_top_out = grid_to_pixel(7, 14, 'midbottom')
        raw_ap_mid_out = grid_to_pixel(9, 15, 'midleft')
        raw_ap_bot_out = grid_to_pixel(7, 16, 'midtop')
        raw_ap_bot_in  = grid_to_pixel(6, 16, 'midtop')
        raw_ap_mid_in  = grid_to_pixel(8, 15, 'midleft')

        p_ap_top_in  = (raw_ap_top_in[0],  raw_ap_top_in[1] - 10 + 8)
        p_ap_top_out = (raw_ap_top_out[0], raw_ap_top_out[1] - 10 + 8)
        p_ap_mid_out = (raw_ap_mid_out[0], cy)
        p_ap_bot_out = (raw_ap_bot_out[0], raw_ap_bot_out[1] + 10 + 8)
        p_ap_bot_in  = (raw_ap_bot_in[0],  raw_ap_bot_in[1] + 10 + 8)
        p_ap_mid_in  = (raw_ap_mid_in[0],  cy)

        bg_armor_points = [p_ap_top_in, p_ap_top_out, p_ap_mid_out, p_ap_bot_out, p_ap_bot_in, p_ap_mid_in]
        # Глубокий темно-синий фон подложки
        pygame.draw.polygon(self.game.screen, (12, 16, 26), bg_armor_points)
        
        if armor > 0:
            armor_ratio = armor / 100.0
            # 🔥 НОВЫЙ НЕОНОВЫЙ ЦВЕТ БРОНИ
            # Электрический бирюзовый/циан в тон контуру компаса
            armor_color = (0, 140, 255)
            
            total_height = p_ap_bot_in[1] - p_ap_top_in[1]
            cutoff_y = p_ap_bot_in[1] - int(total_height * armor_ratio)
            
            fill_armor_points = []
            for pt in bg_armor_points:
                if pt[1] >= cutoff_y:
                    fill_armor_points.append(pt)
                else:
                    fill_armor_points.append((pt[0], cutoff_y))
            
            pygame.draw.polygon(self.game.screen, armor_color, fill_armor_points)

        # Отрисовка головы игрока
        self.draw_health_sprite(cx, cy)

        # ==================================================================
        # 4. ВЫВОД ТЕКСТА ОРУЖИЯ И ПАТРОНОВ
        # ==================================================================
        weapon_name_pos = grid_to_pixel(25, 15)
        weapon_ammo_pos = grid_to_pixel(25, 16)

        font = pygame.font.Font(font_path, 48)
        text_weapon = font.render(current_weapon, True, (255, 255, 255))
        font = pygame.font.Font(font_path, 50)
        # Подкрасим текст патронов в легкий неоново-пурпурный оттенок
        text_ammo = font.render(str(ammo), True, (0, 240, 255))

        self.game.screen.blit(text_weapon, weapon_name_pos)
        self.game.screen.blit(text_ammo, weapon_ammo_pos)
        
        # ==================================================================
        # 5. ОТРИСОВКА КЛЮЧ-КАРТ ИЗ ИНВЕНТАРЯ ИГРОКА (СПРАВА НА СЕТКЕ)
        # ==================================================================
        # Начальная стартовая колонка для первого найденного ключа
        start_key_col = 4
        key_row = 17
        
        # Проверяем, что инвентарь ключей существует и не пуст
        if hasattr(self.game.player, 'keys_inventory') and self.game.player.keys_inventory:
            for key_obj in self.game.player.keys_inventory:
                # Определяем цвет ключа. Если в списке лежат объекты классов, берем их свойство (например, .color или .type)
                # Если в инвентаре лежат просто строки 'red', 'blue', то используем саму переменную.
                if isinstance(key_obj, str):
                    key_color = key_obj.strip().lower()
                else:
                    # Модифицируйте под ваше свойство в классе ключа (например, key_obj.color или key_obj.type)
                    key_color = getattr(key_obj, 'type', getattr(key_obj, 'color', 'red')).strip().lower()
                
                # Достаем заранее загруженный спрайт ключ-карты
                key_img = self.key_sprites.get(key_color)
                
                if key_img:
                    # Получаем пиксельную позицию для текущей колонки
                    key_pos = grid_to_pixel(start_key_col, key_row, 'topleft')
                    self.game.screen.blit(key_img, key_pos)
                    
                    # Сдвигаем следующую ключ-карту на 1 колонку вправо, чтобы они выстраивались в ряд
                    start_key_col += 1

        self.draw_compass()


        #self.draw_line_of_cells()

    def draw_line_of_cells(self):
        """Рисует линии сетки (для отладки)"""
        thickness = 2
        COLOR_CELL = (100, 100, 100)
        COLOR_CENTER = (255, 100, 0)

        for i in range(GRID_W + 1):
            x = i * CELL_W
            pygame.draw.line(self.game.screen, COLOR_CELL, (x, 0), (x, HEIGHT), 1)
            if i < GRID_W:
                font = pygame.font.Font(None, int(CELL_H * 0.3))
                text = font.render(str(i), True, (50, 50, 50))
                self.game.screen.blit(text, (x + 5, 5))

        for i in range(GRID_H + 1):
            y = i * CELL_H
            pygame.draw.line(self.game.screen, COLOR_CELL, (0, y), (WIDTH, y), 1)
            if i < GRID_H:
                font = pygame.font.Font(None, int(CELL_H * 0.3))
                text = font.render(str(i), True, (50, 50, 50))
                self.game.screen.blit(text, (5, y + 5))

        center_x = WIDTH // 2
        center_y = HEIGHT // 2
        pygame.draw.line(self.game.screen, COLOR_CENTER,
                         (center_x, center_y - CELL_H * 0.5),
                         (center_x, center_y + CELL_H * 0.5), thickness)
        pygame.draw.line(self.game.screen, COLOR_CENTER,
                         (center_x - CELL_W * 0.5, center_y),
                         (center_x + CELL_W * 0.5, center_y), thickness)

    def draw_fog_filter(self):
        """Накладывает лёгкий туман на весь экран (только для уровня 2)"""
        if self.game.current_level == 2:
            fog = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            fog.fill((180, 190, 170, 40))
            self.game.screen.blit(fog, (0, 0))

    def draw_npc_health(self, npc):
        """Рисует полоску HP над NPC"""
        if not npc.alive:
            return
        
        # Теперь эта проверка сработает корректно
        if not hasattr(npc, 'max_hp') or npc.max_hp <= 0:
            return
        
        dx = npc.x - self.game.player.x
        dy = npc.y - self.game.player.y
        dist = math.hypot(dx, dy)
        
        if dist > 25:
            return
        
        theta = math.atan2(dy, dx)
        delta = theta - self.game.player.angle
        delta = (delta + math.pi) % math.tau - math.pi
        
        if abs(delta) > HALF_FOV:
            return
        
        dist_flat = dist * math.cos(delta)
        if dist_flat < 0.2:
            return
        
        # ПОЛУЧАЕМ ИНДЕКС ЛУЧА ДЛЯ ПРОВЕРКИ Z-БУФЕРА
        center_x = (HALF_NUM_RAYS + delta / DELTA_ANGLE) * SCALE
        ray_idx = int(center_x // SCALE)
        
        # Проверяем, не скрыт ли центр NPC стеной
        if 0 <= ray_idx < NUM_RAYS:
            if dist_flat > self.game.raycasting.z_buffer[ray_idx]:
                return  # NPC за стеной, полоску рисовать не нужно
        
        proj_height = int(SCREEN_DIST / dist_flat)
        y_pos = int(HALF_HEIGHT - proj_height // 2 - 20)
        
        # Ширина полоски зависит от размера NPC
        bar_width = max(30, proj_height // 2)
        if bar_width > 80:
            bar_width = 80
        bar_height = 4
        
        bar_x = int(center_x - bar_width // 2)
        bar_y = y_pos
        
        # Ограничение отрисовки границами экрана по горизонтали
        if bar_x + bar_width < 0 or bar_x > WIDTH:
            return

        # Фон
        pygame.draw.rect(self.game.screen, (30, 30, 30), (bar_x, bar_y, bar_width, bar_height))
        
        # HP
        hp_percent = npc.hp / npc.max_hp
        hp_width = int(bar_width * max(0, min(1, hp_percent)))
        
        # Цвет
        if hp_percent > 0.5:
            color = (0, 255, 0)
        elif hp_percent > 0.25:
            color = (255, 255, 0)
        else:
            color = (255, 0, 0)
        
        pygame.draw.rect(self.game.screen, color, (bar_x, bar_y, hp_width, bar_height))
