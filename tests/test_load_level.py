import os
import sys
import json
import pygame

# Инициализируем Pygame для работы с поверхностями в тесте
pygame.init()
pygame.display.set_mode((100, 100), pygame.NOFRAME)

print("====================================================")
print("🔍 ГЛУБОКИЙ ТЕСТ ЗАГРУЗКИ ТЕКСТУР И КЭША ОЗУ ДЛЯ АКТОВ")
print("====================================================")

# 1. Эмулируем минимальные зависимости твоего движка
class MockRenderer:
    def __init__(self):
        self.sky_texture = "СТАРЫЙ_СКАЙБОКС_1"
        self.wall_textures = {1: "СТАРАЯ_СТЕНА_УРОВНЯ_1"}
    def set_background(self, bg_data):
        self.sky_texture = bg_data.get('sky', 'sky_default.png')
        print(f"  📺 [Рендерер] Смена скайбокса! Новое небо в ОЗУ: '{self.sky_texture}'")

class MockRaycasting:
    def __init__(self):
        self.texture_cache = {"wall_1": "КЭШ_ТЕКСТУРЫ_1_УРОВНЯ"}
    def clear_cache(self):
        print("  🧹 [Рейкастер] Запрос .texture_cache.clear() обработан.")
        self.texture_cache.clear()

class MockGame:
    def __init__(self):
        self.renderer = MockRenderer()
        self.raycasting = MockRaycasting()

# 2. Подтягиваем твой реальный LevelManager (или его эмуляцию)
class DiagnosticLevelManager:
    def __init__(self, game):
        self.game = game
        self.levels_folder = "resources/levels"
        self.current_act_idx = 0
        self.acts_sequence = ['act_invasion'] # Твой тестовый акт
        
    def test_load(self, level_num):
        act_name = self.acts_sequence[self.current_act_idx]
        file_path = f"{self.levels_folder}/{act_name}/level_{level_num}.json"
        
        print(f"\n📂 Читаю файл на диске: {file_path}")
        if not os.path.exists(file_path):
            print(f"  ❌ Ошибка: Файл {file_path} физически отсутствует!")
            return False
            
        with open(file_path, 'r', encoding='utf-8') as f:
            level_data = json.load(f)

        print("⚡ [Шаг 1] Очистка старого кэша текстур:")
        if hasattr(self.game, 'raycasting'):
            self.game.raycasting.texture_cache.clear()

        print("⚡ [Шаг 2] Сканирование данных JSON Уровня:")
        # Извлекаем параметры неба
        background = level_data.get('background', {})
        print(f"  -> Данные background из JSON: {background}")
        self.game.renderer.set_background(background)
        
        # Сканируем, есть ли в твоем JSON кастомный словарь новых текстур уровня
        textures_config = level_data.get('textures', level_data.get('wall_textures', None))
        print(f"  -> Кастомные текстуры из JSON: {textures_config}")
        
        # 🔍 КРИТИЧЕСКИЙ АНАЛИЗ СБОЯ:
        if not textures_config:
            print("  ⚠️  [ВНИМАНИЕ] В JSON-файле этого уровня отсутствует блок 'textures'!")
            print("      Рендерер не знает, какие картинки сопоставить числовым ID стен,")
            print("      и движок принудительно оставляет старые текстуры из Уровня 1!")
            
        return True

# Запуск симуляции
game = MockGame()
lm = DiagnosticLevelManager(game)

# Проверяем Уровень 2 в твоем Акте Invasion
success = lm.test_load(2)

print("\n================ Диагностика Завершена ================")
