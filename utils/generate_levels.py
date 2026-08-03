import os
import sys
import json
import math
import random
import argparse
import numpy as np

# Настройка путей импорта строго по вашему ТЗ
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.biome_data import BIOME_DATABASE

class PipelineLevelGenerator:
    def __init__(self, width=100, height=100, style='out', seed=None, level_num=4):
        """Полностью Data-Driven инициализация с поддержкой внешних параметров"""
        self.width = width
        self.height = height
        self.style = style
        self.level_num = level_num
        
        # Динамический рассчет секторов: убираем ручной ввод, считаем от размера и уровня
        base_rooms = 6 + (self.level_num * 2)
        area_factor = (self.width * self.height) // 2500  # Масштабирование от размера 50х50
        self.min_rooms = max(6, min(30, base_rooms + area_factor))
        
        if seed is None:
            self.seed = str(random.randint(100000, 999999))
        else:
            self.seed = str(seed)
        random.seed(self.seed)
        
        # Безопасный вынос биома из базы данных
        self.biome = BIOME_DATABASE.get(self.style, next(iter(BIOME_DATABASE.values())))
        
        # Матрица забивается базовыми списками строк "1"
        self.grid = [["1" for _ in range(self.width)] for _ in range(self.height)]
        self.spawned_counters = {}
        self.rooms_meta = [] 
        
        self.nodes = {}       
        self.edges = []       
        
        # Кешируем имена стен биома
        w_cfg = self.biome.get('walls', {})
        self.primary_wall = w_cfg.get('primary', {}).get('char', 'rocks')
        self.secondary_wall = w_cfg.get('secondary', {}).get('char', 'metal_crunch_wall')
        self.perimeter_wall = self.biome.get('geometry', {}).get('perimeter_wall', self.primary_wall)
        self.valid_walls = [self.primary_wall, self.secondary_wall, self.perimeter_wall, "1"]

    def _clear_grid(self):
        """Очистка сетки и внутренних структур графа перед гео-попыткой"""
        self.grid = [["1" for _ in range(self.width)] for _ in range(self.height)]
        self.nodes = {}
        self.edges = []
        self.rooms_meta = []
        self.spawned_counters = {}

    def _check_local_density(self, r, c, radius=9, max_allowed=2):
        """Heatmap-контроль: предотвращает появление непреодолимых диких куч мяса"""
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
        """Гарантирует соблюдение периодичности спавна редких объектов"""
        if min_dist <= 0:
            return True
        for dr in range(-min_dist, min_dist + 1):
            for dc in range(-min_dist, min_dist + 1):
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.height and 0 <= nc < self.width:
                    if self.grid[nr][nc] == char:
                        return False
        return True

    def _is_adjacent_to_wall(self, r, c):
        """Проверяет, соприкасается ли ячейка со стеной (для прижатия декораций)"""
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.height and 0 <= nc < self.width:
                if self.grid[nr][nc] in ['1', self.primary_wall, self.secondary_wall, 'L', 'G', 'M', 'C']:
                    return True
        return False

    def build_macro_graph(self):
        """Построение логического графа миссии уровня перед развертыванием в матрицу"""
        types_pool = ['canyon', 'plateau', 'canyon']
        self.nodes = {0: {'id': 0, 'type': 'spawn_zone', 'edges': [], 'name': 'Spawn'}}
        
        current_id = 1
        for i in range(self.min_rooms - 2):
            t = random.choice(types_pool)
            if i > (self.min_rooms // 2) and random.random() < 0.6:
                t = 'checkpoint'
            
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
        
        for _ in range(3):
            attach_to = random.randint(1, final_id - 2)
            self.nodes[current_id] = {'id': current_id, 'type': 'secret_cave', 'edges': [], 'name': 'Secret'}
            self.edges.append((attach_to, current_id, 'secret_wall'))
            self.nodes[attach_to]['edges'].append(current_id)
            self.nodes[current_id]['edges'].append(attach_to)
            current_id += 1

        cols = int(math.sqrt(len(self.nodes))) + 1
        rows = (len(self.nodes) // cols) + 1
        sect_w = (self.width - 8) // cols
        sect_h = (self.height - 8) // rows
        
        node_ids = list(self.nodes.keys())
        random.shuffle(node_ids)
        
        idx = 0
        for r in range(rows):
            for c in range(cols):
                if idx >= len(node_ids): break
                n_id = node_ids[idx]
                cx = 4 + c * sect_w + random.randint(1, max(1, sect_w - 9))
                cy = 4 + r * sect_h + random.randint(1, max(1, sect_h - 9))
                
                if self.nodes[n_id]['type'] in ['canyon', 'plateau']:
                    w, h = random.randint(8, 14), random.randint(8, 14)
                else:
                    w, h = random.randint(6, 8), random.randint(6, 8)
                    
                self.nodes[n_id].update({'x': cx, 'y': cy, 'w': w, 'h': h})
                r_type = 'secret' if self.nodes[n_id]['type'] == 'secret_cave' else 'normal'
                self.rooms_meta.append((cx, cy, w, h, r_type))
                idx += 1

    def pass_geometry(self):
        """Прорубает скелет дорог и генерирует органические ущелья извилистым блужданием"""
        # 1. Шумовая инициализация комнат
        for n_id, node in self.nodes.items():
            x, y, w, h = node['x'], node['y'], node['w'], node['h']
            for r in range(y, min(self.height - 2, y + h)):
                for c in range(x, min(self.width - 2, x + w)):
                    if node['type'] in ['canyon', 'plateau']:
                        self.grid[r][c] = "_" if random.random() < 0.65 else "1"
                    else:
                        self.grid[r][c] = "_"

        # 2. ИСПРАВЛЕНО: Широкие извилистые дороги с разделением по типам (Drunkard's Walk)
        for n1_id, n2_id, edge_type in self.edges:  # СТРОГО ИСПРАВЛЕНО: явно извлекаем edge_type!
            n1, n2 = self.nodes[n1_id], self.nodes[n2_id]
            cx, cy = n1['x'] + n1['w'] // 2, n1['y'] + n1['h'] // 2
            tx, ty = n2['x'] + n2['w'] // 2, n2['y'] + n2['h'] // 2
            
            while (cx, cy) != (tx, ty):
                # Если это путь к секрету — делаем узкую тропу (радиус 1), иначе — полноценный каньон (радиус 2)
                is_secret_edge = (edge_type == 'secret_wall')
                road_radius = 1 if is_secret_edge else 2
                
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
                    cx += dx
                    cy += dy
                    
                cx = max(2, min(self.width - 3, cx))
                cy = max(2, min(self.height - 3, cy))


        # 3. Клеточный автомат сбалансированной эрозии каньона
        for _ in range(3):
            next_grid = [row[:] for row in self.grid]
            for r in range(2, self.height - 2):
                for c in range(2, self.width - 2):
                    wall_count = 0
                    for dr in [-1, 0, 1]:
                        for dc in [-1, 0, 1]:
                            if self.grid[r + dr][c + dc] in self.valid_walls:
                                wall_count += 1
                                
                    if self.grid[r][c] in self.valid_walls:
                        if wall_count < 4: next_grid[r][c] = "_"
                    else:
                        if wall_count > 5: next_grid[r][c] = "1"
            self.grid = next_grid

        # 4. НАДЕЖНАЯ ФИКСАЦИЯ ПЕРИМЕТРА
        for c in range(self.width):
            self.grid[0][c] = self.perimeter_wall
            self.grid[self.height - 1][c] = self.perimeter_wall
        for r in range(self.height):
            self.grid[r][0] = self.perimeter_wall
            self.grid[r][self.width - 1] = self.perimeter_wall

    def pass_textures(self):
        """ПРОПОРЦИОНАЛЬНОЕ ТЕКСТУРИРОВАНИЕ СТЕН БИОМА"""
        w_cfg = self.biome.get('walls', {})
        population = [self.primary_wall, self.secondary_wall]
        weights = [w_cfg.get('primary', {}).get('weight', 85), 
                   w_cfg.get('secondary', {}).get('weight', 15)]
        for r in range(self.height):
            for c in range(self.width):
                if self.grid[r][c] == "1":
                    # СТРОГО ИСПРАВЛЕНО: Добавлен индекс, чтобы писать строку, а не список!
                    self.grid[r][c] = random.choices(population, weights=weights)[0]

    def pass_points_of_interest(self):
        """СТАРТ, ВЫХОД, ГАРАНТИРОВАННЫЙ COLT И УМНЫЕ ДВЕРИ ПО ЦЕНТРУ РЕБЕР"""
        spawn_node = self.nodes[0]
        center_x = spawn_node['x'] + spawn_node['w'] // 2
        center_y = spawn_node['y'] + spawn_node['h'] // 2
        self.grid[center_y][center_x] = "Spawn"
        
        if self.grid[center_y + 1][center_x] == "_":
            self.grid[center_y + 1][center_x] = "COLT"
        
        exit_node = next(n for n in self.nodes.values() if n['type'] == 'bunker_exit')
        self.grid[exit_node['y'] + exit_node['h'] // 2][exit_node['x'] + exit_node['w'] // 2] = "Exit"
        
        doors_cfg = self.biome.get('doors', {})
        door_normal = doors_cfg.get('normal', 'door_normal')
        door_locked = doors_cfg.get('locked', 'door_blue_key').strip("'")
        
        for n1_id, n2_id, edge_type in self.edges:
            if edge_type == 'normal' and random.random() > 0.4:
                if self.nodes[n1_id]['type'] not in ['canyon', 'plateau'] or self.nodes[n2_id]['type'] not in ['canyon', 'plateau']:
                    self._place_door_on_edge(n1_id, n2_id, door_normal)
            elif edge_type == 'locked_blue':
                self._place_door_on_edge(n1_id, n2_id, door_locked)
                self._spawn_hidden_key('key_blue')
            elif edge_type == 'secret_wall':
                self._place_door_on_edge(n1_id, n2_id, 'secret_wall')

    def _place_door_on_edge(self, n1_id, n2_id, door_char):
        """
        Искусственно возводит стену-шлюз поперек широкого коридора/каньона
        и врезает туда гермодверь, гарантируя изоляцию зон для рейкастера.
        """
        n1, n2 = self.nodes[n1_id], self.nodes[n2_id]
        mid_x = (n1['x'] + n1['w'] // 2 + n2['x'] + n2['w'] // 2) // 2
        mid_y = (n1['y'] + n1['h'] // 2 + n2['y'] + n2['h'] // 2) // 2
        
        if not (2 <= mid_y < self.height - 2 and 2 <= mid_x < self.width - 2):
            return

        # Определяем направление коридора (вертикальный или горизонтальный)
        # Сравниваем координаты центров комнат
        dx = abs(n1['x'] - n2['x'])
        dy = abs(n1['y'] - n2['y'])
        
        # Выбираем материал для шлюза блокпоста. 
        # Отлично подойдет металлическая стена, показывающая искусственную постройку в горах
        gate_wall = self.secondary_wall # 'metal_crunch_wall'
        
        if dx > dy:
            # Коридор преимущественно ГОРИЗОНТАЛЬНЫЙ. Строим ВЕРТИКАЛЬНУЮ стену-шлюз
            # Перегораживаем проход сверху и снизу от центральной точки двери
            for r_offset in [-3, -2, -1, 1, 2, 3]:
                curr_r = mid_y + r_offset
                if 1 <= curr_r < self.height - 1:
                    # Ставим стену только там, где сейчас пустота или техническая скала
                    if self.grid[curr_r][mid_x] in ["_", "1"] or self.grid[curr_r][mid_x] in self.valid_walls:
                        self.grid[curr_r][mid_x] = gate_wall
            
            # Врезаем саму дверь строго по центру шлюза
            self.grid[mid_y][mid_x] = door_char
            # Гарантируем, что перед дверью и за ней чисто (игрок пройдет)
            self.grid[mid_y][mid_x - 1] = "_"
            self.grid[mid_y][mid_x + 1] = "_"
            
        else:
            # Коридор преимущественно ВЕРТИКАЛЬНЫЙ. Строим ГОРИЗОНТАЛЬНУЮ стену-шлюз
            for c_offset in [-3, -2, -1, 1, 2, 3]:
                curr_c = mid_x + c_offset
                if 1 <= curr_c < self.width - 1:
                    if self.grid[mid_y][curr_c] in ["_", "1"] or self.grid[mid_y][curr_c] in self.valid_walls:
                        self.grid[mid_y][curr_c] = gate_wall
            
            # Врезаем дверь
            self.grid[mid_y][mid_x] = door_char
            self.grid[mid_y - 1][mid_x] = "_"
            self.grid[mid_y + 1][mid_x] = "_"


    def _spawn_hidden_key(self, key_char):
        """Ищет гарантированно доступную свободную ячейку на стартовом пути"""
        accessible_nodes = []
        queue = [0]
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
            kx = k_node['x'] + k_node['w'] // 2
            ky = k_node['y'] + k_node['h'] // 2
            if self.grid[ky][kx] == "_":
                self.grid[ky][kx] = key_char

    def validate_geometry(self):
        """Пайплайн геймдизайнерской валидации связности и плотности пустых ячеек"""
        for c in range(self.width):
            if self.grid[0][c] == "_" or self.grid[self.height - 1][c] == "_": return False
        for r in range(self.height):
            if self.grid[r][0] == "_" or self.grid[r][self.width - 1] == "_": return False

        # ИСПРАВЛЕНО: Смягчили геймплейный баланс пустоты для стиля 'out': от 35% до 70% карты
        total_cells = self.width * self.height
        empty_cells_count = sum(row.count("_") for row in self.grid)
        empty_percentage = empty_cells_count / total_cells
        
        if not (0.35 <= empty_percentage <= 0.70):
            return False

        start_pos = None
        for r in range(self.height):
            for c in range(self.width):
                if self.grid[r][c] == "Spawn":
                    start_pos = (r, c)
                    break
            if start_pos: break
        if not start_pos: return False

        has_key = False
        visited = {start_pos}
        queue = [start_pos]
        while queue:
            curr_r, curr_c = queue.pop(0)
            if self.grid[curr_r][curr_c] == "key_blue": has_key = True
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = curr_r + dr, curr_c + dc
                if 0 <= nr < self.height and 0 <= nc < self.width:
                    cell = self.grid[nr][nc]
                    if (nr, nc) not in visited and cell not in self.valid_walls and cell != 'door_blue_key':
                        visited.add((nr, nc))
                        queue.append((nr, nc))
        if not has_key: return False

        reached_exit = False
        visited_final = {start_pos}
        queue_final = [start_pos]
        while queue_final:
            curr_r, curr_c = queue_final.pop(0)
            if self.grid[curr_r][curr_c] == "Exit":
                reached_exit = True
                break
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = curr_r + dr, curr_c + dc
                if 0 <= nr < self.height and 0 <= nc < self.width:
                    cell = self.grid[nr][nc]
                    if (nr, nc) not in visited_final and cell not in self.valid_walls:
                        visited_final.add((nr, nc))
                        queue_final.append((nr, nc))
        return reached_exit

    # ==================================================================
    # 🛑 ВРЕМЕННЫЕ ЗАГЛУШКИ ДЛЯ НАПОЛНЕНИЯ ФАЗЫ 2
    # ==================================================================
    def pass_decorations(self):
        """
        ФАЗА 2 (ПРОХОД 4): Модернизированный попроцессный спавн декораций.
        Использует Flood-Fill кластеризацию для постройки линий баррикад и групп ящиков
        вдоль стен, строго считывая параметры из Data-Driven конфига биома.
        """
        d_cfg = self.biome.get('decor_settings', {})
        pool = d_cfg.get('pool', {})
        if not pool:
            return

        # Собираем свободные клетки, прилегающие к скалам/стенам для тактического спавна
        empty_cells = [
            (r, c) for r in range(self.height) for c in range(self.width) 
            if self.grid[r][c] == "_" and self._is_adjacent_to_wall(r, c)
        ]
        if not empty_cells:
            return

        # Рассчитываем лимит на основе плотности из конфига
        max_decor = int(len(empty_cells) * d_cfg.get('density', 0.04))
        decor_count = 0
        
        items = list(pool.keys())
        weights = [cfg['weight'] for cfg in pool.values()]
        
        # Перемешиваем стартовые точки
        random.shuffle(empty_cells)

        while decor_count < max_decor and empty_cells:
            r, c = empty_cells.pop()
            if self.grid[r][c] != "_":
                continue

            # 1. Выбираем базовый проп по весам из конфига биома
            decor_key = random.choices(items, weights=weights)[0]
            cfg = pool[decor_key]
            cluster_cfg = cfg.get('cluster', {'type': 'single', 'chance': 0.0, 'size': 1})

            # Проверяем глобальный лимит на этот объект
            if self.spawned_counters.get(decor_key, 0) >= cfg.get('max_count', 99):
                continue
                
            # Проверяем минимальную дистанцию спавна до аналогов
            if not self._check_min_distance(r, c, decor_key, cfg.get('min_dist', 0)):
                continue

            # 2. Логика КЛАСТЕРИЗАЦИИ
            # Если шанс выпал и тип отличный от single — запускаем умную группировку
            if random.random() < cluster_cfg.get('chance', 0.0) and cluster_cfg.get('type') != 'single':
                c_type = cluster_cfg.get('type', 'circle')
                c_size = cluster_cfg.get('size', 2)
                
                # --- ТИП ЛИНИЯ (Идеально для мешков с песком prop_sandbag_wall) ---
                if c_type == 'line':
                    # Выбираем случайное направление линии: горизонтальное или вертикальное
                    dr, dc = random.choice([(0, 1), (1, 0)])
                    for step in range(c_size):
                        nr, nc = r + (dr * step), c + (dc * step)
                        if 1 <= nr < self.height - 1 and 1 <= nc < self.width - 1:
                            if self.grid[nr][nc] == "_" and self._check_min_distance(nr, nc, decor_key, cfg.get('min_dist', 0)):
                                if self.spawned_counters.get(decor_key, 0) < cfg.get('max_count', 99):
                                    self.grid[nr][nc] = decor_key
                                    self.spawned_counters[decor_key] = self.spawned_counters.get(decor_key, 0) + 1
                                    decor_count += 1

                # --- ТИП КРУГ/КУЧА (Идеально для армейских ящиков prop_military_crate) ---
                elif c_type == 'circle':
                    # Заполняем локальную область вокруг стартовой точки в радиусе размера
                    for dr in range(-1, 2):
                        for dc in range(-1, 2):
                            nr, nc = r + dr, c + dc
                            if 1 <= nr < self.height - 1 and 1 <= nc < self.width - 1:
                                if random.random() < 0.65 and self.grid[nr][nc] == "_":
                                    if self.spawned_counters.get(decor_key, 0) < cfg.get('max_count', 99):
                                        self.grid[nr][nc] = decor_key
                                        self.spawned_counters[decor_key] = self.spawned_counters.get(decor_key, 0) + 1
                                        decor_count += 1
            
            # --- ОДИНОЧНЫЙ СПАВН (Если кластер не прокнул) ---
            else:
                self.grid[r][c] = decor_key
                self.spawned_counters[decor_key] = self.spawned_counters.get(decor_key, 0) + 1
                decor_count += 1


    def pass_entities(self, layer_type='npc'):
        """
        ФАЗА 2 (ПРОХОДЫ 5 и 6): Модернизированный DD-спавнер сущностей.
        Исключает скучивание врагов и забивание проходов с помощью
        динамического выжигания локального пула ячеек.
        """
        cfg_layer = self.biome.get('npc_settings', {}) if layer_type == 'npc' else self.biome.get('loot_settings', {})
        pool = cfg_layer.get('pool', {})
        if not pool:
            return

        # Собираем доступные ячейки (не трогаем Спавн и Зону безопасности вокруг игрока)
        empty_cells = []
        spawn_pos = None
        for r in range(self.height):
            for c in range(self.width):
                if self.grid[r][c] == "Spawn":
                    spawn_pos = (r, c)
                elif self.grid[r][c] == "_":
                    empty_cells.append((r, c))

        # Защита: убираем ячейки в радиусе 4 блоков от игрока, чтобы не умереть на старте
        if spawn_pos:
            empty_cells = [
                (r, c) for (r, c) in empty_cells 
                if math.hypot(r - spawn_pos[0], c - spawn_pos[1]) > 4
            ]

        max_spawn = int(len(empty_cells) * cfg_layer.get('density', 0.015))
        spawn_count = 0
        
        items = list(pool.keys())
        weights = [cfg['weight'] for cfg in pool.values()]
        
        random.shuffle(empty_cells)

        while spawn_count < max_spawn and empty_cells:
            # Берем случайную точку
            r, c = empty_cells.pop()
            if self.grid[r][c] != "_":
                continue

            ent_key = random.choices(items, weights=weights)[0]
            cfg = pool[ent_key]
            
            # 1. Фильтр прогрессии уровня
            progress = r / self.height
            if progress < cfg.get('min_progress', 0.0):
                continue

            # 2. Проверка глобального лимита
            if self.spawned_counters.get(ent_key, 0) >= cfg.get('max_count', 99):
                continue

            obj_dist = cfg.get('min_dist', 4)
            cluster_cfg = cfg.get('cluster', {'type': 'single', 'chance': 0.0, 'size': 1})

            # 3. ЛОГИКА СПАВНА СКВАДА ИЛИ ОДИНОЧКИ
            if layer_type == 'npc' and random.random() < cluster_cfg.get('chance', 0.0) and cluster_cfg.get('type') == 'circle':
                c_size = cluster_cfg.get('size', 2)
                
                # Ставим лидера отряда
                self.grid[r][c] = ent_key
                self.spawned_counters[ent_key] = self.spawned_counters.get(ent_key, 0) + 1
                spawn_count += 1
                
                # Ищем места для его напарников в радиусе, но СТРОГО не вплотную!
                # Перебираем ячейки на расстоянии ровно 2 клетки, чтобы они могли маневрировать
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
                # Одиночный спавн (лут или патрульный)
                self.grid[r][c] = ent_key
                self.spawned_counters[ent_key] = self.spawned_counters.get(ent_key, 0) + 1
                spawn_count += 1

            # 4. КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Выжигаем зону вокруг всего сквада/одиночки из пула!
            # Это гарантирует, что следующий сквад не упадет им на голову.
            empty_cells = [
                (ec_r, ec_c) for (ec_r, ec_c) in empty_cells
                if math.hypot(ec_r - r, ec_c - c) > obj_dist
            ]

    def pass_entities(self, layer_type='npc'):
        """
        ФАЗА 2 (ПРОХОДЫ 5 и 6): Универсальный DD-спавнер сущностей и предметов.
        Использует прогрессию, динамическое выжигание локального пула ячеек 
        и кластеризацию объектов снабжения.
        """
        # Динамически переключаем пул настроек в зависимости от слоя (npc или loot)
        cfg_layer = self.biome.get('npc_settings', {}) if layer_type == 'npc' else self.biome.get('loot_settings', {})
        pool = cfg_layer.get('pool', {})
        if not pool:
            return

        # Собираем доступные ячейки, исключая точку Spawn игрока
        empty_cells = []
        spawn_pos = None
        for r in range(self.height):
            for c in range(self.width):
                if self.grid[r][c] == "Spawn":
                    spawn_pos = (r, c)
                elif self.grid[r][c] == "_":
                    empty_cells.append((r, c))

        # Защитная зона вокруг игрока (для предметов радиус меньше, например 2 клетки, чтобы лут мог лежать рядом)
        if spawn_pos:
            safe_radius = 4 if layer_type == 'npc' else 2
            empty_cells = [
                (r, c) for (r, c) in empty_cells 
                if math.hypot(r - spawn_pos[0], c - spawn_pos[1]) > safe_radius
            ]

        # Вычисляем лимит спавна на основе плотности слоя из конфига биома
        max_spawn = int(len(empty_cells) * cfg_layer.get('density', 0.02))
        spawn_count = 0
        
        items = list(pool.keys())
        weights = [cfg['weight'] for cfg in pool.values()]
        
        random.shuffle(empty_cells)

        while spawn_count < max_spawn and empty_cells:
            r, c = empty_cells.pop()
            if self.grid[r][c] != "_":
                continue

            ent_key = random.choices(items, weights=weights)[0]
            cfg = pool[ent_key]
            
            # 1. Фильтр прогрессии (оружие и мощный лут смещаются к выходу)
            progress = r / self.height
            if progress < cfg.get('min_progress', 0.0):
                continue

            # 2. Проверка глобального лимита на карту
            if self.spawned_counters.get(ent_key, 0) >= cfg.get('max_count', 99):
                continue

            # 3. Проверка секретности (элитный лут прячется в секретных пещерах графа)
            if cfg.get('secret_only', False):
                # Проверяем, находится ли клетка в секретной зоне графа
                is_in_secret = False
                for node in self.nodes.values():
                    if node['type'] == 'secret_cave':
                        if node['x'] <= c < node['x'] + node['w'] and node['y'] <= r < node['y'] + node['h']:
                            is_in_secret = True
                            break
                if not is_in_secret:
                    continue # Пропускаем спавн, если это обычный каньон

            obj_dist = cfg.get('min_dist', 3)
            cluster_cfg = cfg.get('cluster', {'type': 'single', 'chance': 0.0, 'size': 1})

            # 4. ЛОГИКА СПАВНА ДЛЯ NPC И КЛАТЕРИЗАЦИИ ЛУТА (ПАЧКИ ПАТРОНОВ)
            if random.random() < cluster_cfg.get('chance', 0.0) and cluster_cfg.get('type') == 'circle':
                c_size = cluster_cfg.get('size', 2)
                
                # Спавним базовый предмет
                self.grid[r][c] = ent_key
                self.spawned_counters[ent_key] = self.spawned_counters.get(ent_key, 0) + 1
                spawn_count += 1
                
                # Кладем припасы пачкой в смежные ячейки (радиус 1), имитируя ящик снабжения
                offsets = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1)]
                random.shuffle(offsets)
                
                added_in_cluster = 1
                for dr, dc in offsets:
                    if added_in_cluster >= c_size or spawn_count >= max_spawn:
                        break
                    nr, nc = r + dr, c + dc
                    if 1 <= nr < self.height - 1 and 1 <= nc < self.width - 1:
                        if self.grid[nr][nc] == "_":
                            if self.spawned_counters.get(ent_key, 0) < cfg.get('max_count', 99):
                                self.grid[nr][nc] = ent_key
                                self.spawned_counters[ent_key] = self.spawned_counters.get(ent_key, 0) + 1
                                spawn_count += 1
                                added_in_cluster += 1
            else:
                # Одиночный спавн предмета (аптечка, броня, пушка)
                self.grid[r][c] = ent_key
                self.spawned_counters[ent_key] = self.spawned_counters.get(ent_key, 0) + 1
                spawn_count += 1

            # 5. ЖЕСТКОЕ ВЫЖИГАНИЕ ХИТМАПА: убираем соседние ячейки, предотвращая кашу лута
            empty_cells = [
                (ec_r, ec_c) for (ec_r, ec_c) in empty_cells
                if math.hypot(ec_r - r, ec_c - c) > obj_dist
            ]


    def validate_entities(self):
        """
        ФАЗА 2.4: Валидация геймплейного баланса сущностей.
        Проверяет зону безопасности игрока, плотность ИИ и экономику лута.
        """
        # Находим координаты игрока
        spawn_pos = None
        for r in range(self.height):
            for c in range(self.width):
                if self.grid[r][c] == "Spawn":
                    spawn_pos = (r, c)
                    break
            if spawn_pos: break
            
        if not spawn_pos:
            return False

        # 1. КРИТЕРИЙ: Проверка зоны безопасности вокруг игрока
        # В радиусе 5 клеток не должно быть ни одного NPC (AGG, CM)
        npc_keys = ['AGG', 'CM'] # Сюда можно добавить любые новые ключи ИИ из твоей БД
        for dr in range(-5, 6):
            for dc in range(-5, 6):
                nr, nc = spawn_pos[0] + dr, spawn_pos[1] + dc
                if 0 <= nr < self.height and 0 <= nc < self.width:
                    if self.grid[nr][nc] in npc_keys:
                        return False # Враг слишком близко к старту!

        # 2. КРИТЕРИЙ: Проверка на перенасыщение (Локальные кучи мяса)
        # Сканируем карту скользящим окном 10x10 ячеек
        window_size = 10
        for r in range(0, self.height - window_size, 4): # Шаг сканирования 4 клетки
            for c in range(0, self.width - window_size, 4):
                local_npc_count = 0
                for wr in range(window_size):
                    for wc in range(window_size):
                        if self.grid[r + wr][c + wc] in npc_keys:
                            local_npc_count += 1
                # Если в зоне 10х10 скопилось больше 5 врагов — это непроходимый затор
                if local_npc_count > 5:
                    return False

        # 3. КРИТЕРИЙ: Экономический баланс (Аптечки против Врагов)
        total_enemies = sum(self.grid[r].count(k) for r in range(self.height) for k in npc_keys)
        total_health = sum(self.grid[r].count("health") for r in range(self.height))
        
        if total_enemies > 0:
            health_to_enemy_ratio = total_health / total_enemies
            # Если аптечек на уровне меньше, чем 1 штука на 4 врагов — хардкор неиграбелен
            if health_to_enemy_ratio < 0.25:
                return False

        return True



    # ==================================================================
    # 💾 ИСПРАВЛЕННЫЙ СУПЕР-КОНВЕЙЕР: СТРОГОЕ СОХРАНЕНИЕ В JSON
    # ==================================================================
    def execute_pipeline_and_save(self):
        """Запускает последовательный конвейер проходов с двухуровневой валидацией"""
        # ФАЗА 1: Утверждение геометрии скал и дверей
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

        # ФАЗА 2: Утверждение расстановки NPC и лута (с независимым откатом)
        entities_approved = False
        attempts_ent = 0
        
        while not entities_approved and attempts_ent < 50:
            attempts_ent += 1
            
            # Очищаем ТОЛЬКО сущности, лут и декор, сохраняя готовую геометрию стен!
            for r in range(self.height):
                for c in range(self.width):
                    if self.grid[r][c] not in self.valid_walls and self.grid[r][c] not in ['Spawn', 'Exit', 'key_blue', 'door_normal', 'door_blue_key', 'secret_wall']:
                        self.grid[r][c] = "_"
            
            self.spawned_counters = {} # Сброс счетчиков
            
            # Повторный спавн наполнения
            self.pass_decorations()
            self.pass_entities(layer_type='npc')
            self.pass_entities(layer_type='loot')
            
            # Проверка наполнения новым валидатором
            entities_approved = self.validate_entities()
            if not entities_approved:
                # Сдвигаем рандом для сущностей, чтобы они легли иначе
                random.seed(self.seed + f"_ent_try_{attempts_ent}")
                
        if not entities_approved:
            print("⚠️ Предупреждение: Наполнение не идеально, но пропущено по мягким критериям.")

        # СБОРКА И ЗАПИСЬ JSON (Твой оригинальный алгоритм пакета)
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
                "floor_color": [20, 20, 25]
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
            
        print(f"\n🏁 [Пайплайн-Успех] Карта уровня {self.level_num} успешно создана всеми 6-ю проходами!")
        print(f"-> Гео-попыток: {attempts_geo} | Энтити-попыток: {attempts_ent}")
        print(f"-> Заспавненные объекты: {self.spawned_counters}\n")

# ==================================================================
# 🕹️ ОРИГИНАЛЬНЫЙ БЛОК ВВОДА С КОНСОЛИ (БЕЗ ОПРОСА КОЛИЧЕСТВА КОМНАТ)
# ==================================================================
if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("=== ИНТЕРАКТИВНЫЙ РЕЖИМ ГЕНЕРАТОРА ЦЕПЕЙ ===")
        while True:
            try:
                level_num = int(input("1. Введите номер уровня (например, 4): ").strip())
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
        
        seed_input = input("4. Укажите сид (нажмите Enter для случайного): ").strip()
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
        parser.add_argument("--width", type=int, default=100, help="Ширина карты")
        parser.add_argument("--height", type=int, default=100, help="Высота карты")
        parser.add_argument("--style", type=str, choices=["hall", "vent", "lab", "out", "hang"], 
                          default="out", help="Стиль биома")
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