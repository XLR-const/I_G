"""Отрисовка стен через рейкастинг

Содержит класс RayCasting для DDA рендеринга стен.
"""

import pygame
import math
from setting import *
from config.game_data import SYMBOLS_CONFIG

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
        """Возвращает вертикальную полоску текстуры

        Args:
            texture: Поверхность текстуры
            tex_x: Координата X в текстуре
            height: Высота полоски

        Returns:
            pygame.Surface: Полоска текстуры или None
        """
        if texture is None or not USE_TEXTURES:
            return None

        cache_key = (id(texture), tex_x, height)
        if cache_key in self.texture_cache:
            return self.texture_cache[cache_key]

        slice_surface = texture.subsurface((tex_x, 0, 1, TEXTURE_SIZE))
        scaled = pygame.transform.scale(slice_surface, (SCALE, height))
        self.texture_cache[cache_key] = scaled

        return scaled

    def ray_cast(self):
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
        """Нативный рейкастинг (медленный, оставлен для справки)"""
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
