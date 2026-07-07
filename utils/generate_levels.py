import sys
import json
import random
import os
import math

class LevelGenerator:
    def __init__(self, width=18, height=48):
        self.width = width
        self.height = height

    def generate_and_save(self, level_num):
        # 1. Заливаем всю карту монолитными стенами "1"
        grid = [["1" for _ in range(self.width)] for _ in range(self.height)]

        # Безопасная функция для вырезания прямоугольных зон (пол "_")
        def carve_rect(x, y, w, h):
            for i in range(y, min(y + h, self.height - 2)):
                for j in range(x, min(x + w, self.width - 2)):
                    if 1 <= j < self.width - 1 and 1 <= i < self.height - 1:
                        grid[i][j] = "_"

        # -------------------------------------------------------------
        # СЕКТОР А: Стартовый Масштабный Зал (y: 2 - 9)
        # -------------------------------------------------------------
        # Занимает почти всю ширину карты (14 клеток из 18)
        carve_rect(2, 2, self.width - 4, 8)
        
        # Ступенчатые тактические ниши в стенах (карманы для лута)
        carve_rect(1, 4, 1, 4)
        carve_rect(self.width - 2, 4, 1, 4)

        # -------------------------------------------------------------
        # ПЕРЕХОД А-Б: Ультра-плавный сглаженный коридор (y: 10 - 20)
        # -------------------------------------------------------------
        # Уменьшен радиус дуги, смещение по X составляет максимум 1-2 клетки на всю длину.
        # Ширина коридора увеличена до 2-3 клеток, чтобы сгладить "ребра" при рейкастинге.
        start_y, end_y = 10, 21
        for y in range(start_y, end_y):
            t = (y - start_y) / (end_y - start_y)
            # Микро-смещение по X (амплитуда всего 1.8 клетки вместо 4)
            center_x = (self.width // 2 - 1) + int(1.8 * math.sin(t * math.pi * 0.5))
            
            # Делаем коридор достаточно широким, чтобы лесенка не зажимала игрока
            grid[y][center_x] = "_"
            grid[y][center_x + 1] = "_"
            grid[y][center_x + 2] = "_"

        # -------------------------------------------------------------
        # СЕКТОР Б: Центральный Командный Комплекс (y: 21 - 33)
        # -------------------------------------------------------------
        # Гермошлюз на входе: плавное коническое сужение-расширение
        grid[21][self.width // 2] = "_"
        grid[21][self.width // 2 + 1] = "_"
        
        # Огромный центральный зал, раскрывающий масштаб карты
        carve_rect(2, 22, self.width - 4, 12)
        
        # Внутренняя архитектурная перегородка (выступ стены в 1 клетку для разделения зон)
        for x in range(2, self.width // 2 + 1):
            grid[27][x] = "1"

        # -------------------------------------------------------------
        # ПЕРЕХОД Б-В: S-образный плавный транзит (y: 34 - 41)
        # -------------------------------------------------------------
        # Зеркальная плавная дуга с минимальным радиусом, убирающая эффект рваных ребер
        start_y2, end_y2 = 34, 42
        for y in range(start_y2, end_y2):
            t = (y - start_y2) / (end_y2 - start_y2)
            center_x = (self.width // 2 - 1) - int(1.5 * math.sin(t * math.pi * 0.5))
            
            grid[y][center_x] = "_"
            grid[y][center_x + 1] = "_"
            grid[y][center_x + 2] = "_"

        # -------------------------------------------------------------
        # СЕКТОР В: Финальный Ангар Эвакуации (y: 42 - 46)
        # -------------------------------------------------------------
        carve_rect(2, 42, self.width - 4, 5)
        # Глубокие торцевые карманы в углах финального зала
        carve_rect(1, 43, 1, 3)
        carve_rect(self.width - 2, 43, 1, 3)

        # -------------------------------------------------------------
        # ГАРАНТИРОВАННЫЕ СТАРТ И ВЫХОД
        # -------------------------------------------------------------
        # Игрок (S) появляется строго один раз на верхнем ярусе базы
        grid[3][self.width // 2] = "S"

        # Финал (E) располагается строго один раз в самом конце ангара эвакуации
        grid[44][self.width // 2] = "E"

        # Генерация палитры цветов в зависимости от уровня
        r_ceil = max(50, 180 - level_num * 15)
        g_ceil = max(30, 100 - level_num * 8)
        b_ceil = max(30, 100 - level_num * 8)

        r_floor = max(20, 60 - level_num * 5)
        g_floor = max(10, 30 - level_num * 2)
        b_floor = max(10, 30 - level_num * 2)

        # Построчное параллельное горизонтальное форматирование для читаемости JSON глазами
        formatted_map_lines = []
        for row in grid:
            json_row = json.dumps(row, ensure_ascii=False)
            formatted_map_lines.append(f"    {json_row}")
        
        map_json_string = "[\n" + ",\n".join(formatted_map_lines) + "\n  ]"

        # Конфигурация мета-данных
        meta_data = {
            "inventory": ["Pistol", "Shotgun", "Machine Gun", "Plasma Gun"],
            "starting_ammo": {
                "Pistol": 40,
                "Shotgun": 20,
                "Machine Gun": 400,
                "Plasma Gun": 15
            },
            "background": {
                "ceiling_texture": "resources/textures/red_sky.png",
                "floor_texture": None,
                "ceiling_color": [r_ceil, g_ceil, b_ceil],
                "floor_color": [r_floor, g_floor, b_floor]
            }
        }

        meta_json_string = json.dumps(meta_data, indent=2, ensure_ascii=False)
        final_json_content = "{\n" + f'  "map": {map_json_string},\n' + meta_json_string[2:]

        # Сохранение в нужный каталог проекта
        output_dir = os.path.join("resources", "levels")
        os.makedirs(output_dir, exist_ok=True)
        
        filename = os.path.join(output_dir, f"level_{level_num}.json")
        with open(filename, "w", encoding="utf-8") as f:
            f.write(final_json_content)
        
        print(f"[Успех] Уровень {level_num} успешно сгенерирован!")
        print(f"Масштаб раскрыт: Плавные дуги коридоров, огромные залы, тонкие стены.")
        print(f"Файл сохранен: {filename}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Ошибка: Укажите номер уровня. Пример: python utils/generate_levels.py 1")
        sys.exit(1)

    try:
        lvl = int(sys.argv[1])
    except ValueError:
        print("Ошибка: Номер уровня должен быть целым числом.")
        sys.exit(1)

    generator = LevelGenerator(width=18, height=48)
    generator.generate_and_save(lvl)
