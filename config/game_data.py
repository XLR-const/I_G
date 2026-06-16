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
        'speed': 0.3,
        'damage': 15,
        'shoot_range': 4.0,
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
        'speed': 1.3,
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
        'speed': 0.1,
        'damage': 8,
        'shoot_range': 5.0,
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
        'speed': 0.05,
        'damage': 10,
        'shoot_range': 4.0,
        'shoot_delay': 600,
        'radius': 0.35,
        'sprite_base': 'resources/npc/lightning/lightning',
        'sound': 'resources/npc/npc_pistol.wav',
        'sound_volume': 0.2,
    },
    '6': {
        'name': 'boss',
        'class_name': 'Boss',
        'hp': 1000,
        'speed': 0.05,
        'damage': 30,
        'shoot_range': 6.0,
        'shoot_delay': 600,
        'radius': 0.8,
        'sprite_base': 'resources/npc/boss/boss',
        'sound': 'resources/npc/npc_rifle.wav',
        'sound_volume': 0.2,
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
        'ammo_start': 20,
    },
    'Shotgun': {
        'name': 'Shotgun',
        'class_name': 'Shotgun',
        'damage': 50,
        'reload_time': 800,
        'continuous': False,
        'sprite': 'resources/weapons/Shotgun.png',
        'sound': 'resources/weapons/Shotgun_shot.wav',
        'ammo_start': 10,
    },
    'Machine Gun': {
        'name': 'Machine Gun',
        'class_name': 'MachineGun',
        'damage': 10,
        'reload_time': 90,
        'continuous': True,
        'sprite': 'resources/weapons/Machine Gun.png',
        'sound': 'resources/weapons/Machine Gun_shot.wav',
        'ammo_start': 100,
    },
    'Plasma Gun': {
        'name': 'Plasma Gun',
        'class_name': 'PlasmaGun',
        'damage': 100,
        'reload_time': 400,
        'continuous': False,
        'sprite': 'resources/weapons/Plasma Gun.png',
        'sound': 'resources/weapons/Plasma Gun_shot.wav',
        'ammo_start': 5,
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
    'death': 'resources/music/deaths/death.wav',
    'level_end': 'resources/music/levelends/level_end.wav',
}
