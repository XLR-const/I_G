# Пример структуры для BIOME_DATABASE под новый генератор
BIOME_DATABASE = {
    'out': {
        'name': '🪖 Улица и Военные Блокпосты',
        'geometry': {
            'perimeter_wall': 'rocks',       # Жесткая рамка уровня (защита от краша)
            'bsp_min_room_size': 6,          # Ограничения для BSP-алгоритма
            'bsp_max_room_size': 12,
        },
        'walls': {
            'primary': { 'char': 'rocks', 'weight': 85 },
            'secondary': { 'char': 'metal_crunch_wall', 'weight': 15 }
        },
        'doors': {
            'normal': 'door_normal',
            'locked': 'door_blue_key',
            'required_key': 'key_blue'       # Перенос логики связки ключа/двери в конфиг
        },
        'npc_settings': {
            'density': 0.012, 
            'pool': {
                'AGG': { 
                    'weight': 100, 'max_count': 25, 'min_dist': 4, 'min_progress': 0.0,
                    'cluster': { 'type': 'circle', 'chance': 0.15, 'size': 2 }
                },
                'CM': { 
                    'weight': 20, 'max_count': 3, 'min_dist': 10, 'min_progress': 0.5, # Вместо хардкода в коде
                    'cluster': { 'type': 'single', 'chance': 0.0, 'size': 1 }
                }
            }
        },
        'decor_settings': {
            'density': 0.04, 
            'pool': {
                'prop_sandbag_wall': { 
                    'weight': 120, 'max_count': 25, 'min_dist': 2, 
                    'cluster': { 'type': 'line', 'chance': 0.60, 'size': 3 } # Мешки строятся линиями-баррикадами
                },
                'prop_military_crate': { 
                    'weight': 50, 'max_count': 12, 'min_dist': 3, 
                    'cluster': { 'type': 'single', 'chance': 0.0, 'size': 1 }
                }
            }
        },
        'loot_settings': {
            'density': 0.025, 
            'pool': {
                'health':  { 'weight': 100, 'max_count': 12, 'min_dist': 3, 'min_progress': 0.0 },
                'shotgun': { 'weight': 12,  'max_count': 2,  'min_dist': 12, 'min_progress': 0.6 }
            }
        }
    }
}
