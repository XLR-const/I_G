"""Тест производительности с рейкастингом и FPS"""

import sys
import os
import time
import pygame
import math

# Добавляем путь к корневой папке проекта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.generate_levels import LevelGenerator
from core.map import Map
from core.player import Player
from rendering.raycasting import RayCasting
from rendering.renderer import Renderer
from setting import *


class GameStub:
    """Заглушка для тестирования без полной игры"""
    def __init__(self):
        self.screen = pygame.display.set_mode((800, 600))
        self.clock = pygame.time.Clock()
        self.delta_time = 0.016
        self.player = None
        self.map = None
        self.raycasting = None
        self.renderer = None
        self.npcs = []
        self.particles = []
        self.font = pygame.font.Font(None, 24)
        self.current_level = 1
        self.level_manager = None
        self.pathfinder = None
        self.music_manager = None
        self.ui_manager = None
        self.total_kills = 0
    
    def load_level(self, map_data):
        """Загружает уровень для теста"""
        self.map = Map(self, map_data)
        
        for y, row in enumerate(map_data):
            for x, char in enumerate(row):
                if char == 'S':
                    self.player = Player(self)
                    self.player.x = x + 0.5
                    self.player.y = y + 0.5
                    break
            if self.player:
                break
        
        if not self.player:
            self.player = Player(self)
            self.player.x = 5.5
            self.player.y = 5.5
        
        self.raycasting = RayCasting(self)
        self.renderer = Renderer(self)
    
    def update(self):
        if self.player:
            self.player.update()
        for npc in self.npcs:
            if hasattr(npc, 'alive') and npc.alive:
                try:
                    dx = self.player.x - npc.x
                    dy = self.player.y - npc.y
                    dist = math.hypot(dx, dy)
                    
                    if dist < npc.shoot_range and npc.has_line_of_sight():
                        npc.state = "ATTACK"
                        npc.shoot()
                    elif dist < 10:
                        if dist > 0.01:
                            move_x = (dx / dist) * npc.speed * 0.01
                            move_y = (dy / dist) * npc.speed * 0.01
                            npc.try_move(move_x, move_y)
                        npc.state = "CHASE"
                    else:
                        npc.state = "IDLE"
                except:
                    pass
    
    def draw(self):
        if self.renderer:
            self.renderer.draw_background()
        if self.raycasting:
            self.raycasting.ray_cast()
        for npc in self.npcs:
            try:
                npc.draw()
            except:
                pass
        pygame.display.flip()


def create_npc(game, npc_type, x, y):
    from core.npc import Solder, Kamikaze, Jaggernaut, Lightning, Boss
    npc_classes = {'2': Solder, '3': Kamikaze, '4': Jaggernaut, '5': Lightning, '6': Boss}
    if npc_type in npc_classes:
        npc = npc_classes[npc_type](game, pos=(x + 0.5, y + 0.5))
        npc.path = []
        npc.last_path_update = 0
        return npc
    return None


def run_test(width, height, level_num, map_label, npc_label):
    """Запускает один тест и возвращает результат"""
    
    generator = LevelGenerator(width=width, height=height)
    
    start_gen = time.time()
    map_str, _, _ = generator.generate(level_num)
    gen_time = time.time() - start_gen
    
    room_count = len(generator.rooms)
    npc_count = 0
    for row in map_str:
        npc_count += row.count('2') + row.count('3') + row.count('4') + row.count('5') + row.count('6')
    
    game = GameStub()
    game.load_level(map_str)
    
    game.npcs = []
    for y, row in enumerate(map_str):
        for x, char in enumerate(row):
            if char in ['2', '3', '4', '5', '6']:
                npc = create_npc(game, char, x, y)
                if npc:
                    game.npcs.append(npc)
    
    for _ in range(10):
        game.update()
        game.draw()
        game.clock.tick(60)
    
    frame_times = []
    for _ in range(100):
        start_frame = time.time()
        game.update()
        game.draw()
        frame_time = time.time() - start_frame
        frame_times.append(frame_time)
        game.clock.tick(120)
    
    avg_frame_time = sum(frame_times) / len(frame_times)
    fps = 1.0 / avg_frame_time if avg_frame_time > 0 else 0
    
    if fps >= 60:
        rating = "✅ Отлично"
    elif fps >= 30:
        rating = "⚠️ Нормально"
    elif fps >= 15:
        rating = "⚠️ Терпимо"
    else:
        rating = "❌ Лаги"
    
    return {
        "map": map_label,
        "npc_label": npc_label,
        "level": level_num,
        "width": width,
        "height": height,
        "rooms": room_count,
        "npc": npc_count,
        "fps": fps,
        "gen_time": gen_time,
        "rating": rating
    }


def main():
    """Главная функция - запускает все тесты и выводит итоговую таблицу"""
    
    print("\n" + "=" * 110)
    print("🔬 ТЕСТ ПРОИЗВОДИТЕЛЬНОСТИ С РЕЙКАСТИНГОМ")
    print("=" * 110)
    
    # ============================================================
    # ВСЕ КОНФИГУРАЦИИ
    # ============================================================
    
    configs = [
        # Маленькая карта
        {"width": 30, "height": 17, "level": 1, "map_label": "Малая", "npc_label": "Мало"},
        {"width": 30, "height": 17, "level": 5, "map_label": "Малая", "npc_label": "Средне"},
        {"width": 30, "height": 17, "level": 10, "map_label": "Малая", "npc_label": "Много"},
        
        # Средняя карта
        {"width": 50, "height": 28, "level": 1, "map_label": "Средняя", "npc_label": "Мало"},
        {"width": 50, "height": 28, "level": 5, "map_label": "Средняя", "npc_label": "Средне"},
        {"width": 50, "height": 28, "level": 10, "map_label": "Средняя", "npc_label": "Много"},
        
        # Большая карта
        {"width": 80, "height": 45, "level": 1, "map_label": "Большая", "npc_label": "Мало"},
        {"width": 80, "height": 45, "level": 5, "map_label": "Большая", "npc_label": "Средне"},
        {"width": 80, "height": 45, "level": 10, "map_label": "Большая", "npc_label": "Много"},
        
        # Огромная карта
        {"width": 120, "height": 68, "level": 5, "map_label": "Огромная", "npc_label": "Средне"},
        {"width": 120, "height": 68, "level": 10, "map_label": "Огромная", "npc_label": "Много"},
        
        # Экстрим
        {"width": 150, "height": 84, "level": 10, "map_label": "Экстрим", "npc_label": "Много"},
    ]
    
    # Инициализация Pygame (ОДИН РАЗ)
    pygame.init()
    pygame.display.set_mode((800, 600))
    
    results = []
    test_num = 1
    
    # Шапка таблицы
    print(f"\n{'#':<4} {'Карта':<12} {'NPC':<10} {'Размер':<12} {'Комнат':<7} {'NPC_шт':<7} {'FPS':<8} {'Время_ген':<10} {'Оценка'}")
    print("-" * 110)
    
    for config in configs:
        print(f"{test_num:<4} ", end="")
        
        try:
            result = run_test(
                config["width"],
                config["height"],
                config["level"],
                config["map_label"],
                config["npc_label"]
            )
            results.append(result)
            
            size = f"{result['width']}x{result['height']}"
            print(f"{result['map']:<12} {result['npc_label']:<10} {size:<12} {result['rooms']:<7} {result['npc']:<7} {result['fps']:.1f}    {result['gen_time']:.3f}s    {result['rating']}")
            
        except Exception as e:
            print(f"{'ОШИБКА':<12} {'—':<10} {'—':<12} {'—':<7} {'—':<7} {'—':<8} {'—':<10} ❌ {str(e)[:30]}")
        
        test_num += 1
    
    # ============================================================
    # ИТОГОВАЯ ТАБЛИЦА (СОРТИРОВАННАЯ)
    # ============================================================
    
    print("\n" + "=" * 110)
    print("📊 ИТОГОВАЯ ТАБЛИЦА ПРОИЗВОДИТЕЛЬНОСТИ (СОРТИРОВАННАЯ ПО РАЗМЕРУ)")
    print("=" * 110)
    
    print(f"\n{'Карта':<12} {'NPC':<10} {'Размер':<12} {'Комнат':<7} {'NPC_шт':<7} {'FPS':<8} {'Время_ген':<10} {'Оценка'}")
    print("-" * 110)
    
    sorted_results = sorted(results, key=lambda r: r['width'] * r['height'])
    
    for r in sorted_results:
        size = f"{r['width']}x{r['height']}"
        print(f"{r['map']:<12} {r['npc_label']:<10} {size:<12} {r['rooms']:<7} {r['npc']:<7} {r['fps']:.1f}    {r['gen_time']:.3f}s    {r['rating']}")
    
    # ============================================================
    # СТАТИСТИКА
    # ============================================================
    
    print("\n" + "=" * 110)
    print("📊 СТАТИСТИКА")
    print("=" * 110)
    
    excellent = [r for r in results if r['fps'] >= 60]
    good = [r for r in results if 30 <= r['fps'] < 60]
    bad = [r for r in results if r['fps'] < 30]
    
    print(f"\n  ✅ Отличная производительность (>=60 FPS): {len(excellent)} конфигураций")
    for r in excellent:
        print(f"     - {r['map']} + {r['npc_label']}: {r['fps']:.1f} FPS ({r['width']}x{r['height']})")
    
    print(f"\n  ⚠️ Нормальная производительность (30-60 FPS): {len(good)} конфигураций")
    for r in good:
        print(f"     - {r['map']} + {r['npc_label']}: {r['fps']:.1f} FPS ({r['width']}x{r['height']})")
    
    print(f"\n  ❌ Низкая производительность (<30 FPS): {len(bad)} конфигураций")
    for r in bad:
        print(f"     - {r['map']} + {r['npc_label']}: {r['fps']:.1f} FPS ({r['width']}x{r['height']})")
    
    # ============================================================
    # РЕКОМЕНДАЦИИ
    # ============================================================
    
    print("\n" + "=" * 110)
    print("💡 РЕКОМЕНДАЦИИ")
    print("=" * 110)
    
    # Самая большая конфигурация с хорошим FPS
    good_configs = [r for r in results if r['fps'] >= 30]
    if good_configs:
        max_good = max(good_configs, key=lambda r: r['width'] * r['height'])
        print(f"\n  ✅ Рекомендуемый максимум для 30+ FPS:")
        print(f"     {max_good['map']} ({max_good['width']}x{max_good['height']}) + {max_good['npc_label']} NPC")
        print(f"     FPS: {max_good['fps']:.1f}, комнат: {max_good['rooms']}, NPC: {max_good['npc']}")
    
    # Самая большая конфигурация с отличным FPS
    excellent_configs = [r for r in results if r['fps'] >= 60]
    if excellent_configs:
        max_excellent = max(excellent_configs, key=lambda r: r['width'] * r['height'])
        print(f"\n  ✅ Рекомендуемый максимум для 60+ FPS:")
        print(f"     {max_excellent['map']} ({max_excellent['width']}x{max_excellent['height']}) + {max_excellent['npc_label']} NPC")
        print(f"     FPS: {max_excellent['fps']:.1f}, комнат: {max_excellent['rooms']}, NPC: {max_excellent['npc']}")
    
    pygame.quit()


if __name__ == "__main__":
    main()