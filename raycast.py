import math
from settings import MAP_WIDTH, MAP_HEIGHT

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