"""Классы предметов на полу"""

import pygame
import math
from setting import *
from config.game_data import SYMBOLS_CONFIG
from core.weapon import Weapon
import os


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
            # ИСПРАВЛЕНИЕ: Сверяем системные weapon_name ('Colt' == 'Colt'), 
            # чтобы избежать дублирования из-за разных красивых имен на экране
            if weapon.weapon_name == self.weapon_name:
                weapon_found = weapon
                break

        if weapon_found:
            # Оружие уже есть → просто добавляем патроны в существующий ствол
            weapon_found.ammo += self.ammo
            self.alive = False
            return True
        else:
            # Оружия нет → добавляем в инвентарь через универсальный класс Weapon
            from core.weapon import Weapon
            
            new_weapon = Weapon(self.game, self.weapon_name)
            new_weapon.ammo = self.ammo
            inventory.append(new_weapon)
            
            # Если это первая пушка или в руках у игрока пусто — сразу даем ее в руки
            if len(inventory) == 1 or self.game.weapon is None:
                self.game.weapon = new_weapon
                self.game.level_manager.current_weapon_index = len(inventory) - 1

            self.alive = False
            return True

class KeyItem(Item):
    """Цветная ключ-карта для запертых дверей"""

    def __init__(self, game, x, y, key_color='red'):
        self.key_color = str(key_color).strip().lower()
        super().__init__(game, x, y, 'key', amount=0)

    def _load_sprite(self):
        """Загружает спрайт для конкретного цвета ключа"""
        target_symbol = f"key_{self.key_color}"
        
        config = SYMBOLS_CONFIG.get(target_symbol)
        if config:
            sprite_path = config.get('sprite')
            if sprite_path:
                try:
                    self.sprite = pygame.image.load(sprite_path).convert_alpha()
                    self.sprite = pygame.transform.scale(self.sprite, (32, 32))
                    self.sprite_width, self.sprite_height = self.sprite.get_size()
                    self.sprite_ratio = self.sprite_width / self.sprite_height
                    return
                except Exception as e:
                    print(f"[KeyItem] Ошибка загрузки {sprite_path}: {e}")

        self._create_fallback_sprite()

    def _create_fallback_sprite(self):
        """Цветная заглушка для ключа"""
        colors = {
            'red': (200, 0, 0),
            'blue': (0, 100, 200),
            'yellow': (200, 200, 0),
            'green': (0, 200, 0),
        }
        color = colors.get(self.key_color, (200, 200, 200))
        
        self.sprite = pygame.Surface((32, 32))
        self.sprite.fill(color)
        # Рисуем букву "K" для ключа
        font = pygame.font.Font(None, 24)
        text = font.render("K", True, (255, 255, 255))
        text_rect = text.get_rect(center=(16, 16))
        self.sprite.blit(text, text_rect)
        
        self.sprite_width, self.sprite_height = self.sprite.get_size()
        self.sprite_ratio = self.sprite_width / self.sprite_height

    def pick_up(self, player):
        if not self.alive:
            return False

        if not hasattr(player, 'keys_inventory'):
            player.keys_inventory = []

        if self.key_color not in player.keys_inventory:
            player.keys_inventory.append(self.key_color)
            self.alive = False
            print(f"[ИНВЕНТАРЬ] Подобрана {self.key_color.upper()} ключ-карта!")
            return True

        return False

class DecorItem(Item):
    """Класс для статичных декораций на полу в виде 3D спрайтов-биллбордов"""

    def __init__(self, game, x, y, decor_name):
        # 🔥 СНАЧАЛА СОХРАНЯЕМ ИМЯ: Чтобы метод _load_sprite() сразу его увидел при вызове из super()!
        self.decor_name = str(decor_name).strip().lower()
        
        # Вызываем базовый конструктор, передавая 'key' как временный тип (как у твоих ключей)
        super().__init__(game, x, y, 'key', amount=0)
        
        # Настраиваем стейты для совместимости с твоим менеджером объектов
        self.item_type = 'decor'
        self.type = self.decor_name
        self.alive = True

    def _load_sprite(self):
        """Загружает спрайт для конкретного декора из SYMBOLS_CONFIG"""
        config = SYMBOLS_CONFIG.get(self.decor_name)
        if config:
            sprite_path = config.get('sprite')
            if sprite_path:
                try:
                    self.sprite = pygame.image.load(sprite_path).convert_alpha()
                    self.sprite = pygame.transform.scale(self.sprite, (32, 32))
                    self.sprite_width, self.sprite_height = self.sprite.get_size()
                    self.sprite_ratio = self.sprite_width / self.sprite_height
                    
                    # Передаем картинку в image для твоего менеджера спрайтов
                    self.image = self.sprite
                    return # Успех, выходим из метода!
                except Exception as e:
                    print(f"[DecorItem] Ошибка загрузки {sprite_path}: {e}")

        self._create_fallback_sprite()

    def pick_up(self, player):
        # Декорацию нельзя подобрать
        return False


