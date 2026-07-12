"""Классы предметов на полу"""

import pygame
import math
from setting import *
from config.game_data import SYMBOLS_CONFIG


class Item:
    """Базовый класс предмета"""

    def __init__(self, game, x, y, item_type, amount=0):
        self.game = game
        self.x = x + 0.5
        self.y = y + 0.5
        self.item_type = item_type
        self.amount = amount
        self.alive = True

        self.sprite = None
        self.sprite_width = 0
        self.sprite_height = 0
        self.sprite_ratio = 1.0

        self._load_sprite()

    def _load_sprite(self):
        """Загружает спрайт предмета"""
        for symbol, config in SYMBOLS_CONFIG.items():
            if config.get('type') == 'item':
                if config.get('item_type') == self.item_type:
                    sprite_path = config.get('sprite')
                    if sprite_path:
                        try:
                            self.sprite = pygame.image.load(sprite_path).convert_alpha()
                            self.sprite = pygame.transform.scale(self.sprite, (32, 32))
                            self.sprite_width, self.sprite_height = self.sprite.get_size()
                            self.sprite_ratio = self.sprite_width / self.sprite_height
                            return
                        except Exception as e:
                            print(f"[Item] Ошибка загрузки: {e}")
                    break

        self._create_fallback_sprite()

    def _create_fallback_sprite(self):
        """Заглушка"""
        self.sprite = pygame.Surface((32, 32))
        self.sprite.fill((200, 200, 200))
        pygame.draw.circle(self.sprite, (100, 100, 100), (16, 16), 12)
        self.sprite_width, self.sprite_height = self.sprite.get_size()
        self.sprite_ratio = self.sprite_width / self.sprite_height

    def pick_up(self, player):
        """Подбор предмета (переопределяется в наследниках)"""
        return False

    def update(self, player):
        if self.alive:
            dx = player.x - self.x
            dy = player.y - self.y
            if math.hypot(dx, dy) < 0.5:
                self.pick_up(player)

    def draw(self):
        if not self.alive or self.sprite is None:
            return

        dx = self.x - self.game.player.x
        dy = self.y - self.game.player.y
        dist = math.hypot(dx, dy)

        if dist < 0.1:
            return

        theta = math.atan2(dy, dx)
        delta = theta - self.game.player.angle
        delta = (delta + math.pi) % math.tau - math.pi

        # Немного расширяем FOV для проверки, чтобы края спрайта не исчезали внезапно
        if abs(delta) > HALF_FOV + 0.5:
            return

        # Плоская дистанция (для корректного Z-буфера)
        dist_flat = dist * math.cos(delta)
        if dist_flat < 0.1:
            return

        # Расчёт размеров
        proj_height = int(SCREEN_DIST / dist_flat * 0.35)
        if proj_height < 2:
            return

        proj_width = int(proj_height * (self.sprite.get_width() / self.sprite.get_height()))

        # Позиционирование на экране
        center_x = (HALF_NUM_RAYS + delta / DELTA_ANGLE) * SCALE
        screen_x = int(center_x - proj_width // 2)

        # Привязка к полу
        screen_y = int(HALF_HEIGHT + (SCREEN_DIST / dist_flat * 0.5) - proj_height)

        # Масштабируем спрайт
        scaled_sprite = pygame.transform.scale(self.sprite, (proj_width, proj_height))

        # Пополосный рендеринг с проверкой Z-буфера
        for col in range(proj_width):
            x_pos = screen_x + col

            if 0 <= x_pos < WIDTH:
                ray_idx = int(x_pos // SCALE)

                if 0 <= ray_idx < NUM_RAYS:
                    if dist_flat < self.game.raycasting.z_buffer[ray_idx]:
                        sub_surface = scaled_sprite.subsurface(col, 0, 1, proj_height)
                        self.game.screen.blit(sub_surface, (x_pos, screen_y))


# ============================================================
# НАСЛЕДНИКИ
# ============================================================

class HealthItem(Item):
    """Аптечка"""

    def __init__(self, game, x, y, amount=25):
        super().__init__(game, x, y, 'health', amount)

    def _create_fallback_sprite(self):
        self.sprite = pygame.Surface((32, 32))
        self.sprite.fill((200, 0, 0))
        pygame.draw.rect(self.sprite, (255, 255, 255), (8, 14, 16, 4))
        pygame.draw.rect(self.sprite, (255, 255, 255), (14, 8, 4, 16))
        self.sprite_width, self.sprite_height = self.sprite.get_size()
        self.sprite_ratio = self.sprite_width / self.sprite_height

    def pick_up(self, player):
        if not self.alive:
            return False

        old_hp = player.hp
        player.hp = min(100, player.hp + self.amount)
        healed = player.hp - old_hp

        if healed > 0:
            self.alive = False
            #print(f"[Аптечка] +{healed} HP")
            return True

        #print("[Аптечка] HP полное")
        return False


class ArmorItem(Item):
    """Броня"""

    def __init__(self, game, x, y, amount=25):
        super().__init__(game, x, y, 'armor', amount)

    def _create_fallback_sprite(self):
        self.sprite = pygame.Surface((32, 32))
        self.sprite.fill((0, 100, 200))
        pygame.draw.polygon(self.sprite, (200, 200, 255), [
            (8, 16), (16, 4), (24, 16), (20, 28), (12, 28)
        ])
        self.sprite_width, self.sprite_height = self.sprite.get_size()
        self.sprite_ratio = self.sprite_width / self.sprite_height

    def pick_up(self, player):
        if not self.alive:
            return False

        old_armor = player.armor
        player.armor = min(100, player.armor + self.amount)
        added = player.armor - old_armor

        if added > 0:
            self.alive = False
            #print(f"[Броня] +{added} Armor")
            return True

        #print("[Броня] Armor полное")
        return False


class WeaponItem(Item):
    """Оружие на полу"""

    def __init__(self, game, x, y, weapon_name, ammo=0):
        self.weapon_name = weapon_name
        self.ammo = ammo
        super().__init__(game, x, y, 'weapon', ammo)

    def _load_sprite(self):
        """Загружает спрайт оружия"""
        # Ищем спрайт в SYMBOLS_CONFIG
        for symbol, config in SYMBOLS_CONFIG.items():
            if config.get('type') == 'item':
                if config.get('weapon_name') == self.weapon_name:
                    sprite_path = config.get('sprite')
                    if sprite_path:
                        try:
                            self.sprite = pygame.image.load(sprite_path).convert_alpha()
                            self.sprite = pygame.transform.scale(self.sprite, (32, 32))
                            self.sprite_width, self.sprite_height = self.sprite.get_size()
                            self.sprite_ratio = self.sprite_width / self.sprite_height
                            return
                        except Exception as e:
                            print(f"[WeaponItem] Ошибка загрузки: {e}")
                    break

        self._create_fallback_sprite()

    def _create_fallback_sprite(self):
        """Заглушка для оружия"""
        self.sprite = pygame.Surface((32, 32))
        self.sprite.fill((200, 200, 0))
        pygame.draw.rect(self.sprite, (150, 150, 0), (4, 4, 24, 24))
        self.sprite_width, self.sprite_height = self.sprite.get_size()
        self.sprite_ratio = self.sprite_width / self.sprite_height

    def pick_up(self, player):
        if not self.alive:
            return False

        # Получаем инвентарь из level_manager
        inventory = self.game.level_manager.inventory
        if inventory is None:
            return False

        # Проверяем, есть ли уже такое оружие в инвентаре
        weapon_found = None
        for weapon in inventory:
            if weapon.name == self.weapon_name:
                weapon_found = weapon
                break

        if weapon_found:
            # Оружие уже есть → просто добавляем патроны
            weapon_found.ammo += self.ammo
            self.alive = False
            return True
        else:
            # Оружия нет → добавляем в инвентарь
            from core.weapon import Pistol, Shotgun, MachineGun, PlasmaGun, NewWeapon
            
            # Старые хардкод-классы
            weapon_classes = {
                'Pistol': Pistol,
                'Shotgun': Shotgun,
                'Machine Gun': MachineGun,
                'Plasma Gun': PlasmaGun,
            }

            # Проверяем, старая это пушка или новая
            if self.weapon_name in weapon_classes:
                weapon_class = weapon_classes[self.weapon_name]
                # ИСПРАВЛЕНИЕ: Старым классам передаем ТОЛЬКО объект игры (self.game)
                new_weapon = weapon_class(self.game)
            else:
                weapon_class = NewWeapon
                # ИСПРАВЛЕНИЕ: Универсальному классу NewWeapon передаем игру и имя пушки
                new_weapon = weapon_class(self.game, self.weapon_name)

            new_weapon.ammo = self.ammo
            inventory.append(new_weapon)
            
            # Если это первое оружие в инвентаре или у игрока вообще не было активного оружия
            if len(inventory) == 1 or self.game.weapon is None:
                self.game.weapon = new_weapon
                self.game.level_manager.current_weapon_index = len(inventory) - 1

            self.alive = False
            return True


