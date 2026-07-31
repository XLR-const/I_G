import os
import sys
import json
import math
import random
import numpy as np

# Настройка путей импорта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.biome_data import BIOME_DATABASE

# ==================================================================
# 📂 DATA-DRIVEN КОНФИГУРАЦИЯ С ХАРДКОЖЕННЫМИ НАЧАЛЬНЫМИ ПАРАМЕТРАМИ
# ==================================================================
CONFIG = {
    "MAP_WIDTH": 100,         # Ширина карты ячеек
    "MAP_HEIGHT": 100,        # Высота карты ячеек
    "BIOME_STYLE": "out",     # Текущий биом из базы данных ('out', 'lab')
    "SEED": "777888",         # Хардкоженный сид уровня (None для полного рандома)
    "LEVEL_NUM": 4,           # Номер генерируемого уровня для файла
    "MIN_ROOMS": 16,          # Количество бункеров-КПП на карте
    "STARTING_WEAPONS": ["KNIFE", "COLT"],  # Начальное оружие игрока КАПСОМ строго по WEAPON_CONFIG
    "STARTING_AMMO": {"KNIFE": 1, "COLT": 60}  # Начальный боезапас (подняли до 60)
}


class PipelineLevelGenerator:
    def __init__(self, config=CONFIG):
        """Инициализирует конвейер генератора на основе Data-Driven конфигурации"""
        self.width = config["MAP_WIDTH"]
        self.height = config["MAP_HEIGHT"]
        self.style = config["BIOME_STYLE"]
        self.level_num = config["LEVEL_NUM"]
        self.config = config
        
        if config["SEED"] is None:
            self.seed = str(random.randint(100000, 999999))
        else:
            self.seed = str(config["SEED"])
            
        random.seed(self.seed)
        
        # Безопасно вытягиваем биом
        self.biome = BIOME_DATABASE.get(self.style, next(iter(BIOME_DATABASE.values())))
        
        # Забиваем карту стенами "1"
        self.grid = [["1" for _ in range(self.width)] for _ in range(self.height)]
        self.spawned_counters = {}
        self.rooms_meta = []  # Метаданные бункеров для умной врезки дверей
        
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
    # ⚙️ ПРОХОД 1: ГЕОМЕТРИЯ (УЛЬТИМАТИВНЫЙ ТРЁХРУКАВНЫЙ ГРАФ С РАЗВИЛКАМИ)
    # ==================================================================
    def pass_geometry(self):
        # Изначально заливаем всё базовой стеной
        self.grid = [["1" for _ in range(self.width)] for _ in range(self.height)]
        
        # Очищаем метаданные комнат перед заполнением, чтобы не было мусора
        self.rooms_meta = []
        
        # Три магистральных рукава дорог (Лево, Центр, Право)
        path_channels = [self.width // 4, self.width // 2, (self.width // 4) * 3]
        for center_x in path_channels:
            for r in range(1, self.height - 1):
                self.grid[r][center_x] = "_"
                self.grid[r][center_x + 1] = "_"

        # Горизонтальные перемычки-развилки
        cross_junctions = [self.height // 5, self.height // 2, (self.height // 5) * 4]
        for cross_y in cross_junctions:
            for c in range(self.width // 4, (self.width // 4) * 3 + 2):
                self.grid[cross_y][c] = "_"
                self.grid[cross_y + 1][c] = "_"

        # Нанизываем просторные закрытые бункеры-КПП
        num_rooms = 14
        for i in range(num_rooms):
            rw = random.randint(6, 11)
            rh = random.randint(6, 11)
            ry = random.randint(6, self.height - rh - 7)
            
            target_channel = random.choice(path_channels)
            rx = random.randint(target_channel - rw + 2, target_channel + 1)
            
            # 🔥 ГАРАНТИРУЕМ СТРОГО 4 ЭЛЕМЕНТА В КОРТЕЖЕ:
            self.rooms_meta.append((int(rx), int(ry), int(rw), int(rh)))
            
            for r in range(ry, ry + rh):
                for c in range(rx, rx + rw):
                    if 1 <= r < self.height - 1 and 1 <= c < self.width - 1:
                        self.grid[r][c] = "_"

    # ==================================================================
    # ⚙️ ПРОХОД 2: ПРОПОРЦИОНАЛЬНОЕ ТЕКСТУРИРОВАНИЕ СТЕН
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
    # ⚙️ ПРОХОД 3: СТАРТ, ВЫХОД, ГАРАНТИРОВАННЫЙ СТАРТОВЫЙ COLT И ДВЕРИ
    # ==================================================================
    def pass_points_of_interest(self):
        center_x = self.width // 2
        
        # Точки старта и финиша
        self.grid[2][center_x] = "Spawn"
        self.grid[self.height - 4][center_x] = "Exit"
        
        # 🔥 ИСПРАВЛЕНО: Клодём строго 'colt' маленькими буквами по твоей концепции!
        if self.grid[3][center_x] == "_":
            self.grid[3][center_x] = "colt"
            print("🎯 [Баланс] Подбираемый предмет 'colt' успешно заспавнен под ногами игрока!")

        door_normal = self.biome['doors']['normal']
        door_locked = self.biome['doors']['locked']
        locked_door_spawned = False
        
        for rx, ry, rw, rh in self.rooms_meta:
            door_placed = False
            for c in range(rx + 2, rx + rw - 2):
                if 0 <= c < self.width and 0 <= ry + rh < self.height:
                    if self.grid[ry + rh][c] in ['rocks', 'metal_crunch_wall'] and self.grid[ry + rh + 1][c] == "_":
                        if not locked_door_spawned and ry > self.height // 2:
                            self.grid[ry + rh][c] = door_locked
                            locked_door_spawned = True
                            self._spawn_hidden_key('key_blue')
                        else:
                            self.grid[ry + rh][c] = door_normal
                        door_placed = True
                        break 
            
            if not door_placed:
                for c in range(rx + 1, rx + rw - 1):
                    if 0 <= c < self.width and 0 <= ry - 1 < self.height:
                        if self.grid[ry - 1][c] in ['rocks', 'metal_crunch_wall'] and self.grid[ry - 2][c] == "_":
                            self.grid[ry - 1][c] = door_normal
                            door_placed = True
                            break
                            
            if not door_placed:
                for r in range(ry + 1, ry + rh - 1):
                    if 0 <= rx + rw < self.width and 0 <= r < self.height:
                        if self.grid[r][rx + rw] in ['rocks', 'metal_crunch_wall'] and self.grid[r][rx + rw + 1] == "_":
                            self.grid[r][rx + rw] = door_normal
                            break


    # ==================================================================
    # ⚙️ ПРОХОД 4: ДЕКОРАЦИИ С УТОПЛЕНИЕМ В ВЫЕМКИ СТЕН (WALL CARVING)
    # Декорации больше никогда не спавнятся под ногами в коридорах!
    # ==================================================================
    def pass_decorations(self):
        d_cfg = self.biome['decor_settings']
        pool = d_cfg['pool']
        
        # 1. Считаем лимит декораций от общего числа пустых клеток
        empty_count = sum(1 for r in range(self.height) for c in range(self.width) if self.grid[r][c] == "_")
        max_decor = int(empty_count * d_cfg['density'])
        decor_count = 0
        
        items = list(pool.keys())
        weights = [cfg['weight'] for cfg in pool.values()]

        # 2. Ищем ВСЕ клетки, которые сейчас являются стенами, но граничат с пустым коридором
        # Это идеальные кандидаты для выгрызания ниш!
        wall_types = ['rocks', 'metal_crunch_wall']
        
        attempts = 0
        while decor_count < max_decor and attempts < 3000:
            attempts += 1
            
            # Берем случайную координату на карте (пропуская самые крайние внешние границы)
            r = random.randint(2, self.height - 3)
            c = random.randint(2, self.width - 3)
            
            # Нам нужна строго клетка стены!
            if self.grid[r][c] not in wall_types:
                continue

            # Проверяем соседние клетки (вверх, вниз, влево, вправо)
            # Нам нужно, чтобы стена граничила СТРОГО с пустым проходом '_', но не с дверями или игроком
            neighbors = [
                self.grid[r-1][c], self.grid[r+1][c], 
                self.grid[r][c-1], self.grid[r][c+1]
            ]
            
            # Если эта стена глухая (вокруг только другие стены) или граничит с объектами — пропускаем
            if "_" not in neighbors:
                continue

            # Выбираем декорацию по весу из паспорта биома
            decor_key = random.choices(items, weights=weights)[0]
            cfg = pool[decor_key]
            char = decor_key

            # Проверка жестких лимитов и радиусов исключения
            if self.spawned_counters.get(char, 0) >= cfg['max_count']: continue
            if not self._check_min_distance(r, c, char, cfg['min_dist']): continue

            c_type = cfg['cluster_type']
            c_size = cfg['cluster_size']
            
            if c_type == 'line' and random.random() < cfg['cluster_chance']:
                # Для линий (баррикад мешков) выгрызаем нишу-полосу вдоль дороги
                dr, dc = random.choice([(0, 1), (1, 0)])
                for step in range(c_size):
                    nr = r + dr * step
                    nc = c + dc * step
                    # Выгрызаем только если это блоки стен
                    if 0 <= nr < self.height and 0 <= nc < self.width and self.grid[nr][nc] in wall_types:
                        self.grid[nr][nc] = char
                        decor_count += 1
                self.spawned_counters[char] = self.spawned_counters.get(char, 0) + 1
            else:
                # 🔥 ОДИНOЧНОЕ УТOПЛЕНИЕ: Превращаем блок стены в декорацию!
                # Дорога остается нетронутой, а пропсы уходят вглубь стены
                self.grid[r][c] = char
                self.spawned_counters[char] = self.spawned_counters.get(char, 0) + 1
                decor_count += 1


    # ==================================================================
    # ⚙️ ПРОХОД 5 И 6: СТОПРОЦЕНТНО ДИНАМИЧЕСКИЙ ЗОНАЛЬНЫЙ СПАВН (БЕЗ ХАРДКОДА)
    # Автоматически высчитывает прогресс карты по Y для баланса сложности!
    # ==================================================================
    def pass_entities(self, layer_type='npc'):
        cfg_layer = self.biome['npc_settings'] if layer_type == 'npc' else self.biome['loot_settings']
        pool = cfg_layer['pool']
        
        # Собираем пустые ячейки для спавна
        empty_cells = [(r, c) for r in range(self.height) for c in range(self.width) if self.grid[r][c] == "_"]
        if not empty_cells: 
            return

        max_spawn = int(len(empty_cells) * cfg_layer['density'])
        spawn_count = 0
        
        items = list(pool.keys())
        weights = [cfg['weight'] for cfg in pool.values()]

        attempts = 0
        while spawn_count < max_spawn and attempts < 2500 and empty_cells:
            attempts += 1
            r, c = random.choice(empty_cells)
            if self.grid[r][c] != "_": 
                continue

            # Достаем случайный объект на основе весов
            ent_key = random.choices(items, weights=weights)[0]
            cfg = pool[ent_key]
            char = ent_key
            
            # =============================================================
            # 📐 АВТОМАТИЧЕСКАЯ УМНАЯ МАТЕМАТИКА ЗОНИРОВАНИЯ СЛОЖНОСТИ:
            # Считаем прогресс клетки от верха (0.0 - старт) до низа (1.0 - выход)
            # =============================================================
            progress = r / self.height
            
            # 1. Автоматический баланс ОРУЖИЯ и БОССОВ:
            # Дробовики (shotgun) и пулеметчики (CM) могут родиться только в финальной трети карты!
            if char in ['CM', 'shotgun'] and progress < 0.65:
                continue
                
            # 2. Автоматы (ak47) появляются строго начиная со второй трети уровня
            if char == 'ak47' and progress < 0.35:
                continue
                
            # 3. Базовая защита спавна: броня (armor) не валяется прямо у входа
            if char == 'armor' and progress < 0.20:
                continue

            # =============================================================
            # 🧠 МАТЕМАТИЧЕСКИЙ ФИЛЬТР ЛОКАЛЬНОЙ ПЛОТНОСТИ (HEATMAP):
            # Если это тяжелый юнит или оружие — лимит строго 1 штука на сектор,
            # чтобы они не кучковались. Для рядовых врагов и аптечек — до 3.
            # =============================================================
            is_heavy_or_rare = char in ['CM', 'shotgun', 'ak47', 'armor']
            max_local = 1 if is_heavy_or_rare else 3
            
            if not self._check_local_density(r, c, radius=9, max_allowed=max_local):
                continue

            # Проверяем жесткий лимит штук на карту и минимальную дистанцию
            if self.spawned_counters.get(char, 0) >= cfg['max_count']: 
                continue
            if not self._check_min_distance(r, c, char, cfg['min_dist']): 
                continue

            # Логика геометрической кучности (circle)
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


    # ==================================================================
    # 💾 ГЛАВНЫЙ СБОРЩИК КОНВЕЙЕРА И ЗАПИСЬ В JSON
    # ==================================================================
    def execute_pipeline_and_save(self):
        self.pass_geometry()
        self.pass_textures()
        self.pass_points_of_interest()
        self.pass_decorations()
        self.pass_entities(layer_type='npc')
        self.pass_entities(layer_type='loot')
        
        # Форматируем красивую горизонтальную матрицу JSON
        formatted_map_lines = []
        for row in self.grid:
            json_row = json.dumps(row, ensure_ascii=False)
            formatted_map_lines.append(f"    {json_row}")
        
        map_json_string = "[\n" + ",\n".join(formatted_map_lines) + "\n  ]"
        
        # Полностью Data-Driven вынос инвентаря на основе захардкоженного CONFIG
        meta_data = {
            "inventory": self.config["STARTING_WEAPONS"],
            "starting_ammo": self.config["STARTING_AMMO"],
            "background": {
                "ceiling_texture": "resources/textures/rocks.png",
                "floor_texture": None,
                "ceiling_color": None,
                "floor_color": [20, 10, 10]
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
        print(f"-> Файл сохранен: {filename}")
        print(f"-> Итоговый баланс заспавненных штук: {self.spawned_counters}\n")


if __name__ == "__main__":
    # Запуск генератора на основе Data-Driven настроек из CONFIG
    generator = PipelineLevelGenerator(CONFIG)
    generator.execute_pipeline_and_save()