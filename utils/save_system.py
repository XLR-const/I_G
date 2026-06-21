"""Система сохранения и загрузки прогресса

Содержит класс SaveSystem для работы с файлом сохранения.
"""

import os


class SaveSystem:
    """Класс для работы с сохранениями

    Attributes:
        SAVE_FILE (str): Путь к файлу сохранения
    """

    SAVE_FILE = 'resources/save.sav'

    @staticmethod
    def save(level_num, total_kills, level_time):
        """Сохраняет прогресс игры

        Args:
            level_num: Номер текущего уровня
            total_kills: Общее количество убийств
            level_time: Время прохождения уровня

        Returns:
            bool: True если сохранение успешно, False если ошибка
        """
        try:
            with open(SaveSystem.SAVE_FILE, 'w') as f:
                f.write("[PROGRESS]\n")
                f.write(f"current_level={level_num}\n")
                f.write(f"total_kills={total_kills}\n")
                f.write(f"last_level_time={level_time}\n")
            return True
        except Exception as e:
            print(f"Ошибка сохранения: {e}")
            return False

    @staticmethod
    def load():
        """Загружает сохранённый прогресс

        Returns:
            dict: Данные сохранения или None если файл не найден
        """
        if not os.path.exists(SaveSystem.SAVE_FILE):
            print("Файл сохранения не найден")
            return None

        try:
            data = {}
            with open(SaveSystem.SAVE_FILE, 'r') as f:
                for line in f:
                    if '=' in line:
                        key, value = line.strip().split('=')
                        data[key] = value
            return data
        except Exception as e:
            print(f"Ошибка загрузки: {e}")
            return None

    @staticmethod
    def delete():
        """Удаляет файл сохранения"""
        if os.path.exists(SaveSystem.SAVE_FILE):
            os.remove(SaveSystem.SAVE_FILE)
