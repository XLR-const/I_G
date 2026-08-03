import os
import sys
import json
import math
import random
import argparse

# Настройка путей импорта строго по вашему ТЗ
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.biome_data import BIOME_DATABASE

class PipelineLevelGenerator:
    def __init__(self, width=100, height=100, style='out', seed=None, level_num=4):
        """Полностью Data-Driven инициализация с поддержкой полиморфных стилей"""
        self.width = width
        self.height = height
        self.style = style
        self.level_num = level_num
        
        # Динамический рассчет количества секторов от масштаба карты и уровня
        base_rooms = 6 + (self.level_num * 2)
        area_factor = (self.width * self.height) // 2500
        self.min_rooms = max(6, min(30, base_rooms + area_factor))
        
        # Для закрытых комплексов ограничиваем плотность залов, чтобы избежать каши
        if self.style in ['hall', 'lab', 'vent']:
            max_rooms_limit = 12 if self.level_num < 5 else 16
            self.min_rooms = min(max_rooms_limit, self.min_rooms)
        
        if seed is None:
            self.seed = str(random.randint(100000, 999999))
        else:
            self.seed = str(seed)
        random.seed(self.seed)
        
        # Извлекаем профиль биома
        self.biome = BIOME_DATABASE.get(self.style, next(iter(BIOME_DATABASE.values())))
        
        self.grid = [["1" for _ in range(self.width)] for _ in range(self.height)]
        self.spawned_counters = {}
        self.rooms_meta = [] 
        
        self.nodes = {}       
        self.edges = []       
        
        # Кешируем имена стен биома
        w_cfg = self.biome.get('walls', {})
        self.primary_wall = w_cfg.get('primary', {}).get('char', 'metal_crunch_wall')
        self.secondary_wall = w_cfg.get('secondary', {}).get('char', '1')
        self.perimeter_wall = self.biome.get('geometry', {}).get('perimeter_wall', self.primary_wall)
        self.valid_walls = [self.primary_wall, self.secondary_wall, self.perimeter_wall, "1"]

    def _clear_grid(self):
        """Полная очистка сетки перед повторной попыткой генерации"""
        self.grid = [["1" for _ in range(self.width)] for _ in range(self.height)]
        self.nodes = {}
        self.edges = []
        self.rooms_meta = []
        self.spawned_counters = {}

    def _check_local_density(self, r, c, radius=9, max_allowed=2):
        all_pool_keys = list(self.biome.get('npc_settings', {}).get('pool', {}).keys()) + \
                        list(self.biome.get('loot_settings', {}).get('pool', {}).keys())
        local_count = 0
        for dr in range(-radius, radius + 1):
            for dc in range(-radius, radius + 1):
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.height and 0 <= nc < self.width:
                    if self.grid[nr][nc] in all_pool_keys:
                        local_count += 1
        return local_count < max_allowed

    def _check_min_distance(self, r, c, char, min_dist):
        if min_dist <= 0: return True
        for dr in range(-min_dist, min_dist + 1):
            for dc in range(-min_dist, min_dist + 1):
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.height and 0 <= nc < self.width:
                    if self.grid[nr][nc] == char: return False
        return True

    def _is_adjacent_to_wall(self, r, c):
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.height and 0 <= nc < self.width:
                if self.grid[nr][nc] in self.valid_walls: return True
        return False

    def build_macro_graph(self):
        """ФАЗА 1.1: Построение макро-графа миссии с защитой от наложений на мега-картах"""
        types_pool = ['canyon', 'plateau', 'canyon'] if self.style == 'out' else ['room', 'sector', 'room']
        
        self.nodes = {0: {'id': 0, 'type': 'spawn_zone', 'edges': [], 'name': 'Spawn'}}
        
        current_id = 1
        for i in range(self.min_rooms - 2):
            t = random.choice(types_pool)
            self.nodes[current_id] = {'id': current_id, 'type': t, 'edges': [], 'name': f'Zone {current_id}'}
            self.edges.append((current_id - 1, current_id, 'normal'))
            self.nodes[current_id - 1]['edges'].append(current_id)
            self.nodes[current_id]['edges'].append(current_id - 1)
            current_id += 1
            
        final_id = current_id
        self.nodes[final_id] = {'id': final_id, 'type': 'bunker_exit', 'edges': [], 'name': 'Exit'}
        self.edges.append((final_id - 1, final_id, 'locked_blue'))
        self.nodes[final_id - 1]['edges'].append(final_id)
        self.nodes[final_id]['edges'].append(final_id - 1)
        current_id += 1
        
        num_secrets = 3 if self.width >= 150 else 1
        for _ in range(num_secrets):
            attach_to = random.randint(1, final_id - 2)
            self.nodes[current_id] = {'id': current_id, 'type': 'secret_cave', 'edges': [], 'name': 'Secret'}
            self.edges.append((attach_to, current_id, 'secret_wall'))
            self.nodes[attach_to]['edges'].append(current_id)
            self.nodes[current_id]['edges'].append(attach_to)
            current_id += 1

        cols = int(math.sqrt(len(self.nodes))) + 1
        rows = (len(self.nodes) // cols) + 1
        sect_w = (self.width - 12) // cols
        sect_h = (self.height - 12) // rows
        
        node_ids = list(self.nodes.keys())
        random.shuffle(node_ids)
        
        idx = 0
        for r in range(rows):
            for c in range(cols):
                if idx >= len(node_ids): break
                n_id = node_ids[idx]
                sect_x, sect_y = 6 + c * sect_w, 6 + r * sect_h
                
                if self.width >= 150:
                    w_max = min(sect_w - 6, 22 if self.style == 'hang' else 14)
                    h_max = min(sect_h - 6, 22 if self.style == 'hang' else 14)
                    w, h = random.randint(8, max(9, w_max)), random.randint(8, max(9, h_max))
                else:
                    if self.nodes[n_id]['type'] in ['canyon', 'plateau']:
                        w, h = random.randint(8, 12), random.randint(8, 12)
                    else:
                        w, h = random.randint(5, 7), random.randint(5, 7)
                
                cx = sect_x + (sect_w - w) // 2
                cy = sect_y + (sect_h - h) // 2
                self.nodes[n_id].update({'x': cx, 'y': cy, 'w': w, 'h': h})
                self.rooms_meta.append((cx, cy, w, h, 'secret' if self.nodes[n_id]['type'] == 'secret_cave' else 'normal'))
                idx += 1

    def pass_geometry(self):
        """ФАЗА 1.2: Полиморфное построение каркаса геометрии под все 5 стилей"""
        if self.style == 'out':
            self._generate_organic_canyons()
        elif self.style in ['hall', 'hang']:
            self._generate_industrial_halls()
        elif self.style == 'lab':
            self._generate_bsp_laboratories()
        elif self.style == 'vent':
            self._generate_vent_maze()

        # Накат нерушимого защитного кольца периметра
        for c in range(self.width):
            self.grid[0][c] = self.perimeter_wall
            self.grid[self.height - 1][c] = self.perimeter_wall
        for r in range(self.height):
            self.grid[r][0] = self.perimeter_wall
            self.grid[r][self.width - 1] = self.perimeter_wall

    def _generate_organic_canyons(self):
        for n_id, node in self.nodes.items():
            x, y, w, h = node['x'], node['y'], node['w'], node['h']
            for r in range(y, min(self.height - 2, y + h)):
                for c in range(x, min(self.width - 2, x + w)):
                    self.grid[r][c] = "_" if random.random() < 0.65 else "1" if node['type'] in ['canyon', 'plateau'] else "_"

        for n1_id, n2_id, edge_type in self.edges:
            n1, n2 = self.nodes[n1_id], self.nodes[n2_id]
            cx, cy = n1['x'] + n1['w'] // 2, n1['y'] + n1['h'] // 2
            tx, ty = n2['x'] + n2['w'] // 2, n2['y'] + n2['h'] // 2
            while (cx, cy) != (tx, ty):
                road_radius = 1 if edge_type == 'secret_wall' else 2
                for dr in range(-road_radius, road_radius + 1):
                    for dc in range(-road_radius, road_radius + 1):
                        if 2 <= cy + dr < self.height - 2 and 2 <= cx + dc < self.width - 2:
                            self.grid[cy + dr][cx + dc] = "_"
                choices = []
                if cx < tx: choices.append((1, 0))
                if cx > tx: choices.append((-1, 0))
                if cy < ty: choices.append((0, 1))
                if cy > ty: choices.append((0, -1))
                if random.random() < 0.20 or not choices:
                    cx += random.choice([-1, 0, 1])
                    cy += random.choice([-1, 0, 1])
                else:
                    dx, dy = random.choice(choices)
                    cx += dx; cy += dy
                cx = max(2, min(self.width - 3, cx))
                cy = max(2, min(self.height - 3, cy))

        for _ in range(3):
            next_grid = [row[:] for row in self.grid]
            for r in range(2, self.height - 2):
                for c in range(2, self.width - 2):
                    wall_count = sum(1 for dr in [-1,0,1] for dc in [-1,0,1] if self.grid[r+dr][c+dc] in self.valid_walls)
                    if self.grid[r][c] in self.valid_walls:
                        if wall_count < 4: next_grid[r][c] = "_"
                    else:
                        if wall_count > 5: next_grid[r][c] = "1"
            self.grid = next_grid

    def _generate_industrial_halls(self):
        for node in self.nodes.values():
            multiplier = 1.3 if self.style == 'hang' else 1.0
            w = min(self.width - 4, int(node['w'] * multiplier))
            h = min(self.height - 4, int(node['h'] * multiplier))
            x = max(2, min(self.width - w - 2, node['x']))
            y = max(2, min(self.height - h - 2, node['y']))
            for r in range(y, y + h):
                for c in range(x, x + w):
                    self.grid[r][c] = "_"
            if self.style == 'hall' and w > 8 and h > 8 and random.random() < 0.6:
                self.grid[y + h//2][x + w//2] = "1"
        
        for n1_id, n2_id, _ in self.edges:
            n1, n2 = self.nodes[n1_id], self.nodes[n2_id]
            x1, y1 = n1['x'] + n1['w'] // 2, n1['y'] + n1['h'] // 2
            x2, y2 = n2['x'] + n2['w'] // 2, n2['y'] + n2['h'] // 2
                        # Замените эту строчку внутри цикла коридоров в _generate_industrial_halls:
            offsets = [0, 1] if self.width >= 150 else [-1, 0, 1]

            for c in range(min(x1, x2), max(x1, x2) + 1):
                for offset in offsets:
                    if 2 <= y1 + offset < self.height - 2 and 2 <= c < self.width - 2:
                        self.grid[y1 + offset][c] = "_"
            for r in range(min(y1, y2), max(y1, y2) + 1):
                for offset in offsets:
                    if 2 <= r < self.height - 2 and 2 <= x2 + offset < self.width - 2:
                        self.grid[r][x2 + offset] = "_"

    def _generate_bsp_laboratories(self):
        for node in self.nodes.values():
            for r in range(node['y'], min(self.height - 2, node['y'] + node['h'])):
                for c in range(node['x'], min(self.width - 2, node['x'] + node['w'])):
                    self.grid[r][c] = "_"
        
        step = 14 if self.width >= 150 else 8
        for r in range(6, self.height - 6, step):
            for c in range(2, self.width - 2):
                if random.random() < 0.80:
                    self.grid[r][c] = "1"
        for c in range(6, self.width - 6, step):
            for r in range(2, self.height - 2):
                if random.random() < 0.80:
                    self.grid[r][c] = "1"
        
        for n1_id, n2_id, _ in self.edges:
            n1, n2 = self.nodes[n1_id], self.nodes[n2_id]
            x1, y1 = n1['x'] + n1['w'] // 2, n1['y'] + n1['h'] // 2
            x2, y2 = n2['x'] + n2['w'] // 2, n2['y'] + n2['h'] // 2
            for c in range(min(x1, x2), max(x1, x2) + 1):
                self.grid[y1][c] = "_"
            for r in range(min(y1, y2), max(y1, y2) + 1):
                self.grid[r][x2] = "_"

    def _generate_vent_maze(self):
        for node in self.nodes.values():
            cx, cy = node['x'] + node['w'] // 2, node['y'] + node['h'] // 2
            for r in range(cy - 1, cy + 2):
                for c in range(cx - 1, cx + 2):
                    self.grid[r][c] = "_"
        
        for n1_id, n2_id, _ in self.edges:
            n1, n2 = self.nodes[n1_id], self.nodes[n2_id]
            cx, cy = n1['x'] + n1['w'] // 2, n1['y'] + n1['h'] // 2
            tx, ty = n2['x'] + n2['w'] // 2, n2['y'] + n2['h'] // 2
            while (cx, cy) != (tx, ty):
                if 1 <= cy < self.height - 1 and 1 <= cx < self.width - 1:
                    self.grid[cy][cx] = "_"
                choices = []
                if cx < tx: choices.append((1, 0))
                if cx > tx: choices.append((-1, 0))
                if cy < ty: choices.append((0, 1))
                if cy > ty: choices.append((0, -1))
                if random.random() < 0.40 or not choices:
                    cx += random.choice([-1, 0, 1])
                    cy += random.choice([-1, 0, 1])
                else:
                    dx, dy = random.choice(choices)
                    cx += dx
                    cy += dy
                cx = max(1, min(self.width - 2, cx))
                cy = max(1, min(self.height - 2, cy))

    def pass_textures(self):
        """ФАЗА 1.2.5: Пропорциональное текстурирование технических стен по весам биома"""
        w_cfg = self.biome.get('walls', {})
        population = [self.primary_wall, self.secondary_wall]
        weights = [w_cfg.get('primary', {}).get('weight', 85), w_cfg.get('secondary', {}).get('weight', 15)]
        for r in range(self.height):
            for c in range(self.width):
                if self.grid[r][c] == "1":
                    # СТРОГО ИСПРАВЛЕНО: Извлекаем строку из списка с помощью!
                    self.grid[r][c] = random.choices(population, weights=weights)[0]

    def pass_points_of_interest(self):
        """ФАЗА 1.3: Наложение Спавна, Выхода, Умных Дверей и Ключей"""
        spawn_node = self.nodes[0]
        center_x, center_y = spawn_node['x'] + spawn_node['w'] // 2, spawn_node['y'] + spawn_node['h'] // 2
        self.grid[center_y][center_x] = "Spawn"
        if self.grid[center_y + 1][center_x] == "_":
            self.grid[center_y + 1][center_x] = "COLT"
        
        exit_node = next(n for n in self.nodes.values() if n['type'] == 'bunker_exit')
        self.grid[exit_node['y'] + exit_node['h'] // 2][exit_node['x'] + exit_node['w'] // 2] = "Exit"
        
        doors_cfg = self.biome.get('doors', {})
        door_normal = doors_cfg.get('normal', 'door_normal')
        door_locked = doors_cfg.get('locked', 'door_blue_key').strip("'")
        
        for n1_id, n2_id, edge_type in self.edges:
            d_char = door_normal
            if edge_type == 'locked_blue':
                d_char = door_locked
            elif edge_type == 'secret_wall':
                d_char = 'secret_wall'
            self._place_door_on_edge(n1_id, n2_id, d_char)
            if edge_type == 'locked_blue':
                self._spawn_hidden_key('key_blue')

    def _place_door_on_edge(self, n1_id, n2_id, door_char):
        n1, n2 = self.nodes[n1_id], self.nodes[n2_id]
        if self.style == 'out':
            mid_x = (n1['x'] + n1['w'] // 2 + n2['x'] + n2['w'] // 2) // 2
            mid_y = (n1['y'] + n1['h'] // 2 + n2['y'] + n2['h'] // 2) // 2
            if not (2 <= mid_y < self.height - 2 and 2 <= mid_x < self.width - 2):
                return
            dx, dy = abs(n1['x'] - n2['x']), abs(n1['y'] - n2['y'])
            gate_wall = self.secondary_wall
            if dx > dy:
                for direction in [-1, 1]:
                    offset = 1
                    while True:
                        curr_r = mid_y + (direction * offset)
                        if not (1 <= curr_r < self.height - 1) or self.grid[curr_r][mid_x] in [self.primary_wall, self.perimeter_wall]:
                            break
                        self.grid[curr_r][mid_x] = gate_wall
                        offset += 1
                self.grid[mid_y][mid_x] = door_char
                self.grid[mid_y][mid_x - 1] = "_"
                self.grid[mid_y][mid_x + 1] = "_"
            else:
                for direction in [-1, 1]:
                    offset = 1
                    while True:
                        curr_c = mid_x + (direction * offset)
                        if not (1 <= curr_c < self.width - 1) or self.grid[mid_y][curr_c] in [self.primary_wall, self.perimeter_wall]:
                            break
                        self.grid[mid_y][curr_c] = gate_wall
                        offset += 1
                self.grid[mid_y][mid_x] = door_char
                self.grid[mid_y - 1][mid_x] = "_"
                self.grid[mid_y + 1][mid_x] = "_"
            return
        
        # Для индустриальных стилей трассируем до первой жесткой границы стены
        cx, cy = n1['x'] + n1['w'] // 2, n1['y'] + n1['h'] // 2
        tx, ty = n2['x'] + n2['w'] // 2, n2['y'] + n2['h'] // 2
        # Трассируем по горизонтали контур стены n1
        curr_x, step_x = cx, (1 if tx > cx else -1)
        while curr_x != tx:
            if not (n1['x'] <= curr_x < n1['x'] + n1['w']):
                if 2 <= cy < self.height - 2 and 2 <= curr_x < self.width - 2:
                    self.grid[cy][curr_x] = door_char
                    # Зажимаем дверь стенами из конфига
                    self.grid[cy - 1][curr_x] = self.primary_wall
                    self.grid[cy + 1][curr_x] = self.primary_wall
                    return
            curr_x += step_x

        # Трассируем по вертикали контур стены n1
        curr_y, step_y = cy, (1 if ty > cy else -1)
        while curr_y != ty:
            if not (n1['y'] <= curr_y < n1['y'] + n1['h']):
                if 2 <= curr_y < self.height - 2 and 2 <= tx < self.width - 2:
                    self.grid[curr_y][tx] = door_char
                    self.grid[curr_y][tx - 1] = self.primary_wall
                    self.grid[curr_y][tx + 1] = self.primary_wall
                    return
            curr_y += step_y


    def _get_accessible_nodes_before_lock(self):
        accessible = set()
        queue = [0]  # СТРОГО ИСПРАВЛЕНО: Список, а не int!
        accessible.add(0)
        while queue:
            curr = queue.pop(0)
            for neighbor in self.nodes[curr]['edges']:
                if neighbor not in accessible:
                    edge_is_locked = any(
                        (curr == n1 and neighbor == n2 or curr == n2 and neighbor == n1) 
                        and etype == 'locked_blue' for n1, n2, etype in self.edges
                    )
                    if not edge_is_locked:
                        accessible.add(neighbor)
                        queue.append(neighbor)
        return list(accessible)

    def _spawn_hidden_key(self, key_char):
        accessible_nodes = []
        queue = [0]  # СТРОГО ИСПРАВЛЕНО: Список!
        visited_nodes = {0}
        while queue:
            curr = queue.pop(0)
            accessible_nodes.append(curr)
            for neighbor in self.nodes[curr]['edges']:
                if neighbor not in visited_nodes:
                    edge_is_locked = any(
                        (curr == n1 and neighbor == n2 or curr == n2 and neighbor == n1) 
                        and etype == 'locked_blue' for n1, n2, etype in self.edges
                    )
                    if not edge_is_locked:
                        visited_nodes.add(neighbor)
                        queue.append(neighbor)
        
        valid_nodes = [n_id for n_id in accessible_nodes if n_id != 0]
        if valid_nodes:
            k_node = self.nodes[random.choice(valid_nodes)]
            kx, ky = k_node['x'] + k_node['w'] // 2, k_node['y'] + k_node['h'] // 2
            if self.grid[ky][kx] == "_":
                self.grid[ky][kx] = key_char

    def validate_geometry(self):
        """
        ФАЗА 1.4: Исправленный геймплейный валидатор.
        Проверяет только гарантированную физическую проходимость уровня,
        полностью исключая вечные циклы из-за нелинейных коридоров.
        """
        # 1. Проверка монолитности внешнего контура (защита от краша рейкаста)
        for c in range(self.width):
            if self.grid[0][c] == "_" or self.grid[self.height - 1][c] == "_": return False
        for r in range(self.height):
            if self.grid[r][0] == "_" or self.grid[r][self.width - 1] == "_": return False

        # 2. Находим Spawn
        start_pos = None
        for r in range(self.height):
            for c in range(self.width):
                if self.grid[r][c] == "Spawn":
                    start_pos = (r, c)
                    break
            if start_pos: break
        if not start_pos: return False

        # 3. Находим Key
        key_pos = None
        for r in range(self.height):
            for c in range(self.width):
                if self.grid[r][c] == "key_blue":
                    key_pos = (r, c)
                    break
            if key_pos: break
        if not key_pos: return False

        # 4. Проверяем, может ли игрок дойти от Спавна до Ключа
        # В этой проверке синяя дверь для нас — стена (у нас еще нет ключа)
        can_reach_key = False
        visited = {start_pos}
        queue = [start_pos]
        
        while queue:
            curr_r, curr_c = queue.pop(0)
            if (curr_r, curr_c) == key_pos:
                can_reach_key = True
                break
                
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = curr_r + dr, curr_c + dc
                if 0 <= nr < self.height and 0 <= nc < self.width:
                    cell = self.grid[nr][nc]
                    # Синяя дверь считается непроходимой стеной на этом этапе
                    if (nr, nc) not in visited and cell not in self.valid_walls and cell != 'door_blue_key':
                        visited.add((nr, nc))
                        queue.append((nr, nc))
                        
        if not can_reach_key: 
            return False # Если ключ завалило или он недоступен — откат сида

        # 5. Ключ гарантированно в руках. Проверяем, можно ли от Ключа дойти до Выхода (Exit)
        # Теперь синяя дверь открыта и полностью проходима
        can_reach_exit = False
        visited_final = {key_pos}
        queue_final = [key_pos]
        
        while queue_final:
            curr_r, curr_c = queue_final.pop(0)
            if self.grid[curr_r][curr_c] == "Exit":
                can_reach_exit = True
                break
                
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = curr_r + dr, curr_c + dc
                if 0 <= nr < self.height and 0 <= nc < self.width:
                    cell = self.grid[nr][nc]
                    if (nr, nc) not in visited_final and cell not in self.valid_walls:
                        visited_final.add((nr, nc))
                        queue_final.append((nr, nc))

        return can_reach_exit


    def pass_decorations(self):
        d_cfg = self.biome.get('decor_settings', {})
        pool = d_cfg.get('pool', {})
        if not pool:
            return
        
        empty_cells = [(r, c) for r in range(self.height) for c in range(self.width) 
                      if self.grid[r][c] == "_" and self._is_adjacent_to_wall(r, c)]
        if not empty_cells:
            return
        
        max_decor = int(len(empty_cells) * d_cfg.get('density', 0.04))
        decor_count = 0
        items, weights = list(pool.keys()), [cfg['weight'] for cfg in pool.values()]
        random.shuffle(empty_cells)
        
        while decor_count < max_decor and empty_cells:
            r, c = empty_cells.pop()
            if self.grid[r][c] != "_":
                continue
            decor_key = random.choices(items, weights=weights)[0]
            cfg = pool[decor_key]
            cluster_cfg = cfg.get('cluster', {'type': 'single', 'chance': 0.0, 'size': 1})
            if self.spawned_counters.get(decor_key, 0) >= cfg.get('max_count', 99):
                continue
            if not self._check_min_distance(r, c, decor_key, cfg.get('min_dist', 0)):
                continue
            
            if random.random() < cluster_cfg.get('chance', 0.0) and cluster_cfg.get('type') != 'single':
                c_type, c_size = cluster_cfg.get('type', 'circle'), cluster_cfg.get('size', 2)
                if c_type == 'line':
                    dr, dc = random.choice([(0, 1), (1, 0)])
                    for step in range(c_size):
                        nr, nc = r + (dr * step), c + (dc * step)
                        if 1 <= nr < self.height - 1 and 1 <= nc < self.width - 1:
                            if self.grid[nr][nc] == "_" and self._check_min_distance(nr, nc, decor_key, cfg.get('min_dist', 0)):
                                if self.spawned_counters.get(decor_key, 0) < cfg.get('max_count', 99):
                                    self.grid[nr][nc] = decor_key
                                    self.spawned_counters[decor_key] = self.spawned_counters.get(decor_key, 0) + 1
                                    decor_count += 1
                elif c_type == 'circle':
                    for dr in range(-1, 2):
                        for dc in range(-1, 2):
                            nr, nc = r + dr, c + dc
                            if 1 <= nr < self.height - 1 and 1 <= nc < self.width - 1:
                                if random.random() < 0.65 and self.grid[nr][nc] == "_":
                                    if self.spawned_counters.get(decor_key, 0) < cfg.get('max_count', 99):
                                        self.grid[nr][nc] = decor_key
                                        self.spawned_counters[decor_key] = self.spawned_counters.get(decor_key, 0) + 1
                                        decor_count += 1
            else:
                self.grid[r][c] = decor_key
                self.spawned_counters[decor_key] = self.spawned_counters.get(decor_key, 0) + 1
                decor_count += 1

    def pass_entities(self, layer_type='npc'):
        cfg_layer = self.biome.get('npc_settings', {}) if layer_type == 'npc' else self.biome.get('loot_settings', {})
        pool = cfg_layer.get('pool', {})
        if not pool:
            return
        
        empty_cells, spawn_pos = [], None
        for r in range(self.height):
            for c in range(self.width):
                if self.grid[r][c] == "Spawn":
                    spawn_pos = (r, c)
                elif self.grid[r][c] == "_":
                    empty_cells.append((r, c))
        
        if spawn_pos:
            safe_radius = 4 if layer_type == 'npc' else 2
            empty_cells = [(r, c) for (r, c) in empty_cells 
                          if math.hypot(r - spawn_pos[0], c - spawn_pos[1]) > safe_radius]
        
        max_spawn = int(len(empty_cells) * cfg_layer.get('density', 0.015))
        spawn_count = 0
        items, weights = list(pool.keys()), [cfg['weight'] for cfg in pool.values()]
        random.shuffle(empty_cells)
        
        while spawn_count < max_spawn and empty_cells:
            r, c = empty_cells.pop()
            if self.grid[r][c] != "_":
                continue
            ent_key = random.choices(items, weights=weights)[0]
            cfg = pool[ent_key]
            if (r / self.height) < cfg.get('min_progress', 0.0):
                continue
            if self.spawned_counters.get(ent_key, 0) >= cfg.get('max_count', 99):
                continue
            if cfg.get('secret_only', False):
                is_in_secret = any(
                    node['type'] == 'secret_cave' and node['x'] <= c < node['x'] + node['w'] 
                    and node['y'] <= r < node['y'] + node['h'] for node in self.nodes.values()
                )
                if not is_in_secret:
                    continue
            
            obj_dist = cfg.get('min_dist', 4)
            cluster_cfg = cfg.get('cluster', {'type': 'single', 'chance': 0.0, 'size': 1})
            
            if layer_type == 'npc' and random.random() < cluster_cfg.get('chance', 0.0) and cluster_cfg.get('type') == 'circle':
                c_size = cluster_cfg.get('size', 2)
                self.grid[r][c] = ent_key
                self.spawned_counters[ent_key] = self.spawned_counters.get(ent_key, 0) + 1
                spawn_count += 1
                offsets = [(-2, 0), (2, 0), (0, -2), (0, 2), (-2, -2), (2, 2)]
                random.shuffle(offsets)
                added_in_squad = 1
                for dr, dc in offsets:
                    if added_in_squad >= c_size or spawn_count >= max_spawn:
                        break
                    nr, nc = r + dr, c + dc
                    if 1 <= nr < self.height - 1 and 1 <= nc < self.width - 1:
                        if self.grid[nr][nc] == "_":
                            if self.spawned_counters.get(ent_key, 0) < cfg.get('max_count', 99):
                                self.grid[nr][nc] = ent_key
                                self.spawned_counters[ent_key] = self.spawned_counters.get(ent_key, 0) + 1
                                spawn_count += 1
                                added_in_squad += 1
            else:
                self.grid[r][c] = ent_key
                self.spawned_counters[ent_key] = self.spawned_counters.get(ent_key, 0) + 1
                spawn_count += 1
            empty_cells = [(ec_r, ec_c) for (ec_r, ec_c) in empty_cells 
                          if math.hypot(ec_r - r, ec_c - c) > obj_dist]

    def validate_entities(self):
        spawn_pos = None
        for r in range(self.height):
            for c in range(self.width):
                if self.grid[r][c] == "Spawn":
                    spawn_pos = (r, c)
                    break
            if spawn_pos:
                break
        if not spawn_pos:
            return False
        
        npc_keys = ['AGG', 'CM']
        for dr in range(-5, 6):
            for dc in range(-5, 6):
                nr, nc = spawn_pos[0] + dr, spawn_pos[1] + dc
                if 0 <= nr < self.height and 0 <= nc < self.width:
                    if self.grid[nr][nc] in npc_keys:
                        return False
        
        window_size = 10
        for r in range(0, self.height - window_size, 6):
            for c in range(0, self.width - window_size, 6):
                local_npc_count = sum(1 for wr in range(window_size) for wc in range(window_size) 
                                     if self.grid[r + wr][c + wc] in npc_keys)
                if local_npc_count > 6:
                    return False
        return True

    def execute_pipeline_and_save(self):
        geometry_approved = False
        attempts_geo = 0
        while not geometry_approved and attempts_geo < 100:
            attempts_geo += 1
            self._clear_grid()
            self.build_macro_graph()
            self.pass_geometry()
            self.pass_textures()
            self.pass_points_of_interest()
            geometry_approved = self.validate_geometry()
            if not geometry_approved:
                self.seed = str(int(self.seed) + 1)
                random.seed(self.seed)
        
        if not geometry_approved:
            raise RuntimeError("Ошибка: Граф геометрии не сошелся за 100 попыток.")
        
        entities_approved = False
        attempts_ent = 0
        while not entities_approved and attempts_ent < 50:
            attempts_ent += 1
            for r in range(self.height):
                for c in range(self.width):
                    if self.grid[r][c] not in self.valid_walls and self.grid[r][c] not in ['Spawn', 'Exit', 'key_blue', 'door_normal', 'door_blue_key', 'secret_wall']:
                        self.grid[r][c] = "_"
            self.spawned_counters = {}
            self.pass_decorations()
            self.pass_entities(layer_type='npc')
            self.pass_entities(layer_type='loot')
            entities_approved = self.validate_entities()
            if not entities_approved:
                random.seed(self.seed + f"ent_try{attempts_ent}")
        
        formatted_map_lines = []
        for row in self.grid:
            json_row = json.dumps(row, ensure_ascii=False)
            formatted_map_lines.append(f"    {json_row}")
        map_json_string = "[\n" + ",\n".join(formatted_map_lines) + "\n  ]"
        
        meta_data = {
            "inventory": ["KNIFE", "COLT"],
            "starting_ammo": {"KNIFE": 1, "COLT": 60},
            "background": {
                "ceiling_texture": "resources/textures/rocks.png",
                "floor_texture": None,
                "ceiling_color": None,
                "floor_color": [40, 40, 40]
            },
            "generator_style": self.style,
            "generator_seed": self.seed
        }
        meta_json_string = json.dumps(meta_data, indent=2, ensure_ascii=False)
        
        final_json_content = "{\n" + f'  "map": {map_json_string},\n' + meta_json_string[2:]
        
        output_dir = os.path.join("resources", "levels")
        os.makedirs(output_dir, exist_ok=True)
        filename = os.path.join(output_dir, f"level_{self.level_num}.json")
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(final_json_content)
        
        print(f"\n🏁 [УСПЕХ ВЫПОЛНЕНИЯ] Карта уровня {self.level_num} успешно собрана!")
        print(f"-> Файл записи: {filename}")
        print(f"-> Масштаб: {self.width}x{self.height} | Стиль: {self.style.upper()}")
        print(f"-> Гео-попыток: {attempts_geo} | Энтити-попыток: {attempts_ent}")
        print(f"-> Итог спавна объектов: {self.spawned_counters}\n")

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("=== ИНТЕРАКТИВНЫЙ РЕЖИМ ГЕНЕРАТОРА ЦЕПЕЙ ===")
        while True:
            try:
                level_num = int(input("1. Введите номер уровня (например, 5): ").strip())
                break
            except ValueError:
                print("Ошибка: введите целое число.")
        
        while True:
            try:
                width_input = input("2a. Укажите ШИРИНУ карты в клетках (мин. 10): ").strip()
                width = int(width_input) if width_input else 100
                height_input = input("2b. Укажите ВЫСОТУ карты в клетках (мин. 15): ").strip()
                height = int(height_input) if height_input else 100
                if width >= 10 and height >= 15:
                    break
                print("Ошибка: Минимальные размеры карты — 10x15.")
            except ValueError:
                print("Ошибка: введите целые числа.")
        
        styles = ["hall", "vent", "lab", "out", "hang"]
        while True:
            style = input(f"3. Выберите стиль generation {styles}: ").strip().lower()
            if style in styles:
                break
            print(f"Ошибка: стиль должен быть одним из {styles}")
        
        seed_input = input("4. Укажите сид (Enter для случайного): ").strip()
        seed = seed_input if seed_input else None
        
        generator = PipelineLevelGenerator(
            width=width,
            height=height,
            style=style,
            seed=seed,
            level_num=level_num
        )
        generator.execute_pipeline_and_save()
    
    else:
        parser = argparse.ArgumentParser(description="Пайплайн-генератор уровней")
        parser.add_argument("level_num", type=int, help="Номер уровня")
        parser.add_argument("--width", type=int, default=100, help="Ширина")
        parser.add_argument("--height", type=int, default=100, help="Высота")
        parser.add_argument("--style", type=str, choices=["hall", "vent", "lab", "out", "hang"], 
                          default="out", help="Стиль")
        parser.add_argument("--seed", type=str, default=None, help="Сид")
        args = parser.parse_args()
        
        generator = PipelineLevelGenerator(
            width=max(10, args.width),
            height=max(15, args.height),
            style=args.style,
            seed=args.seed,
            level_num=args.level_num
        )
        generator.execute_pipeline_and_save()