# ==================================================================
# 🌐 СИНХРОНИЗИРОВАННАЯ DATA-DRIVEN БАЗА БИОМОВ ПОД ВАШ К О Н Ф И Г
# ==================================================================
BIOME_DATABASE = {
    # 🌲 1. OUT: Открытые локации в горах, периметр базы (Акт 1)
    'out': {
        'name': '🪖 Улица и Военные Блокпосты',
        'geometry': { 'perimeter_wall': 'rocks', 'bsp_min_room_size': 8, 'bsp_max_room_size': 14, 'min_density': 0.35, 'max_density': 0.70 },
    
        'walls': {
            'primary': { 'char': 'rocks', 'weight': 85 },
            'secondary': { 'char': 'metal_crunch_wall', 'weight': 15 }
        },
        'doors': {
            'normal': 'door_normal',
            'locked': 'door_blue_key'
        },
        'npc_settings': {
            'density': 0.015,
            'pool': {
                'AGG': { 'weight': 100, 'max_count': 25, 'min_dist': 4, 'min_progress': 0.0, 'cluster': { 'type': 'circle', 'chance': 0.30, 'size': 3 } },
                'CM':  { 'weight': 20,  'max_count': 3,  'min_dist': 12, 'min_progress': 0.5, 'cluster': { 'type': 'single', 'chance': 0.0, 'size': 1 } }
            }
        },
        'decor_settings': {
            'density': 0.04,
            'pool': {
                'prop_sandbag_wall':    { 'weight': 100, 'max_count': 20, 'min_dist': 2, 'cluster': { 'type': 'line', 'chance': 0.60, 'size': 3 } },
                'prop_military_crate':   { 'weight': 60,  'max_count': 15, 'min_dist': 4, 'cluster': { 'type': 'circle', 'chance': 0.40, 'size': 2 } },
                'prop_searchlight':      { 'weight': 20,  'max_count': 4,  'min_dist': 10, 'cluster': { 'type': 'single', 'chance': 0.0, 'size': 1 } },
                'prop_fuel_tank':        { 'weight': 15,  'max_count': 3,  'min_dist': 12, 'cluster': { 'type': 'single', 'chance': 0.0, 'size': 1 } }
            }
        },
        'loot_settings': {
            'density': 0.02,
            'pool': {
                'health':    { 'weight': 70,  'max_count': 15, 'min_dist': 6,  'min_progress': 0.0, 'cluster': { 'type': 'single', 'chance': 0.0, 'size': 1 } },
                'colt':      { 'weight': 100, 'max_count': 25, 'min_dist': 4,  'min_progress': 0.0, 'cluster': { 'type': 'single', 'chance': 0.0, 'size': 1 } },
                'shotgun':   { 'weight': 15,  'max_count': 2,  'min_dist': 20, 'min_progress': 0.5, 'cluster': { 'type': 'single', 'chance': 0.0, 'size': 1 } },
                'armor':     { 'weight': 15,  'max_count': 4,  'min_dist': 15, 'min_progress': 0.3, 'secret_only': True, 'cluster': { 'type': 'single', 'chance': 0.0, 'size': 1 } }
            }
        }
    },

    # 🏢 2. HALL: Главные коридоры, офисы, парадные залы комплекса
    'hall': {
        'name': '🏢 Главные Коридоры и Вестибюли',
        'geometry': {
            'perimeter_wall': 'metal_crunch_wall',
            'bsp_min_room_size': 10,
            'bsp_max_room_size': 16,
            'min_density': 0.40,  # Парадные холлы просторнее коридоров вентиляции
            'max_density': 0.75   # Но плотнее огромных открытых ангаров hang
        },
        'walls': {
            'primary': { 'char': 'hall_main', 'weight': 90 },
            'secondary': { 'char': 'hall_second', 'weight': 10 } # Использование вашей базовой белой стены
        },
        'doors': {
            'normal': 'door_normal',
            'locked': 'door_blue_key'
        },
        'npc_settings': {
            'density': 0.012,
            'pool': {
                'SOS': { 'weight': 80, 'max_count': 20, 'min_dist': 5, 'min_progress': 0.0, 'cluster': { 'type': 'circle', 'chance': 0.20, 'size': 2 } },
                'SOM':  { 'weight': 30, 'max_count': 4,  'min_dist': 10, 'min_progress': 0.4, 'cluster': { 'type': 'single', 'chance': 0.0, 'size': 1 } },
                'SOR': { 'weight': 80, 'max_count': 20, 'min_dist': 5, 'min_progress': 0.0, 'cluster': { 'type': 'circle', 'chance': 0.20, 'size': 2 } },
            }
        },
        'decor_settings': {
            'density': 0.03,
            'pool': {
                'prop_control_console': { 'weight': 60,  'max_count': 8,  'min_dist': 5, 'cluster': { 'type': 'single', 'chance': 0.0, 'size': 1 } },
                'prop_ceiling_lamp':     { 'weight': 100, 'max_count': 15, 'min_dist': 3, 'cluster': { 'type': 'single', 'chance': 0.0, 'size': 1 } },
                'prop_comm_antenna':     { 'weight': 20,  'max_count': 2,  'min_dist': 20, 'cluster': { 'type': 'single', 'chance': 0.0, 'size': 1 } }
            }
        },
        'loot_settings': {
            'density': 0.018,
            'pool': {
                'health':    { 'weight': 80,  'max_count': 12, 'min_dist': 6, 'min_progress': 0.0, 'cluster': { 'type': 'single', 'chance': 0.0, 'size': 1 } },
                'colt':      { 'weight': 100, 'max_count': 20, 'min_dist': 5, 'min_progress': 0.0, 'cluster': { 'type': 'circle', 'chance': 0.20, 'size': 2 } },
                'ak47':      { 'weight': 20,  'max_count': 3,  'min_dist': 15, 'min_progress': 0.4, 'cluster': { 'type': 'single', 'chance': 0.0, 'size': 1 } },
                'armor':     { 'weight': 20,  'max_count': 3,  'min_dist': 12, 'min_progress': 0.3, 'secret_only': True, 'cluster': { 'type': 'single', 'chance': 0.0, 'size': 1 } }
            }
        }
    },

    # 🧪 3. LAB: Исследовательские зоны, лаборатории (Акт 3 и Акт 4)
    'lab': {
        'name': '🧪 Научные Лаборатории Комплекса',
        'geometry': {
            'perimeter_wall': 'metal_crunch_wall',
            'bsp_min_room_size': 6,
            'bsp_max_room_size': 10,
            'min_density': 0.30,  # Нарезка BSP-перегородками забирает много места под стены
            'max_density': 0.60   # Лаборатории компактные и блочные
        },
        'walls': {
            'primary': { 'char': 'metal_crunch_wall', 'weight': 80 },
            'secondary': { 'char': '1', 'weight': 20 }
        },
        'doors': {
            'normal': 'door_normal',
            'locked': 'door_blue_key'
        },
        'npc_settings': {
            'density': 0.018,
            'pool': {
                'AGG': { 'weight': 100, 'max_count': 30, 'min_dist': 3, 'min_progress': 0.0, 'cluster': { 'type': 'circle', 'chance': 0.40, 'size': 3 } }
            }
        },
        'decor_settings': {
            'density': 0.04,
            'pool': {
                'prop_lab_capsule':      { 'weight': 80,  'max_count': 12, 'min_dist': 3, 'cluster': { 'type': 'circle', 'chance': 0.30, 'size': 2 } },
                'prop_server_rack':      { 'weight': 100, 'max_count': 16, 'min_dist': 2, 'cluster': { 'type': 'line', 'chance': 0.50, 'size': 3 } },
                'prop_microscope_bench': { 'weight': 60,  'max_count': 10, 'min_dist': 4, 'cluster': { 'type': 'single', 'chance': 0.0, 'size': 1 } },
                'prop_autopsy_table':    { 'weight': 30,  'max_count': 4,  'min_dist': 6,  'cluster': { 'type': 'single', 'chance': 0.0, 'size': 1 } },
                'prop_core_reactor':     { 'weight': 10,  'max_count': 1,  'min_dist': 30, 'min_progress': 0.8, 'cluster': { 'type': 'single', 'chance': 0.0, 'size': 1 } }
            }
        },
        'loot_settings': {
            'density': 0.022,
            'pool': {
                'health':    { 'weight': 100, 'max_count': 20, 'min_dist': 4, 'min_progress': 0.0, 'cluster': { 'type': 'single', 'chance': 0.0, 'size': 1 } },
                'colt':      { 'weight': 60,  'max_count': 15, 'min_dist': 6, 'min_progress': 0.0, 'cluster': { 'type': 'single', 'chance': 0.0, 'size': 1 } },
                'plasmagun': { 'weight': 10,  'max_count': 1,  'min_dist': 25, 'min_progress': 0.7, 'secret_only': True, 'cluster': { 'type': 'single', 'chance': 0.0, 'size': 1 } },
                'armor':     { 'weight': 30,  'max_count': 5,  'min_dist': 10, 'min_progress': 0.2, 'secret_only': True, 'cluster': { 'type': 'single', 'chance': 0.0, 'size': 1 } }
            }
        }
    },

    # 💨 4. VENT: Запутанные коллекторы и вентиляционные шахты (Акт 2)
    'vent': {
        'name': '💨 Вентиляционные Шахты и Техподполье',
        'geometry': { 'perimeter_wall': 'metal_crunch_wall', 'bsp_min_room_size': 4, 'bsp_max_room_size': 6, 'min_density': 0.12, 'max_density': 0.35 },
        'walls': {
            'primary': { 'char': 'M', 'weight': 95 },
            'secondary': { 'char': 'L', 'weight': 5 }
        },
        'doors': {
            'normal': 'door_normal',
            'locked': 'door_blue_key'
        },
        'npc_settings': {
            'density': 0.010,
            'pool': {
                'AGG': { 'weight': 100, 'max_count': 15, 'min_dist': 6, 'min_progress': 0.0, 'cluster': { 'type': 'single', 'chance': 0.0, 'size': 1 } }
            }
        },
        'decor_settings': {
            'density': 0.025,
            'pool': {
                'prop_vent_fan':     { 'weight': 100, 'max_count': 12, 'min_dist': 4, 'cluster': { 'type': 'single', 'chance': 0.0, 'size': 1 } },
                'prop_sewage_pipe':  { 'weight': 80,  'max_count': 10, 'min_dist': 5, 'cluster': { 'type': 'single', 'chance': 0.0, 'size': 1 } },
                'prop_sewage_pillar':{ 'weight': 60,  'max_count': 8,  'min_dist': 6, 'cluster': { 'type': 'single', 'chance': 0.0, 'size': 1 } },
                'prop_bio_puddle':   { 'weight': 50,  'max_count': 14, 'min_dist': 3, 'cluster': { 'type': 'circle', 'chance': 0.30, 'size': 2 } }
            }
        },
        'loot_settings': {
            'density': 0.015,
            'pool': {
                'health':    { 'weight': 80,  'max_count': 10, 'min_dist': 8, 'min_progress': 0.0, 'cluster': { 'type': 'single', 'chance': 0.0, 'size': 1 } },
                'colt':      { 'weight': 100, 'max_count': 18, 'min_dist': 5, 'min_progress': 0.0, 'cluster': { 'type': 'single', 'chance': 0.0, 'size': 1 } }
            }
        }
    },

    # 📦 5. HANG: Огромные складские ангары и доки эвакуации (Акт 5)
    'hang': {
        'name': '📦 Складские Ангары и Погрузочные Доки',
        'geometry': { 'perimeter_wall': 'metal_crunch_wall', 'bsp_min_room_size': 14, 'bsp_max_room_size': 22, 'min_density': 0.50, 'max_density': 0.85 },
        'walls': {
            'primary': { 'char': 'metal_crunch_wall', 'weight': 90 },
            'secondary': { 'char': '1', 'weight': 10 } # Разбавление дефолтной белой стеной
        },
        'doors': {
            'normal': 'door_normal',
            'locked': 'door_blue_key'
        },
        'npc_settings': {
            'density': 0.014,
            'pool': {
                # Враги на открытых пространствах ангара нападают большими группами до 4 человек
                'AGG': { 'weight': 70, 'max_count': 25, 'min_dist': 5, 'min_progress': 0.0, 'cluster': { 'type': 'circle', 'chance': 0.35, 'size': 4 } },
                'CM':  { 'weight': 40, 'max_count': 5,  'min_dist': 8,  'min_progress': 0.3, 'cluster': { 'type': 'single', 'chance': 0.0, 'size': 1 } }
            }
        },
        'decor_settings': {
            'density': 0.05, # Повышенная плотность объектов для создания сети укрытий
            'pool': {
                # Тяжелые контейнеры строятся линиями-перегородками
                'prop_cargo_container':     { 'weight': 70,  'max_count': 12, 'min_dist': 5, 'cluster': { 'type': 'line', 'chance': 0.40, 'size': 2 } },
                # Поддоны с грузом генерируются кучами-складами по 3 штуки рядом
                'prop_cargo_pallet':        { 'weight': 100, 'max_count': 25, 'min_dist': 3, 'cluster': { 'type': 'circle', 'chance': 0.50, 'size': 3 } },
                # Одиночные погрузчики и промышленные генераторы в углах
                'prop_forklift':            { 'weight': 40,  'max_count': 6,  'min_dist': 8, 'cluster': { 'type': 'single', 'chance': 0.0, 'size': 1 } },
                'prop_industrial_generator':{ 'weight': 30,  'max_count': 5,  'min_dist': 10, 'cluster': { 'type': 'single', 'chance': 0.0, 'size': 1 } }
            }
        },
        'loot_settings': {
            'density': 0.025,
            'pool': {
                'health':    { 'weight': 60,  'max_count': 15, 'min_dist': 6,  'min_progress': 0.0, 'cluster': { 'type': 'single', 'chance': 0.0, 'size': 1 } },
                # Патроны для пистолета лежат сразу большими пачками по 4 коробки
                'colt':      { 'weight': 100, 'max_count': 30, 'min_dist': 4,  'min_progress': 0.0, 'cluster': { 'type': 'circle', 'chance': 0.50, 'size': 4 } },
                'shotgun':   { 'weight': 20,  'max_count': 3,  'min_dist': 15, 'min_progress': 0.3, 'cluster': { 'type': 'single', 'chance': 0.0, 'size': 1 } },
                # Мощный автоматический дробовик AA12 спрятан строго в секретных зонах ангара!
                'aa12':      { 'weight': 10,  'max_count': 1,  'min_dist': 20, 'min_progress': 0.6, 'secret_only': True, 'cluster': { 'type': 'single', 'chance': 0.0, 'size': 1 } }
            }
        }
    }
}
