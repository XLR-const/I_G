"""Точка входа в редактор карт"""

import sys
import os

# Добавляем путь к папке utils
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.map_editor.editor import MapEditor


def main():
    """Запуск редактора"""
    level_file = None

    # Проверяем аргументы командной строки
    if len(sys.argv) > 1:
        level_file = sys.argv[1]

    editor = MapEditor(level_file)
    editor.run()


if __name__ == "__main__":
    main()