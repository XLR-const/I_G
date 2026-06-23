import pygame
import time
import sys
import math
import os
sys.path.append('.')

from setting import *
from core.npc import Solder


def test_npc_performance():
    """Тест: сколько NPC можно держать без лагов"""
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    clock = pygame.time.Clock()

    # Создаём фейковую игру
    class FakeGame:
        def __init__(self):
            self.delta_time = 16
            self.screen = screen
            self.particles = []
            self.total_kills = 0

            # Фейковый игрок
            self.player = type('Player', (), {
                'x': 5, 'y': 5, 'hp': 100,
                'angle': 0,
                'take_damage': lambda self, d: None,
                'update_regen': lambda self: None
            })()

            # Фейковая карта
            class FakeMap:
                def __init__(self):
                    self.width = 32
                    self.height = 32
                    self.world_map = {}
                    self.doors = []

                def is_wall(self, x, y):
                    return False

            self.map = FakeMap()

            # Фейковый pathfinder
            class FakePathFinder:
                def a_star(self, start, goal, max_distance=5):
                    return []

            self.pathfinder = FakePathFinder()

            # Фейковый renderer для Z-буфера
            self.raycasting = type('RayCasting', (), {
                'z_buffer': [float('inf')] * 100
            })()

    # Тестируем разное количество NPC
    for count in [5, 10, 15, 20, 30]:
        game = FakeGame()
        game.npcs = []

        for i in range(count):
            npc = Solder(game, pos=(i % 10 + 1, i // 10 + 1))
            npc.alive = True
            npc.hp = 100
            npc.waypoints = [(1, 1), (2, 2), (3, 3)]
            game.npcs.append(npc)

        start = time.time()
        frames = 0
        while time.time() - start < 1:
            for npc in game.npcs:
                npc.update()
            frames += 1
            clock.tick(1000)  # ограничиваем, чтобы не грузить CPU

        elapsed = time.time() - start
        print(f"{count} NPC: {frames} кадров за {elapsed:.1f} сек (~{frames} FPS)")
        if frames < 30:
            print(f"  ⚠️ Рекомендуемый лимит: {count}")
            break


def test_pathfinding_performance():
    """Тест: производительность A* поиска пути"""
    from utils.pathfinding import PathFinder

    class FakeGame:
        def __init__(self, size):
            self.map = type('Map', (), {
                'width': size,
                'height': size,
                'world_map': {},
                'doors': [],
                'is_wall': lambda self, x, y: x <= 0 or y <= 0 or x >= size - 1 or y >= size - 1
            })()

            self.player = type('Player', (), {'x': size // 2, 'y': size // 2})()

    for size in [32, 64, 100]:
        game = FakeGame(size)
        pf = PathFinder(game)

        start = time.time()
        searches = 0
        while time.time() - start < 1:
            pf.a_star((size // 2, size // 2), (size - 2, size - 2), max_distance=20)
            searches += 1
        elapsed = time.time() - start

        print(f"Карта {size}x{size}: {searches} поисков/сек")
        if searches < 10:
            print(f"  ⚠️ Рекомендуемый размер: {size // 2}")
            break


def test_a_star_pathfinding():
    """Тест: A* находит путь, обходя стены"""
    from utils.pathfinding import PathFinder

    # Создаём карту с препятствием
    class FakeGame:
        def __init__(self):
            self.map = type('Map', (), {
                'width': 10,
                'height': 10,
                'world_map': {},
                'doors': [],
                'is_wall': lambda self, x, y: (x == 5 and 2 <= y <= 7)
            })()

            self.player = type('Player', (), {'x': 0, 'y': 0})()

    game = FakeGame()
    pf = PathFinder(game)

    start = (2, 2)
    goal = (8, 8)

    path = pf.a_star(start, goal, max_distance=20)

    print("\n=== ТЕСТ A* ===")
    print(f"Старт: {start}")
    print(f"Цель: {goal}")
    print(f"Найден путь: {len(path)} клеток")

    if len(path) > 1:
        print(f"Первые шаги: {path[:5]}...")
        # Проверяем, что путь не идёт сквозь стены
        for cell in path:
            assert not game.map.is_wall(cell[0], cell[1]), f"Путь идёт сквозь стену {cell}"
        print("✅ Путь корректен, стены обойдены!")
        return True
    else:
        print("❌ Путь не найден!")
        return False


def test_collision():
    """Тест: проверка коллизии со стенами"""
    from core.player import Player

    class FakeGame:
        def __init__(self):
            class FakeMap:
                def __init__(self):
                    self.world_map = {(5, 5): '1', (5, 6): '1', (6, 5): '1'}
                    self.doors = []
                    self.width = 10
                    self.height = 10

                def is_wall(self, x, y):
                    return (x, y) in self.world_map

            self.map = FakeMap()
            self.npcs = []
            self.delta_time = 16

    game = FakeGame()
    player = Player(game)
    player.x, player.y = 1.5, 1.5

    # Проверка на блок движение при столкновении со стеной
    wall_x, wall_y = 5.5, 5.5
    can_move = player._check_collision(wall_x - player.x, wall_y - player.y)

    print("\n=== ТЕСТ КОЛЛИЗИЙ ===")
    print(f"Попытка войти в стену ({wall_x}, {wall_y})")
    print(f"Движение заблокировано: {not can_move}")
    assert not can_move, "Коллизия должна блокировать проход сквозь стены"
    print("✅ Коллизия работает!")
    return True


def test_door_opening():
    """Тест: дверь открывается при приближении"""
    from core.door import Door

    class FakeGame:
        def __init__(self):
            self.player = type('Player', (), {'x': 5.2, 'y': 5.2})()
            self.map = type('Map', (), {'doors': []})()

    game = FakeGame()
    door = Door(game, 5.0, 5.0)

    print("\n=== ТЕСТ ДВЕРИ ===")
    print(f"Начальное состояние: {door.state}")
    door.update()
    print(f"После приближения игрока: {door.state}")

    assert door.state in ["OPENING", "OPEN"], "Дверь должна начать открываться!"
    print("✅ Дверь работает!")
    return True


def test_player_health():
    """Тест: HP игрока не уходит в минус"""
    from core.player import Player

    class FakeGame:
        def __init__(self):
            self.ui_manager = type('UIManager', (), {
                'states': {'DEAD': 6},
                'current_state': 0
            })()

    game = FakeGame()
    player = Player(game)
    player.hp = 100

    print("\n=== ТЕСТ ЗДОРОВЬЯ ===")
    print(f"Начальное HP: {player.hp}")

    player.take_damage(150)
    print(f"После урона 150: {player.hp}")
    assert player.hp >= 0, "HP не может быть отрицательным!"
    assert player.hp == 0, "При уроне > HP должно остаться 0"
    print("✅ Здоровье работает!")
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("ЗАПУСК ТЕСТОВ")
    print("=" * 60)

    tests = [
        ("A* поиск пути", test_a_star_pathfinding),
        ("Коллизия со стенами", test_collision),
        ("Механика дверей", test_door_opening),
        ("Здоровье игрока", test_player_health),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            print(f"\n--- {name} ---")
            result = test_func()
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ ОШИБКА: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"РЕЗУЛЬТАТ: {passed} пройдено, {failed} не пройдено")
    print("=" * 60)

    # Тесты производительности
    print("\n" + "=" * 60)
    print("ТЕСТЫ ПРОИЗВОДИТЕЛЬНОСТИ")
    print("=" * 60)

    test_npc_performance()
    print("\n" + "=" * 60)
    test_pathfinding_performance()
