import os
import re

# Настройки префикса и имени твоего NPC
NPC_NAME = "TERM"  # Будет подставлено в начало: TERM_move_front_1.png

# Словари соответствия направлений из Doom в твой текстовый формат
DIRECTION_MAP = {
    '1': 'move_front',
    '2': 'move_front_left',
    '3': 'move_left',
    '4': 'move_back_left',
    '5': 'move_back',
    '6': 'move_back_right',
    '7': 'move_right',
    '8': 'move_front_right'
}

# Словари соответствия букв шага в порядковые номера кадров (1, 2, 3, 4)
FRAME_MAP = {
    'A': '1',
    'B': '2',
    'C': '3',
    'D': '4'
}

def convert_doom_sprites():
    print("🚀 Запуск конвертера спрайтов из Doom-формата в кастомный...")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Регулярное выражение для поиска файлов (например, TERM_A1.png, TERMA1.png, BOSSB2C8.png)
    # Ищет 4 буквы названия, затем букву кадра, затем цифру направления
    pattern = re.compile(r'^([A-Z0-True]{4})_?([A-D])([1-8])(?:_?([A-D])([1-8]))?\.png$', re.IGNORECASE)
    
    success_count = 0
    
    # Перебираем все файлы в текущей папке скрипта
    for file_name in os.listdir(current_dir):
        if not file_name.lower().endswith('.png') or file_name == __file__:
            continue
            
        match = pattern.match(file_name)
        if match:
            # Префикс (например, TERM), первая буква кадра, первая цифра направления
            _, frame1, dir1, frame2, dir2 = match.groups()
            
            # Переводим в верхний регистр для надежности
            frame1 = frame1.upper()
            
            # Обработка первой (или единственной) пары кадра/направления
            if frame1 in FRAME_MAP and dir1 in DIRECTION_MAP:
                new_dir_name = DIRECTION_MAP[dir1]
                new_frame_num = FRAME_MAP[frame1]
                new_name = f"{NPC_NAME}_{new_dir_name}_{new_frame_num}.png"
                
                old_path = os.path.join(current_dir, file_name)
                new_path = os.path.join(current_dir, new_name)
                
                try:
                    # Если это одиночный спрайт, просто переименовываем
                    if not frame2:
                        os.rename(old_path, new_path)
                        print(f"✅ {file_name} ➔ {new_name}")
                        success_count += 1
                    else:
                        # Если это совмещенный зеркальный спрайт (например, TERMA2A8.png)
                        # Мы копируем его содержимое во второй файл
                        import shutil
                        
                        # Сохраняем первый файл
                        shutil.copy_file(old_path, new_path)
                        print(f"✅ {file_name} ➔ {new_name} (Копия 1)")
                        success_count += 1
                        
                        # Обрабатываем вторую зеркальную сторону
                        frame2 = frame2.upper()
                        if frame2 in FRAME_MAP and dir2 in DIRECTION_MAP:
                            new_dir_name2 = DIRECTION_MAP[dir2]
                            new_frame_num2 = FRAME_MAP[frame2]
                            new_name2 = f"{NPC_NAME}_{new_dir_name2}_{new_frame_num2}.png"
                            new_path2 = os.path.join(current_dir, new_name2)
                            
                            shutil.copy_file(old_path, new_path2)
                            print(f"✅ {file_name} ➔ {new_name2} (Зеркальная копия 2)")
                            success_count += 1
                            
                        # Удаляем оригинальный совмещенный файл, так как мы его разбили на два
                        os.remove(old_path)
                        
                except Exception as e:
                    print(f"❌ Ошибка при обработке файла {file_name}: {e}")

    print(f"\n🏁 Конвертация завершена! Успешно обработано объектов: {success_count}")

if __name__ == "__main__":
    convert_doom_sprites()
