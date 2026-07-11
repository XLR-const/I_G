"""Отрисовка стен через рейкастинг

Содержит класс RayCasting для DDA рендеринга стен.
"""

import pygame
import math
from setting import *
from config.game_data import SYMBOLS_CONFIG
import numpy as np
from numba import njit

@njit
def run_dda_numba(ox, oy, player_angle, numeric_grid, num_rays, 
                  half_fov, delta_angle, screen_dist, texture_size):
    z_buffer = np.zeros(num_rays, dtype=np.float32)
    render_data = np.zeros((num_rays, 5), dtype=np.int32)
    
    map_height, map_width = numeric_grid.shape

    for i in range(num_rays):
        ray_angle = player_angle - half_fov + i * delta_angle
        ray_angle = ray_angle % (2.0 * math.pi)
        
        sin_a = math.sin(ray_angle)
        cos_a = math.cos(ray_angle)

        x_map, y_map = int(ox), int(oy)

        delta_dist_x = abs(1.0 / cos_a) if abs(cos_a) > 1e-6 else 1e30
        delta_dist_y = abs(1.0 / sin_a) if abs(sin_a) > 1e-6 else 1e30

        if cos_a < 0.0:
            step_x = -1
            side_dist_x = (ox - x_map) * delta_dist_x
        else:
            step_x = 1
            side_dist_x = (x_map + 1.0 - ox) * delta_dist_x

        if sin_a < 0.0:
            step_y = -1
            side_dist_y = (oy - y_map) * delta_dist_y
        else:
            step_y = 1
            side_dist_y = (y_map + 1.0 - oy) * delta_dist_y

        wall_hit = False
        side = 0
        wall_char_id = 0
        
        # Увеличиваем шаги для больших карт (150+ клеток), чтобы лучи не бросали расчет на полпути
        max_steps = 400  
        steps = 0

        while not wall_hit and steps < max_steps:
            steps += 1
            if side_dist_x < side_dist_y:
                side_dist_x += delta_dist_x
                x_map += step_x
                side = 0
            else:
                side_dist_y += delta_dist_y
                y_map += step_y
                side = 1

            if 0 <= x_map < map_width and 0 <= y_map < map_height:
                cell_value = numeric_grid[y_map, x_map]
                if cell_value > 0:
                    wall_hit = True
                    wall_char_id = cell_value
            else:
                # Вылетели за границы карты — гарантированный стоп
                wall_hit = True
                wall_char_id = 0

        # Если луч улетел в пустоту и стены нет — пишем специальный маркер (wall_char_id = 0)
        if not wall_hit or wall_char_id == 0:
            z_buffer[i] = 999.0
            render_data[i, 0] = 0  # Стены нет
            continue

        if side == 0:
            dist = side_dist_x - delta_dist_x
        else:
            dist = side_dist_y - delta_dist_y

        if dist < 0.1:
            dist = 0.1

        z_buffer[i] = dist

        # Коррекция рыбьего глаза
        dist_corrected = dist * math.cos(player_angle - ray_angle)
        if dist_corrected < 0.1:
            dist_corrected = 0.1

        proj_height = screen_dist / dist_corrected

        # ИСПРАВЛЕНИЕ ТЕКСТУР: Высокоточный расчет пересечения через floor
        if side == 0:
            hit_y = oy + dist * sin_a
            tex_x = hit_y - math.floor(hit_y)
        else:
            hit_x = ox + dist * cos_a
            tex_x = hit_x - math.floor(hit_x)

        if (side == 0 and cos_a > 0.0) or (side == 1 and sin_a < 0.0):
            tex_x = 1.0 - tex_x

        tex_x_pixel = int(tex_x * texture_size)
        tex_x_pixel = max(0, min(tex_x_pixel, texture_size - 1))

        # Передаем «чистую» высоту в Pygame, ограничивать будем при отрисовке для спасения FPS
        render_data[i, 0] = wall_char_id
        render_data[i, 1] = side
        render_data[i, 2] = 0 # Посчитаем в Python безопаснее
        render_data[i, 3] = int(proj_height)
        render_data[i, 4] = tex_x_pixel

    return z_buffer, render_data

class RayCasting:
    """Класс для рейкастинга и отрисовки стен

    Attributes:
        game: Объект игры
        z_buffer: Буфер глубин для каждого луча
        textures: Словарь загруженных текстур
        texture_cache: Кэш полосок текстур
    """

    def __init__(self, game):
        """Инициализирует рейкастинг

        Args:
            game: Объект игры
        """
        self.game = game
        self.z_buffer = [float('inf')] * NUM_RAYS
        self.textures = {}
        self.texture_cache = {}
        self.load_textures()

    def load_textures(self):
        """Загружает текстуры из SYMBOLS_CONFIG"""
        if not USE_TEXTURES:
            return

        for symbol, config in SYMBOLS_CONFIG.items():
            texture_path = config.get('texture')
            if texture_path:
                try:
                    tex = pygame.image.load(texture_path).convert_alpha()
                    self.textures[symbol] = pygame.transform.scale(tex, (TEXTURE_SIZE, TEXTURE_SIZE))
                except Exception as e:
                    print(f"Ошибка загрузки текстуры {texture_path}: {e}")
                    self.textures[symbol] = None

    def get_texture_slice(self, texture, tex_x, height):
        """Возвращает сглаженную вертикальную полоску текстуры из кэша"""
        if texture is None or not USE_TEXTURES:
            return None

        # 1. Округляем высоту до четного числа (шаг 2 пикселя)
        # Это защищает кэш от переполнения и убирает микро-дёрганья
        height = (height // 2) * 2
        if height < 2:
            height = 2

        # 2. Проверяем наличие полоски в кэше
        cache_key = (id(texture), tex_x, height)
        if cache_key in self.texture_cache:
            return self.texture_cache[cache_key]

        # Защита координат
        if not (0 <= tex_x < TEXTURE_SIZE):
            tex_x = max(0, min(tex_x, TEXTURE_SIZE - 1))

        try:
            # Вырезаем оригинальный срез
            slice_surface = texture.subsurface((tex_x, 0, 1, TEXTURE_SIZE))
            
            # 3. Применяем качественное сглаживание
            scaled = pygame.transform.smoothscale(slice_surface, (SCALE, height))
            
            # Ограничиваем размер кэша в оперативной памяти
            if len(self.texture_cache) > 4000:
                self.texture_cache.clear()
                
            # Сохраняем в кэш
            self.texture_cache[cache_key] = scaled
            return scaled
        except:
            # Откат на быстрый scale, если smoothscale выдал ошибку на гигантской высоте
            try:
                scaled = pygame.transform.scale(slice_surface, (SCALE, height))
                self.texture_cache[cache_key] = scaled
                return scaled
            except:
                return None


    
    def ray_cast(self):
        """Выполняет DDA рейкастинг через Numba с пикселизацией вблизи и кэшем"""
        if not hasattr(self.game.map, 'numeric_grid'):
            return

        ox, oy = self.game.player.x, self.game.player.y

        # Запускаем стабильное ядро Numba
        z_buffer_numba, render_data = run_dda_numba(
            ox, oy, self.game.player.angle, self.game.map.numeric_grid,
            NUM_RAYS, HALF_FOV, DELTA_ANGLE, SCREEN_DIST, TEXTURE_SIZE
        )

        for i in range(NUM_RAYS):
            self.z_buffer[i] = z_buffer_numba[i]

        id_to_char = getattr(self, 'id_to_char', {})
        
        # Настраиваем клиппинг под размеры игрового окна
        original_clip = self.game.screen.get_clip()
        self.game.screen.set_clip(pygame.Rect(0, 0, WIDTH, HEIGHT))

        for i in range(NUM_RAYS):
            wall_char_id, side, _, proj_height, tex_x = render_data[i]
            
            if wall_char_id == 0 or proj_height <= 0:
                continue

            x = int(i * SCALE)
            wall_char = id_to_char.get(wall_char_id, '1')
            texture = self.textures.get(wall_char)

            # --- ИСПРАВЛЕННЫЙ ИДЕАЛЬНЫЙ РАСЧЁТ ДЛЯ ПИКСЕЛИЗАЦИИ БЕЗ ВОЛН ---
            h = int(proj_height)
            
            if h > HEIGHT:
                # Если стена выше экрана, вычисляем точный шаг пикселя текстуры на один пиксель экрана
                # Это гарантирует, что рисунок зафиксируется на месте и волны исчезнут
                tex_step = TEXTURE_SIZE / h
                
                # Сколько пикселей текстуры физически помещается в высоту нашего экрана (HEIGHT)
                tex_h = int(HEIGHT * tex_step)
                tex_h = max(1, min(tex_h, TEXTURE_SIZE))
                
                # Точно находим верхнюю точку обрезки текстуры без дробных погрешностей
                tex_y = int((TEXTURE_SIZE - tex_h) / 2)
                
                # Насильно ставим высоту полосы равной высоте экрана
                h_render = HEIGHT
                y = 0
                
                # Извлекаем ровный кусок и используем ОБЫЧНЫЙ scale для жестких пикселей
                if texture is not None:
                    try:
                        # Округляем высоту для стабильной работы кэша
                        h_cache = (h_render // 2) * 2
                        cache_key = (id(texture), tex_x, h_cache, tex_y, tex_h)
                        
                        if cache_key in self.texture_cache:
                            texture_slice = self.texture_cache[cache_key]
                        else:
                            slice_surface = texture.subsurface((tex_x, tex_y, 1, tex_h))
                            texture_slice = pygame.transform.scale(slice_surface, (SCALE, h_render))
                            
                            if len(self.texture_cache) > 4000:
                                self.texture_cache.clear()
                            self.texture_cache[cache_key] = texture_slice
                    except:
                        texture_slice = None
                else:
                    texture_slice = None
            else:
                # Обычная стена вдалеке (меньше высоты экрана)
                y = int(HALF_HEIGHT - h // 2)
                
                if texture is not None:
                    try:
                        h_cache = (h // 2) * 2
                        cache_key = (id(texture), tex_x, h_cache, 0, TEXTURE_SIZE)
                        
                        if cache_key in self.texture_cache:
                            texture_slice = self.texture_cache[cache_key]
                        else:
                            slice_surface = texture.subsurface((tex_x, 0, 1, TEXTURE_SIZE))
                            texture_slice = pygame.transform.scale(slice_surface, (SCALE, h_cache))
                            
                            if len(self.texture_cache) > 4000:
                                self.texture_cache.clear()
                            self.texture_cache[cache_key] = texture_slice
                    except:
                        texture_slice = None
                else:
                    texture_slice = None

            # Отрисовка
            if texture_slice is not None:
                self.game.screen.blit(texture_slice, (x, y))
                if side == 1:
                    dark_surface = pygame.Surface((SCALE, texture_slice.get_height()))
                    dark_surface.set_alpha(80)
                    dark_surface.fill((0, 0, 0))
                    self.game.screen.blit(dark_surface, (x, y))
            else:
                # Отрезаем цвета по высоте экрана для корректного draw.rect
                rect_y = max(0, y)
                rect_h = min(HEIGHT, h)
                color = WALL_COLORS.get(wall_char, (200, 200, 200))
                if side == 1:
                    color = (int(color[0] * 0.7), int(color[1] * 0.7), int(color[2] * 0.7))
                pygame.draw.rect(self.game.screen, color, (x, rect_y, SCALE, rect_h))

        # Восстанавливаем оригинальный клиппинг
        self.game.screen.set_clip(original_clip)





    def ray_cast_non_optimized(self):
        """Выполняет DDA рейкастинг и отрисовывает стены"""
        ox, oy = self.game.player.x, self.game.player.y
        x_map, y_map = int(ox), int(oy)

        if not hasattr(self.game.map, 'width') or not hasattr(self.game.map, 'height'):
            return

        for i in range(NUM_RAYS):
            ray_angle = self.game.player.angle - HALF_FOV + i * DELTA_ANGLE
            sin_a = math.sin(ray_angle)
            cos_a = math.cos(ray_angle)

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

            wall_hit = False
            while not wall_hit:
                if side_dist_x < side_dist_y:
                    side_dist_x += delta_dist_x
                    x_map += step_x
                    side = 0
                else:
                    side_dist_y += delta_dist_y
                    y_map += step_y
                    side = 1

                if (x_map, y_map) in self.game.map.world_map:
                    wall_hit = True

                for door in self.game.map.doors:
                    if int(door.x) == x_map and int(door.y) == y_map:
                        if door.is_wall():
                            wall_hit = True
                        break

            if side == 0:
                dist = side_dist_x - delta_dist_x
            else:
                dist = side_dist_y - delta_dist_y

            if dist < 0.2:
                dist = 0.2

            self.z_buffer[i] = dist

            dist *= math.cos(self.game.player.angle - ray_angle)

            if dist < 0.2:
                dist = 0.2

            proj_height = SCREEN_DIST / (dist + 0.0001)
            if proj_height > HEIGHT * 3:
                proj_height = HEIGHT * 3

            wall_char = self.game.map.world_map.get((x_map, y_map), '1')

            door_frame = 0
            for door in self.game.map.doors:
                if int(door.x) == x_map and int(door.y) == y_map:
                    wall_char = 'D'
                    door_frame = door.get_texture_offset()
                    break

            color = WALL_COLORS.get(wall_char, (200, 200, 200))

            if side == 1:
                color = (color[0] * 0.7, color[1] * 0.7, color[2] * 0.7)
            color = (
                int(color[0] / (1 + dist * dist * 0.01)),
                int(color[1] / (1 + dist * dist * 0.01)),
                int(color[2] / (1 + dist * dist * 0.01))
            )

            w = SCALE
            h = int(proj_height)
            x = int(i * SCALE)
            y = int(HALF_HEIGHT - h // 2)

            if h > HEIGHT * 2:
                h = HEIGHT * 2
                y = int(HALF_HEIGHT - h // 2)

            texture = self.textures.get(wall_char)
            if texture is not None:
                if side == 0:
                    hit_x = ox + (side_dist_x - delta_dist_x) * cos_a
                    hit_y = oy + (side_dist_x - delta_dist_x) * sin_a
                    tex_x = hit_y % 1.0
                else:
                    hit_x = ox + (side_dist_y - delta_dist_y) * cos_a
                    hit_y = oy + (side_dist_y - delta_dist_y) * sin_a
                    tex_x = hit_x % 1.0

                tex_x = int(tex_x * TEXTURE_SIZE)
                tex_x = max(0, min(tex_x, TEXTURE_SIZE - 1))

                texture_slice = self.get_texture_slice(texture, tex_x, h)
                if texture_slice is not None:
                    self.game.screen.blit(texture_slice, (x, y))
                    if side == 1:
                        dark_surface = pygame.Surface((w, h))
                        dark_surface.set_alpha(80)
                        dark_surface.fill((0, 0, 0))
                        self.game.screen.blit(dark_surface, (x, y))
            else:
                pygame.draw.rect(self.game.screen, color, (x, y, w, h))

            x_map, y_map = int(ox), int(oy)

    def ray_cast_native(self):
        """Нативный рейкастинг (оставлен для справки)"""
        ox, oy = self.game.player.x, self.game.player.y
        for i in range(NUM_RAYS):
            ray_angle = self.game.player.angle - HALF_FOV + i * DELTA_ANGLE

            sin_a = math.sin(ray_angle)
            cos_a = math.cos(ray_angle)

            for depth in range(1, MAX_DEPTH * 10):
                dist = depth / 10
                x = ox + dist * cos_a
                y = oy + dist * sin_a

                if (int(x), int(y)) in self.game.map.world_map:
                    break

                dist *= math.cos(self.game.player.angle - ray_angle)
                proj_height = SCREEN_DIST / (dist + 0.0001)
                color = [255 / (1 + dist ** 2 * 0.1)] * 3
                pygame.draw.rect(self.game.screen, color,
                                 (i * (WIDTH // NUM_RAYS), HALF_HEIGHT - proj_height // 2,
                                  WIDTH // NUM_RAYS, proj_height))
