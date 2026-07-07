import sys
import json
import random
import os

class LevelGenerator:
    def __init__(self, width=18, height=48):
        self.width = width
        self.height = height

    def generate_and_save(self, level_num):
        # 1. Заливаем всё стенами "1" — будем вырезать сложный комплекс
        grid = [["1" for _ in range(self.width)] for _ in range(self.height)]

        # Вспомогательная функция, чтобы безопасно вырезать прямоугольные зоны
        def carve_rect(x, y, w, h):
            for i in range(y, min(y + h, self.height - 2)):
                for j in range(x, min(x + w, self.width - 2)):
                    if 1 <= j < self.width - 1 and 1 <= i < self.height - 1:
                        grid[i][j] = "_"

        # 2. ГЕНЕРАЦИЯ СЛОЖНЫХ ЗАЛОВ И ЗОН (Сверху Вниз)
        
        # СЕКТОР А: Стартовый комплекс (Верхняя треть)
        # Делаем Т-образный начальный зал с боковыми карманами
        carve_rect(4, 2, self.width - 8, 5)   # Центральная часть
        carve_rect(2, 4, 3, 3)                # Левое крыло-ниша
        carve_rect(self.width - 5, 4, 3, 3)   # Правое крыло-ниша

        # СЕКТОР Б: Центральная аренная зона (Середина)
        # Большой зал сложной формы с выступами стен вместо одиночных колонн
        carve_rect(3, 16, self.width - 6, 12)
        # Наращиваем выступы стен внутри зала, чтобы разбить прямую видимость (для тактики)
        for y_wall in range(20, 24):
            grid[y_wall][3] = "1"
            grid[y_wall][4] = "1"
            grid[y_wall][self.width - 4] = "1"
            grid[y_wall][self.width - 5] = "1"

        # СЕКТОР В: Финальный комплекс и катакомбы (Нижняя треть)
        # Два параллельных зала, соединенных переходами
        carve_rect(2, 34, 6, 6)               # Левый склад
        carve_rect(self.width - 8, 34, 6, 6)  # Правый склад
        carve_rect(4, 42, self.width - 8, 4)  # Комната эвакуации (Выход)

        # 3. РАЗВЕТВЛЕННАЯ СЕТЬ КОРИДОРОВ И КОЛЬЦЕВЫЕ МАРШРУТЫ (СВЯЗНОСТЬ)
        
        # Кольцо 1: Соединяем Сектор А и Сектор Б ДВУМЯ разными путями
        # Левый обходной путь
        for y in range(7, 17): grid[y][3] = "_"
        # Правый основной коридор с зигзагом
        for y in range(7, 12): grid[y][self.width - 4] = "_"
        for x in range(self.width - 7, self.width - 3): grid[11][x] = "_"
        for y in range(11, 17): grid[y][self.width - 7] = "_"

        # Боковой секретный тупик (карман для лута) в центре первого коридора
        for x in range(3, 7): grid[10][x] = "_"

        # Кольцо 2: Соединяем Сектор Б с нижними складами Сектора В
        # Проход из центрального зала в левый склад
        for y in range(28, 35): grid[y][4] = "_"
        # Проход из центрального зала в правый склад
        for y in range(28, 35): grid[y][self.width - 5] = "_"
        # Соединяем левый и правый склады между собой поперечным коридором
        for x in range(5, self.width - 5): grid[37][x] = "_"

        # Пути к финалу: Склады соединяются с комнатой эвакуации
        for y in range(40, 43): grid[y][5] = "_"
        for y in range(40, 43): grid[y][self.width - 6] = "_"

        # 4. РАССТАНОВКА ТОЧЕК СТАРТА И ВЫХОДА
        # Старт (S) строго один раз в центре верхнего Т-образного зала
        sx, sy = self.width // 2, 4
        grid[sy][sx] = "S"

        # Выход (E) строго один раз в самом конце нижнего комплекса
        ex, ey = self.width // 2, 44
        grid[ey][ex] = "E"

        # 5. ЦВЕТОВАЯ ГАММА (ПРОГРЕССИЯ)
        r_ceil = max(50, 180 - level_num * 15)
        g_ceil = max(30, 100 - level_num * 8)
        b_ceil = max(30, 100 - level_num * 8)

        r_floor = max(20, 60 - level_num * 5)
        g_floor = max(10, 30 - level_num * 2)
        b_floor = max(10, 30 - level_num * 2)

        # Построчное параллельное горизонтальное форматирование для красивого JSON
        formatted_map_lines = []
        for row in grid:
            json_row = json.dumps(row, ensure_ascii=False)
            formatted_map_lines.append(f"    {json_row}")
        
        map_json_string = "[\n" + ",\n".join(formatted_map_lines) + "\n  ]"

        # Шаблон мета-данных
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

        # Сохранение по указанному пути
        output_dir = os.path.join("resources", "levels")
        os.makedirs(output_dir, exist_ok=True)
        
        filename = os.path.join(output_dir, f"level_{level_num}.json")
        with open(filename, "w", encoding="utf-8") as f:
            f.write(final_json_content)
        
        print(f"[Успех] Уровень {level_num} успешно сгенерирован!")
        print(f"Архитектура раскрыта: Кольцевые маршруты, извилистые развилки, сложные залы и укрытия-ниши.")
        print(f"Файл сохранен по пути: {filename}")

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
