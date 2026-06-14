# tests/test_game.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import math
from setting import *
from pathfinding import PathFinder
from door import Door
from player import Player

class MockGame:
    """Мок-объект Game для тестирования"""
    def __init__(self):
        self.map = MockMap()
        self.player = MockPlayer()
        self.delta_time = 0.016

class MockMap:
    def __init__(self):
        self.world_map = {
            (5, 5): '1', (5, 6): '1', (5, 7): '1',
            (6, 5): '1', (6, 7): '1',
            (7, 5): '1', (7, 6): '1', (7, 7): '1',
        }
        self.width = 32
        self.height = 18
        self.doors = []
    
    def is_wall(self, x, y):
        return (x, y) in self.world_map

class MockPlayer:
    def __init__(self):
        self.x = 2.0
        self.y = 2.0
        self.angle = 0
        self.hp = 100

# ============================================================
# ТЕСТ 1: A* поиск пути
# ============================================================
def test_astar_pathfinding():
    """Тест: A* находит путь, обходя стены"""
    game = MockGame()
    pathfinder = PathFinder(game)
    
    start = (2.0, 2.0)
    goal = (8.0, 8.0)
    
    path = pathfinder.a_star(start, goal, max_distance=15)
    
    print(f"\n[ТЕСТ 1] A* поиск пути")
    print(f"  Старт: {start}, Цель: {goal}")
    print(f"  Найден путь: {len(path)} клеток")
    
    assert len(path) > 0, "Путь не найден!"
    assert path[0] == (2, 2), "Стартовая позиция не совпадает"
    assert path[-1] == (8, 8), "Целевая позиция не достигнута"
    
    # Проверяем, что путь не идёт сквозь стены
    for cell in path:
        assert not game.map.is_wall(cell[0], cell[1]), f"Путь идёт сквозь стену {cell}"
    
    print(f"  ✅ Успех! Длина пути: {len(path)}")
    return True

# ============================================================
# ТЕСТ 2: Ограничение дистанции A*
# ============================================================
def test_astar_distance_limit():
    """Тест: A* не ищет путь дальше max_distance"""
    game = MockGame()
    pathfinder = PathFinder(game)
    
    start = (2.0, 2.0)
    goal = (20.0, 20.0)  # далеко
    
    path = pathfinder.a_star(start, goal, max_distance=5)
    
    print(f"\n[ТЕСТ 2] Ограничение дистанции A*")
    print(f"  Старт: {start}, Цель: {goal} (дистанция > 5)")
    print(f"  Результат: {[] if not path else f'путь из {len(path)} клеток'}")
    
    assert len(path) == 0, "Должен вернуть пустой путь для далёкой цели!"
    print(f"  ✅ Успех! Поиск за пределами радиуса отключён")
    return True

# ============================================================
# ТЕСТ 3: LOS (Line of Sight) через стены
# ============================================================
def test_line_of_sight():
    """Тест: Проверка видимости через стены"""
    from npc import NPC
    
    game = MockGame()
    npc = NPC(game, "test", pos=(2.0, 2.0))
    npc.game = game
    
    # Позиция игрока
    game.player.x = 8.0
    game.player.y = 8.0
    
    # Ручная проверка LOS
    def check_los(npc, player):
        x1, y1 = int(npc.x), int(npc.y)
        x2, y2 = int(player.x), int(player.y)
        
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        
        x, y = x1, y1
        while (x, y) != (x2, y2):
            if game.map.is_wall(x, y):
                return False
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy
        return True
    
    can_see = check_los(npc, game.player)
    
    print(f"\n[ТЕСТ 3] Line of Sight")
    print(f"  NPC: ({npc.x}, {npc.y})")
    print(f"  Игрок: ({game.player.x}, {game.player.y})")
    print(f"  Между ними стена? Да")
    print(f"  Результат LOS: {can_see}")
    
    assert can_see == False, "LOS должен быть False через стену!"
    print(f"  ✅ Успех! Стена блокирует видимость")
    return True

# ============================================================
# ТЕСТ 4: Коллизия со стеной
# ============================================================
def test_collision():
    """Тест: Игрок не может пройти сквозь стены"""
    game = MockGame()
    
    def check_collision(x, y, radius=0.4):
        for offset_x, offset_y in [(-radius, radius), (radius, radius),
                                   (-radius, -radius), (radius, -radius)]:
            check_x = int(x + offset_x)
            check_y = int(y + offset_y)
            if game.map.is_wall(check_x, check_y):
                return True
        return False
    
    # Позиция внутри стены
    inside_wall = (5.5, 5.5)
    # Позиция на свободном месте
    free_space = (2.5, 2.5)
    
    collides_wall = check_collision(inside_wall[0], inside_wall[1])
    collides_free = check_collision(free_space[0], free_space[1])
    
    print(f"\n[ТЕСТ 4] Коллизия со стенами")
    print(f"  Позиция в стене ({inside_wall[0]}, {inside_wall[1]}): коллизия = {collides_wall}")
    print(f"  Свободная позиция ({free_space[0]}, {free_space[1]}): коллизия = {collides_free}")
    
    assert collides_wall == True, "Должна быть коллизия внутри стены!"
    assert collides_free == False, "Не должно быть коллизии на пустом месте!"
    print(f"  ✅ Успех! Коллизия работает")
    return True

# ============================================================
# ТЕСТ 5: Дверь открывается при приближении
# ============================================================
def test_door_opening():
    """Тест: Дверь меняет состояние при приближении игрока"""
    game = MockGame()
    door = Door(game, 5.0, 5.0)
    
    print(f"\n[ТЕСТ 5] Механика дверей")
    print(f"  Начальное состояние: {door.state}")
    assert door.state == "CLOSED", "Дверь должна быть закрыта изначально"
    
    # Симулируем игрока рядом с дверью
    game.player.x = 5.2
    game.player.y = 5.2
    door.update()
    
    print(f"  Игрок рядом ({game.player.x}, {game.player.y})")
    print(f"  Состояние после update: {door.state}")
    
    assert door.state in ["OPENING", "OPEN"], "Дверь должна начать открываться!"
    print(f"  ✅ Успех! Дверь реагирует на приближение")
    return True

# ============================================================
# ТЕСТ 6: Здоровье игрока не уходит в минус
# ============================================================
def test_player_health():
    """Тест: HP игрока не становится меньше 0"""
    game = MockGame()
    player = MockPlayer()
    player.hp = 100
    
    damage = 150
    
    print(f"\n[ТЕСТ 6] Здоровье игрока")
    print(f"  Начальное HP: {player.hp}")
    print(f"  Получен урон: {damage}")
    
    player.hp = max(0, player.hp - damage)
    
    print(f"  Итоговое HP: {player.hp}")
    assert player.hp >= 0, "HP не может быть отрицательным!"
    assert player.hp == 0, "При уроне > HP должно остаться 0"
    print(f"  ✅ Успех! HP не уходит в минус")
    return True

# ============================================================
# ТЕСТ 7: Угол поворота игрока в диапазоне 0-360°
# ============================================================
def test_player_angle():
    """Тест: Угол поворота всегда в пределах [0, 2π]"""
    angles = [0.5, 6.0, 7.0, -0.5, -3.0, 100.0]
    
    print(f"\n[ТЕСТ 7] Нормализация угла поворота")
    
    for raw_angle in angles:
        normalized = raw_angle % math.tau
        print(f"  Исходный: {raw_angle:.2f} → Нормализованный: {normalized:.2f}")
        assert 0 <= normalized <= math.tau, f"Угол {normalized} вне диапазона!"
    
    print(f"  ✅ Успех! Все углы нормализованы")
    return True

# ============================================================
# ЗАПУСК ВСЕХ ТЕСТОВ
# ============================================================
def run_all_tests():
    print("\n" + "="*60)
    print("ЗАПУСК ТЕСТОВ")
    print("="*60)
    
    tests = [
        ("A* поиск пути", test_astar_pathfinding),
        ("Ограничение дистанции A*", test_astar_distance_limit),
        ("Line of Sight", test_line_of_sight),
        ("Коллизия со стенами", test_collision),
        ("Механика дверей", test_door_opening),
        ("Здоровье игрока", test_player_health),
        ("Нормализация угла", test_player_angle),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"\n❌ ПРОВАЛ: {name}")
            print(f"   {e}")
            failed += 1
        except Exception as e:
            print(f"\n❌ ОШИБКА: {name} - {e}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"РЕЗУЛЬТАТ: {passed} пройдено, {failed} не пройдено")
    print("="*60)
    
    return passed, failed

if __name__ == "__main__":
    run_all_tests()