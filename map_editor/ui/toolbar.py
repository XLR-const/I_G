"""Панель объектов (легенда) — упрощённая версия"""

import os
import sys
import pygame

# СНАЧАЛА добавляем путь к корню
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# ПОТОМ импортируем всё остальное
from ..config_loader import SYMBOLS_CONFIG, NPC_CONFIG
from ..config import COLORS, TEXTURES_DIR, NPC_DIR


class Toolbar:
    """Панель с объектами"""

    def __init__(self, rect):
        self.rect = rect
        
        # Все объекты в плоском списке
        self.items = []
        self.selected_index = 0
        self.scroll_offset = 0
        self.item_height = 48
        self.visible_items = 0
        
        # Отступ сверху для заголовка
        self.top_padding = 30
        
        self._build_items()
        self._update_visible_count()

    def _build_items(self):
        """Собирает все объекты в плоский список"""
        self.items = []

        # 1. Стены
        wall_symbols = []
        for symbol, config in SYMBOLS_CONFIG.items():
            if config.get('type') == 'wall':
                wall_symbols.append(symbol)
        wall_symbols.sort()

        self.items.append({'type': 'separator', 'label': 'СТЕНЫ'})
        for symbol in wall_symbols:
            surf = self._load_texture(symbol)
            self.items.append({
                'type': 'item',
                'symbol': symbol,
                'surface': surf,
                'label': symbol,
                'sub': 'стена'
            })

        # 2. Объекты
        self.items.append({'type': 'separator', 'label': 'ОБЪЕКТЫ'})

        for symbol, config in SYMBOLS_CONFIG.items():
            if config.get('type') == 'door':
                surf = self._load_texture(symbol)
                self.items.append({
                    'type': 'item',
                    'symbol': symbol,
                    'surface': surf,
                    'label': symbol,
                    'sub': 'дверь'
                })

        for symbol, config in SYMBOLS_CONFIG.items():
            if config.get('type') == 'exit':
                surf = self._create_surface(symbol, (0, 100, 0))
                self.items.append({
                    'type': 'item',
                    'symbol': symbol,
                    'surface': surf,
                    'label': symbol,
                    'sub': 'выход'
                })

        for symbol, config in SYMBOLS_CONFIG.items():
            if config.get('type') == 'player_spawn':
                surf = self._create_surface(symbol, (120, 100, 0))
                self.items.append({
                    'type': 'item',
                    'symbol': symbol,
                    'surface': surf,
                    'label': symbol,
                    'sub': 'спавн'
                })

        surf = self._create_surface('_', (30, 30, 35))
        self.items.append({
            'type': 'item',
            'symbol': '_',
            'surface': surf,
            'label': '_',
            'sub': 'пустота'
        })

        # Items
        self.items.append({'type': 'separator', 'label': 'ПРЕДМЕТЫ'})

        # Аптечка
        surf = self._create_surface('h', (200, 0, 0))
        self.items.append({
            'type': 'item',
            'symbol': 'h',
            'surface': surf,
            'label': 'h',
            'sub': 'аптечка +25 HP'
        })

        # 3. NPC
        self.items.append({'type': 'separator', 'label': 'NPC'})

        for symbol, config in NPC_CONFIG.items():
            name = config.get('name', 'unknown')
            surf = self._load_npc_sprite(name)
            if surf is None:
                surf = self._create_surface(symbol, (100, 0, 0))

            is_boss = config.get('class_name') == 'Boss'
            self.items.append({
                'type': 'item',
                'symbol': symbol,
                'surface': surf,
                'label': symbol,
                'sub': f'{name} {"(босс)" if is_boss else ""}'
            })

    def _load_texture(self, symbol):
        try:
            path = os.path.join(TEXTURES_DIR, f"{symbol}.png")
            if os.path.exists(path):
                surf = pygame.image.load(path).convert_alpha()
                return pygame.transform.scale(surf, (32, 32))
        except:
            pass
        return self._create_surface(symbol, (60, 60, 70))

    def _load_npc_sprite(self, name):
        try:
            path = os.path.join(NPC_DIR, name, f"{name}_idle_front.png")
            if os.path.exists(path):
                surf = pygame.image.load(path).convert_alpha()
                return pygame.transform.scale(surf, (32, 32))
        except:
            pass
        return None

    def _create_surface(self, symbol, color):
        size = 32
        surf = pygame.Surface((size, size))
        surf.fill(color)
        pygame.draw.rect(surf, (80, 80, 90), surf.get_rect(), 1)
        font = pygame.font.Font(None, 22)
        text = font.render(symbol, True, (255, 255, 255))
        text_rect = text.get_rect(center=surf.get_rect().center)
        surf.blit(text, text_rect)
        return surf

    def _update_visible_count(self):
        """Обновляет количество видимых элементов"""
        height = self.rect.height - self.top_padding - 10
        self.visible_items = max(1, height // self.item_height)

    def get_selected_symbol(self):
        """Возвращает выбранный символ"""
        if self.selected_index < len(self.items):
            item = self.items[self.selected_index]
            if item['type'] == 'item':
                return item['symbol']
        return 'M'

    def handle_click(self, mouse_x, mouse_y):
        """Обрабатывает клик"""
        if not self.rect.collidepoint(mouse_x, mouse_y):
            return False

        # Относительная позиция (с учётом отступа сверху)
        rel_y = mouse_y - self.rect.y - self.top_padding + self.scroll_offset
        index = rel_y // self.item_height

        if 0 <= index < len(self.items):
            self.selected_index = index
            item = self.items[index]
            if item['type'] == 'item':
                print(f"[Выбран] '{item['symbol']}' ({item['sub']})")
            else:
                print(f"[Раздел] {item['label']}")
            return True

        return False

    def scroll(self, delta):
        """Прокрутка"""
        total_height = len(self.items) * self.item_height + self.top_padding + 5
        max_scroll = max(0, total_height - self.rect.height + 10)
        self.scroll_offset = max(0, min(max_scroll, self.scroll_offset + delta))

    def draw(self, screen):
        """Отрисовка"""
        # Фон
        pygame.draw.rect(screen, (35, 35, 40), self.rect)
        pygame.draw.rect(screen, (80, 80, 90), self.rect, 1)

        # Заголовок
        font_title = pygame.font.Font(None, 16)
        title = font_title.render("ОБЪЕКТЫ", True, (240, 240, 240))
        screen.blit(title, (self.rect.x + 10, self.rect.y + 3))

        # Счётчик
        font_count = pygame.font.Font(None, 11)
        item_count = sum(1 for i in self.items if i['type'] == 'item')
        count_text = font_count.render(f"{item_count} объектов", True, (140, 140, 140))
        screen.blit(count_text, (self.rect.x + 10, self.rect.y + 20))

        # Список (со смещением на top_padding)
        y = self.rect.y + self.top_padding - self.scroll_offset
        font_sep = pygame.font.Font(None, 13)
        font_label = pygame.font.Font(None, 16)
        font_sub = pygame.font.Font(None, 12)

        for i, item in enumerate(self.items):
            if y + self.item_height < self.rect.y or y > self.rect.bottom:
                y += self.item_height
                continue

            rect = pygame.Rect(self.rect.x + 5, y, self.rect.width - 10, self.item_height)

            if item['type'] == 'separator':
                # Разделитель
                pygame.draw.rect(screen, (50, 50, 60), rect)
                text = font_sep.render(item['label'], True, (200, 200, 220))
                screen.blit(text, (rect.x + 10, rect.y + 14))
            else:
                # Элемент
                if i == self.selected_index:
                    pygame.draw.rect(screen, (80, 80, 160), rect)
                else:
                    pygame.draw.rect(screen, (45, 45, 50), rect)

                # Иконка
                if item['surface']:
                    icon_rect = item['surface'].get_rect(topleft=(rect.x + 6, rect.y + 8))
                    screen.blit(item['surface'], icon_rect)

                # Символ и название
                label_x = rect.x + 44
                label_y = rect.y + 6

                text = font_label.render(item['label'], True, (255, 255, 255))
                screen.blit(text, (label_x, label_y))

                sub_text = font_sub.render(item['sub'], True, (160, 160, 180))
                screen.blit(sub_text, (label_x, label_y + 22))

                # Рамка
                pygame.draw.rect(screen, (70, 70, 80), rect, 1)

            y += self.item_height

        # Полоса прокрутки
        total_height = len(self.items) * self.item_height + self.top_padding + 5
        if total_height > self.rect.height:
            bar_height = max(20, int(self.rect.height * (self.rect.height / total_height)))
            scroll_ratio = self.scroll_offset / (total_height - self.rect.height)
            bar_y = self.rect.y + int((self.rect.height - bar_height) * scroll_ratio)
            pygame.draw.rect(screen, (120, 120, 140), (self.rect.right - 10, bar_y, 6, bar_height))