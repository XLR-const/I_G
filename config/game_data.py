"""Конфигурация игры - все данные в одном месте

Содержит:
- SYMBOLS_CONFIG: соответствие символов на карте типам объектов
- NPC_CONFIG: параметры всех типов NPC
- WEAPON_CONFIG: параметры всех типов оружия
- MUSIC_CONFIG: пути к музыкальным трекам
"""


# 🔥 РЕГИСТРАЦИЯ ВСЕХ ДЕКОРАЦИЙ ПО СТАРИНКЕ С РАЗМЕРАМИ И ОПИСАНИЕМ
DECOR_CONFIG = {
    # --- АКТ 1: ПЕРИМЕТР БАЗЫ ---
    'prop_military_crate': {
        'type': 'item', 
        'item_type': 'decor', 
        'sprite': 'resources/decorations/prop_military_crate.png',
        'ammo': 50,  # Высота: 50% от стены (низкий кубический ящик)
        'radius': 0.4,
        'desc': 'Армейский ящик'
    },
    'prop_sandbag_wall': {
        'type': 'item', 
        'item_type': 'decor', 
        'sprite': 'resources/decorations/prop_sandbag_wall.png',
        'ammo': 40,  # Высота: 40% от стены (низкий бруствер укрытия)
        'desc': 'Мешки с песком'
    },
    
    # --- АКТ 2: КОЛЛЕКТОРЫ И ВЕНТИЛЯЦИЯ ---
    'prop_sewage_pillar': {
        'type': 'item', 
        'item_type': 'decor', 
        'sprite': 'resources/decorations/prop_sewage_pillar.png',
        'ammo': 100, # Высота: 100% (монументальная бетонная опора до потолка)
        'desc': 'Колонна коллектора'
    },
    
    # --- АКТ 3: ЛАБОРАТОРИЯ ---
    'prop_lab_capsule': {
        'type': 'item', 
        'item_type': 'decor', 
        'sprite': 'resources/decorations/prop_lab_capsule.png',
        'ammo': 85,  # Высота: 85% от стены (высокая колба содержания)
        'desc': 'Био-капсула'
    },
    'prop_server_rack': {
        'type': 'item', 
        'item_type': 'decor', 
        'sprite': 'resources/decorations/prop_server_rack.png',
        'ammo': 100, # Высота: 100% (серверный шкаф в полный рост)
        'desc': 'Серверная стойка'
    },
    
    # --- АКТ 4: ГЛУБИНЫ ЛАБОРАТОРИИ ---
    'prop_core_reactor': {
        'type': 'item', 
        'item_type': 'decor', 
        'sprite': 'resources/decorations/prop_core_reactor.png',
        'ammo': 90,  # Высота: 90% от стены (массивное круглое ядро бомбы)
        'desc': 'Ядро реактора бомбы'
    },
    
    # --- АКТ 5: ЭВАКУАЦИЯ И АНГАРЫ ---
    'prop_cargo_container': {
        'type': 'item', 
        'item_type': 'decor', 
        'sprite': 'resources/decorations/prop_cargo_container.png',
        'ammo': 95,  # Высота: 95% от стены (тяжелый грузовой блок)
        'radius': 0.9,
        'desc': 'Грузовой контейнер'
    },
    'prop_hangar_frame': {
        'type': 'item', 
        'item_type': 'decor', 
        'sprite': 'resources/decorations/prop_hangar_frame.png',
        'ammo': 100, # Высота: 100% (промышленная несущая металлоконструкция)
        'desc': 'Балка ангара'
    },
    'prop_sewage_pipe': {
        'type': 'item', 'item_type': 'decor', 
        'sprite': 'resources/decorations/prop_sewage_pipe.png',
        'ammo': 100, 'desc': 'Сточная труба коллектора'
    },
    'prop_industrial_generator': {
        'type': 'item', 'item_type': 'decor', 
        'sprite': 'resources/decorations/prop_industrial_generator.png',
        'ammo': 75,  'desc': 'Индустриальный генератор'
    },
    'prop_vent_fan': {
        'type': 'item', 'item_type': 'decor', 
        'sprite': 'resources/decorations/prop_vent_fan.png',
        'ammo': 100, 'desc': 'Вентиляционная турбина'
    },
    'prop_bio_puddle': {
        'type': 'item', 'item_type': 'decor', 
        'sprite': 'resources/decorations/prop_bio_puddle.png',
        'ammo': 15,  'desc': 'Лужа био-слизи'
    },
    'prop_microscope_bench': {
        'type': 'item', 'item_type': 'decor', 
        'sprite': 'resources/decorations/prop_microscope_bench.png',
        'ammo': 65,  'desc': 'Лабораторный стол'
    },
    'prop_chemical_barrel': {
        'type': 'item', 'item_type': 'decor', 
        'sprite': 'resources/decorations/prop_chemical_barrel.png',
        'ammo': 55,  'desc': 'Химическая бочка'
    },
    'prop_ceiling_lamp': {
        'type': 'item', 'item_type': 'decor', 
        'sprite': 'resources/decorations/prop_ceiling_lamp.png',
        'ammo': 100, 'desc': 'Подвесной прожектор'
    },
    'prop_control_console': {
        'type': 'item', 'item_type': 'decor', 
        'sprite': 'resources/decorations/prop_control_console.png',
        'fixed_angle': 70,
        'ammo': 70,  'desc': 'Консоль управления'
    },
    'prop_laser_grid': {
        'type': 'item', 'item_type': 'decor', 
        'sprite': 'resources/decorations/prop_laser_grid.png',
        'ammo': 100, 'desc': 'Лазерная перегородка'
    },
    'prop_ammo_crate': {
        'type': 'item', 'item_type': 'decor', 
        'sprite': 'resources/decorations/prop_ammo_crate.png',
        'ammo': 45,  'desc': 'Ящик со снаряжением'
    },
    'prop_forklift': {
        'type': 'item', 'item_type': 'decor', 
        'sprite': 'resources/decorations/prop_forklift.png',
        'ammo': 80,  'desc': 'Складской погрузчик'
    },
        # ==================================================================
    # 🔥 НОВЕЙШИЙ ПАК 11 ДЕКОРАЦИЙ ДЛЯ СЮЖЕТНЫХ АКТОВ И СИКВЕЛА
    # ==================================================================
    'prop_searchlight': {
        'type': 'item', 'item_type': 'decor', 'sprite': 'resources/decorations/prop_searchlight.png',
        'ammo': 120, 'desc': 'Прожектор периметра базы (Высокая вышка)'
    },
    'prop_comm_antenna': {
        'type': 'item', 'item_type': 'decor', 'sprite': 'resources/decorations/prop_comm_antenna.png',
        'ammo': 110, 'desc': 'Спутниковая антенна связи скрытой организации'
    },
    'prop_sewage_pump': {
        'type': 'item', 'item_type': 'decor', 'sprite': 'resources/decorations/prop_sewage_pump.png',
        'ammo': 65,  'desc': 'Промышленный насос коллектора с вентилем'
    },
    'prop_toxic_waste': {
        'type': 'item', 'item_type': 'decor', 'sprite': 'resources/decorations/prop_toxic_waste.png',
        'ammo': 80,  'desc': 'Ржавый бак с подтекающими отходами'
    },
    'prop_hydraulic_press': {
        'type': 'item', 'item_type': 'decor', 'sprite': 'resources/decorations/prop_hydraulic_press.png',
        'ammo': 95,  'desc': 'Гидравлический компрессор поршневого типа'
    },
    'prop_autopsy_table': {
        'type': 'item', 'item_type': 'decor', 'sprite': 'resources/decorations/prop_autopsy_table.png',
        'ammo': 45,  'desc': 'Медицинский стол в крови после вскрытия мутантов'
    },
    'prop_decon_shower': {
        'type': 'item', 'item_type': 'decor', 'sprite': 'resources/decorations/prop_decon_shower.png',
        'ammo': 100, 'desc': 'Рамка шлюза дезинфекции и деконтаминации'
    },
    'prop_mainframe_wall': {
        'type': 'item', 'item_type': 'decor', 'sprite': 'resources/decorations/prop_mainframe_wall.png',
        'ammo': 100, 'desc': 'Стена суперкомпьютера злодея с лентами ОЗУ'
    },
    'prop_stasis_chamber': {
        'type': 'item', 'item_type': 'decor', 'sprite': 'resources/decorations/prop_stasis_chamber.png',
        'ammo': 95,  'desc': 'Стазис-инкубатор с силуэтом био-оружия'
    },
    'prop_fuel_tank': {
        'type': 'item', 'item_type': 'decor', 'sprite': 'resources/decorations/prop_fuel_tank.png',
        'ammo': 85,  'desc': 'Топливный бак заправщика ОГНЕОПАСНО'
    },
    'prop_cargo_pallet': {
        'type': 'item', 'item_type': 'decor', 'sprite': 'resources/decorations/prop_cargo_pallet.png',
        'ammo': 50,  'desc': 'Складской поддон паллета с замотанным грузом'
    }

}




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
    'rocks': {
        'type': 'wall',
        'texture': 'resources/textures/rocks.png'
    },
    'bruce': {
      'type': 'wall',
      'texture': 'resources/textures/bruce.png'  
    },
    'metal_crunch_wall': {
        'type': 'wall',
        'texture': 'resources/textures/metal_crunch_wall.png'
    },
    
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
        'ammo': 25,
        'sprite': 'resources/weapons/PLASMA/icon.png',
        'description': 'PLASMA'
    },
    'bfg': {
            'type': 'item',
            'item_type': 'weapon',
            'weapon_name': 'BFG',
            'ammo': 1,
            'sprite': 'resources/weapons/BFG/icon.png',
            'description': 'BFG'
        },
        'knife2': {
        'type': 'item',
        'item_type': 'weapon',
        'weapon_name': 'KNIFE2',
        'ammo': 1,
        'sprite': 'resources/weapons/KNIFE2/icon.png',
        'description': 'PLASMA'
    },
        'aa12': {
            'type': 'item',
            'item_type': 'weapon',
            'weapon_name': 'AA12',
            'ammo': 12,
            'sprite': 'resources/weapons/AA12/icon.png'
        },

        'bazooka': {
            'type': 'item',
            'item_type': 'weapon',
            'weapon_name': 'BAZOOKA',
            'ammo': 3,
            'sprite': 'resources/weapons/BAZOOKA/icon.png'
        },
    'napalm': {
        'type': 'item',
        'item_type': 'weapon',
        'weapon_name': 'NAPALM',
        'ammo': 50,
        'sprite': 'resources/weapons/NAPALM/icon.png'
        },
    
    'grenade': {
        'type': 'item',
        'item_type': 'weapon',
        'weapon_name': 'GRENADE',
        'ammo': 3,
        'sprite': 'resources/weapons/GRENADE/icon.png'
    },
    
 # --- СИСТЕМА ДВЕРЕЙ И СЕКРЕТОК С ТЕКСТУРАМИ ---
    'door_normal': {
        'type': 'door', 
        'door_type': 'normal', 
        'required_key': None,
        'texture': 'resources/textures/door.png'       # Путь к текстуре обычной двери!
    },
    'door_red_key': {
        'type': 'door', 
        'door_type': 'locked', 
        'required_key': 'red',
        'texture': 'resources/textures/door_red.png'   # Путь к красной двери!
    },
    'door_blue_key': {
        'type': 'door', 
        'door_type': 'locked', 
        'required_key': 'blue',
        'texture': 'resources/textures/door_blue.png'
    },
    'door_yellow_key': {
        'type': 'door', 
        'door_type': 'locked', 
        'required_key': 'yellow',
        'texture': 'resources/textures/door_yellow.png'
    },
    'secret_wall': {
        'type': 'door', 
        'door_type': 'secret', 
        'required_key': None,
        'texture': 'resources/textures/brick.png'      # Дефолтная текстура секретки (на всякий случай)
    },

    # --- КЛЮЧИ ---
    'key_red': {
        'type': 'item', 'item_type': 'key', 'key_color': 'red',
        'sprite': 'resources/items/key_red.png'
    },
    'key_blue': {
        'type': 'item', 'item_type': 'key', 'key_color': 'blue',
        'sprite': 'resources/items/key_blue.png'
    },
    'key_yellow': {
        'type': 'item', 'item_type': 'key', 'key_color': 'yellow',
        'sprite': 'resources/items/key_yellow.png'
    },

    # Выход
    'Exit': {'type': 'exit'},
    
    # Спавн игрока
    'Spawn': {'type': 'player_spawn'},
}

SYMBOLS_CONFIG.update(DECOR_CONFIG)

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
    'TERM': {
        'name': 'TERM',
        'speed': 0.3,
        'hp': 2000,
        'damage': 20,
        'activation_distance': 45,      # Оптимизация (ИИ просыпается за 35 клеток)
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
    # SpecOps pack
    'SOS': {
        'name': 'SpecOpsShotgun',
        'speed': 0.48, 
        'hp': 120,      
        'damage': 9,  
        'activation_distance': 35,     # Оптимизация (ИИ спит, если игрок дальше 25 клеток)
        'view_distance': 12,           # Зоркость (Бот заметит игрока и побежит, только если тот ближе 12 клеток)
        'shoot_range': 7.0,            # Стрельба (Остановится и откроет огонь на расстоянии 7 клеток)
        'shoot_delay': 1400,
        'sound_volume': 0.25,
    },
    'SOM': {
        'name': 'SpecOpsMachinegun',        # Должно строго совпадать с именем папки!
        'speed': 0.18,                 # Медлительный из-за тяжелого пулемета
        'hp': 170,                     # Живучий мини-босс
        'damage': 8,                   # Урон за одну пулю (небольшой, но их летит очень много!)
        # --- Дистанции ---
        'activation_distance': 30,     # Активируется издалека
        'view_distance': 15,           # Замечает игрока с 15 клеток
        'shoot_range': 9.0,            # Лупит через длинные коридоры
        'shoot_delay': 2200,           # Задержка МЕЖДУ длинными очередями
        'sound_volume': 0.3,
    },
    'SOR': {
        'name': 'SpecOpsRailgun',
        'speed': 0.28,
        'hp': 120,
        'damage': 35,
        # --- ТРИ СТУПЕНИ ДИСТАНЦИЙ ---
        'activation_distance': 35,     # Оптимизация (ИИ спит, если игрок дальше 25 клеток)
        'view_distance': 12,           # Зоркость (Бот заметит игрока и побежит, только если тот ближе 12 клеток)
        'shoot_range': 7.0,            # Стрельба (Остановится и откроет огонь на расстоянии 7 клеток)
        'shoot_delay': 2000,
        'sound_volume': 0.25,
    },
    
    # Science pack
    'ScF': {
        'name': 'ScienceFreeze',
        'speed': 0.28,
        'hp': 100,
        'damage': 35,
        # --- ТРИ СТУПЕНИ ДИСТАНЦИЙ ---
        'activation_distance': 35,     # Оптимизация (ИИ спит, если игрок дальше 25 клеток)
        'view_distance': 12,           # Зоркость (Бот заметит игрока и побежит, только если тот ближе 12 клеток)
        'shoot_range': 7.0,            # Стрельба (Остановится и откроет огонь на расстоянии 7 клеток)
        'shoot_delay': 2000,
        'sound_volume': 0.25,
    },
    'ScP': {
        'name': 'SciencePistol',
        'speed': 0.28,
        'hp': 80,
        'damage': 15,
        # --- ТРИ СТУПЕНИ ДИСТАНЦИЙ ---
        'activation_distance': 35,     # Оптимизация (ИИ спит, если игрок дальше 25 клеток)
        'view_distance': 12,           # Зоркость (Бот заметит игрока и побежит, только если тот ближе 12 клеток)
        'shoot_range': 7.0,            # Стрельба (Остановится и откроет огонь на расстоянии 7 клеток)
        'shoot_delay': 2000,
        'sound_volume': 0.25,
    },
    'ScPl': {
        'name': 'SciencePlasma',
        'speed': 0.28,
        'hp': 100,
        'damage': 35,
        # --- ТРИ СТУПЕНИ ДИСТАНЦИЙ ---
        'activation_distance': 35,     # Оптимизация (ИИ спит, если игрок дальше 25 клеток)
        'view_distance': 12,           # Зоркость (Бот заметит игрока и побежит, только если тот ближе 12 клеток)
        'shoot_range': 7.0,            # Стрельба (Остановится и откроет огонь на расстоянии 7 клеток)
        'shoot_delay': 2000,
        'sound_volume': 0.25,
    },
    'ScU': {
        'name': 'ScienceUzi',
        'speed': 0.28,
        'hp': 100,
        'damage': 8,
        # --- ТРИ СТУПЕНИ ДИСТАНЦИЙ ---
        'activation_distance': 35,     # Оптимизация (ИИ спит, если игрок дальше 25 клеток)
        'view_distance': 12,           # Зоркость (Бот заметит игрока и побежит, только если тот ближе 12 клеток)
        'shoot_range': 7.0,            # Стрельба (Остановится и откроет огонь на расстоянии 7 клеток)
        'shoot_delay': 2000,
        'sound_volume': 0.25,
    },
    'UB': {
        'name': 'UacBot',
        'speed': 0.28,
        'hp': 150,
        'damage': 5,
        # --- ТРИ СТУПЕНИ ДИСТАНЦИЙ ---
        'activation_distance': 35,     # Оптимизация (ИИ спит, если игрок дальше 25 клеток)
        'view_distance': 12,           # Зоркость (Бот заметит игрока и побежит, только если тот ближе 12 клеток)
        'shoot_range': 7.0,            # Стрельба (Остановится и откроет огонь на расстоянии 7 клеток)
        'shoot_delay': 2000,
        'sound_volume': 0.25,
    },
    
    # Tanks pack
    'TM': {
        'name': 'TankMachinegun',
        'speed': 0.28,
        'hp': 150,
        'damage': 10,
        # --- ТРИ СТУПЕНИ ДИСТАНЦИЙ ---
        'activation_distance': 35,     # Оптимизация (ИИ спит, если игрок дальше 25 клеток)
        'view_distance': 12,           # Зоркость (Бот заметит игрока и побежит, только если тот ближе 12 клеток)
        'shoot_range': 7.0,            # Стрельба (Остановится и откроет огонь на расстоянии 7 клеток)
        'shoot_delay': 2000,
        'sound_volume': 0.25,
    },
    'TR': {
        'name': 'TankRocket',
        'speed': 0.28,
        'hp': 150,
        'damage': 15,
        # --- ТРИ СТУПЕНИ ДИСТАНЦИЙ ---
        'activation_distance': 35,     # Оптимизация (ИИ спит, если игрок дальше 25 клеток)
        'view_distance': 12,           # Зоркость (Бот заметит игрока и побежит, только если тот ближе 12 клеток)
        'shoot_range': 7.0,            # Стрельба (Остановится и откроет огонь на расстоянии 7 клеток)
        'shoot_delay': 2000,
        'sound_volume': 0.25,
    },
    'TP': {
        'name': 'TankPlasma',
        'speed': 0.28,
        'hp': 150,
        'damage': 15,
        # --- ТРИ СТУПЕНИ ДИСТАНЦИЙ ---
        'activation_distance': 35,     # Оптимизация (ИИ спит, если игрок дальше 25 клеток)
        'view_distance': 12,           # Зоркость (Бот заметит игрока и побежит, только если тот ближе 12 клеток)
        'shoot_range': 7.0,            # Стрельба (Остановится и откроет огонь на расстоянии 7 клеток)
        'shoot_delay': 2000,
        'sound_volume': 0.25,
    },






}

# ============================================================
# КОНФИГУРАЦИЯ ОРУЖИЯ
# ============================================================
WEAPON_CONFIG = {
        'AK-47': {
        'name': 'AK-47',
        #'class_name': 'NewWeapon',       # Используем наш новый универсальный класс
        'slot': 4,
        'type': 'hitscan',
        'spread': 0.05,      # Ощутимый разброс при зажиме
        'recoil': 0.04,
        'damage': 25,
        'reload_time': 200,              # 4 кадра анимации * 60 мс скорость = 240 мс
        'continuous': True,              # Автоматическая стрельба (зажим)
        'ammo_start': 30,
        'max_distance': 12,              # Автомат стреляет дальше пистолета и плазмы
        'folder_name': 'AK47',           # Точное имя папки из resources/weapons/
        'sprite_prefix': 'AK47',
        'max_distance': 5
    },
        'COLT': {
        'name': 'Colt 1911',
        #'class_name': 'NewWeapon',
        'slot': 2,
        'type': 'hitscan',
        'spread': 0.02,
        'recoil': 0.03,
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
        'name': 'Toz',
        'class_name': 'NewWeapon',       # Используем наш универсальный класс
        'slot': 3,
        'type': 'hitscan',
        'spread': 0.38,      # Широкий веер дроби!
        'recoil': 0.12,
        'damage': 5,                    # Огромный урон вблизи
        'pellets': 10,
        'reload_time': 350,              # 5 кадров анимации * 70 мс скорость = 350 мс
        'continuous': False,             # Одиночные выстрелы
        'max_distance': 2,               # Эффективна только на ближней дистанции
        'folder_name': 'COCH',           # Имя папки в resources/weapons/
        'sprite_prefix': 'COCH',         # Префикс файлов картинок
        'ammo_start': 30
    },
        'PLASMA': {
            'name': 'Plasma Gun',
            'slot': 5,
            'type': 'projectile',
            'prefix_fly': 'RGTR',
            'prefix_exp': 'RGTX',
            'projectile_speed': 0.3, 
            'spread': 0.01,      # Ощутимый разброс при зажиме
            'recoil': 0.04,
            'damage': 25,
            'reload_time': 350,
            'continuous': True,
            'max_distance': 6,
            'folder_name': 'PLASMA',
            'sprite_prefix': 'PLASMA',
            'ammo_start': 50
            
        },
        'BFG': {
            'name': 'Big F Gun',
            'slot': 5,
            'type': 'projectile',
            'prefix_fly': 'BBGB',
            'prefix_exp': 'BBGX',
            'projectile_speed': 0.3, 
            'spread': 0.001,      # Ощутимый разброс при зажиме
            'recoil': 0.04,
            'damage': 25,
            'splash_radius': 10.5,
            'splash_damage': 150,
            'reload_time': 350,
            'shoot_delay': 450,
            'continuous': False,
            'max_distance': 6,
            'folder_name': 'BFG',
            'sprite_prefix': 'BG2G',
            'ammo_start': 50
            
        },
        'BAZOOKA': {
            'name': 'Bazooka',
            'slot': 6,
            'type': 'projectile',
            'prefix_fly': 'QROK',
            'prefix_exp': 'EXP2',
            'projectile_speed': 0.3, 
            'spread': 0.001,
            'recoil': 0.04,
            'damage': 50,
            'splash_radius': 10.5,
            'splash_damage': 40,
            'reload_time': 350,
            #'shoot_delay': 450,
            'continuous': False,
            'max_distance': 6,
            'folder_name': 'BAZOOKA',
            'sprite_prefix': 'RPGA',
            'ammo_start': 3,
            'explosive': 'resources/weapons/BAZOOKA/explosive.wav'
            
        },
        'NAPALM': {
            'name': 'Vietnams Hy',
            'slot': 6,
            'type': 'projectile',
            'prefix_fly': 'FIRE',
            'prefix_exp': 'EXP2',
            'projectile_speed': 0.8, 
            'spread': 0.001,
            'recoil': 0.04,
            'damage': 50,
            'splash_radius': 10.5,
            'splash_damage': 40,
            'reload_time': 30,
            #'shoot_delay': 450,
            'continuous': True,
            'max_distance': 6,
            'folder_name': 'NAPALM',
            'sprite_prefix': 'NLAN',
            'ammo_start': 50,
            'explosive': 'resources/weapons/BAZOOKA/explosive.wav'
            
        },
        
        'GRENADE': {
            'name': 'Grenade',
            'slot': 6,
            'type': 'projectile',
            'prefix_fly': 'HGN1',
            'prefix_exp': 'EXP3',
            'projectile_speed': 0.3, 
            'spread': 0.001,
            'recoil': 0.04,
            'damage': 50,
            'splash_radius': 10.5,
            'splash_damage': 40,
            'reload_time': 350,
            'shoot_delay': 450,
            'continuous': False,
            'max_distance': 6,
            'folder_name': 'GRENADE',
            'sprite_prefix': 'HGRN',
            'ammo_start': 3,
            'explosive': 'resources/weapons/GRENADE/explosive.wav'
            
        },
    'KNIFE': {
        'name': 'Knife',
        'slot': 1,
        'damage': 40,
        'reload_time': 400,        # Время перезарядки строго под длину анимации!
        'continuous': True,       # Одиночные выстрелы
        'max_distance': 0.5,
        'folder_name': 'KNIFE',
        'sprite_prefix': 'KNFS',
        'ammo_start': 10,
        'infinite_ammo': True
    },
        'KNIFE2': {
        'name': 'Knife2',
        'slot': 1,
        'damage': 40,
        'reload_time': 1000,        # Время перезарядки строго под длину анимации!
        'continuous': True,       # Одиночные выстрелы
        'max_distance': 0.5,
        'folder_name': 'KNIFE2',
        'sprite_prefix': 'KNFG',
        'ammo_start': 10,
        'infinite_ammo': True
    },
        'AA12': {
            'name': 'aa12',
            'slot': 3,
            'damage': 3,
            'pellets': 5,
            'reload_time': 300,
            'spread': 0.5,
            'continuous': True,
            'max_distance': 1.3,
            'folder_name': 'AA12',
            'sprite_prefix': 'AA12',
            'ammo_start': 12
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
