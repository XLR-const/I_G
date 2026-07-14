import os
import sys
import math
import pygame

# Добавляем корень проекта в путь
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Инициализируем pygame
pygame.init()
pygame.mixer.init()

# ============================================================
# ИМПОРТИРУЕМ РЕАЛЬНЫЕ КОНФИГИ И КЛАССЫ
# ============================================================
from setting import *
from config.game_data import NPC_CONFIG, SYMBOLS_CONFIG
from core.npc import NPC, NPCAnimator


# ============================================================
# МОКИ ДЛЯ ИГРЫ
# ============================================================
class MockPlayer:
    def __init__(self):
        self.x, self.y = 5.5, 5.5
        self.angle = 0.0
        self.hp = 100
        self.armor = 0
    
    def take_damage(self, dmg):
        self.hp -= dmg
        print(f"[MockPlayer] Получен урон {dmg}, HP: {self.hp}")


class MockMap:
    def is_wall(self, x, y):
        return False
    
    def is_walkable(self, x, y):
        return True


class MockRaycasting:
    def __init__(self):
        self.z_buffer = [99.0] * NUM_RAYS


class MockLevelManager:
    def __init__(self):
        self.total_kills = 0
        self.map = MockMap()
        self.width = 30
        self.height = 20


class MockGame:
    def __init__(self):
        self.player = MockPlayer()
        self.map = MockMap()
        self.raycasting = MockRaycasting()
        self.level_manager = MockLevelManager()
        self.delta_time = 0.016
        self.particles = []
        self.screen = pygame.Surface((WIDTH, HEIGHT))
        self.npcs = []
        self.items = []
        self.pathfinder = None


# ============================================================
# ТЕСТ
# ============================================================
def run_npc_test():
    print("\n" + "=" * 70)
    print("🧪 ТЕСТ: НОВАЯ СИСТЕМА NPC (NPCAnimator + NPC)")
    print("=" * 70)

    game = MockGame()
    
    # ============================================================
    # 1. СОЗДАНИЕ NPC
    # ============================================================
    print("\n[1] Создание NPC...")
    
    # Используем существующий NPC из конфига (например, '2' — Solder)
    npc = NPC(game, '2', pos=(10.0, 10.0))
    
    print(f"  Имя: {npc.name}")
    print(f"  HP: {npc.hp}")
    print(f"  Скорость: {npc.speed}")
    print(f"  Радиус: {npc.radius}")
    print(f"  Дальность стрельбы: {npc.shoot_range}")
    print(f"  Дальность активации: {npc.activation_distance}")
    print(f"  Дальность видимости: {npc.view_distance}")
    print(f"  Состояние: {npc.state}")
    
    # ============================================================
    # 2. ПРОВЕРКА АНИМАЦИЙ
    # ============================================================
    print("\n[2] Проверка анимаций...")
    
    # Проверяем загрузку спрайтов
    print(f"  Спрайтов в кэше: {len(npc.animator.sprites)}")
    print(f"  Текущий спрайт: {npc.animator.current_image is not None}")
    
    # Проверяем движение
    for direction in ['front', 'back', 'left', 'right']:
        key = f"move_{direction}_1"
        if key in npc.animator.sprites:
            print(f"  ✅ {key} — загружен")
        else:
            print(f"  ❌ {key} — НЕ загружен")
    
    # ============================================================
    # 3. ПРОВЕРКА FSM
    # ============================================================
    print("\n[3] Проверка конечного автомата...")
    
    # IDLE
    npc.state = "IDLE"
    npc.update()
    print(f"  IDLE: состояние {npc.state}")
    
    # CHASE (ставим игрока рядом)
    game.player.x = 11.0
    game.player.y = 10.0
    npc.state = "CHASE"
    npc.update()
    print(f"  CHASE: состояние {npc.state}, дистанция до игрока: {math.hypot(npc.x - game.player.x, npc.y - game.player.y):.2f}")
    
    # ATTACK (ставим игрока вплотную)
    game.player.x = 10.2
    game.player.y = 10.0
    npc.state = "ATTACK"
    npc.update()
    print(f"  ATTACK: состояние {npc.state}")
    
    # SHOOT
    npc.shoot_flash = 10
    npc.update()
    print(f"  SHOOT: вспышка {npc.shoot_flash}")
    
    # ============================================================
    # 4. ПРОВЕРКА УРОНА
    # ============================================================
    print("\n[4] Проверка получения урона...")
    
    hp_before = npc.hp
    npc.get_damage(25)
    print(f"  Урон 25: {hp_before} -> {npc.hp}")
    
    # ============================================================
    # 5. ПРОВЕРКА СМЕРТИ
    # ============================================================
    print("\n[5] Проверка смерти...")
    
    npc.hp = 10
    npc.get_damage(50)
    print(f"  alive: {npc.alive}")
    print(f"  state: {npc.state}")
    print(f"  death_type: {npc.death_type}")
    print(f"  death_frame: {npc.animator.death_frame}")
    
    # ============================================================
    # 6. ПРОВЕРКА ОТРИСОВКИ
    # ============================================================
    print("\n[6] Проверка отрисовки...")
    
    try:
        npc.draw()
        print("  ✅ draw() выполнен без ошибок")
    except Exception as e:
        print(f"  ❌ Ошибка в draw(): {e}")

    print("\n" + "=" * 70)
    print("✅ ТЕСТ ЗАВЕРШЁН")
    print("=" * 70)


if __name__ == "__main__":
    run_npc_test()
