"""Конфигурация игры - все данные в одном месте

Содержит:
- SYMBOLS_CONFIG: соответствие символов на карте типам объектов
- NPC_CONFIG: параметры всех типов NPC
- WEAPON_CONFIG: параметры всех типов оружия
- MUSIC_CONFIG: пути к музыкальным трекам
"""

# ============================================================
# КОНФИГУРАЦИЯ СИМВОЛОВ КАРТЫ
# ============================================================
SYMBOLS_CONFIG = {
    # Стены
    '1': {'type': 'wall'},  # дефолтная белая стена (без текстуры)
    'M': {'type': 'wall', 'texture': 'resources/textures/M.png'},
    'C': {'type': 'wall', 'texture': 'resources/textures/C.png'},
    'L': {'type': 'wall', 'texture': 'resources/textures/L.png'},
    'R': {'type': 'wall', 'texture': 'resources/textures/R.png'},
    'G': {'type': 'wall', 'texture': 'resources/textures/G.png'},
    'W': {'type': 'wall', 'texture': 'resources/textures/W.png'},
    'I': {'type': 'wall', 'texture': 'resources/textures/I.png'},
    'N': {'type': 'wall', 'texture': 'resources/textures/N.png'},
    
    # Предметы
    'health': {
        'type': 'item',
        'item_type': 'health',
        'amount': 25,
        'sprite': 'resources/items/health.png',
        'description': 'Аптечка (+25 HP)'
    },
    'armor': {
        'type': 'item',
        'item_type': 'armor',
        'amount': 25,
        'sprite': 'resources/items/armor.png',
        'description': 'Броня (+25 Armor)'
    },
    
    'ak47': {
        'type': 'item',
        'item_type': 'weapon',
        'weapon_name': 'AK-47',
        'ammo': 30,
        'sprite': 'resources/weapons/AK47/icon.png',  # Используем готовую иконку из папки пушки!
        'description': 'Автомат АК-47 (+30 патронов)'
    },
    'colt': {
        'type': 'item',
        'item_type': 'weapon',
        'weapon_name': 'COLT',
        'ammo': 15,
        'sprite': 'resources/weapons/Colt/icon.png',  # Иконка Кольта
        'description': 'Пистолет Colt 1911 (+7 патронов)'
    },
    'shotgun': {
        'type': 'item',
        'item_type': 'weapon',
        'weapon_name': 'COCH',
        'ammo': 4,
        'sprite': 'resources/weapons/COCH/icon.png',  # Иконка двустволки
        'description': 'Двустволка Super Shotgun (+4 патрона)'
    },
    'plasmagun': {
        'type': 'item',
        'item_type': 'weapon',
        'weapon_name': 'PLASMA',
        'ammo': 1,
        'sprite': 'resources/weapons/PLASMA/icon.png',
        'description': 'PLASMA'
    },

    
    # Дверь
    'Door': {'type': 'door', 'texture': 'resources/textures/D.png'},
    
    # Выход
    'Exit': {'type': 'exit'},
    
    # Спавн игрока
    'Spawn': {'type': 'player_spawn'},
}

# ============================================================
# КОНФИГУРАЦИЯ NPC
# ============================================================
NPC_CONFIG = {
        'AGG': {
        'name': 'AutoGunGuy',
        'speed': 0.28,
        'hp': 100,
        'damage': 6,
        # --- ТРИ СТУПЕНИ ДИСТАНЦИЙ ---
        'activation_distance': 35,     # Оптимизация (ИИ спит, если игрок дальше 25 клеток)
        'view_distance': 12,           # Зоркость (Бот заметит игрока и побежит, только если тот ближе 12 клеток)
        'shoot_range': 7.0,            # Стрельба (Остановится и откроет огонь на расстоянии 7 клеток)
        'shoot_delay': 1400,
        'sound_volume': 0.25,
    },
        'BS': {
        'name': 'BeamSolder',
        'speed': 0.28,
        'hp': 100,
        'damage': 20,
        # --- ТРИ СТУПЕНИ ДИСТАНЦИЙ ---
        'activation_distance': 35,     # Оптимизация (ИИ спит, если игрок дальше 25 клеток)
        'view_distance': 12,           # Зоркость (Бот заметит игрока и побежит, только если тот ближе 12 клеток)
        'shoot_range': 7.0,            # Стрельба (Остановится и откроет огонь на расстоянии 7 клеток)
        'shoot_delay': 2000,
        'sound_volume': 0.25,
    },
        'CM': {
        'name': 'ChaingunMajor',        # Должно строго совпадать с именем папки!
        'speed': 0.18,                 # Медлительный из-за тяжелого пулемета
        'hp': 150,                     # Живучий мини-босс
        'damage': 4,                   # Урон за одну пулю (небольшой, но их летит очень много!)
        # --- Дистанции ---
        'activation_distance': 30,     # Активируется издалека
        'view_distance': 15,           # Замечает игрока с 15 клеток
        'shoot_range': 9.0,            # Лупит через длинные коридоры
        'shoot_delay': 2200,           # Задержка МЕЖДУ длинными очередями
        'sound_volume': 0.3,
    },
    'HS': {
        'name': 'HellSmith',            # Имя папки со спрайтами и logic.py
        'speed': 0.15,                  # Идет медленно, но неумолимо, сотрясая пол
        'hp': 2000,                     # Огромный запас здоровья для долгого боя
        'damage': 20,                   # Базовый урон (кастомные атаки в logic.py пересчитают его)
        # --- ТРЕХСТУПЕНЧАТАЯ СИСТЕМА ДИСТАНЦИЙ ---
        'activation_distance': 35,      # Оптимизация (ИИ просыпается за 35 клеток)
        'view_distance': 25,            # Зоркость (Заметит игрока и включит боевой клич с 25 клеток)
        'shoot_range': 15.0,            # Дальний бой (Начнет спавнить вихри с 12 клеток)
        'shoot_delay': 1800,            # Кулдаун в миллисекундах МЕЖДУ его супер-атаками
        'sound_volume': 0.45,           # Слышно на весь уровень!
    },
        'SB': {
        'name': 'SuicideBomber',
        'speed': 0.48,        # Быстрый как пуля!
        'hp': 80,             # Мало здоровья, чтобы игрок успевал сбрить его на подлете
        'damage': 60,         # Больно взрывается
        'activation_distance': 30,
        'view_distance': 20,
        'shoot_range': 0.6,   # Дистанция взрыва в упор
        'shoot_delay': 0,
        'sound_volume': 0.5,
    },





}

# ============================================================
# КОНФИГУРАЦИЯ ОРУЖИЯ
# ============================================================
WEAPON_CONFIG = {
        'AK-47': {
        'name': 'AK-47',
        'class_name': 'NewWeapon',       # Используем наш новый универсальный класс
        'damage': 25,
        'reload_time': 240,              # 4 кадра анимации * 60 мс скорость = 240 мс
        'continuous': True,              # Автоматическая стрельба (зажим)
        'ammo_start': 30,
        'max_distance': 12,              # Автомат стреляет дальше пистолета и плазмы
        'folder_name': 'AK47',           # Точное имя папки из resources/weapons/
        'sprite_prefix': 'AK47',
        'max_distance': 5
    },
        'COLT': {
        'name': 'Colt 1911',
        'class_name': 'NewWeapon',
        'damage': 15,
        'reload_time': 270,        # Время перезарядки строго под длину анимации!
        'continuous': False,       # Одиночные выстрелы
        'max_distance': 8,
        'folder_name': 'COLT',
        'sprite_prefix': 'COLT',
        'max_distance': 2,
        'ammo_start': 30
    },
        'COCH': {
        'name': 'Super Shotgun',
        'class_name': 'NewWeapon',       # Используем наш универсальный класс
        'damage': 50,                    # Огромный урон вблизи
        'reload_time': 350,              # 5 кадров анимации * 70 мс скорость = 350 мс
        'continuous': False,             # Одиночные выстрелы
        'max_distance': 2,               # Эффективна только на ближней дистанции
        'folder_name': 'COCH',           # Имя папки в resources/weapons/
        'sprite_prefix': 'COCH',         # Префикс файлов картинок
        'ammo_start': 30
    },
        'PLASMA': {
            'name': 'Plasma Gun',
            'damage': 75,
            'reload_time': 350,
            'continuous': False,
            'max_distance': 6,
            'folder_name': 'PLASMA',
            'sprite_prefix': 'PLASMA',
            'ammo_start': 1
            
        }


}

# ============================================================
# КОНФИГУРАЦИЯ МУЗЫКИ
# ============================================================
MUSIC_CONFIG = {
    'menu': 'resources/music/menus/menu.wav',
    'briefing': 'resources/music/briefings/briefing.wav',
    'level_1': 'resources/music/levels/level_1.wav',
    'level_2': 'resources/music/levels/level_2.wav',
    'level_3': 'resources/music/levels/level_3.wav',
    'level_4': 'resources/music/levels/level_4.wav',
    'level_5': 'resources/music/levels/level_5.wav',
    'death': 'resources/music/deaths/death.wav',
    'level_end': 'resources/music/levelends/levelend.wav',
}
