import os
import sys
import json
import math
import random

# Настройка путей импорта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.biome_data import BIOME_DATABASE

class PipelineLevelGenerator:
    def __init__(self, width=100, height=100, style='out', seed=None, level_num=4):
        self.width = width
        self.height = height
        self.style = style
        self.level_num = level_num
        
        if seed is None:
            self.seed = str(random.randint(100000, 999999))
        else:
            self.seed = str(seed)
        random.seed(self.seed)

        self.biome = BIOME_DATABASE.get(self.style, BIOME_DATABASE['out'])
        self.grid = [["0" for _ in range(self.width)] for _ in range(self.height)]
        self.spawned_counters = {}

    def _check_min_distance(self, r, c, char, min_dist):
        if min_dist <= 0: return True
        for dr in range(-min_dist, min_dist + 1):
            for dc in range(-min_dist, min_dist + 1):
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.height and 0 <= nc < self.width:
                    if self.grid[nr][nc] == char: return False
        return True

    # ⚙️ ПРОХОД 1: ГЕОМЕТРИЯ (МАГИСТРАЛЬ + НАНИЗАННЫЕ КОМНАТЫ)
    def pass_geometry(self):
        self.grid = [["1" for _ in range(self.width)] for _ in range(self.height)]
        center_x = self.width // 2
        for r in range(1, self.height - 1):
            self.grid[r][center_x - 1] = "_"
            self.grid[r][center_x] = "_"
            self.grid[r][center_x + 1] = "_"

        num_rooms = 15
        for i in range(num_rooms):
            rw, rh = random.randint(6, 12), random.randint(6, 12)
            ry = random.randint(5, self.height - rh - 6)
            rx = random.randint(center_x - rw + 2, center_x - 2) if i % 2 == 0 else random.randint(center_x - 1, center_x + rw - 3)
            
            for r in range(ry, ry + rh):
                for c in range(rx, rx + rw):
                    if 1 <= r < self.height - 1 and 1 <= c < self.width - 1:
                        self.grid[r][c] = "_"

    # =============================================================
    # ⚙️ ПРОХОД 2: ТЕКСТУРИРОВАНИЕ СТЕН (ИСПРАВЛЕНО НА СТРОКИ)
    # =============================================================
    def pass_textures(self):
        w_cfg = self.biome['walls']
        p_char, p_weight = w_cfg['primary']['char'], w_cfg['primary']['weight']
        s_char, s_weight = w_cfg['secondary']['char'], w_cfg['secondary']['weight']
        population, weights = [p_char, s_char], [p_weight, s_weight]

        for r in range(self.height):
            for c in range(self.width):
                if self.grid[r][c] == "1":
                    # 🔥 КРИТИЧЕСКИЙ ФИКС: Забираем строго нулевой элемент списка!
                    # Теперь в матрицу запишется чистая строка "rocks" или "metal_crunch_wall"
                    self.grid[r][c] = random.choices(population, weights=weights)[0]

    # ⚙️ ПРОХОД 3: СТАРТ И ВЫХОД СТРОГО ПО PDF
    def pass_points_of_interest(self):
        center_x = self.width // 2
        # Твои маркеры из PDF: 'Spawn' и 'Exit'
        self.grid[4][center_x] = "Spawn"
        self.grid[self.height - 5][center_x] = "Exit"

    # ⚙️ ПРОХОД 4: ДЕКОРАЦИИ С ПОДДЕРЖКОЙ КУЧНОСТИ И ЛИНИЙ
    def pass_decorations(self):
        d_cfg = self.biome['decor_settings']
        pool = d_cfg['pool']
        empty_cells = [(r, c) for r in range(self.height) for c in range(self.width) if self.grid[r][c] == "_"]
        if not empty_cells: return
        
        max_decor = int(len(empty_cells) * d_cfg['density'])
        decor_count = 0
        items, weights = list(pool.keys()), [cfg['weight'] for cfg in pool.values()]

        attempts = 0
        while decor_count < max_decor and attempts < 1500 and empty_cells:
            attempts += 1
            r, c = random.choice(empty_cells)
            if self.grid[r][c] != "_": continue

            decor_key = random.choices(items, weights=weights)[0]
            cfg = pool[decor_key]
            char = decor_key

            if self.spawned_counters.get(char, 0) >= cfg['max_count']: continue
            if not self._check_min_distance(r, c, char, cfg['min_dist']): continue

            c_type = cfg['cluster_type']
            c_size = cfg['cluster_size']
            
            if c_type == 'line' and random.random() < cfg['cluster_chance']:
                # Извлекаем смещения по строкам (dr) и столбцам (dc) из выбранного кортежа направления
                dr, dc = random.choice([(0, 1), (1, 0)]) # Горизонтально или вертикально
                
                for step in range(c_size):
                    # 🔥 ЧЕСТНЫЙ ИСПРАВЛЕННЫЙ РАСЧЕТ ВЕКТOРА ПО ОСЯМ:
                    # Умножаем шаг на сдвиг отдельно для строк и отдельно для столбцов
                    nr = r + dr * step
                    nc = c + dc * step
                    
                    if 0 <= nr < self.height and 0 <= nc < self.width and self.grid[nr][nc] == "_":
                        self.grid[nr][nc] = char
                        decor_count += 1
                self.spawned_counters[char] = self.spawned_counters.get(char, 0) + 1

            else:
                self.grid[r][c] = char
                self.spawned_counters[char] = self.spawned_counters.get(char, 0) + 1
                decor_count += 1

    # ⚙️ ПРОХОД 5: ЗОНАЛЬНЫЙ УМНЫЙ СПАВН СТРОГО ПО PDF КЛЮЧАМ
    def pass_entities(self, layer_type='npc'):
        cfg_layer = self.biome['npc_settings'] if layer_type == 'npc' else self.biome['loot_settings']
        pool = cfg_layer['pool']
        empty_cells = [(r, c) for r in range(self.height) for c in range(self.width) if self.grid[r][c] == "_"]
        if not empty_cells: return

        max_spawn = int(len(empty_cells) * cfg_layer['density'])
        spawn_count = 0
        items, weights = list(pool.keys()), [cfg['weight'] for cfg in pool.values()]

        attempts = 0
        while spawn_count < max_spawn and attempts < 1500 and empty_cells:
            attempts += 1
            r, c = random.choice(empty_cells)
            if self.grid[r][c] != "_": continue

            ent_key = random.choices(items, weights=weights)[0]
            cfg = pool[ent_key]
            char = ent_key
            
            progress = r / self.height
            # Защита: тяжелый Бот CM и убер-пушка Shotgun спавнятся только в конце
            if char in ['CM', 'shotgun'] and progress < 0.65: continue
            if char == 'armor' and progress < 0.30: continue

            if self.spawned_counters.get(char, 0) >= cfg['max_count']: continue
            if not self._check_min_distance(r, c, char, cfg['min_dist']): continue

            c_type = cfg['cluster_type']
            c_size = cfg['cluster_size']

            if c_type == 'circle' and random.random() < cfg['cluster_chance']:
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < self.height and 0 <= nc < self.width and self.grid[nr][nc] == "_":
                            if spawn_count < max_spawn:
                                self.grid[nr][nc] = char
                                spawn_count += 1
                self.spawned_counters[char] = self.spawned_counters.get(char, 0) + 1
            else:
                self.grid[r][c] = char
                self.spawned_counters[char] = self.spawned_counters.get(char, 0) + 1
                spawn_count += 1

    def execute_pipeline_and_save(self):
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

        meta_data = {
            "inventory": ["Knife", "Colt"],
            "starting_ammo": { "Knife": 1, "Colt": 15 },
            "background": {
                "ceiling_texture": "resources/textures/rocks.png",
                "floor_texture": None,
                "ceiling_color": (100, 100, 20),
                "floor_color": [30, 15, 15]
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

        print(f"🏁 [Пайплайн-Успех] Карта уровня {self.level_num} успешно создана!")
        print(f"-> Файл: {filename}")
        print(f"-> Использованы ключи: {list(self.spawned_counters.keys())}\n")

if __name__ == "__main__":
    generator = PipelineLevelGenerator(width=100, height=100, style='out', seed=None, level_num=4)
    generator.execute_pipeline_and_save()
