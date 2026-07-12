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
    'B': {'type': 'wall', 'texture': 'resources/textures/B.png'},
    'G': {'type': 'wall', 'texture': 'resources/textures/G.png'},
    'W': {'type': 'wall', 'texture': 'resources/textures/W.png'},
    'I': {'type': 'wall', 'texture': 'resources/textures/I.png'},
    'N': {'type': 'wall', 'texture': 'resources/textures/N.png'},
    
    # Предметы
    'h': {
        'type': 'item',
        'item_type': 'health',
        'amount': 25,
        'sprite': 'resources/items/health.png',
        'description': 'Аптечка (+25 HP)'
    },
    'a': {
        'type': 'item',
        'item_type': 'armor',
        'amount': 25,
        'sprite': 'resources/items/armor.png',
        'description': 'Броня (+25 Armor)'
    },
        'p': {
        'type': 'item',
        'item_type': 'weapon',
        'weapon_name': 'Pistol',
        'ammo': 8,
        'sprite': 'resources/items/pistol.png',
        'description': 'Пистолет (+20 патронов)'
    },
    's': {
        'type': 'item',
        'item_type': 'weapon',
        'weapon_name': 'Shotgun',
        'ammo': 4,
        'sprite': 'resources/items/shotgun.png',
        'description': 'Дробовик (+10 патронов)'
    },
    'm': {
        'type': 'item',
        'item_type': 'weapon',
        'weapon_name': 'Machine Gun',
        'ammo': 50,
        'sprite': 'resources/items/machine_gun.png',
        'description': 'Автомат (+150 патронов)'
    },
    'g': {
        'type': 'item',
        'item_type': 'weapon',
        'weapon_name': 'Plasma Gun',
        'ammo': 1,
        'sprite': 'resources/items/plasma_gun.png',
        'description': 'Плазмаган (+4 патрона)'
    },
    
    # Дверь
    'D': {'type': 'door', 'texture': 'resources/textures/D.png'},
    
    # Выход
    'E': {'type': 'exit'},
    
    # Спавн игрока
    'S': {'type': 'player_spawn'},
}

# ============================================================
# КОНФИГУРАЦИЯ NPC
# ============================================================
NPC_CONFIG = {
    '2': {
        'name': 'solder',
        'class_name': 'Solder',
        'hp': 100,
        'speed': 0.6,
        'damage': 15,
        'shoot_range': 8.0,
        'shoot_delay': 600,
        'radius': 0.35,
        'sprite_base': 'resources/npc/solder/solder',
        'sound': 'resources/npc/npc_rifle.wav',
        'sound_volume': 0.2,
    },
    '3': {
        'name': 'kamikaze',
        'class_name': 'Kamikaze',
        'hp': 40,
        'speed': 1.8,
        'damage': 40,
        'shoot_range': 1.2,
        'shoot_delay': 0,
        'radius': 0.4,
        'sprite_base': 'resources/npc/kamikaze/kamikaze',
        'sound': 'resources/npc/npc_explosive.wav',
        'sound_volume': 0.2,
    },
    '4': {
        'name': 'jaggernaut',
        'class_name': 'Jaggernaut',
        'hp': 300,
        'speed': 0.3,
        'damage': 8,
        'shoot_range': 10.0,
        'shoot_delay': 150,
        'radius': 0.5,
        'sprite_base': 'resources/npc/jaggernaut/jaggernaut',
        'sound': 'resources/npc/npc_machine_gun.wav',
        'sound_volume': 0.2,
    },
    '5': {
        'name': 'lightning',
        'class_name': 'Lightning',
        'hp': 30,
        'speed': 1.1,
        'damage': 10,
        'shoot_range': 5.0,
        'shoot_delay': 600,
        'radius': 0.35,
        'sprite_base': 'resources/npc/lightning/lightning',
        'sound': 'resources/npc/npc_pistol.wav',
        'sound_volume': 0.2,
    },
    '6': {
        'class_name': 'Boss',
        'name': 'boss',
        'hp': 2000,
        'speed': 0.3,
        'damage': 25,
        'shoot_range': 8.0,
        'shoot_delay': 600,
        'radius': 0.9,
        'sprite_base': 'resources/npc/boss/boss',
        'sound': 'resources/npc/npc_rifle.wav',
        'sound_volume': 0.2,
        'ball_speed': 2.5,
        'ball_damage': 20,
        'ball_count': 12,
        'ball_cooldown': 2000,
    },
}

# ============================================================
# КОНФИГУРАЦИЯ ОРУЖИЯ
# ============================================================
WEAPON_CONFIG = {
    'Pistol': {
        'name': 'Pistol',
        'class_name': 'Pistol',
        'damage': 10,
        'reload_time': 150,
        'continuous': False,
        'sprite': 'resources/weapons/Pistol.png',
        'sound': 'resources/weapons/Pistol_shot.wav',
        'ammo_start': 40,
        'max_distance': 4,
    },
    'Shotgun': {
        'name': 'Shotgun',
        'class_name': 'Shotgun',
        'damage': 50,
        'reload_time': 800,
        'continuous': False,
        'sprite': 'resources/weapons/Shotgun.png',
        'sound': 'resources/weapons/Shotgun_shot.wav',
        'ammo_start': 20,
        'max_distance': 2,
    },
    'Machine Gun': {
        'name': 'Machine Gun',
        'class_name': 'MachineGun',
        'damage': 10,
        'reload_time': 90,
        'continuous': True,
        'sprite': 'resources/weapons/Machine Gun.png',
        'sound': 'resources/weapons/Machine Gun_shot.wav',
        'ammo_start': 300,
        'max_distance': 5,
    },
    'Plasma Gun': {
        'name': 'Plasma Gun',
        'class_name': 'PlasmaGun',
        'damage': 100,
        'reload_time': 400,
        'continuous': False,
        'sprite': 'resources/weapons/Plasma Gun.png',
        'sound': 'resources/weapons/Plasma Gun_shot.wav',
        'ammo_start': 8,
        'max_distance': 5,
    },
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
        'folder_name': 'Colt',
        'sprite_prefix': 'COLT',
        'max_distance': 2,
        'ammo_start': 30
    },
        'COCH': {
        'name': 'Super Shotgun',
        'class_name': 'NewWeapon',       # Используем наш универсальный класс
        'damage': 80,                    # Огромный урон вблизи
        'reload_time': 350,              # 5 кадров анимации * 70 мс скорость = 350 мс
        'continuous': False,             # Одиночные выстрелы
        'max_distance': 2,               # Эффективна только на ближней дистанции
        'folder_name': 'COCH',           # Имя папки в resources/weapons/
        'sprite_prefix': 'COCH',         # Префикс файлов картинок
        'ammo_start': 30
    },


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
