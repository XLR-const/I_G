import pygame
import math
from raycast import cast_ray

class Weapon:
    
    def __init__(self, name, damage, fire_rate, shoot_distance, max_ammo, color=(255, 255, 255)):
        self.name = name
        self.damage = damage
        self.fire_rate = fire_rate #кадров между выстрелами
        self.shoot_distance = shoot_distance
        self.color = color
        self.current_cooldown = 0
        self.ammo = -1 #unlimitted ammo
        self.max_ammo = -1 #ammo in magazine
        self.current_ammo = max_ammo if self.max_ammo != -1 else -1
        self.owned = False #Подобран ли
        
    def can_shoot(self):
        if self.max_ammo == -1:
            return self.current_cooldown <= 0
        return self.current_cooldown <= 0 and self.current_ammo > 0
    
    def shoot(self, player, world):
        if not self.can_shoot():
            return False, None
        
        #Расход патронов (без магазинного питания)
        if self.max_ammo != -1:
            self.current_ammo -= 1
            
        #Луч стрельбы
        dist, hit, side, hit_pos = cast_ray(player.x, player.y, player.angle, world.map)
        
        hit_info = {
            'hit': hit,
            'distance': dist,
            'side': side,
            'position': hit_pos,
            'damage': 0.,
            'weapon': self.name
        }
        
        if hit and dist < self.shoot_distance:
            hit_info['damage'] = self.damage
            self.current_cooldown = self.fire_rate
            return True, hit_info
        
        self.current_cooldown = self.fire_rate
        return False, hit_info
    
    def update(self):
        if self.current_cooldown > 0:
            self.current_cooldown -= 1
            
    def reload(self):
        if self.max_ammo > 0:
            self.ammo = self.max_ammo
            
    def add_ammo(self, amount):
        """Для добавления чилса патронов"""
        if self.ammo != -1:
            self.ammo = min(self.max_ammo, self.add_ammo + amount) #остаток/фулл
    
class WeaponPickup:
    """Оружие лежащее на полу"""
    
    def __init__(self, weapon_name, x, y, weapon_data):
        self.weapon_name = weapon_name
        self.x = x
        self.y = y
        # Копирование из словаря параметрова ствола
        data = weapon_data[weapon_name]
        self.damage = data['damage']
        self.fire_rate = data['fire_rate']
        self.shoot_distance = data['shoot_distance']
        self.max_ammo = data['max_ammo']
        self.color = data['color']
        self.radius = 0.5   # радиус подбора в клетках
        
    def check_pickup(self, player_x, player_y):
        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.sqrt(dx*dx + dy*dy)
        return dist <= self.radius
    
    
class WeaponManager:
    """Селектор оружия"""
    
    def __init__(self):
        self.inventory = []
        self.current_index = 0
        self.current_weapon = None
        
    def add_weapon(self, weapon):
        """Добавляет оружие в инвентарь, если его ещё нет"""
        # Проверяем, есть ли уже такое оружие
        for w in self.inventory:
            if w.name == weapon.name:
                # Если есть — просто добавляем патроны
                if weapon.max_ammo != -1:
                    w.add_ammo(weapon.max_ammo // 2)  # половина от максимальных
                return w
        
        # Нового оружия нет — добавляем
        weapon.owned = True
        self.inventory.append(weapon)
        
        # Если это первое оружие — делаем текущим
        if len(self.inventory) == 1:
            self.current_index = 0
            self.current_weapon = weapon
        
        return weapon
    
    def switch_to(self, index):
        """Переключается на оружие по индексу"""
        if 0 <= index < len(self.inventory):
            self.current_index = index
            self.current_weapon = self.inventory[index]
            return True
        return False
    
    def switch_next(self):
        """Следующее оружие (колесо мыши)"""
        if len(self.inventory) > 1:
            self.current_index = (self.current_index + 1) % len(self.inventory)
            self.current_weapon = self.inventory[self.current_index]
            
    def switch_prev(self):
        """Предыдущее оружие"""
        if len(self.inventory) > 1:
            self.current_index = (self.current_index - 1) % len(self.inventory)
            self.current_weapon = self.inventory[self.current_index]
    
    def shoot(self, player, world):
        if self.current_weapon:
            return self.current_weapon.shoot(player, world)
        return False, None
    
    def update(self):
        if self.current_weapon:
            self.current_weapon.update()
            
    def get_weapon_slot(self, index):
        """Возвращает оружие для слота (0-9)"""
        if 0 <= index < len(self.inventory):
            return self.inventory[index]
        return None
    
    