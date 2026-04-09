import math
from settings import MAP_WIDTH, MAP_HEIGHT
import pygame

def cast_ray(px, py, angle, world_map, map_width=MAP_WIDTH, map_height=MAP_HEIGHT):
    """
    DDA алгоритм рейкастинга
    Возвращает: (distance, hit, side, hit_pos)
    """
    ray_dir_x = math.cos(angle)
    ray_dir_y = math.sin(angle)
    
    map_x = int(px)
    map_y = int(py)
    
    # Длина луча до следующей вертикальной/горизонтальной границы
    delta_dist_x = abs(1 / ray_dir_x) if ray_dir_x != 0 else 1e30
    delta_dist_y = abs(1 / ray_dir_y) if ray_dir_y != 0 else 1e30
    
    # Направление шага
    step_x = 1 if ray_dir_x > 0 else -1
    step_y = 1 if ray_dir_y > 0 else -1
    
    # Начальное расстояние до ближайшей границы
    side_dist_x = (map_x + 1 - px) * delta_dist_x if ray_dir_x > 0 else (px - map_x) * delta_dist_x
    side_dist_y = (map_y + 1 - py) * delta_dist_y if ray_dir_y > 0 else (py - map_y) * delta_dist_y
    
    hit = False
    side = 0  # 0 = вертикальная стена, 1 = горизонтальная
    max_distance = 20
    distance = 0
    
    while not hit and distance < max_distance:
        if side_dist_x < side_dist_y:
            side_dist_x += delta_dist_x
            map_x += step_x
            side = 0
        else:
            side_dist_y += delta_dist_y
            map_y += step_y
            side = 1
        
        # Проверка выхода за границы карты
        if map_x < 0 or map_x >= map_width or map_y < 0 or map_y >= map_height:
            break
        
        # Проверка столкновения со стеной
        if world_map[map_y][map_x] > 0:
            hit = True
            
            # Расчёт точного расстояния
            if side == 0:
                distance = (map_x - px + (1 - step_x) / 2) / ray_dir_x
            else:
                distance = (map_y - py + (1 - step_y) / 2) / ray_dir_y
            distance = abs(distance)
    
    if not hit:
        distance = 9999
    
    return distance, hit, side, (map_x, map_y)

def draw_sprites(screen, player_x, player_y, player_angle, sprites, fov, screen_width, screen_height, world_map):
    sprites_to_draw = []
    
    for sprite in sprites:
        dx = sprite.x - player_x
        dy = sprite.y - player_y
        
        distance = (dx*dx + dy*dy) ** 0.5
        if distance > 10 or distance < 0.3:
            continue
        
        # ПРОВЕРКА ВИДИМОСТИ (не рисуем сквозь стены)
        if not is_sprite_visible(player_x, player_y, sprite.x, sprite.y, world_map):
            continue
        
        sprite_angle = math.atan2(dy, dx)
        angle_diff = sprite_angle - player_angle
        while angle_diff > math.pi:
            angle_diff -= 2 * math.pi
        while angle_diff < -math.pi:
            angle_diff += 2 * math.pi
        
        if abs(angle_diff) < fov / 2:
            # Уменьшенный размер
            sprite_size = int(screen_height / distance * 0.25)
            if sprite_size < 20:
                sprite_size = 20
            if sprite_size > 100:
                sprite_size = 100
            
            screen_x = (angle_diff / (fov / 2)) * (screen_width / 2) + screen_width / 2
            
            # Эффект парения
            float_offset = math.sin(pygame.time.get_ticks() * 0.005) * 5
            screen_y = screen_height // 2 - sprite_size // 2 + float_offset
            
            sprites_to_draw.append({
                'distance': distance,
                'screen_x': screen_x,
                'screen_y': screen_y,
                'size': sprite_size,
                'color': sprite.color,
                'name': sprite.weapon_name,
                'sprite': sprite
            })
    
    # Сортируем по расстоянию (дальние первыми)
    sprites_to_draw.sort(key=lambda x: x['distance'], reverse=True)
    
    for s in sprites_to_draw:
        # Полупрозрачный фон с цветом оружия
        alpha_surf = pygame.Surface((s['size'], s['size']), pygame.SRCALPHA)
        alpha_surf.fill((*s['color'], 180))  # полупрозрачный
        screen.blit(alpha_surf, (s['screen_x'] - s['size']//2, s['screen_y']))
        
        # Буква
        font = pygame.font.Font(None, s['size'] // 2)
        text = font.render(s['name'][0], True, (255, 255, 255))
        text_rect = text.get_rect(center=(s['screen_x'], s['screen_y'] + s['size']//2))
        screen.blit(text, text_rect)
        
        # Рамка
        pygame.draw.rect(screen, (255, 255, 255), 
                        (s['screen_x'] - s['size']//2, 
                         s['screen_y'], 
                         s['size'], s['size']), 2)
        
def is_sprite_visible(player_x, player_y, sprite_x, sprite_y, world_map):
    """Проверяет, есть ли прямая видимость до спрайта (без стен)"""
    # Вектор к спрайту
    dx = sprite_x - player_x
    dy = sprite_y - player_y
    distance = (dx*dx + dy*dy) ** 0.5
    
    if distance < 0.3:
        return True
    
    # Направление луча
    ray_dir_x = dx / distance
    ray_dir_y = dy / distance
    
    # DDA проверка (упрощённая)
    map_x = int(player_x)
    map_y = int(player_y)
    
    delta_dist_x = abs(1 / ray_dir_x) if ray_dir_x != 0 else 1e30
    delta_dist_y = abs(1 / ray_dir_y) if ray_dir_y != 0 else 1e30
    
    step_x = 1 if ray_dir_x > 0 else -1
    step_y = 1 if ray_dir_y > 0 else -1
    
    side_dist_x = (map_x + 1 - player_x) * delta_dist_x if ray_dir_x > 0 else (player_x - map_x) * delta_dist_x
    side_dist_y = (map_y + 1 - player_y) * delta_dist_y if ray_dir_y > 0 else (player_y - map_y) * delta_dist_y
    
    max_distance = distance
    current_distance = 0
    
    while current_distance < max_distance:
        if side_dist_x < side_dist_y:
            side_dist_x += delta_dist_x
            map_x += step_x
            side = 0
        else:
            side_dist_y += delta_dist_y
            map_y += step_y
            side = 1
        
        if map_x < 0 or map_x >= len(world_map[0]) or map_y < 0 or map_y >= len(world_map):
            break
        
        if world_map[map_y][map_x] > 0:
            # Стена на пути к спрайту
            return False
        
        if side == 0:
            current_distance = abs(map_x - player_x) / abs(ray_dir_x) if ray_dir_x != 0 else max_distance
        else:
            current_distance = abs(map_y - player_y) / abs(ray_dir_y) if ray_dir_y != 0 else max_distance
    
    return True