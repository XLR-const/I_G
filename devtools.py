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
MAIN_DIR = os.path.join("main.py")
PTP_DIR = os.path.join("utils", "py_to_pdf.py")


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

def select_act():
    """Динамически сканирует диск и предлагает выбрать существующую папку Акта"""
    if not os.path.exists(LEVELS_DIR):
        print(f"\n⚠️ Корневая папка '{LEVELS_DIR}' отсутствует на диске!")
        input("\nНажмите Enter для возврата...")
        return None

    # Находим все папки внутри resources/levels (отсекаем бэкапы и файлы json)
    acts = []
    for entry in os.listdir(LEVELS_DIR):
        full_path = os.path.join(LEVELS_DIR, entry)
        if os.path.isdir(full_path) and not entry.startswith('.') and 'backup' not in entry:
            acts.append(entry)
            
    acts = sorted(acts)

    if not acts:
        print(f"\n⚠️ Внутри '{LEVELS_DIR}' еще не создано ни одной папки Акта!")
        print(" Создайте структуру папок (например: resources/levels/act_invasion/) вручную.")
        input("\nНажмите Enter для возврата...")
        return None

    while True:
        clear_screen()
        print_header()
        print("\n 🎭 ВЫБЕРИТЕ СЮЖЕТНЫЙ АКТ (ОБНАРУЖЕНО НА ДИСКЕ):")
        print("-" * 60)
        for i, act_folder in enumerate(acts):
            # Красиво форматируем для отображения: act_ventilation -> Ventilation
            display_name = act_folder.replace('act_', '').capitalize()
            print(f"  [{i + 1}] {display_name} ({act_folder})")
        print("  [0] Назад в главное меню")
        print("-" * 60)
        
        choice = input("\n Введите номер акта: ").strip()
        if choice == '0':
            return None
            
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(acts):
                return acts[idx]
            else:
                print(f" ❌ Неверный номер. Выберите от 1 до {len(acts)}")
                input(" Нажмите Enter для повтора...")
        except ValueError:
            print(" ❌ Введите число!")
            input(" Нажмите Enter для повтора...")

def get_levels(act_folder):
    """Возвращает список доступных числовых уровней внутри выбранной папки Акта"""
    act_dir = os.path.join(LEVELS_DIR, act_folder)
    if not os.path.exists(act_dir):
        return []
        
    levels = []
    for f in os.listdir(act_dir):
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
    print("  🗺️   DEV TOOLS - ИНСТРУМЕНТ ДЛЯ РАЗРАБОТКИ")
    print("=" * 60)


def print_menu():
    """Печатает меню"""
    print("\n  [1] Генератор уровней")
    print("  [2] Редактор уровней")
    print("  [3] Список уровней")
    print("  [4] Запустить игру (DEV MODE)")
    print("  [5] Запустить игру (main.py)")
    print("  [6] Запустить тесты")
    print("  [7] Запустить форматирование имен нпс спрайтов")
    print("  [8] Запустить скрипт форматирования .py -> pdf")
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
    """Запускает редактор карт с динамическим выбором Акта и уровня без хардкода"""
    # 1. Шаг первый — динамически выбираем папку на диске
    chosen_act = select_act()
    if not chosen_act:
        return

    # 2. Шаг второй — вытаскиваем уровни из этой папки
    clear_screen()
    print_header()
    levels = get_levels(chosen_act)
    
    if not levels:
        print(f"\n⚠️ В папке '{chosen_act}' еще нет файлов уровней!")
        print(f" Создайте .json и положите его по пути: {LEVELS_DIR}/{chosen_act}/")
        input("\nНажмите Enter для возврата...")
        return

    print(f"\n 📂 ДОСТУПНЫЕ УРОВНИ В ПАПКЕ '{chosen_act.upper()}':")
    print("-" * 60)
    for i, num in enumerate(levels):
        print(f"  {i+1:2d}. Уровень {num}")
    print("-" * 60)

    # 3. Шаг третий — выбираем и запускаем уровень в map_editor
    while True:
        try:
            choice = input("\n Выберите номер уровня (или 0 для отмены): ").strip()
            if choice == '0':
                return
            idx = int(choice) - 1
            if 0 <= idx < len(levels):
                level_num = levels[idx]
                
                # 🔥 СБOРКА ДИНАМИЧЕСКOГО ПУТИ К КАРТЕ: resources/levels/[ПАПКА_АКТА]/level_[№].json
                file_path = os.path.join(LEVELS_DIR, chosen_act, f"level_{level_num}.json")
                
                print(f"\n 🚀 Открываю {chosen_act}/level_{level_num}.json в редакторе...")
                subprocess.run([sys.executable, EDITOR_PATH, file_path])
                input("\nНажмите Enter для возврата в меню...")
                return
            else:
                print(f" ❌ Неверный номер. Выберите от 1 до {len(levels)}")
        except ValueError:
            print(" ❌ Введите число!")



def list_levels():
    """Показывает структурированный список всех уровней по выбранной папке"""
    chosen_act = select_act()
    if not chosen_act:
        return

    clear_screen()
    print_header()
    levels = get_levels(chosen_act)
    
    if not levels:
        print(f"\n⚠️ В папке '{chosen_act}' нет доступных уровней!")
        input("\nНажмите Enter для возврата...")
        return

    print(f"\n 📂 СПИСОК КАРТ В ПАПКЕ '{chosen_act.upper()}':")
    print("-" * 60)
    print(f"  {'№':<6} {'Имя файла':<25} {'Размер сетки':<15}")
    print("-" * 60)
    
    for num in levels:
        file_path = os.path.join(LEVELS_DIR, chosen_act, f"level_{num}.json")
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
        print(f"  {num:<6} level_{num}.json{' ':<15} {size:<15}")
        
    print("-" * 60)
    print(f"  Всего карт в этой папке: {len(levels)}")
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
    
def run_rename():
    """Запускает утилиту автоматической конвертации спрайтов из папки utils"""
    print("\n" + "=" * 60)
    print("  ⚙️  ЗАПУСК АВТОМАТИЧЕСКОГO КОНВЕРТЕРА REALM667")
    print("=" * 60)
    print("\n  Запускается скрипт utils/converter.py")
    print("  Утилита автоматически переименует DOOM-префиксы,")
    print("  отзеркалит правые ракурсы ног для 2.5D ходьбы,")
    print("  выделит боевые кадры и застрахует X-Die при смерти.")
    
    # Задаем точный относительный путь к файлу конвертера в проекте
    CONVERTER_PATH = os.path.join("utils", "name_converter.py")

    # Страховка: проверяем, что разработчик не забыл создать этот файл
    if not os.path.exists(CONVERTER_PATH):
        print(f"\n  🚨 [КРИТ] Файл утилиты не найден по пути: '{CONVERTER_PATH}'!")
        print("  Убедитесь, что скрипт converter.py лежит внутри папки utils/.")
        input("\nНажмите Enter для возврата в меню...")
        return

    input("\nНажмите Enter для продолжения...")

    try:
        # Запускаем скрипт в том же интерпретаторе Python
        # Консольный ввод/вывод (input папки NPC) автоматически пробросится в текущее окно!
        subprocess.run([sys.executable, CONVERTER_PATH])
    except Exception as e:
        print(f"\n  ❌ Ошибка при выполнении скрипта конвертера: {e}")

    print("\n" + "-" * 60)
    print("  ✅ Возврат в главное меню проекта.")
    print("-" * 60)
    input("Нажмите Enter для продолжения...")
    
def run_main():
    """Запускает мейн версию проекта"""
    try:
        subprocess.run([sys.executable, MAIN_DIR])
    except Exception as e:
        print(f"\n Ошибка запуска: {e}")
    finally:
        print("\n" + "-" * 60)
        print("  ✅ Возврат в главное меню проекта.")
        print("-" * 60)
        input("Нажмите Enter для продолжения...")
        


def run_pdf():
    """Запускает скрипт конвертации папки с файлами
    .py в pdf для ллм"""
    print("\n" + "=" * 60)
    print("  ⚙️  ЗАПУСК АВТОМАТИЧЕСКОГO КОНВЕРТЕРА .py -> pdf")
    input("Нажмите Enter для запуска...")
    
    try:
        subprocess.run([sys.executable, PTP_DIR])
    except Exception as e:
        print(f"Ошибка выполнения: {e}")
    finally:
        print("\n" + "-" * 60)
        print("  ✅ Возврат в главное меню проекта.")
        print("-" * 60)
        input("Нажмите Enter для продолжения...")



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
            run_main()
        elif choice == '6':
            run_tests()
        elif choice == '7':
            run_rename()
        elif choice == '8':
            run_pdf()
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
