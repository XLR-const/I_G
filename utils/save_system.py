import os

class SaveSystem:
    SAVE_FILE = 'resources/save.sav'

    @staticmethod
    def save(level_manager, total_kills, level_time):
        """
        Сохраняет прогресс игрока, автоматически вытягивая данные из LevelManager.
        Совместим со стандартным вызовом из движка игры.
        """
        try:
            # Гарантируем наличие папки resources, если её вдруг стерли
            os.makedirs(os.path.dirname(SaveSystem.SAVE_FILE), exist_ok=True)
            
            # Извлекаем данные напрямую из переданного объекта менеджера уровней
            act_idx = getattr(level_manager, 'current_act_index', 0)
            level_num = getattr(level_manager, 'current_level', 1)
            
            with open(SaveSystem.SAVE_FILE, 'w', encoding='utf-8') as f:
                f.write("[PROGRESS]\n")
                # Записываем индекс акта из секвенсора ACTS_SEQUENCE
                f.write(f"current_act_idx={act_idx}\n")
                f.write(f"current_level={level_num}\n")
                f.write(f"total_kills={total_kills}\n")
                f.write(f"last_level_time={level_time}\n")
                
            print(f"💾 [Сейв-Система] Прогресс успешно сохранен! Акт индекс: {act_idx}, Уровень: {level_num}")
            return True
        except Exception as e:
            print(f"❌ Ошибка сохранения: {e}")
            return False

    @staticmethod
    def load():
        """Загружает данные сохранения и автоматически переводит их в числа"""
        if not os.path.exists(SaveSystem.SAVE_FILE):
            print("Файл сохранения не найден")
            return None
        try:
            raw_data = {}
            with open(SaveSystem.SAVE_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    if '=' in line:
                        key, value = line.strip().split('=')
                        raw_data[key] = value

            # УМНЫЙ СТРОГИЙ ПАРСИНГ: Переводим строки в честные int для движка Pygame
            processed_data = {
                'current_act_idx': int(raw_data.get('current_act_idx', 0)), # По дефолту 0 акт
                'current_level': int(raw_data.get('current_level', 1)),     # По дефолту 1 уровень
                'total_kills': int(raw_data.get('total_kills', 0)),
                'last_level_time': int(raw_data.get('last_level_time', 0))
            }
            print(f"📂 [Сейв-Система] Сейв успешно считан! Загружаем Акт {processed_data['current_act_idx']}, Уровень {processed_data['current_level']}")
            return processed_data
        except Exception as e:
            print(f"❌ Ошибка загрузки: {e}")
            return None

    @staticmethod
    def delete():
        """Удаляет файл сохранения"""
        if os.path.exists(SaveSystem.SAVE_FILE):
            try:
                os.remove(SaveSystem.SAVE_FILE)
                print("🗑️ [Сейв-Система] Файл сохранения успешно удален.")
                return True
            except Exception as e:
                print(f"❌ Ошибка удаления сейва: {e}")
                return False
        return False
