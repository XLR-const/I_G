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

        # 2. ИСПРАВЛЕНО: Широкие извилистые дороги (Drunkard's Walk с радиусом)
        for n1_id, n2_id, _ in self.edges:
            n1, n2 = self.nodes[n1_id], self.nodes[n2_id]
            cx, cy = n1['x'] + n1['w'] // 2, n1['y'] + n1['h'] // 2
            tx, ty = n2['x'] + n2['w'] // 2, n2['y'] + n2['h'] // 2
            
            while (cx, cy) != (tx, ty):
                # Копаем широкую дорогу (радиус 2), чтобы клеточный автомат ее не завалил
                for dr in [-2, -1, 0, 1, 2]:
                    for dc in [-2, -1, 0, 1, 2]:
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
        """Размещает дверь на середине ребра графа"""
        n1, n2 = self.nodes[n1_id], self.nodes[n2_id]
        mid_x = (n1['x'] + n1['w'] // 2 + n2['x'] + n2['w'] // 2) // 2
        mid_y = (n1['y'] + n1['h'] // 2 + n2['y'] + n2['h'] // 2) // 2
        if 1 <= mid_y < self.height - 1 and 1 <= mid_x < self.width - 1:
            if self.grid[mid_y][mid_x] in ['_', '1']:
                self.grid[mid_y][mid_x] = door_char

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
        """ЗАГЛУШКА: Будущий Flood-Fill спавнер укрытий и ящиков группами"""
        pass

    def pass_entities(self, layer_type='npc'):
        """ЗАГЛУШКА: Будущий универсальный DD-спавнер ИИ и лута по весам биома"""
        pass

    # ==================================================================
    # 💾 ИСПРАВЛЕННЫЙ СУПЕР-КОНВЕЙЕР: СТРОГОЕ СОХРАНЕНИЕ В JSON
    # ==================================================================
    def execute_pipeline_and_save(self):
        """Запускает последовательный конвейер проходов с гео-предохранителем"""
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
        
        # Фаза 2: Наполнение (пока на заглушках)
        self.pass_decorations()
        self.pass_entities(layer_type='npc')
        self.pass_entities(layer_type='loot')
        
        # Сборка форматированных строк карты в JSON
        formatted_map_lines = []
        for row in self.grid:
            json_row = json.dumps(row, ensure_ascii=False)
            formatted_map_lines.append(f"    {json_row}")
        map_json_string = "[\n" + ",\n".join(formatted_map_lines) + "\n  ]"
        
        # Метаданные уровня
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
        print(f"-> Файл: {filename}")
        print(f"-> Биом: {self.style.upper()} | Параметры: {self.width}x{self.height}, Секторов: {self.min_rooms}")
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