import os
import sys
import math
import pygame
import types
import importlib.util

# ==============================================================================
# 1. СЕТАП
# ==============================================================================
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    pygame.mixer.init()
except:
    pass

WIDTH, HEIGHT = 1024, 768
HALF_WIDTH, HALF_HEIGHT = WIDTH // 2, HEIGHT // 2
NUM_RAYS = 120
HALF_NUM_RAYS = NUM_RAYS // 2
SCALE = WIDTH // NUM_RAYS
FOV = math.pi / 3
HALF_FOV = FOV / 2
DELTA_ANGLE = FOV / NUM_RAYS
SCREEN_DIST = HALF_WIDTH / math.tan(HALF_FOV)

NPC_CONFIG = {
    'B': {
        'name': 'HellSmith',
        'speed': 0.15, 'hp': 2000, 'damage': 20,
        'activation_distance': 35, 'view_distance': 25, 'shoot_range': 12.0, 'shoot_delay': 1800,
        'sound_volume': 0.45,
    }
}

class MockSettings:
    globals().update({
        'WIDTH': WIDTH, 'HEIGHT': HEIGHT, 'HALF_WIDTH': HALF_WIDTH, 'HALF_HEIGHT': HALF_HEIGHT,
        'NUM_RAYS': NUM_RAYS, 'HALF_NUM_RAYS': HALF_NUM_RAYS, 'SCALE': SCALE,
        'FOV': FOV, 'HALF_FOV': HALF_FOV, 'DELTA_ANGLE': DELTA_ANGLE, 'SCREEN_DIST': SCREEN_DIST
    })

class MockGameData:
    NPC_CONFIG = NPC_CONFIG

sys.modules['setting'] = MockSettings
sys.modules['config'] = MockSettings
sys.modules['config.game_data'] = MockGameData

from core.npc import NPC, NPCAnimator

class MockPlayer:
    def __init__(self):
        self.x, self.y = 5.5, 5.5
        self.angle = 0.0
        self.hp = 100
        self.armor = 0
    def take_damage(self, dmg): 
        self.hp -= dmg
        print(f"   [ИГРОК] Получен урон {dmg}, HP: {self.hp}")

class MockMap:
    def is_wall(self, x, y): 
        return False
    def is_walkable(self, x, y):
        return True

class MockRaycasting:
    def __init__(self):
        self.z_buffer = [99.0] * NUM_RAYS

class MockSurface:
    def __init__(self, filename):
        self.file_name = filename
    def get_size(self):
        return (128, 128)
    def get_width(self):
        return 128
    def get_height(self):
        return 128
    def subsurface(self, *args, **kwargs):
        return self

class TrackedSound:
    def __init__(self, filepath):
        self.filepath = filepath
        self.played_count = 0
    def set_volume(self, vol): 
        pass
    def play(self, loops=0):
        self.played_count += 1
        return pygame.mixer.Channel(0)
    def stop(self): 
        pass

class MockLevelManager:
    def __init__(self):
        self.npcs = []
        self.total_kills = 0
        self.map = MockMap()
        self.width = 50
        self.height = 50

class MockPathfinder:
    def a_star(self, start, goal, max_distance=5):
        return []

class MockGame:
    def __init__(self):
        self.player = MockPlayer()
        self.map = MockMap()
        self.raycasting = MockRaycasting()
        self.level_manager = MockLevelManager()
        self.pathfinder = MockPathfinder()
        self.delta_time = 0.016
        self.particles = []
        self.screen = pygame.Surface((WIDTH, HEIGHT))
        self.items = []
        self.npcs = []


# ==============================================================================
# 2. ФУНКЦИЯ ЗАГРУЗКИ LOGIC.PY ИЗ ПАПКИ БОССА
# ==============================================================================

def load_boss_logic(boss):
    """Загружает logic.py из папки босса и вызывает init_logic"""
    logic_path = os.path.join(boss.folder_path, 'logic.py')
    
    if not os.path.exists(logic_path):
        print(f"  ⚠️ logic.py не найден: {logic_path}")
        return False
    
    print(f"  📂 Загружаем logic.py из: {logic_path}")
    
    try:
        spec = importlib.util.spec_from_file_location("boss_logic", logic_path)
        logic_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(logic_module)
        
        if hasattr(logic_module, 'init_logic'):
            print("  ✅ init_logic найден, вызываем...")
            logic_module.init_logic(boss)
            return True
        else:
            print("  ❌ init_logic не найден в logic.py")
            return False
    except Exception as e:
        print(f"  ❌ Ошибка загрузки logic.py: {e}")
        return False


# ==============================================================================
# 3. ТЕСТ
# ==============================================================================

def run_boss_debug():
    print("=" * 100)
    print("🔍 ПОШАГОВАЯ ДИАГНОСТИКА: ПОЧЕМУ БОСС СТРЕЛЯЕТ КАК ОБЫЧНЫЙ NPC")
    print("=" * 100)

    # Мокаем загрузчик
    def mock_loader(self_animator, filename, scale, fallback_color=(0,0,0), fallback_sprite=None):
        return MockSurface(filename)
    NPCAnimator._load_and_scale_file = mock_loader
    pygame.mixer.Sound = TrackedSound

    game = MockGame()
    
    # ============================================================
    # ШАГ 1: СОЗДАНИЕ БОССА
    # ============================================================
    print("\n[ШАГ 1] Создание босса...")
    boss = NPC(game, 'B', pos=(10.5, 10.5))
    game.level_manager.npcs.append(boss)
    game.npcs.append(boss)
    boss.has_line_of_sight = lambda: True
    boss.activation_distance = 50
    
    print(f"  ✅ Босс создан")
    print(f"  📁 Имя: {boss.name}")
    print(f"  📁 Папка: {boss.folder_path}")
    print(f"  📊 state: {boss.state}")
    print(f"  📊 boss_state: {boss.boss_state if hasattr(boss, 'boss_state') else 'НЕТУ!'}")
    
    # ============================================================
    # ШАГ 2: ЗАГРУЗКА LOGIC.PY
    # ============================================================
    print("\n[ШАГ 2] Загрузка logic.py из папки босса...")
    success = load_boss_logic(boss)
    
    if success:
        print(f"  ✅ logic.py загружен!")
        print(f"  📊 boss_state: {boss.boss_state}")
        print(f"  📊 boss_projectiles: {len(boss.boss_projectiles) if hasattr(boss, 'boss_projectiles') else 0}")
    else:
        print("  ❌ logic.py НЕ загружен!")
    
    # ============================================================
    # ШАГ 3: ПРОВЕРКА UPDATE
    # ============================================================
    print("\n[ШАГ 3] Проверка метода update...")
    print(f"  📍 Текущий update: {boss.update}")
    print(f"  📍 Это стандартный NPC.update? {'✅ ДА' if 'NPC.update' in str(boss.update) else '❌ НЕТ'}")
    print(f"  📍 Это кастомный boss_custom_update? {'✅ ДА' if 'boss_custom_update' in str(boss.update) else '❌ НЕТ'}")
    
    if 'NPC.update' in str(boss.update):
        print("\n  ⚠️  ПРОБЛЕМА: update не был заменён на кастомный!")
        print("  🔧 Решение: в logic.py в init_logic добавить:")
        print("     import types")
        print("     self.update = types.MethodType(boss_custom_update, self)")
    
    # ============================================================
    # ШАГ 4: ПРОВЕРКА АТАКИ
    # ============================================================
    print("\n[ШАГ 4] Проверка атаки...")
    print("  🎯 Устанавливаем игрока на дистанции 10 клеток...")
    game.player.x = boss.x + 10.0
    game.player.y = boss.y
    boss.last_shot = pygame.time.get_ticks() - 5000
    
    # Проверяем, какой метод вызывается
    if 'boss_custom_update' in str(boss.update):
        print("  🔄 Вызываем кастомный update...")
        boss.update(0.016)
    else:
        print("  ⚠️ Кастомный update не подключен, вызываем стандартный...")
        boss.update()  # Без аргумента
    
    print(f"\n  📊 Результат:")
    print(f"     state: {boss.state}")
    print(f"     boss_state: {boss.boss_state if hasattr(boss, 'boss_state') else 'НЕТУ!'}")
    print(f"     boss_attack_frame: {boss.boss_attack_frame if hasattr(boss, 'boss_attack_frame') else 'НЕТУ!'}")
    print(f"     Снарядов: {len(boss.boss_projectiles) if hasattr(boss, 'boss_projectiles') else 0}")
    
    # ============================================================
    # ШАГ 5: ПОШАГОВОЕ ТИКАНЬЕ
    # ============================================================
    print("\n[ШАГ 5] Пошаговое тиканье атаки (5 тиков)...")
    
    for tick in range(1, 6):
        if hasattr(boss, 'boss_attack_timer'):
            boss.boss_attack_timer -= 200
        
        if 'boss_custom_update' in str(boss.update):
            boss.update(0.016)
        else:
            boss.update()
        
        tex_name = getattr(boss.image, 'file_name', str(boss.image))
        proj_count = len(boss.boss_projectiles) if hasattr(boss, 'boss_projectiles') else 0
        
        print(f"\n  Тик {tick}:")
        print(f"     Кадр: {boss.boss_attack_frame if hasattr(boss, 'boss_attack_frame') else 'НЕТУ'}")
        print(f"     state: {boss.state}")
        print(f"     boss_state: {boss.boss_state if hasattr(boss, 'boss_state') else 'НЕТУ'}")
        print(f"     Текстура: {tex_name}")
        print(f"     Снарядов: {proj_count}")

    # ============================================================
    # ИТОГИ
    # ============================================================
    print("\n" + "=" * 100)
    print("📊 ИТОГОВЫЙ ДИАГНОЗ")
    print("=" * 100)
    
    issues = []
    if not hasattr(boss, 'boss_state') or boss.boss_state == "CHASE":
        issues.append("❌ boss_state не установлен или не меняется")
    if 'NPC.update' in str(boss.update):
        issues.append("❌ update не заменён на кастомный")
    if len(boss.boss_projectiles) == 0:
        issues.append("❌ Снаряды не создаются")
    
    if issues:
        print("\n  Найдены проблемы:")
        for i, issue in enumerate(issues, 1):
            print(f"     {i}. {issue}")
        print("\n  🔧 Рекомендации:")
        print("     1. Проверь, что в logic.py есть:")
        print("        self.update = types.MethodType(boss_custom_update, self)")
        print("     2. Проверь имена файлов эффектов в папке босса")
        print("     3. Убедись, что файлы эффектов существуют")
    else:
        print("\n  ✅ Все системы работают корректно!")

if __name__ == '__main__':
    run_boss_debug()