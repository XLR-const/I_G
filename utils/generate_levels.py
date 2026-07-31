import os
import sys
import json
import math
import random
import argparse
import numpy as np

# Настройка путей импорта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.biome_data import BIOME_DATABASE


class PipelineLevelGenerator:
    def __init__(self, width=100, height=100, style='out', seed=None, level_num=4, min_rooms=16):
        """Полностью Data-Driven инициализация с поддержкой внешних параметров интерактива"""
        self.width = width
        self.height = height
        self.style = style
        self.level_num = level_num
        self.min_rooms = min_rooms
        
        if seed is None:
            self.seed = str(random.randint(100000, 999999))
        else:
            self.seed = str(seed)
            
        random.seed(self.seed)
        
        # Безопасный вынос биома из базы данных
        self.biome = BIOME_DATABASE.get(self.style, next(iter(BIOME_DATABASE.values())))
        
        # Матрица забивается базовыми стенами "1"
        self.grid = [["1" for _ in range(self.width)] for _ in range(self.height)]
        self.spawned_counters = {}
        self.rooms_meta = []  # Координаты бункеров для умных дверей

        # Кешируем имена стен биома
        w_cfg = self.biome.get('walls', {})
        self.primary_wall = w_cfg.get('primary', {}).get('char', 'rocks')
        self.secondary_wall = w_cfg.get('secondary', {}).get('char', 'metal_crunch_wall')
        self.valid_walls = [self.primary_wall, self.secondary_wall]

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

    # ==================================================================
    # ⚙️ ПРОХОД 1: ГЕОМЕТРИЯ (ДИНАМИЧЕСКИЕ МАГИСТРАЛИ И БУНКЕРЫ-КПП)
    # ==================================================================
    def pass_geometry(self):
        """Прорубает сквозной скелет дорог, комнат и генерирует запертые секретки"""
        path_channels = [self.width // 4, self.width // 2, (self.width // 4) * 3]
        
        # Прорубаем 3 магистрали
        for center_x in path_channels:
            for r in range(1, self.height - 1):
                self.grid[r][center_x] = "_"
                self.grid[r][center_x + 1] = "_"
                
        # Обходные петли-развилки
        cross_junctions = [self.height // 5, self.height // 2, (self.height // 5) * 4]
        for cross_y in cross_junctions:
            for c in range(self.width // 4, (self.width // 4) * 3 + 2):
                self.grid[cross_y][c] = "_"
                self.grid[cross_y + 1][c] = "_"
                
        # Спавним секционные бункеры на основе переданного num_rooms
        for i in range(self.min_rooms):
            rw, rh = random.randint(6, 11), random.randint(6, 11)
            ry = random.randint(6, self.height - rh - 7)
            target_channel = random.choice(path_channels)
            rx = random.randint(target_channel - rw + 2, target_channel + i % 2)
            
            self.rooms_meta.append((rx, ry, rw, rh, 'normal'))
            
            for r in range(ry, ry + rh):
                for c in range(rx, rx + rw):
                    if 1 <= r < self.height - 1 and 1 <= c < self.width - 1:
                        self.grid[r][c] = "_"

        # Врезаем 3 секретные комнаты, запечатанные стеной secret_wall
        for _ in range(3):
            s_x = random.randint(15, self.width - 15)
            s_y = random.randint(15, self.height - 15)
            if self.grid[s_y][s_x] == "1" and (self.grid[s_y + 1][s_x] == "_" or self.grid[s_y - 1][s_x] == "_"):
                self.grid[s_y][s_x] = "_"
                if self.grid[s_y + 1][s_x] == "_":
                    self.grid[s_y][s_x] = "secret_wall"
                else:
                    self.grid[s_y][s_x] = "secret_wall"
                self.rooms_meta.append((s_x, s_y, 2, 1, 'secret'))

    # ==================================================================
    # ⚙️ ПРОХОД 2: ПРОПОРЦИОНАЛЬНОЕ ТЕКСТУРИРОВАНИЕ СТЕН БИОМА
    # ==================================================================
    def pass_textures(self):
        w_cfg = self.biome.get('walls', {})
        population = [self.primary_wall, self.secondary_wall]
        weights = [w_cfg.get('primary', {}).get('weight', 85), w_cfg.get('secondary', {}).get('weight', 15)]
        
        for r in range(self.height):
            for c in range(self.width):
                if self.grid[r][c] == "1":
                    self.grid[r][c] = random.choices(population, weights=weights)[0]

    # ==================================================================
    # ⚙️ ПРОХОД 3: СТАРТ, ВЫХОД, ГАРАНТИРОВАННЫЙ COLT И УМНЫЕ ДВЕРИ ПО ЦЕНТРУ
    # ==================================================================
    def pass_points_of_interest(self):
        center_x = self.width // 2
        self.grid[3][center_x] = "Spawn"
        self.grid[self.height - 5][center_x] = "Exit"
        
        if self.grid[4][center_x] == "_":
            self.grid[4][center_x] = "COLT"
            
        doors_cfg = self.biome.get('doors', {})
        door_normal = doors_cfg.get('normal', 'door_normal')
        door_locked = doors_cfg.get('locked', 'door_blue_key').strip("'")
        locked_door_spawned = False
        
        for rx, ry, rw, rh, r_type in self.rooms_meta:
            if r_type == 'secret':
                continue
            
            wall_options = ['south', 'north', 'east']
            random.shuffle(wall_options)
            door_placed = False
            
            for option in wall_options:
                if door_placed:
                    break
                
                if option == 'south':
                    mid_c = rx + rw // 2
                    if 0 <= mid_c < self.width and 0 <= ry + rh < self.height:
                        if self.grid[ry + rh][mid_c] in self.valid_walls and self.grid[ry + rh + 1][mid_c] == "_":
                            if not locked_door_spawned and ry > self.height // 2:
                                self.grid[ry + rh][mid_c] = door_locked
                                locked_door_spawned = True
                                self._spawn_hidden_key('key_blue')
                            else:
                                self.grid[ry + rh][mid_c] = door_normal
                            door_placed = True
                            
                elif option == 'north':
                    mid_c = rx + rw // 2
                    if 0 <= mid_c < self.width and 0 <= ry - 1 < self.height:
                        if self.grid[ry - 1][mid_c] in self.valid_walls and self.grid[ry - 2][mid_c] == "_":
                            self.grid[ry - 1][mid_c] = door_normal
                            door_placed = True
                            
                elif option == 'east':
                    mid_r = ry + rh // 2
                    if 0 <= rx + rw < self.width and 0 <= mid_r < self.height:
                        if self.grid[mid_r][rx + rw] in self.valid_walls and self.grid[mid_r][rx + rw + 1] == "_":
                            self.grid[mid_r][rx + rw] = door_normal
                            door_placed = True

    def _spawn_hidden_key(self, key_char):
        for r in range(12, self.height // 3):
            for c in range(15, self.width - 15):
                if self.grid[r][c] == "_":
                    self.grid[r][c] = key_char
                    print(f"🔑 [Секрет] Ключ {key_char} успешно спрятан на уровне!")
                    return

    # ==================================================================
    # ⚙️ ПРОХОД 4: ДЕКОРАЦИИ ПО ЦЕПЯМ МАРКОВА С ПРИЖАТИЕМ К СТЕНАМ
    # ==================================================================
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
        items = list(pool.keys())
        weights = [cfg['weight'] for cfg in pool.values()]
        random.shuffle(empty_cells)
        
        while decor_count < max_decor and empty_cells:
            r, c = empty_cells.pop()
            if self.grid[r][c] != "_":
                continue
            
            neighbors = []
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                if 0 <= r + dr < self.height and 0 <= c + dc < self.width:
                    neighbors.append(self.grid[r + dr][c + dc])
            
            if 'prop_sandbag_wall' in neighbors and random.random() < 0.85 and 'prop_sandbag_wall' in pool:
                decor_key = 'prop_sandbag_wall'
            elif 'prop_military_crate' in neighbors and random.random() < 0.70 and 'prop_military_crate' in pool:
                decor_key = 'prop_military_crate'
            else:
                decor_key = random.choices(items, weights=weights)[0]
            
            cfg = pool[decor_key]
            
            if self.spawned_counters.get(decor_key, 0) >= cfg.get('max_count', 99):
                continue
            if not self._check_min_distance(r, c, decor_key, cfg.get('min_dist', 0)):
                continue
            
            self.grid[r][c] = decor_key
            self.spawned_counters[decor_key] = self.spawned_counters.get(decor_key, 0) + 1
            decor_count += 1

    # ==================================================================
    # ⚙️ ПРОХОД 5 и 6: МАРКОВСКИЙ КОНТРОЛЬ ПЛОТНОСТИ И ЗОНИРОВАНИЕ (NPC/ЛУТ)
    # ==================================================================
    def pass_entities(self, layer_type='npc'):
        cfg_layer = self.biome.get('npc_settings', {}) if layer_type == 'npc' else self.biome.get('loot_settings', {})
        pool = cfg_layer.get('pool', {})
        if not pool:
            return
        
        empty_cells = [(r, c) for r in range(self.height) for c in range(self.width) if self.grid[r][c] == "_"]
        if not empty_cells:
            return
        
        max_spawn = int(len(empty_cells) * cfg_layer.get('density', 0.02))
        spawn_count = 0
        items = list(pool.keys())
        weights = [cfg['weight'] for cfg in pool.values()]
        random.shuffle(empty_cells)
        
        while spawn_count < max_spawn and empty_cells:
            r, c = empty_cells.pop()
            if self.grid[r][c] != "_":
                continue
            
            neighbors = []
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                if 0 <= r + dr < self.height and 0 <= c + dc < self.width:
                    neighbors.append(self.grid[r + dr][c + dc])
            
            progress = r / self.height
            
            if layer_type == 'npc':
                if 'AGG' in neighbors and random.random() < 0.75 and 'AGG' in pool:
                    ent_key = 'AGG'
                elif 'prop_sandbag_wall' in neighbors and random.random() < 0.50 and 'AGG' in pool:
                    ent_key = 'AGG'
                else:
                    ent_key = random.choices(items, weights=weights)[0]
            else:
                if ('ak47' in neighbors or 'shotgun' in neighbors) and random.random() < 0.85:
                    available_loot = [k for k in ['health', 'armor'] if k in pool]
                    ent_key = random.choice(available_loot) if available_loot else random.choices(items, weights=weights)[0]
                else:
                    ent_key = random.choices(items, weights=weights)[0]
            
            cfg = pool[ent_key]
            
            if ent_key in ['CM', 'shotgun'] and progress < 0.60:
                continue
            if ent_key == 'ak47' and progress < 0.35:
                continue
            if ent_key == 'armor' and progress < 0.15:
                continue
            
            max_local = 1 if ent_key in ['CM', 'shotgun', 'ak47', 'armor'] else 3
            if not self._check_local_density(r, c, radius=9, max_allowed=max_local):
                continue
            
            if self.spawned_counters.get(ent_key, 0) >= cfg.get('max_count', 99):
                continue
            if not self._check_min_distance(r, c, ent_key, cfg.get('min_dist', 0)):
                continue
            
            self.grid[r][c] = ent_key
            self.spawned_counters[ent_key] = self.spawned_counters.get(ent_key, 0) + 1
            spawn_count += 1

    # ==================================================================
    # 💾 СБОРКА И ЗАПИСЬ РЕЗУЛЬТАТА В JSON ПАКЕТ СТРУКТУРЫ
    # ==================================================================
    def execute_pipeline_and_save(self):
        """Запускает последовательный конвейер проходов"""
        self.pass_geometry()
        self.pass_textures()
        self.pass_points_of_interest()
        self.pass_decorations()
        self.pass_entities(layer_type='npc')
        self.pass_entities(layer_type='loot')
        
        formatted_map_lines = []
        for row in self.grid:
            json_row = json.dumps(row, ensure_ascii=False)
            formatted_map_lines.append(f"    {json_row}")
        
        map_json_string = "[\n" + ",\n".join(formatted_map_lines) + "\n  ]"
        
        # Передаем хардкоженный COLT и KNIFE капсом строго по твоему ТЗ
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


if __name__ == "__main__":
    # Проверяем, запущен ли скрипт в интерактивном консольном режиме
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
        
        while True:
            try:
                rooms_input = input("3. Введите количество комнат/секторов (2-30) [по умолчанию 16]: ").strip()
                num_rooms = int(rooms_input) if rooms_input else 16
                if 2 <= num_rooms <= 30:
                    break
                print("Ошибка: количество комнат должно быть от 2 до 30.")
            except ValueError:
                print("Ошибка: введите целое число.")
        
        styles = ["hall", "vent", "lab", "out", "hang"]
        while True:
            style = input(f"4. Выберите стиль генерации {styles}: ").strip().lower()
            if style in styles:
                break
            print(f"Ошибка: стиль должен быть одним из {styles}")
        
        seed_input = input("5. Укажите сид (нажмите Enter для случайного): ").strip()
        seed = seed_input if seed_input else None
        
        # Запуск полноценного 6-проходного генератора с полученными через интерактив данными!
        generator = PipelineLevelGenerator(
            width=width, height=height, style=style, seed=seed, 
            level_num=level_num, min_rooms=num_rooms
        )
        generator.execute_pipeline_and_save()
    
    # Режим чтения флагов командной строки (из твоего файла интерактива)
    else:
        parser = argparse.ArgumentParser(description="Пайплайн-генератор уровней")
        parser.add_argument("level_num", type=int, help="Номер уровня")
        parser.add_argument("--width", type=int, default=100, help="Ширина карты")
        parser.add_argument("--height", type=int, default=100, help="Высота карты")
        parser.add_argument("--rooms", type=int, default=16, help="Количество комнат")
        parser.add_argument("--style", type=str, choices=["hall", "vent", "lab", "out", "hang"], 
                           default="out", help="Стиль биома")
        parser.add_argument("--seed", type=str, default=None, help="Сид")
        args = parser.parse_args()
        
        level_num = args.level_num
        width = max(10, args.width)
        height = max(15, args.height)
        num_rooms = max(2, min(30, args.rooms))
        style = args.style
        seed = args.seed
        
        # Запуск полноценного 6-проходного генератора с полученными через интерактив данными!
        generator = PipelineLevelGenerator(
            width=width, height=height, style=style, seed=seed, 
            level_num=level_num, min_rooms=num_rooms
        )
        generator.execute_pipeline_and_save()