from setting import *
from math import sin, cos
import pygame

class RayCasting:
    def __init__(self, game):
        self.game = game
        # Z-буфер для расстояний до стен каждого луча
        self.z_buffer = [float('inf')] * NUM_RAYS 
        self.textures = {}
        self.texture_cache = {}
        self.load_textures()
    
    def ray_cast_native(self):
        ox, oy = self.game.player.x, self.game.player.y
        for i in range(NUM_RAYS):
            ray_angle = self.game.player.angle - HALF_FOV + i * DELTA_ANGLE
            
            sin_a = math.sin(ray_angle)
            cos_a = math.cos(ray_angle)
            
            # Полет луча
            for depth in range(1, MAX_DEPTH * 10):
                dist = depth / 10 # Шаг по 0.1 клетки
                
                # текущее координаты конца луча
                x = ox + dist * cos_a
                y = oy + dist * sin_a
                
                # проверка на попадание в стену
                if (int(x), int(y)) in self.game.map.world_map:
                    #pygame.draw.line(self.game.screen, 'white',
                    #                 (100 * ox, 100 * oy),
                    #                (100 * x, 100 * y), 1)

                    break
                dist *=  cos(self.game.player.angle - ray_angle) # Рыбий глаз
                
                # Рассчет высоты проекции стены
                proj_height = SCREEN_DIST / (dist + 0.0001)
                
                # Рисовка полоски стены по лучу i
                color = [255 / (1 + dist ** 2 * 0.1)] * 3 # Глубина цвета
                pygame.draw.rect(self.game.screen, color,
                                 (i * (WIDTH // NUM_RAYS), HALF_HEIGHT - proj_height // 2, 
                                WIDTH // NUM_RAYS, proj_height))
    
    def load_textures(self):
        """Загрузка текстур из TEXTURES_PATH"""
        try:
            if USE_TEXTURES:
                for name in TEXTURE_NAMES:
                    try:
                        path = TEXTURES_PATH + f"{name}.png"
                        tex = pygame.image.load(path).convert_alpha()
                        self.textures[name] = pygame.transform.scale(tex, (TEXTURE_SIZE, TEXTURE_SIZE))
                    except:
                        print(f"Ошибка загрузки {path}")
                        self.textures[name] = None
            else:
                self.textures[name] = None
        except Exception as e:
            print(f"Ошибка загрузки текстур: {e}")
            self.textures[name] = None
    
    def get_texture_slice(self, texture, tex_x, height):
        """
        Возвращает вертикальную полоску текстуры в пиксель
        мастштабирования height
        tex_x: номер пикселя в текстуре
        height: высота полоски в пикселях
        """
        if texture is None or not USE_TEXTURES:
            return None
        
        # Создание уникального ключа для кэша
        cache_key = (id(texture), tex_x, height)
        if cache_key in self.texture_cache:
            return self.texture_cache[cache_key]
        # Нарезаем текстуру
        slice_surface = texture.subsurface((tex_x, 0, 1, TEXTURE_SIZE))
        # Масштабируем
        scaled = pygame.transform.scale(slice_surface, (SCALE, height))
        # Кэшируем
        self.texture_cache[cache_key] = scaled
        
        return scaled
        
    # Внедрение алгоритма DDA raycast            
    def ray_cast(self):
        #print(f"ray_cast: player at ({ox}, {oy}), map size: {len(self.game.map.world_map)}")
        ox, oy = self.game.player.x, self.game.player.y
        x_map, y_map = int(ox), int(oy)

        # ЗАЩИТА: проверка границ карты
        if not hasattr(self.game.map, 'width') or not hasattr(self.game.map, 'height'):
            return  # карта не загружена
        
        for i in range(NUM_RAYS):
            ray_angle = self.game.player.angle - HALF_FOV + i * DELTA_ANGLE
            sin_a = math.sin(ray_angle)
            cos_a = math.cos(ray_angle)

            # 1. Рассчет изменения пролета луча через одну клетку по диагонали на X и Y
            # Если cos_a равен 0, дистанция бесконечна (1e30)
            delta_dist_x = abs(1 / cos_a) if cos_a != 0 else 1e30
            delta_dist_y = abs(1 / sin_a) if sin_a != 0 else 1e30

            # 2. Чекаем к какой линии сетки ближе находится наблюдатель,
            # который находится где то внутри клетки, и считаем это расстояние
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

            # 3. Цикл DDA: прыгаем по клеткам, пока не найдем стену
            wall_hit = False
            while not wall_hit:
                # Выбираем, куда прыгнуть: к следующей линии X или к следующей Y
                if side_dist_x < side_dist_y: # Вертикаль ближе
                    side_dist_x += delta_dist_x
                    x_map += step_x
                    side = 0 # Ударились в вертикальную стену
                else:
                    side_dist_y += delta_dist_y
                    y_map += step_y
                    side = 1 # Ударились в горизонтальную стену
                
                # Проверяем, есть ли стена в этой клетке
                if (x_map, y_map) in self.game.map.world_map:
                    wall_hit = True
                # проверка дверей    
                for door in self.game.map.doors:
                    if int(door.x) == x_map and int(door.y) == y_map:
                        if door.is_wall():
                            wall_hit = True
                        break

            # 4. Считаем финальную дистанцию до стены
            if side == 0:
                dist = side_dist_x - delta_dist_x
            else:
                dist = side_dist_y - delta_dist_y

            self.z_buffer[i] = dist

            # 5. Убираем эффект рыбьего глаза
            dist *= math.cos(self.game.player.angle - ray_angle)

            # 6. Проекция
            proj_height = SCREEN_DIST / (dist + 0.0001)
            
            wall_char = self.game.map.world_map.get((x_map, y_map), '1')
            
            # обрабатываем анимацию дверей
            for door in self.game.map.doors:
                if int(door.x) == x_map and int(door.y) == y_map:
                    wall_char = 'D'
                    door_frame = door.get_texture_offset()
                    break
            
            color = WALL_COLORS.get(wall_char, (200, 200, 200))
            
            # Затенения от положения стены
            if side == 1:
                color = (color[0] * 0.7, color[1] * 0.7, color[2] * 0.7)
            
            # Затенения от дистанции с учетом леса  
            if self.game.current_level == 2:
                dark_factor = 1 / (1 + dist * dist * 0.0005)
                color = (int(color[0] * dark_factor),
                        int(color[1] * dark_factor),
                        int(color[2] * dark_factor))
            else:
                color = (int(color[0] / (1 + dist * dist * 0.01)),
                    int(color[1] / (1 + dist * dist * 0.01)),
                    int(color[2] / (1 + dist * dist * 0.01)))

            # Фикс прорисовки стен - зубчики
            # Рассчитываем параметры один раз
            w = SCALE
            h = int(proj_height)
            x = int(i * SCALE)
            y = int(HALF_HEIGHT - h // 2)
            # Ограничиваем высоту, чтобы не было "зубьев" при взгляде в упор
            if h > HEIGHT * 2: # даем запас, но не бесконечность
                h = HEIGHT * 2
                y = int(HALF_HEIGHT - h // 2)
                
            # РАБОТА С ТЕКСТУРКАМИ    
            texture = self.textures.get(wall_char)
            if texture is not None:
                # Точка попадания луча в стену
                if side == 0:  # Вертикальная стена
                    hit_x = ox + (side_dist_x - delta_dist_x) * cos_a
                    hit_y = oy + (side_dist_x - delta_dist_x) * sin_a
                    # Для вертикальной стены используем координату Y
                    tex_x = hit_y % 1.0
                else:  # Горизонтальная стена
                    hit_x = ox + (side_dist_y - delta_dist_y) * cos_a
                    hit_y = oy + (side_dist_y - delta_dist_y) * sin_a
                    # Для горизонтальной стены используем координату X
                    tex_x = hit_x % 1.0
                if self.game.current_level == 2 and side == 0:
                    speed = 2
                    time_offset = (pygame.time.get_ticks() * speed / 1000) % 1.0
                    tex_x = (tex_x - time_offset) % 1.0
                tex_x = int(tex_x * TEXTURE_SIZE)
                
                # Получаем полоску из кэша
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
            #pygame.draw.line(self.game.screen, color, (x, y), (x, y + h), w)
            # Сбрасываем координаты сетки для следующего луча!
            x_map, y_map = int(ox), int(oy)
