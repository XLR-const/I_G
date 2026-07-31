# ==================================================================
# 🌐 УЛЬТИМАТИВНАЯ DATA-DRIVEN БАЗА ДАННЫХ ДЛЯ КОНТРОЛЯ БАЛАНСА БИОМОВ
# Полная поддержка геометрических куч, радиусов исключения и жестких лимитов!
# ==================================================================

BIOME_DATABASE = {
    'out': {
        'name': '🪖 Улица и Военные Блокпосты',
        
        # 🧱 СЛОЙ 1: ДОМИНАЦИЯ СТЕН
        'walls': {
            'primary': { 'char': 'rocks', 'weight': 85 },             # Основополагающая стена каньона (80%)
            'secondary': { 'char': 'metal_crunch_wall', 'weight': 15 } # Дополняющая броня блокпостов (20%)
        },
        
        # 🚪 СЛОЙ 2: ДВЕРИ
        'doors': {
            'normal': 'door_normal',
            'locked': 'door_blue_key'
        },
        
        # 🧟 СЛОЙ 3: МОНСТРЫ И NPC
        'npc_settings': {
            'density': 0.012,  
            'pool': {
                'AGG': { 
                    'weight': 100, 'max_count': 25, 'min_dist': 5, 
                    'cluster_type': 'circle', 'cluster_chance': 0.15, 'cluster_size': 2 
                }, # Патрульные: спавнятся кучками по 2 человека с шансом 15%
                'CM': { 
                    'weight': 20, 'max_count': 3, 'min_dist': 12, 
                    'cluster_type': 'single', 'cluster_chance': 0.0, 'cluster_size': 1 
                }  # Чайнганнер (Мини-босс)
            }
        },
        
        # 📦 СЛОЙ 4: ДЕКОРАЦИИ И ПРОПСЫ
        'decor_settings': {
            'density': 0.04,  
            'pool': {
                'prop_sandbag_wall': { 'weight': 120, 'max_count': 25, 'min_dist': 3, 'cluster_type': 'line', 'cluster_chance': 0.60, 'cluster_size': 3 }, 
                'prop_military_crate': { 'weight': 50, 'max_count': 12, 'min_dist': 4, 'cluster_type': 'single', 'cluster_chance': 0.0, 'cluster_size': 1 }, 
                'prop_searchlight': { 'weight': 15, 'max_count': 4, 'min_dist': 10, 'cluster_type': 'single', 'cluster_chance': 0.0, 'cluster_size': 1 }  
            }
        },
        
        # 🔫 СЛОЙ 5: ПРЕДМЕТЫ И АРСЕНАЛ (ЛУТ)
        'loot_settings': {
            'density': 0.025,  
            'pool': {
                'health': { 'weight': 100, 'max_count': 12, 'min_dist': 4, 'cluster_type': 'single', 'cluster_chance': 0.0, 'cluster_size': 1 }, 
                'armor':  { 'weight': 80,  'max_count': 10, 'min_dist': 5, 'cluster_type': 'single', 'cluster_chance': 0.0, 'cluster_size': 1 }, 
                'colt':   { 'weight': 40,  'max_count': 4,  'min_dist': 10, 'cluster_type': 'single', 'cluster_chance': 0.0, 'cluster_size': 1 }, 
                'ak47':   { 'weight': 25,  'max_count': 3,  'min_dist': 15, 'cluster_type': 'single', 'cluster_chance': 0.0, 'cluster_size': 1 }, 
                'shotgun':{ 'weight': 12,  'max_count': 2,  'min_dist': 25, 'cluster_type': 'single', 'cluster_chance': 0.0, 'cluster_size': 1 }  
            }
        }
    },
    
    'lab': {
        'name': '🔬 Стерильная Лаборатория',
        'walls': { 
            'primary': { 'char': 'L', 'weight': 80 }, 
            'secondary': { 'char': 'G', 'weight': 20 } 
        },
        'doors': { 'normal': 'door_normal', 'locked': 'door_red_key' },
        'npc_settings': { 
            'density': 0.02, 
            'pool': {
                'Z': { 'weight': 100, 'max_count': 30, 'min_dist': 2, 'cluster_type': 'circle', 'cluster_chance': 0.2, 'cluster_size': 2 }
            } 
        },
        'decor_settings': {
            'density': 0.04,
            'pool': {
                'prop_chemical_barrel': { 'weight': 80, 'max_count': 20, 'min_dist': 2, 'cluster_type': 'single', 'cluster_chance': 0.0, 'cluster_size': 1 },
                'prop_lab_capsule':     { 'weight': 20, 'max_count': 12, 'min_dist': 3, 'cluster_type': 'line',   'cluster_chance': 0.85, 'cluster_size': 4 }
            }
        },
        'loot_settings': { 
            'density': 0.02, 
            'pool': {
                'colt': { 'weight': 100, 'max_count': 5, 'min_dist': 5, 'cluster_type': 'single', 'cluster_chance': 0.0, 'cluster_size': 1 }
            } 
        }
    }
}
