import sys
import json
import random
import os
import math
import argparse

class LevelGenerator:
    def __init__(self, width=18, height=48):
        self.width = width
        self.height = height

    def _carve_rect(self, grid, x, y, w, h):
        for i in range(y, min(y + h, self.height - 2)):
            for j in range(x, min(x + w, self.width - 2)):
                if 1 <= j < self.width - 1 and 1 <= i < self.height - 1:
                    grid[i][j] = "_"

    def generate_and_save(self, level_num, seed, style, num_rooms):
        # Инициализируем сид случайности
        if seed:
            random.seed(seed)
        else:
            seed = str(random.randint(100000, 999999))
            random.seed(seed)
        
        # Заливаем карту монолитными стенами "1"
        grid = [["1" for _ in range(self.width)] for _ in range(self.height)]

        playable_height = self.height - 8
        section_h = playable_height // num_rooms
        rooms_y_centers = []

        # -------------------------------------------------------------
        # ГЕНЕРАЦИЯ СТРУКТУРЫ ПО СТИЛЯМ
        # -------------------------------------------------------------
        
        if style == "lab":
            # Стиль ЛАБОРАТОРИЯ: Прямая сквозная шахта-коридор по центру
            center_corridor_x = self.width // 2 - 1
            for y in range(2, self.height - 2):
                grid[y][center_corridor_x] = "_"
                grid[y][center_corridor_x + 1] = "_"

            # Генерируем боковые комнаты-боксы
            for i in range(num_rooms):
                min_y = 4 + (i * section_h)
                rh = random.randint(5, max(5, section_h - 2))
                ry = random.randint(min_y, min_y + section_h - rh - 1 if section_h > rh else min_y)
                
                # Случайно выбираем сторону: левая комната или правая
                if random.choice([True, False]):
                    # Левый бокс
                    rw = random.randint(4, 5)
                    rx = 2
                    self._carve_rect(grid, rx, ry, rw, rh)
                    # Проход в центральный коридор
                    grid[ry + rh // 2][center_corridor_x - 1] = "_"
                    grid[ry + rh // 2][center_corridor_x] = "_"
                else:
                    # Правый бокс
                    rw = random.randint(4, 5)
                    rx = center_corridor_x + 2
                    self._carve_rect(grid, rx, ry, rw, rh)
                    # Проход в центральный коридор
                    grid[ry + rh // 2][center_corridor_x + 1] = "_"
                    grid[ry + rh // 2][center_corridor_x + 2] = "_"
                    
                rooms_y_centers.append((center_corridor_x + 1, ry + rh // 2, ry, ry + rh))

        elif style == "out":
            # Стиль УЛИЦА: Вырезаем огромный сквозной полигон под открытым небом
            self._carve_rect(grid, 1, 1, self.width - 2, self.height - 2)
            
            # Возводим внутри редкие строения, бункеры или заборы-КПП
            for i in range(num_rooms):
                min_y = 4 + (i * section_h)
                bw = random.randint(5, 7)
                bh = random.randint(5, 6)
                bx = random.randint(2, self.width - bw - 2)
                by = random.randint(min_y, min_y + max(1, section_h - bh - 1))
                
                # Заливаем эту зону стеной (строение на улице)
                for y in range(by, by + bh):
                    for x in range(bx, bx + bw):
                        if 1 <= x < self.width - 1 and 1 <= y < self.height - 1:
                            grid[y][x] = "1"
                
                # Вырезаем внутренность домика (комнату внутри бункера)
                for y in range(by + 1, by + bh - 1):
                    for x in range(bx + 1, bx + bw - 1):
                        grid[y][x] = "_"
                        
                # Прорубаем дверь в бункер
                grid[by + bh - 1][bx + bw // 2] = "_"
                rooms_y_centers.append((bx + bw // 2, by + bh // 2, by, by + bh))

        else:
            # Стили HALL и VENT (классическая зачистка по секциям)
            for i in range(num_rooms):
                min_y = 4 + (i * section_h)
                max_y = min_y + section_h - 2
                
                if style == "hall":
                    rw = random.randint(10, self.width - 4)
                    rh = random.randint(6, max(6, section_h - 3))
                    rx = random.randint(2, self.width - rw - 2)
                    ry = random.randint(min_y, max(min_y, max_y - rh))
                    self._carve_rect(grid, rx, ry, rw, rh)
                    if random.choice([True, False]):
                        self._carve_rect(grid, rx - 1, ry + 1, 1, rh - 2)
                        self._carve_rect(grid, rx + rw, ry + 1, 1, rh - 2)
                else:  # vent
                    rw = random.randint(4, 6)
                    rh = random.randint(4, 5)
                    rx = random.randint(2, self.width - rw - 2)
                    ry = random.randint(min_y, max(min_y, max_y - rh))
                    self._carve_rect(grid, rx, ry, rw, rh)
                    
                rooms_y_centers.append((rx + rw // 2, ry + rh // 2, ry, ry + rh))

            # Прокладываем извилистые коридоры для Hall и Vent
            for i in range(num_rooms - 1):
                cx1, cy1, _, r1_bottom = rooms_y_centers[i]
                cx2, cy2, r2_top, _ = rooms_y_centers[i+1]
                start_y, end_y = r1_bottom, r2_top
                
                if start_y >= end_y:
                    continue
                    
                for y in range(start_y, end_y + 1):
                    t = (y - start_y) / (end_y - start_y) if end_y != start_y else 0.5
                    if style == "hall":
                        amp = 1.2
                        center_x = int((cx1 + (cx2 - cx1) * t) + amp * math.sin(t * math.pi))
                        center_x = max(2, min(self.width - 5, center_x))
                        grid[y][center_x] = "_"
                        grid[y][center_x + 1] = "_"
                        grid[y][center_x + 2] = "_"
                    else:  # vent
                        amp = 2.5
                        center_x = int((cx1 + (cx2 - cx1) * t) + amp * math.sin(t * math.pi))
                        center_x = max(1, min(self.width - 3, center_x))
                        grid[y][center_x] = "_"
                        if random.choice([True, False]) and center_x + 1 < self.width - 1:
                            grid[y][center_x + 1] = "_"

        # -------------------------------------------------------------
        # РАССТАНОВКА СТАРТА И ВЫХОДА (Исправленные индексы)
        # -------------------------------------------------------------
        if style == "lab":
            grid[3][self.width // 2] = "S"
            grid[self.height - 4][self.width // 2] = "E"
        elif style == "out":
            grid[3][self.width // 2] = "S"
            grid[self.height - 4][self.width // 2] = "E"
        else:
            first_room_x = rooms_y_centers[0][0]
            first_room_y = rooms_y_centers[0][1]
            grid[first_room_y][first_room_x] = "S"
            
            last_room_x = rooms_y_centers[-1][0]
            grid[self.height - 4][last_room_x] = "E"

        # Настройки цвета под уровень
        r_ceil = max(50, 180 - level_num * 15)
        g_ceil = max(30, 100 - level_num * 8)
        b_ceil = max(30, 100 - level_num * 8)
        r_floor = max(20, 60 - level_num * 5)
        g_floor = max(10, 30 - level_num * 2)
        b_floor = max(10, 30 - level_num * 2)

        # Построчное параллельное горизонтальное форматирование для читаемости JSON
        formatted_map_lines = []
        for row in grid:
            json_row = json.dumps(row, ensure_ascii=False)
            formatted_map_lines.append(f"    {json_row}")
        
        map_json_string = "[\n" + ",\n".join(formatted_map_lines) + "\n  ]"

        meta_data = {
            "inventory": ["Pistol", "Shotgun", "Machine Gun", "Plasma Gun"],
            "starting_ammo": { "Pistol": 40, "Shotgun": 20, "Machine Gun": 400, "Plasma Gun": 15 },
            "background": {
                "ceiling_texture": "resources/textures/red_sky.png" if style == "out" else "resources/textures/ceiling.png",
                "floor_texture": None,
                "ceiling_color": [r_ceil, g_ceil, b_ceil],
                "floor_color": [r_floor, g_floor, b_floor]
            },
            "generator_style": style,
            "generator_seed": seed
        }

        meta_json_string = json.dumps(meta_data, indent=2, ensure_ascii=False)
        final_json_content = "{\n" + f'  "map": {map_json_string},\n' + meta_json_string[2:]

        output_dir = os.path.join("resources", "levels")
        os.makedirs(output_dir, exist_ok=True)
        
        filename = os.path.join(output_dir, f"level_{level_num}.json")
        with open(filename, "w", encoding="utf-8") as f:
            f.write(final_json_content)
        
        print(f"\n[Успех] Уровень {level_num} успешно сгенерирован!")
        print(f"-> Файл: {filename}")
        print(f"-> Параметры: Сид='{seed}', Стиль='{style}', Комнат={num_rooms}\n")


if __name__ == "__main__":
    # Если скрипт запущен вообще без аргументов, включается пошаговый интерактивный опрос
    if len(sys.argv) == 1:
        print("=== ИНТЕРАКТИВНЫЙ РЕЖИМ ГЕНЕРАТОРА ===")
        
        # 1. Запрос номера уровня
        while True:
            try:
                level_num = int(input("1. Введите номер уровня (например, 1): ").strip())
                break
            except ValueError:
                print("Ошибка: введите целое число.")
        
        # 2. Запрос стиля
        styles = ["hall", "vent", "lab", "out"]
        while True:
            style = input(f"2. Выберите стиль генерации {styles}: ").strip().lower()
            if style in styles:
                break
            print(f"Ошибка: стиль должен быть одним из {styles}")

        # 3. Запрос сида
        seed_input = input("3. Укажите сид (нажмите Enter для случайного): ").strip()
        seed = seed_input if seed_input else None

        # 4. Запрос количества комнат
        while True:
            try:
                rooms_input = input("4. Введите количество комнат/секторов (2-5) [по умолчанию 3]: ").strip()
                num_rooms = int(rooms_input) if rooms_input else 3
                if 2 <= num_rooms <= 5:
                    break
                print("Ошибка: количество комнат должно быть от 2 до 5.")
            except ValueError:
                print("Ошибка: введите целое число.")

    else:
        # Режим чтения стандартных флагов, если вы передаете аргументы сразу в консоли
        parser = argparse.ArgumentParser(description="Генератор уровней")
        parser.add_argument("level_num", type=int, help="Номер уровня")
        parser.add_argument("--seed", type=str, default=None, help="Сид")
        parser.add_argument("--style", type=str, choices=["hall", "vent", "lab", "out"], default="hall", help="Стиль")
        parser.add_argument("--rooms", type=int, default=3, help="Количество комнат (2-5)")
        
        args = parser.parse_args()
        level_num = args.level_num
        seed = args.seed
        style = args.style
        num_rooms = max(2, min(5, args.rooms))

    # Финальный запуск сборки уровня с правильными параметрами
    generator = LevelGenerator(width=18, height=48)
    generator.generate_and_save(level_num, seed, style, num_rooms)

