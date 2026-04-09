import pygame
from weapons import Weapon
def load_weapons_from_file(filename):
    weapons = {}
    
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # Пропускаем пустые строки и комментарии
            if not line or line.startswith('#'):
                continue
            
            parts = line.split('|')
            if len(parts) == 8:
                name = parts[0]
                damage = int(parts[1])
                fire_rate = int(parts[2])
                shoot_distance = int(parts[3])
                max_ammo = int(parts[4])
                color = (int(parts[5]), int(parts[6]), int(parts[7]))
                
                weapons[name] = {
                    'damage': damage,
                    'fire_rate': fire_rate,
                    'shoot_distance': shoot_distance,
                    'max_ammo': max_ammo,
                    'color': color
                }
    
    return weapons

def create_starting_weapons(weapons_data):
    inventory = []
    
    if 'Pistol' in weapons_data:
        pistol = Weapon(
            'Pistol',
            weapons_data['Pistol']['damage'],
            weapons_data['Pistol']['fire_rate'],
            weapons_data['Pistol']['shoot_distance'],
            weapons_data['Pistol']['max_ammo'],
            weapons_data['Pistol']['color']
        )
        
    pistol.owned = True
    inventory.append(pistol)
    
    return inventory