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
        if seed:
            random.seed(seed)
        else:
            seed = str(random.randint(100000, 999999))
            random.seed(seed)
        
        # Заливаем карту монолитными стенами "1"
        grid = [["1" for _ in range(self.width)] for _ in range(self.height)]

        rooms_y_centers = []
        start_y = 4
        end_y = self.height - 5
        playable_height = end_y - start_y
        section_h = max(2, playable_height // num_rooms)

        # -------------------------------------------------------------
        # ГЕНЕРАЦИЯ СТРУКТУРЫ ПО СТИЛЯМ (Динамический размер)
        # -------------------------------------------------------------
        
        if style == "lab":
            # Стиль ЛАБОРАТОРИЯ: Центральный сквозной коридор
            center_corridor_x = self.width // 2 - 1
            for y in range(2, self.height - 2):
                grid[y][center_corridor_x] = "_"
                grid[y][center_corridor_x + 1] = "_"

            # Компактные боксы по бокам распределяются по высоте
            for i in range(num_rooms):
                t = i / max(1, num_rooms - 1) if num_rooms > 1 else 0.5
                ry = int(start_y + t * (playable_height - 4))
                rh = random.randint(3, max(4, section_h))
                
                # Ограничиваем высоту комнаты, чтобы не выйти за массив
                rh = min(rh, self.height - ry - 3)
                if rh < 3: continue

                if i % 2 == 0:  # Левый бокс
                    rw = random.randint(3, max(4, self.width // 4))
                    rx = 2
                    self._carve_rect(grid, rx, ry, rw, rh)
                    grid[ry + rh // 2][center_corridor_x - 1] = "_"
                    grid[ry + rh // 2][center_corridor_x] = "_"
                else:  # Правый бокс
                    rw = random.randint(3, max(4, self.width // 4))
                    rx = center_corridor_x + 2
                    self._carve_rect(grid, rx, ry, rw, rh)
                    grid[ry + rh // 2][center_corridor_x + 1] = "_"
                    grid[ry + rh // 2][center_corridor_x + 2] = "_"
                    
                rooms_y_centers.append((center_corridor_x + 1, ry + rh // 2, ry, ry + rh))

        elif style == "out":
            # Стиль УЛИЦА: Очищаем весь внутренний полигон
            self._carve_rect(grid, 1, 1, self.width - 2, self.height - 2)
            
            # Возводим домики/бункеры пропорционально размерам карты
            for i in range(num_rooms):
                t = i / max(1, num_rooms - 1) if num_rooms > 1 else 0.5
                by = int(start_y + t * (playable_height - 5)) + random.randint(-1, 1)
                by = max(start_y, min(end_y - 4, by))
                
                bw = random.randint(3, max(4, self.width // 4))
                bh = random.randint(3, max(4, self.height // 10))
                bx = random.randint(2, max(3, self.width - bw - 2))
                
                # Проверка границ перед заливкой
                if by + bh >= self.height - 1: bh = self.height - by - 2
                if bh < 3 or bw < 3: continue

                for y in range(by, by + bh):
                    for x in range(bx, bx + bw):
                        if 1 <= x < self.width - 1 and 1 <= y < self.height - 1:
                            grid[y][x] = "1"
                
                # Вырезаем пол внутри бункера, если позволяют размеры
                if bw > 3 and bh > 3:
                    for y in range(by + 1, by + bh - 1):
                        for x in range(bx + 1, bx + bw - 1):
                            grid[y][x] = "_"
                    grid[by + bh - 1][bx + bw // 2] = "_"  # Дверь
                else:
                    grid[by][bx] = "_"  # Микро-ниша
                    
                rooms_y_centers.append((bx + bw // 2, by + bh // 2, by, by + bh))

        else:
            # Стили HALL и VENT
            for i in range(num_rooms):
                t = i / max(1, num_rooms - 1) if num_rooms > 1 else 0.5
                ry = int(start_y + t * (playable_height - 5)) + random.randint(-1, 1)
                ry = max(start_y, min(end_y - 5, ry))
                
                if style == "hall":
                    rw = random.randint(max(4, self.width // 3), self.width - 4)
                    rh = random.randint(3, max(4, self.height // 10))
                    rx = random.randint(2, max(3, self.width - rw - 2))
                    self._carve_rect(grid, rx, ry, rw, rh)
                else:  # vent
                    rw = random.randint(3, max(4, self.width // 5))
                    rh = random.randint(3, max(4, self.height // 12))
                    rx = random.randint(2, max(3, self.width - rw - 2))
                    self._carve_rect(grid, rx, ry, rw, rh)
                    
                rooms_y_centers.append((rx + rw // 2, ry + rh // 2, ry, ry + rh))

            # Прокладка коридоров-дуг
            for i in range(len(rooms_y_centers) - 1):
                cx1, cy1, _, r1_bottom = rooms_y_centers[i]
                cx2, cy2, r2_top, _ = rooms_y_centers[i+1]
                s_y, e_y = r1_bottom, r2_top
                
                if s_y >= e_y:
                    grid[s_y][cx1] = "_"
                    grid[s_y][cx2] = "_"
                    continue
                    
                for y in range(s_y, e_y + 1):
                    progress = (y - s_y) / (e_y - s_y) if e_y != s_y else 0.5
                    if style == "hall":
                        amp = max(0.5, self.width * 0.05)
                        center_x = int((cx1 + (cx2 - cx1) * progress) + amp * math.sin(progress * math.pi))
                        center_x = max(2, min(self.width - 4, center_x))
                        grid[y][center_x] = "_"
                        if center_x + 1 < self.width - 1: grid[y][center_x + 1] = "_"
                    else:  # vent
                        amp = max(1.0, self.width * 0.12)
                        center_x = int((cx1 + (cx2 - cx1) * progress) + amp * math.sin(progress * math.pi))
                        center_x = max(1, min(self.width - 2, center_x))
                        grid[y][center_x] = "_"

        # -------------------------------------------------------------
        # РАССТАНОВКА СТАРТА И ВЫХОДА
        # -------------------------------------------------------------
        if style in ["lab", "out"]:
            grid[2][self.width // 2] = "S"
            grid[self.height - 3][self.width // 2] = "E"
        else:
            if rooms_y_centers:
                first_x, first_y = rooms_y_centers[0][0], rooms_y_centers[0][1]
                grid[first_y][first_x] = "S"
                last_x = rooms_y_centers[-1][0]
                grid[self.height - 3][last_x] = "E"
            else:
                grid[2][self.width // 2] = "S"
                grid[self.height - 3][self.width // 2] = "E"

        # Настройки палитры
        r_ceil = max(50, 180 - level_num * 15)
        g_ceil = max(30, 100 - level_num * 8)
        b_ceil = max(30, 100 - level_num * 8)
        r_floor = max(20, 60 - level_num * 5)
        g_floor = max(10, 30 - level_num * 2)
        b_floor = max(10, 30 - level_num * 2)

        # Построчное красивое форматирование для горизонтальной матрицы JSON
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
        print(f"-> Геометрия: {self.width}x{self.height}, Комнат: {num_rooms}, Стиль: {style}\n")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("=== ИНТЕРАКТИВНЫЙ РЕЖИМ ГЕНЕРАТОРА ===")
        
        # 1. Номер уровня
        while True:
            try:
                level_num = int(input("1. Введите номер уровня (например, 1): ").strip())
                break
            except ValueError:
                print("Ошибка: введите целое число.")
        
        # 2. Размеры карты (Ширина и Высота)
        while True:
            try:
                width = int(input("2a. Укажите ШИРИНУ карты в клетках (мин. 10): ").strip())
                height = int(input("2b. Укажите ВЫСОТУ карты в клетках (мин. 15): ").strip())
                if width >= 10 and height >= 15:
                    break
                print("Ошибка: Минимальные размеры карты — 10x15.")
            except ValueError:
                print("Ошибка: введите целые числа.")

        # 3. Количество комнат
        while True:
            try:
                rooms_input = input("3. Введите количество комнат/секторов (2-30) [по умолчанию 3]: ").strip()
                num_rooms = int(rooms_input) if rooms_input else 3
                if 2 <= num_rooms <= 30:
                    break
                print("Ошибка: количество комнат должно быть от 2 до 30.")
            except ValueError:
                print("Ошибка: введите целое число.")

        # 4. Выбор стиля
        styles = ["hall", "vent", "lab", "out"]
        while True:
            style = input(f"4. Выберите стиль генерации {styles}: ").strip().lower()
            if style in styles:
                break
            print(f"Ошибка: стиль должен быть одним из {styles}")

        # 5. Сид
        seed_input = input("5. Укажите сид (нажмите Enter для случайного): ").strip()
        seed = seed_input if seed_input else None

    else:
        # Режим чтения флагов командной строки
        parser = argparse.ArgumentParser(description="Генератор уровней")
        parser.add_argument("level_num", type=int, help="Номер уровня")
        parser.add_argument("--width", type=int, default=18, help="Ширина карты")
        parser.add_argument("--height", type=int, default=48, help="Высота карты")
        parser.add_argument("--rooms", type=int, default=3, help="Количество комнат (2-30)")
        parser.add_argument("--style", type=str, choices=["hall", "vent", "lab", "out"], default="hall", help="Стиль")
        parser.add_argument("--seed", type=str, default=None, help="Сид")
        
        args = parser.parse_args()
        level_num = args.level_num
        width = max(10, args.width)
        height = max(15, args.height)
        num_rooms = max(2, min(30, args.rooms))
        style = args.style
        seed = args.seed

    # Запуск генератора с полученными параметрами
    generator = LevelGenerator(width=width, height=height)
    generator.generate_and_save(level_num, seed, style, num_rooms)

