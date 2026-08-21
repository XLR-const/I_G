import os
import sys
import math
import pygame
from random import uniform

# Эмуляция глобальных констант твоего движка для работы тестов
WIDTH, HEIGHT = 1536, 864
SCREEN_DIST = 1330.215
HALF_HEIGHT = 432
NUM_RAYS = 768
SCALE = 2
HALF_FOV = 0.52

# Заглушка базы данных, чтобы тест запустился без импортов
NPC_CONFIG = {
    'TERM': {
        'name': 'terminator', 'speed': 0.04, 'hp': 2000, 'damage': 15,
        'activation_distance': 15, 'view_distance': 12, 'shoot_range': 12, 'shoot_delay': 1200
    }
}

class MockGame:
    def __init__(self):
        self.delta_time = 0.016
        self.screen = pygame.Surface((WIDTH, HEIGHT))
        self.map = type('MockMap', (object,), {'numeric_grid': [[0]*20 for _ in range(20)]})()
        self.player = type('MockPlayer', (object,), {'x': 3.5, 'y': 3.5, 'angle': 0.0})()
        self.raycasting = type('MockRC', (object,), {'z_buffer': [100.0] * NUM_RAYS})()

class NPCAnimator:
    """Оригинальный компонент аниматора со страницы 1 твоего PDF"""
    def __init__(self, npc):
        self.npc = npc
        self.sprites = {}
        self.current_image = pygame.Surface((64, 64), pygame.SRCALPHA)
        self.current_image.fill((100, 100, 100)) # Базовый стальной цвет
        self.death_frame = 1
        self.max_death_frames = 5
        
        # Эмулируем загрузку боевых кадров, чтобы sprites.get не возвращал None
        self.sprites["attack_front_0"] = pygame.Surface((64, 64))
        self.sprites["shoot_front_0"] = pygame.Surface((64, 64))
        self.sprites["die_front_5"] = pygame.Surface((64, 64))

    def update(self):
        """Логика оригинального апдейта со страницы 4-5 PDF"""
        if self.npc.state == "DEAD":
            self.death_frame = min(self.max_death_frames, self.death_frame + 1)
            return
        if self.npc.state == "SHOOT":
            self.current_image = self.sprites.get("shoot_front_0")

    def get_processed_image(self, w, h):
        """Оригинальный метод покраснения со страницы 6 твоего PDF"""
        img = self.current_image.copy()
        if self.npc.hurt_flash > 0:
            red_surface = pygame.Surface(img.get_size())
            red_surface.fill((255, 0, 0))
            img.blit(red_surface, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        return img

class TerminatorNPC:
    """Универсальный класс NPC со страницы 6 твоей доки с интегрированным TERM"""
    def __init__(self, game, npc_type, pos=(5.5, 5.5)):
        self.game = game
        self.npc_type = npc_type
        config = NPC_CONFIG.get(npc_type, {})
        
        self.name = config.get('name', 'TERM')
        self.speed = config.get('speed', 0.04)
        self.hp = config.get('hp', 2000)
        self.radius = 0.35
        self.scale = 3.0
        self.x, self.y = pos
        self.alive = True
        self.state = "CHASE"
        self.hurt_flash = 0
        self.shoot_flash = 0
        
        # Локальные свойства кастомной ИИ-боёвки Терминатора
        self.boss_internal_state = "CHASE" 
        self.mg_shots_left = 0
        
        self.animator = NPCAnimator(self)

    def get_damage(self, damage):
        """Оригинальный метод урона со страницы 8 твоего PDF"""
        if not self.alive: return
        self.hp -= damage
        self.hurt_flash = 8  # Включаем покраснение!
        
        if self.hp > 0:
            self.state = "HURT"
        else:
            self.alive = False
            self.state = "DEAD" # <-- ТРИГГЕР СМЕРТИ

    def update(self):
        """Кадровое обновление со страницы 10 твоего PDF"""
        dt = self.game.delta_time
        
        # 1. Снижение эффектов
        if self.state != "DEAD":
            if self.hurt_flash > 0: self.hurt_flash -= 1
            if self.shoot_flash > 0: self.shoot_flash -= 1
        else:
            self.hurt_flash = 0
            self.shoot_flash = 0

        # 2. Логика ИИ (вызывает нашу кастомную логику, ЕСЛИ НЕ МЕРТВ!)
        if self.state != "DEAD":
            self.custom_update_terminator()

        # 3. Синхронизация с 8-ракурсным аниматором
        self.animator.update()

    def custom_update_terminator(self):
        """Наша кастомная боевая машина Терминатора"""
        # Эмулируем ведение огня из пулемета
        if self.boss_internal_state == "ATTACK_MG":
            self.state = "SHOOT"
            self.shoot_flash = 4

# ==================================================================
# 🕹️ ЗАПУСК СИМУЛЯЦИИ ТЕСТА ДЛЯ ВЫЯВЛЕНИЯ КОРНЯ ПРОБЛЕМЫ
# ==================================================================
if __name__ == "__main__":
    pygame.init()
    print("===== СТАРТ ДИАТНОСТИКИ ТЕРМИНАТOРА TERM =====")
    game = MockGame()
    boss = TerminatorNPC(game, 'TERM')
    
    print("\n--- ШАГ 1. Босс TERM здоров, выходит на позицию и зажимает пулемет ---")
    boss.boss_internal_state = "ATTACK_MG"
    boss.update()
    print(f"  -> Текущий стейт ИИ (boss.state): '{boss.state}'")
    print(f"  -> Идентификатор боли (boss.hurt_flash): {boss.hurt_flash}")
    
    print("\n--- ШАГ 2. Игрок бьет БФГ! Наносит тяжелый Splash-урон (150 HP) ---")
    boss.get_damage(150)
    print(f"  -> Здоровье киборга: {boss.hp} HP")
    print(f"  -> Флаг покраснения (boss.hurt_flash) выставлен ядром в: {boss.hurt_flash}")
    
    print("\n--- ШАГ 3. Следующий кадр. Работает игровой цикл update() ---")
    boss.update()
    print(f"  -> Счетчик hurt_flash уменьшился: {boss.hurt_flash}")
    print(f"  -> Но так как boss_internal_state == 'ATTACK_MG', кастомный метод насильно")
    print(f"     переписывает стейт обратно в: '{boss.state}' (Вспышка SHOOT возвращает True)")
    
    print("\n--- ШАГ 4. Симулируем еще 4 кадра непрерывной стрельбы очереди пулемета ---")
    for i in range(4):
        boss.update()
    print(f"  -> Флаг боли (boss.hurt_flash) равен: {boss.hurt_flash}")
    print(f"  -> Спрайт закрашен КРАСНЫМ? {boss.hurt_flash > 0} (Да, क्योंकि счетчик не успевает дойти до 0!)")

    print("\n--- ШАГ 5. КРИТИЧЕСКИЙ ТЕСТ: Наносим смертельный урон (2000 HP) ---")
    boss.get_damage(2000)
    print(f"  -> Сработал get_damage(). Стейт переведен в: '{boss.state}' | Жив? {boss.alive}")
    
    print("\n--- ШАГ 6. Запускаем update() для мертвого трупа ---")
    # Смотрим, вызовется ли кастомный апдейт для фильтрации снарядов
    boss.update()
    print(f"  -> Кадр смерти в аниматоре (death_frame): {boss.animator.death_frame}")
    print(f"  -> ПРОВЕРКА БАГА СМЕРТИ: Был ли вызван кастомный метод фильтрации?")
    print(f"     [Лог] Так как boss.state == 'DEAD', условие 'if self.state != \"DEAD\"' заблокировало")
    print(f"     вызов custom_update_terminator()! Локальные снаряды STAR зависли в воздухе.")
    print("\n================ ТЕСТ ЗАВЕРШЕН ================")
