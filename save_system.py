import os

class SaveSystem:
    SAVE_FILE = 'resources/save.sav'
    
    @staticmethod
    def save(level_num, total_kills, level_time):
        """Сохранение игры после лвла
        без создания экземпляра класса"""
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
        """Загрузка сохранения"""
        if not os.path.exists(SaveSystem.SAVE_FILE):
            print("Файл сохранения не найден")
            return None
        try:
            data ={}
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
        """Удаление сохранения при новом старте игры"""
        if os.path.exists(SaveSystem.SAVE_FILE):
            os.remove(SaveSystem.SAVE_FILE)
