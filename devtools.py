#!/usr/bin/env python
"""Map Tools — единый инструмент для генерации и редактирования уровней"""

import os
import sys
import subprocess
import glob

# Пути к скриптам
GENERATOR_PATH = os.path.join("utils", "generate_levels.py")
EDITOR_PATH = os.path.join("map_editor", "main.py")
DEV_MODE_PATH = os.path.join("dev_mode.py")
LEVELS_DIR = os.path.join("resources", "levels")
TESTS_DIR = os.path.join("tests")


def clear_screen():
    """Очищает экран терминала"""
    os.system('cls' if os.name == 'nt' else 'clear')


def get_levels():
    """Возвращает список доступных уровней"""
    if not os.path.exists(LEVELS_DIR):
        return []
    levels = []
    for f in os.listdir(LEVELS_DIR):
        if f.endswith('.json') and not f.startswith('level_backup'):
            try:
                num = int(f.replace('level_', '').replace('.json', ''))
                levels.append(num)
            except:
                pass
    return sorted(levels)


def get_tests():
    """Возвращает список тестов из папки tests"""
    if not os.path.exists(TESTS_DIR):
        return []
    tests = []
    for f in os.listdir(TESTS_DIR):
        if f.endswith('.py') and f != '__init__.py':
            tests.append(f)
    return sorted(tests)


def print_header():
    """Печатает заголовок"""
    print("\n" + "=" * 60)
    print("  🗺️  MAP TOOLS — Управление уровнями")
    print("=" * 60)


def print_menu():
    """Печатает меню"""
    print("\n  [1] Генератор уровней")
    print("  [2] Редактор уровней")
    print("  [3] Список уровней")
    print("  [4] Запустить игру (DEV MODE)")
    print("  [5] Запустить тесты")
    print("  [0] Выход")
    print("-" * 60)


def run_generator():
    """Запускает генератор в интерактивном режиме"""
    print("\n" + "=" * 60)
    print("  🔧 ГЕНЕРАТОР УРОВНЕЙ")
    print("=" * 60)
    print("\n[Интерактивный режим]")
    print("  Будет запущен генератор с пошаговым вводом параметров.\n")
    
    input("Нажмите Enter для запуска генератора...")
    
    subprocess.run([sys.executable, GENERATOR_PATH])
    
    input("\nНажмите Enter для возврата в меню...")


def run_editor():
    """Запускает редактор с выбором уровня"""
    clear_screen()
    print_header()
    
    levels = get_levels()
    
    if not levels:
        print("\n⚠️  Нет доступных уровней!")
        print("  Сначала создайте уровень через генератор (пункт 1).")
        input("\nНажмите Enter для возврата...")
        return
    
    print("\n  📂 ДОСТУПНЫЕ УРОВНИ:")
    print("-" * 60)
    
    for i, num in enumerate(levels):
        print(f"    {i+1:2d}. Уровень {num}")
    
    print("-" * 60)
    
    while True:
        try:
            choice = input("\n  Выберите номер уровня (или 0 для отмены): ").strip()
            
            if choice == '0':
                return
            
            idx = int(choice) - 1
            
            if 0 <= idx < len(levels):
                level_num = levels[idx]
                file_path = os.path.join(LEVELS_DIR, f"level_{level_num}.json")
                
                print(f"\n  🚀 Открываю уровень {level_num} в редакторе...")
                
                subprocess.run([sys.executable, EDITOR_PATH, file_path])
                
                input("\nНажмите Enter для возврата в меню...")
                return
            else:
                print(f"  ❌ Неверный номер. Выберите от 1 до {len(levels)}")
        except ValueError:
            print("  ❌ Введите число!")


def list_levels():
    """Показывает список уровней с информацией"""
    clear_screen()
    print_header()
    
    levels = get_levels()
    
    if not levels:
        print("\n⚠️  Нет доступных уровней!")
        print("  Сначала создайте уровень через генератор (пункт 1).")
        input("\nНажмите Enter для возврата...")
        return
    
    print("\n  📂 СПИСОК УРОВНЕЙ:")
    print("-" * 60)
    print(f"  {'№':<6} {'Файл':<20} {'Размер':<15}")
    print("-" * 60)
    
    for num in levels:
        file_path = os.path.join(LEVELS_DIR, f"level_{num}.json")
        size = "—"
        try:
            import json
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                map_data = data.get('map', [])
                if map_data:
                    size = f"{len(map_data[0])}x{len(map_data)}"
        except:
            pass
        
        print(f"  {num:<6} level_{num}.json{' ':<12} {size:<15}")
    
    print("-" * 60)
    print(f"  Всего уровней: {len(levels)}")
    
    input("\nНажмите Enter для возврата в меню...")


def run_dev_mode():
    """Запускает dev_mode.py"""
    print("\n" + "=" * 60)
    print("  🛠️  ЗАПУСК РЕЖИМА РАЗРАБОТКИ")
    print("=" * 60)
    print("\n  Запускается dev_mode.py")
    print("  По умолчанию: без UI и без музыки (быстрый запуск)")
    print("  Будет предложено настроить компоненты.")

    input("\nНажмите Enter для запуска...")

    subprocess.run([sys.executable, DEV_MODE_PATH])

    input("\nНажмите Enter для возврата в меню...")


def run_tests():
    """Запускает тесты из папки tests"""
    clear_screen()
    print_header()
    
    tests = get_tests()
    
    if not tests:
        print("\n⚠️  Нет доступных тестов в папке tests/")
        print("  Добавьте тесты в папку tests/")
        input("\nНажмите Enter для возврата...")
        return
    
    print("\n  🧪 ДОСТУПНЫЕ ТЕСТЫ:")
    print("-" * 60)
    
    for i, test_name in enumerate(tests):
        print(f"    {i+1:2d}. {test_name}")
    
    print("-" * 60)
    
    while True:
        try:
            choice = input("\n  Выберите номер теста (или 0 для отмены): ").strip()
            
            if choice == '0':
                return
            
            idx = int(choice) - 1
            
            if 0 <= idx < len(tests):
                test_name = tests[idx]
                test_path = os.path.join(TESTS_DIR, test_name)
                
                print(f"\n  🚀 Запускаю тест: {test_name}")
                print("  " + "-" * 40)
                
                subprocess.run([sys.executable, test_path])
                
                print("\n  " + "-" * 40)
                print(f"  ✅ Тест {test_name} завершён.")
                
                input("\nНажмите Enter для возврата в меню...")
                return
            else:
                print(f"  ❌ Неверный номер. Выберите от 1 до {len(tests)}")
        except ValueError:
            print("  ❌ Введите число!")


def main():
    """Главный цикл"""
    while True:
        clear_screen()
        print_header()
        print_menu()
        
        choice = input("\n  Введите номер действия: ").strip()
        
        if choice == '1':
            run_generator()
        elif choice == '2':
            run_editor()
        elif choice == '3':
            list_levels()
        elif choice == '4':
            run_dev_mode()
        elif choice == '5':
            run_tests()
        elif choice == '0':
            print("\n  👋 До свидания!")
            sys.exit(0)
        else:
            print("\n  ❌ Неверный ввод. Выберите 0-5.")
            input("\nНажмите Enter для продолжения...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  👋 До свидания!")
        sys.exit(0)
