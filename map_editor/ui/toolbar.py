"""Панель объектов (легенда)"""

import os
import pygame
from ..config import COLORS, SYMBOL_COLORS, TEXTURES_DIR, NPC_DIR


class Toolbar:
    """Панель с объектами для рисования"""

    def __init__(self, rect):
        self.rect = rect
        self.objects = []  # [(symbol, surface, label)]
        self.selected_index = 0
        self.scroll_offset = 0
        self.item_height = 40
        self.item_width = rect.width - 20

        self._build_objects()

    def _build_objects(self):
        """Собирает список объектов для панели"""
        self.objects = []

        # 1. Стены
        walls = ['M', 'C', 'L', 'R', 'B', 'G', 'W', 'I']
        for symbol in walls:
            surf = self._load_texture(symbol)
            self.objects.append({
                'symbol': symbol,
                'surface': surf,
                'label': symbol,
                'type': 'wall'
            })

        # 2. Пустота
        surf = self._create_surface('_', COLORS['floor'])
        self.objects.append({
            'symbol': '_',
            'surface': surf,
            'label': '_ (пол)',
            'type': 'floor'
        })

        # 3. Старт
        surf = self._create_surface('S', COLORS['start'])
        self.objects.append({
            'symbol': 'S',
            'surface': surf,
            'label': 'S (старт)',
            'type': 'start'
        })

        # 4. Выход
        surf = self._create_surface('N', COLORS['exit'])
        self.objects.append({
            'symbol': 'N',
            'surface': surf,
            'label': 'N (выход)',
            'type': 'exit'
        })

        # 5. Дверь
        surf = self._create_surface('D', COLORS['door'])
        self.objects.append({
            'symbol': 'D',
            'surface': surf,
            'label': 'D (дверь)',
            'type': 'door'
        })

        # 6. NPC
        npc_list = [
            ('2', 'solder'),
            ('3', 'kamikaze'),
            ('4', 'jaggernaut'),
            ('5', 'lightning'),
        ]
        for symbol, name in npc_list:
            surf = self._load_npc_sprite(name)
            if surf is None:
                surf = self._create_surface(symbol, COLORS['npc'])
            self.objects.append({
                'symbol': symbol,
                'surface': surf,
                'label': f'{symbol} ({name})',
                'type': 'npc'
            })

        # 7. Босс
        surf = self._load_npc_sprite('boss')
        if surf is None:
            surf = self._create_surface('6', COLORS['boss'])
        self.objects.append({
            'symbol': '6',
            'surface': surf,
            'label': '6 (босс)',
            'type': 'boss'
        })

    def _load_texture(self, symbol):
        """Загружает текстуру стены"""
        try:
            path = os.path.join(TEXTURES_DIR, f"{symbol}.png")
            if os.path.exists(path):
                surf = pygame.image.load(path).convert_alpha()
                # Масштабируем до размера иконки
                size = 28
                return pygame.transform.scale(surf, (size, size))
        except:
            pass
        return self._create_surface(symbol, COLORS['wall'])

    def _load_npc_sprite(self, name):
        """Загружает спрайт NPC"""
        try:
            path = os.path.join(NPC_DIR, name, f"{name}_idle_front.png")
            if os.path.exists(path):
                surf = pygame.image.load(path).convert_alpha()
                size = 28
                return pygame.transform.scale(surf, (size, size))
        except:
            pass
        return None

    def _create_surface(self, symbol, color):
        """Создаёт поверхность с символом"""
        size = 28
        surf = pygame.Surface((size, size))
        surf.fill(color)
        pygame.draw.rect(surf, COLORS['panel_border'], surf.get_rect(), 1)

        font = pygame.font.Font(None, 20)
        text = font.render(symbol, True, COLORS['text'])
        text_rect = text.get_rect(center=surf.get_rect().center)
        surf.blit(text, text_rect)
        return surf

    def get_selected_symbol(self):
        """Возвращает выбранный символ"""
        if 0 <= self.selected_index < len(self.objects):
            return self.objects[self.selected_index]['symbol']
        return 'M'

    def handle_click(self, mouse_x, mouse_y):
        """Обрабатывает клик по панели"""
        if not self.rect.collidepoint(mouse_x, mouse_y):
            return False

        rel_y = mouse_y - self.rect.y - 10 + self.scroll_offset
        index = rel_y // self.item_height

        if 0 <= index < len(self.objects):
            self.selected_index = index
            return True
        return False

    def draw(self, screen):
        """Отрисовывает панель"""
        pygame.draw.rect(screen, COLORS['panel_bg'], self.rect)
        pygame.draw.rect(screen, COLORS['panel_border'], self.rect, 1)

        # Заголовок
        font = pygame.font.Font(None, 16)
        title = font.render("ОБЪЕКТЫ", True, COLORS['text'])
        screen.blit(title, (self.rect.x + 10, self.rect.y + 5))

        # Список объектов
        y = self.rect.y + 30 - self.scroll_offset
        for i, obj in enumerate(self.objects):
            if y + self.item_height < self.rect.y or y > self.rect.bottom:
                y += self.item_height
                continue

            # Фон элемента
            rect = pygame.Rect(self.rect.x + 5, y, self.item_width, self.item_height)
            if i == self.selected_index:
                pygame.draw.rect(screen, (100, 100, 150), rect)
            else:
                pygame.draw.rect(screen, COLORS['panel_bg'], rect)

            # Иконка
            if obj['surface']:
                icon_rect = obj['surface'].get_rect(topleft=(rect.x + 5, rect.y + 6))
                screen.blit(obj['surface'], icon_rect)

            # Название
            font_small = pygame.font.Font(None, 14)
            text = font_small.render(obj['label'], True, COLORS['text'])
            screen.blit(text, (rect.x + 38, rect.y + 12))

            pygame.draw.rect(screen, COLORS['panel_border'], rect, 1)

            y += self.item_height

        # Общее количество объектов в панели для скролла
        total_height = len(self.objects) * self.item_height + 30
        if total_height > self.rect.height:
            # Показываем полосу прокрутки (заглушка)
            pass

    def scroll(self, delta):
        """Прокрутка панели"""
        total_height = len(self.objects) * self.item_height + 30
        max_scroll = max(0, total_height - self.rect.height + 10)
        self.scroll_offset = max(0, min(max_scroll, self.scroll_offset + delta))