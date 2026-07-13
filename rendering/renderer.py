import pygame
import math
from setting import *


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
        """Рисует компас с направлением к выходу"""
        goal = self.game.map.exit_pos
        if goal is None:
            return

        player = (self.game.player.x, self.game.player.y)
        d_x, d_y = goal[0] - player[0], goal[1] - player[1]
        angle_to_goal = math.degrees(math.atan2(d_y, d_x))

        compass_col = 11
        compass_row = 0
        compass_width = 10
        compass_height = 1

        compass_x = compass_col * CELL_W
        compass_y = compass_row * CELL_H
        compass_w = compass_width * CELL_W
        compass_h = int(compass_height * CELL_H * 0.6)

        pygame.draw.rect(self.game.screen, (100, 100, 100),
                         (compass_x, compass_y, compass_w, compass_h), 2)

        center_x = compass_x + compass_w // 2
        center_y = compass_y + compass_h // 2
        player_angle_deg = math.degrees(self.game.player.angle)

        directions = [
            ('N', 90), ('NE', 45), ('E', 0), ('SE', 315),
            ('S', 270), ('SW', 225), ('W', 180), ('NW', 135),
            ('<!>', angle_to_goal)
        ]

        visible_range = 120
        pixels_per_degree = compass_w / visible_range

        for name, angle in directions:
            diff = angle - player_angle_deg
            while diff > 180:
                diff -= 360
            while diff < -180:
                diff += 360

            if abs(diff) <= visible_range // 2:
                x = center_x + diff * pixels_per_degree

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

    def draw_health_sprite(self):
        """Рисует иконку здоровья"""
        hp = self.game.player.hp

        if hp >= 80:
            sprite = self.nice_hp
            pos = self.hp_positions[-1]
        elif 50 <= hp < 80:
            sprite = self.average_hp
            pos = self.hp_positions[-2]
        else:
            sprite = self.bad_hp
            pos = self.hp_positions[-3]

        try:
            self.game.screen.blit(sprite, pos)
        except Exception:
            pass

    def draw_interface(self):
        """Рисует интерфейс: полоску здоровья, оружие, патроны"""
        hp = self.game.player.hp
        if self.game.weapon:
            current_weapon = self.game.weapon.name
            ammo = self.game.weapon.ammo
        else:
            current_weapon = "Fists"
            ammo = 0
        font_path = 'resources/fonts/Fy.ttf'
        
        health_bar_pos = grid_to_pixel(1, 16)
        health_bar_width = 6 * CELL_W
        health_bar_height = 1 * CELL_H
        health_bar_progress = (hp / 100) * health_bar_width

        if health_bar_progress > 6 * CELL_W:
            health_bar_progress = 6 * CELL_W
        
        armor = self.game.player.armor
        armor_bar_pos = grid_to_pixel(1, 17)
        armor_bar_width = 6 * CELL_W
        armor_bar_height = 1 * CELL_H

        # Фон полоски брони
        pygame.draw.rect(self.game.screen, (50, 50, 60),
                        (armor_bar_pos[0], armor_bar_pos[1], armor_bar_width, armor_bar_height))
        
        # Заполнение полоски брони
        armor_bar_progress = (armor / 100) * armor_bar_width
        pygame.draw.rect(self.game.screen, (0, 100, 200),  # Синий цвет
                        (armor_bar_pos[0], armor_bar_pos[1], armor_bar_progress, armor_bar_height))

        weapon_name_pos = grid_to_pixel(25, 15)
        weapon_ammo_pos = grid_to_pixel(25, 16)

        font = pygame.font.Font(font_path, 48)
        text_weapon = font.render(current_weapon, True, (255, 255, 255))
        font = pygame.font.Font(font_path, 50)
        text_ammo = font.render(str(ammo), True, (255, 200, 255))

        pygame.draw.rect(self.game.screen, (200, 50, 50),
                         (health_bar_pos[0], health_bar_pos[1], health_bar_width, health_bar_height))
        pygame.draw.rect(self.game.screen, (50, 240, 0),
                         (health_bar_pos[0], health_bar_pos[1], health_bar_progress, health_bar_height))

        self.game.screen.blit(text_weapon, weapon_name_pos)
        self.game.screen.blit(text_ammo, weapon_ammo_pos)
        self.draw_health_sprite()
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
