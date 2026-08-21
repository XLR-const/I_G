import os
import re
import shutil
from PIL import Image

def convert_all_doom_sprites():
    print("====================================================")
    print("⚙️ ПОЛНОСТЬЮ АДАПТИВНЫЙ КОНВЕРТЕР АССЕТОВ REALM667 (ФИКС РАКУРСА 0)")
    print("====================================================")
    
    target_folder = input("📂 Введите точное имя папки NPC: ").strip()
    base_path = os.path.join("resources", "npc", target_folder)
    
    if not os.path.exists(base_path):
        print(f"🚨 [ОШИБКА] Путь '{base_path}' не найден!")
        return

    npc_name = target_folder

    # 1. СТРУКТУРА ХОДЬБЫ (Walk/Move): Буквы A, B, C, D -> Шаги ног 1, 2, 3, 4
    phase_mapping = {'A': '1', 'B': '2', 'C': '3', 'D': '4'}
    direction_mapping = {
        '1': ('_move_front_', False), '2': ('_move_front_left_', False),
        '3': ('_move_left_', False),  '4': ('_move_back_left_', False),
        '5': ('_move_back_', False),  '6': ('_move_back_right_', True),
        '7': ('_move_right_', True), '8': ('_move_front_right_', True)
    }

    # 2. ТОЧНЫЕ ДИАПАЗОНЫ БУКВ НА ОСНОВЕ ТВОЕГО СКРИНШОТА (С учётом сдвигов)
    attack_letters = ['E', 'F']
    shoot_letters = ['G', 'H']   # H0 со скриншота железно попадёт в shoot_front_0!
    die_letters = ['I', 'J', 'K', 'L', 'M', 'N'] # Смерть со скриншота начнется с I0
    x_die_letters = ['O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
    
    die_counter = 1
    xdie_counter = 1

    all_files = [f for f in os.listdir(base_path) if f.lower().endswith('.png')]
    all_files.sort() # Сортируем strictly по алфавиту для сохранения линии кадров
    
    print(f"🔍 Анализирую {len(all_files)} файлов... Запуск адаптивного парсера...\n")
    
    converted_count = 0
    
    # 🔥 ФИКС РЕГУЛЯРНОГO ВЫРАЖЕНИЯ: ([0-8]) теперь корректно перехватывает Omni-ракурс "0" со скриншота!
    doom_pattern = re.compile(r'^([A-Z0-9]{4})([A-Z])([0-8])(?:([A-Z])([0-8]))?\.png$', re.IGNORECASE)

    files_to_delete = []
    
    has_attack_frame = False
    has_shoot_frame = False

    for filename in all_files:
        match = doom_pattern.match(filename)
        if not match:
            continue

        raw_prefix, phase, view1, mirror_phase, view2 = match.groups()
        phase = phase.upper()
        src_path = os.path.join(base_path, filename)
        files_to_delete.append(src_path)

        # ----------------==================================
        # БЛОК А: ЦИКЛ ХОДЬБЫ (Фазы A, B, C, D)
        # ----------------==================================
        if phase in phase_mapping:
            if view1 in direction_mapping:
                step = phase_mapping[phase]
                prefix, flip = direction_mapping[view1]
                dst = os.path.join(base_path, f"{npc_name}{prefix}{step}.png")
                try:
                    with Image.open(src_path) as img:
                        if flip: img = img.transpose(Image.FLIP_LEFT_RIGHT)
                        img.save(dst)
                    converted_count += 1
                except Exception as e: print(f"❌ Ошибка ходьбы: {e}")

            if mirror_phase and view2:
                m_phase = mirror_phase.upper()
                if m_phase in phase_mapping and view2 in direction_mapping:
                    step = phase_mapping[m_phase]
                    prefix, flip = direction_mapping[view2]
                    dst_mirror = os.path.join(base_path, f"{npc_name}{prefix}{step}.png")
                    try:
                        with Image.open(src_path) as img:
                            img_flipped = img.transpose(Image.FLIP_LEFT_RIGHT)
                            img_flipped.save(dst_mirror)
                        converted_count += 1
                    except Exception as e: print(f"❌ Ошибка зеркала: {e}")

        # ----------------==================================
        # БЛОК Б: БOЕВЫЕ КАДРЫ (Строгий и точный перехват фаз)
        # ----------------==================================
        # Жестко ловим букву E под кадр прицеливания и стойки
        elif phase == 'E' and not has_attack_frame and view1 in ['0', '1']:
            dst = os.path.join(base_path, f"{npc_name}_attack_front_0.png")
            try:
                with Image.open(src_path) as img: img.save(dst)
                has_attack_frame = True
                converted_count += 1
                print(f"⚔️ Записан кадр прицеливания (Буква {phase}{view1}): {npc_name}_attack_front_0.png")
            except: pass

        # Жестко ловим букву F (или резервную G/H, если F не было) под вспышку выстрела
        elif (phase == 'F' or (phase in ['G', 'H'] and not has_shoot_frame)) and not has_shoot_frame and view1 in ['0', '1']:
            dst = os.path.join(base_path, f"{npc_name}_shoot_front_0.png")
            try:
                with Image.open(src_path) as img: img.save(dst)
                has_shoot_frame = True
                converted_count += 1
                print(f"🔥 Записан кадр выстрела (Буква {phase}{view1}): {npc_name}_shoot_front_0.png")
            except: pass


        # ----------------==================================
        # БЛОК В: ОБЫЧНАЯ СМЕРТЬ (Перехват ракурсов 1 и 0 для H...N)
        # ----------------==================================
        elif phase in die_letters and phase not in attack_letters and phase not in shoot_letters and view1 in ['0', '1']:
            dst = os.path.join(base_path, f"{npc_name}_die_front_{die_counter}.png")
            try:
                with Image.open(src_path) as img: img.save(dst)
                print(f"💀 Обычная смерть: Создан кадр №{die_counter} (Буква {phase}{view1})")
                die_counter += 1
                converted_count += 1
            except: pass

        # ----------------==================================
        # БЛОК Г: ЖЕСТОКАЯ СМЕРТЬ (Перехват ракурсов 1 и 0 для O...Z)
        # ----------------==================================
        elif phase in x_die_letters and phase not in die_letters and view1 in ['0', '1']:
            dst = os.path.join(base_path, f"{npc_name}_x_die_front_{xdie_counter}.png")
            try:
                with Image.open(src_path) as img: img.save(dst)
                print(f"💥 Жестокая смерть: Создан кадр №{xdie_counter} (Буква {phase}{view1})")
                xdie_counter += 1
                converted_count += 1
            except: pass

    # 🔥 СТРОГАЯ СТРАХОВКА КЛОНИРОВАНИЯ X-DIE
    if xdie_counter == 1 and die_counter > 1:
        print("\n⚠️ [Страховка] Кадры экстремальной смерти X-Die отсутствуют на диске!")
        print(f"  -> Автоматически дублирую {die_counter - 1} кадров обычной смерти во флаг x_die_front...")
        for i in range(1, die_counter):
            src_die = os.path.join(base_path, f"{npc_name}_die_front_{i}.png")
            dst_xdie = os.path.join(base_path, f"{npc_name}_x_die_front_{i}.png")
            try:
                shutil.copy(src_die, dst_xdie)
                converted_count += 1
            except Exception as e:
                print(f"❌ Ошибка копирования кадра смерти: {e}")

    # Полностью вычищаем оригинальные файлы DOOM, оставляя папку чистой
    for old_path in files_to_delete:
        try:
            if os.path.exists(old_path):
                os.remove(old_path)
        except:
            pass

    print("====================================================")
    print("🎉 КОНВЕРТАЦИЯ ПОЛНОСТЬЮ ЗАВЕРШЕНА!")
    print(f"  -> Всего создано ассетов: {converted_count}")
    print(f"  -> Папка ресурсов '{target_folder}' полностью синхронизирована!")
    print("====================================================")

if __name__ == "__main__":
    convert_all_doom_sprites()
