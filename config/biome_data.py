# ==================================================================
# 🌐 УЛЬТИМАТИВНАЯ DATA-DRIVEN БАЗА ДАННЫХ ДЛЯ КОНТРОЛЯ БАЛАНСА БИОМОВ
# Использованы СТРОГО реальные ключи из SYMBOLS_CONFIG и DECOR_CONFIG!
# ==================================================================

BIOME_DATABASE = {
    'out': {
        'name': '🪖 Улица и Военные Блокпосты',
        
        # 🧱 СЛОЙ 1: ДОМИНАЦИЯ СТЕН (Из твоего SYMBOLS_CONFIG)
        'walls': {
            'primary': { 'char': 'rocks', 'weight': 80 },             # Основополагающая стена каньона
            'secondary': { 'char': 'metal_crunch_wall', 'weight': 20 } # Дополняющая броня блокпостов
        },
        
        # 🚪 СЛОЙ 2: ДВЕРИ
        'doors': {
            'normal': 'door_normal',
            'locked': 'door_blue_key'
        },
        
        # 🧟 СЛОЙ 3: МОНСТРЫ И NPC (Из твоего NPC_CONFIG)
        'npc_settings': {
            'density': 0.04,  
            'pool': {
                'AGG': { # Твой AutoGunGuy
                    'weight': 100, 'max_count': 30, 'min_dist': 2, 
                    'cluster_type': 'circle', 'cluster_chance': 0.35, 'cluster_size': 3 
                }, 
                'CM': { # Твой ChaingunMajor (Мини-босс)
                    'weight': 15, 'max_count': 3, 'min_dist': 8, 
                    'cluster_type': 'single', 'cluster_chance': 0.0, 'cluster_size': 1 
                }  
            }
        },
        
        # 📦 СЛОЙ 4: ДЕКОРАЦИИ И ПРОПСЫ (Из твоего DECOR_CONFIG)
        'decor_settings': {
            'density': 0.08,  
            'pool': {
                'prop_sandbag_wall': { # Строго по PDF!
                    'weight': 120, 'max_count': 30, 'min_dist': 1, 
                    'cluster_type': 'line', 'cluster_chance': 0.70, 'cluster_size': 4 
                }, 
                'prop_military_crate': { # Строго по PDF!
                    'weight': 60, 'max_count': 15, 'min_dist': 2, 
                    'cluster_type': 'circle', 'cluster_chance': 0.50, 'cluster_size': 2 
                }, 
                'prop_searchlight': { # Строго по PDF!
                    'weight': 20, 'max_count': 6, 'min_dist': 6, 
                    'cluster_type': 'single', 'cluster_chance': 0.0, 'cluster_size': 1 
                }  
            }
        },
        
        # 🔫 СЛОЙ 5: ПРЕДМЕТЫ И АРСЕНАЛ (Из твоего SYMBOLS_CONFIG)
        'loot_settings': {
            'density': 0.06,  
            'pool': {
                'health': { # Строго по PDF!
                    'weight': 100, 'max_count': 15, 'min_dist': 1, 
                    'cluster_type': 'circle', 'cluster_chance': 0.30, 'cluster_size': 2 
                }, 
                'armor': { # Строго по PDF!
                    'weight': 80, 'max_count': 12, 'min_dist': 1, 
                    'cluster_type': 'single', 'cluster_chance': 0.0, 'cluster_size': 1 
                }, 
                'shotgun': { # Строго по PDF! (это твоя двустволка COCH)
                    'weight': 10, 'max_count': 1, 'min_dist': 99, 
                    'cluster_type': 'single', 'cluster_chance': 0.0, 'cluster_size': 1 
                }  
            }
        }
    },
    
    'lab': {
        'name': '🔬 Стерильная Лаборатория',
        'walls': { 
            'primary': { 'char': 'L', 'weight': 85 }, #
            'secondary': { 'char': 'G', 'weight': 15 } #
        },
        'doors': { 'normal': 'door_normal', 'locked': 'door_red_key' }, #
        'npc_settings': { 
            'density': 0.04, 
            'pool': {
                'BS': { 'weight': 100, 'max_count': 25, 'min_dist': 2, 'cluster_type': 'single', 'cluster_chance': 0.0, 'cluster_size': 1 } # BeamSolder
            } 
        },
        'decor_settings': {
            'density': 0.06,
            'pool': {
                'prop_chemical_barrel': { 'weight': 80, 'max_count': 25, 'min_dist': 1, 'cluster_type': 'circle', 'cluster_chance': 0.30, 'cluster_size': 2 }, #
                'prop_lab_capsule':     { 'weight': 20, 'max_count': 12, 'min_dist': 3, 'cluster_type': 'line',   'cluster_chance': 0.85, 'cluster_size': 4 }  #
            }
        },
        'loot_settings': { 
            'density': 0.05, 
            'pool': {
                'colt': { 'weight': 100, 'max_count': 10, 'min_dist': 1, 'cluster_type': 'single', 'cluster_chance': 0.0, 'cluster_size': 1 } #
            } 
        }
    }
}
