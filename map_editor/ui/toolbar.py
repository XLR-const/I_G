# map_editor/ui/toolbar.py
"""Панель объектов - с раскрывающимися группами (аккордеон)"""

import os
import pygame
from ..config import COLORS, SYMBOL_COLORS, TEXTURES_DIR, NPC_DIR
from config.game_data import SYMBOLS_CONFIG, NPC_CONFIG

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class Toolbar:
    """Панель объектов с группами (аккордеон)"""

    def __init__(self, rect):
        self.rect = rect
        self.groups = []  # Список групп
        self.selected_symbol = 'M'
        self.scroll_offset = 0
        self.item_height = 48
        self.columns = 2  # Количество колонок в сетке
        self.top_padding = 35
        
        # Состояния групп (свёрнуты/развёрнуты)
        self.collapsed_groups = set()
        
        self._build_groups()
        
    def _build_groups(self):
        """Строит группы объектов из конфигов"""
        self.groups = []
        
        # =============================================
        # 1. СТЕНЫ
        # =============================================
        wall_items = []
        for symbol, config in SYMBOLS_CONFIG.items():
            if config.get('type') == 'wall':
                surf = self._load_texture_or_color(symbol)
                wall_items.append({
                    'symbol': symbol,
                    'surface': surf,
                    'label': symbol,
                    'sub': 'стена'
                })
        if wall_items:
            wall_items.sort(key=lambda x: x['label'])
            self.groups.append({
                'id': 'walls',
                'label': '🧱 СТЕНЫ',
                'items': wall_items,
                'collapsed': False
            })
        
        # =============================================
        # 2. ДВЕРИ
        # =============================================
        door_items = []
        for symbol, config in SYMBOLS_CONFIG.items():
            if config.get('type') == 'door':
                surf = self._load_texture_or_color(symbol)
                door_type = config.get('door_type', 'normal')
                required_key = config.get('required_key', '')
                
                if door_type == 'secret':
                    sub = 'секретная'
                elif required_key:
                    sub = f'ключ: {required_key}'
                else:
                    sub = 'обычная'
                    
                door_items.append({
                    'symbol': symbol,
                    'surface': surf,
                    'label': symbol,
                    'sub': sub
                })
        if door_items:
            door_items.sort(key=lambda x: x['label'])
            self.groups.append({
                'id': 'doors',
                'label': '🚪 ДВЕРИ',
                'items': door_items,
                'collapsed': False
            })
        
        # =============================================
        # 3. ОБЪЕКТЫ (спавн, выход, пол)
        # =============================================
        object_items = []
        
        # Спавн
        for symbol, config in SYMBOLS_CONFIG.items():
            if config.get('type') == 'player_spawn':
                surf = self._create_surface(symbol, (120, 100, 0))
                object_items.append({
                    'symbol': symbol,
                    'surface': surf,
                    'label': symbol,
                    'sub': 'старт'
                })
        
        # Выход
        for symbol, config in SYMBOLS_CONFIG.items():
            if config.get('type') == 'exit':
                surf = self._create_surface(symbol, (0, 100, 0))
                object_items.append({
                    'symbol': symbol,
                    'surface': surf,
                    'label': symbol,
                    'sub': 'выход'
                })
        
        # Пол (пустота)
        surf = self._create_surface('_', (20, 20, 25))
        object_items.append({
            'symbol': '_',
            'surface': surf,
            'label': '_',
            'sub': 'пустота'
        })
        
        if object_items:
            self.groups.append({
                'id': 'objects',
                'label': '📦 ОБЪЕКТЫ',
                'items': object_items,
                'collapsed': False
            })
        
        # =============================================
        # 4. ПРЕДМЕТЫ
        # =============================================
        item_items = []
        for symbol, config in SYMBOLS_CONFIG.items():
            if config.get('type') == 'item':
                surf = self._load_texture_or_color(symbol)
                item_type = config.get('item_type', '')
                
                if item_type == 'health':
                    sub = f'аптечка +{config.get("amount", 25)} HP'
                elif item_type == 'armor':
                    sub = f'броня +{config.get("amount", 25)}'
                elif config.get('weapon_name'):
                    weapon_name = config.get('weapon_name')
                    ammo = config.get('ammo', 0)
                    sub = f'{weapon_name} +{ammo}'
                elif config.get('key_color'):
                    sub = f'ключ {config.get("key_color")}'
                else:
                    sub = 'предмет'
                    
                item_items.append({
                    'symbol': symbol,
                    'surface': surf,
                    'label': symbol,
                    'sub': sub
                })
        if item_items:
            item_items.sort(key=lambda x: x['label'])
            self.groups.append({
                'id': 'items',
                'label': '💊 ПРЕДМЕТЫ',
                'items': item_items,
                'collapsed': False
            })
        
        # =============================================
        # 5. NPC
        # =============================================
        npc_items = []
        for symbol, config in NPC_CONFIG.items():
            name = config.get('name', 'unknown')
            surf = self._load_npc_sprite(name)
            if surf is None:
                surf = self._create_surface(symbol, (100, 0, 0))
            
            is_boss = config.get('class_name') == 'Boss'
            sub = f'{name} {"(БОСС)" if is_boss else ""}'
            
            npc_items.append({
                'symbol': symbol,
                'surface': surf,
                'label': symbol,
                'sub': sub
            })
        if npc_items:
            npc_items.sort(key=lambda x: x['label'])
            self.groups.append({
                'id': 'npc',
                'label': '👾 NPC',
                'items': npc_items,
                'collapsed': False
            })
        
        # Всего объектов
        total_items = sum(len(g['items']) for g in self.groups)
        print(f"[Toolbar] Загружено {len(self.groups)} групп, {total_items} объектов")

    def _load_texture_or_color(self, symbol):
        """Загружает текстуру или создаёт цветной квадрат"""
        config = SYMBOLS_CONFIG.get(symbol, {})
        texture_path = config.get('texture') or config.get('sprite')

        if texture_path:
            full_path = os.path.join(ROOT_DIR, texture_path)
            if os.path.exists(full_path):
                try:
                    surf = pygame.image.load(full_path).convert_alpha()
                    size = 34
                    return pygame.transform.scale(surf, (size, size))
                except:
                    pass

        # Fallback: цвет
        color = SYMBOL_COLORS.get(symbol, (60, 60, 70))
        return self._create_surface(symbol, color)

    def _load_npc_sprite(self, name):
        """Загружает спрайт NPC"""
        try:
            # Новая система: name_move_front_1.png
            path = os.path.join(NPC_DIR, name, f"{name}_move_front_1.png")
            if os.path.exists(path):
                surf = pygame.image.load(path).convert_alpha()
                size = 34
                return pygame.transform.scale(surf, (size, size))

            # Старая система: name_idle_front.png
            path_old = os.path.join(NPC_DIR, name, f"{name}_idle_front.png")
            if os.path.exists(path_old):
                surf = pygame.image.load(path_old).convert_alpha()
                size = 34
                return pygame.transform.scale(surf, (size, size))
        except:
            pass
        return None

    def _create_surface(self, symbol, color):
        """Создаёт поверхность с символом"""
        size = 34
        surf = pygame.Surface((size, size))
        surf.fill(color)
        pygame.draw.rect(surf, (80, 80, 90), surf.get_rect(), 1)
        
        font = pygame.font.Font(None, 22)
        text = font.render(symbol, True, (255, 255, 255))
        text_rect = text.get_rect(center=surf.get_rect().center)
        surf.blit(text, text_rect)
        return surf

    def get_selected_symbol(self):
        """Возвращает выбранный символ"""
        return self.selected_symbol

    def handle_click(self, mouse_x, mouse_y):
        """Обрабатывает клик по панели"""
        if not self.rect.collidepoint(mouse_x, mouse_y):
            return False

        rel_y = mouse_y - self.rect.y - self.top_padding + self.scroll_offset
        current_y = 0
        group_header_height = 28
        item_spacing = 4
        item_size = 40  # Размер иконки в сетке
        
        # Проходим по группам
        for group in self.groups:
            # Заголовок группы
            header_rect = pygame.Rect(
                self.rect.x + 5,
                self.rect.y + self.top_padding + current_y - self.scroll_offset,
                self.rect.width - 10,
                group_header_height
            )
            
            # Проверяем клик по заголовку
            if header_rect.collidepoint(mouse_x, mouse_y):
                # Переключаем состояние группы
                if group['id'] in self.collapsed_groups:
                    self.collapsed_groups.remove(group['id'])
                else:
                    self.collapsed_groups.add(group['id'])
                return True
            
            # Если группа свёрнута - пропускаем её содержимое
            if group['id'] in self.collapsed_groups:
                current_y += group_header_height + 2
                continue
            
            # Отображаем элементы группы в сетке
            items = group['items']
            cols = self.columns
            rows = (len(items) + cols - 1) // cols
            
            for row in range(rows):
                for col in range(cols):
                    idx = row * cols + col
                    if idx >= len(items):
                        break
                    
                    item_rect = pygame.Rect(
                        self.rect.x + 5 + col * (item_size + item_spacing),
                        self.rect.y + self.top_padding + current_y + group_header_height + row * (item_size + item_spacing) - self.scroll_offset,
                        item_size,
                        item_size
                    )
                    
                    if item_rect.collidepoint(mouse_x, mouse_y):
                        self.selected_symbol = items[idx]['symbol']
                        print(f"[Toolbar] Выбран объект: '{self.selected_symbol}'")
                        return True
            
            # Переходим к следующей группе
            current_y += group_header_height + rows * (item_size + item_spacing) + 8
        
        return False

    def scroll(self, delta):
        """Прокрутка панели"""
        total_height = self._get_total_height()
        max_scroll = max(0, total_height - self.rect.height + 10)
        self.scroll_offset = max(0, min(max_scroll, self.scroll_offset + delta))

    def _get_total_height(self):
        """Вычисляет общую высоту всех групп"""
        total = 0
        group_header_height = 28
        item_size = 40
        item_spacing = 4
        cols = self.columns
        
        for group in self.groups:
            total += group_header_height + 2
            
            if group['id'] not in self.collapsed_groups:
                items = group['items']
                rows = (len(items) + cols - 1) // cols
                total += rows * (item_size + item_spacing) + 4
        
        return total + self.top_padding

    def draw(self, screen):
        """Отрисовывает панель с группами"""
        # Фон панели
        pygame.draw.rect(screen, COLORS['panel_bg'], self.rect)
        pygame.draw.rect(screen, COLORS['panel_border'], self.rect, 1)
        
        # Заголовок
        font_title = pygame.font.Font(None, 16)
        title = font_title.render("ОБЪЕКТЫ", True, (240, 240, 240))
        screen.blit(title, (self.rect.x + 10, self.rect.y + 5))
        
        # Счётчик объектов
        total_items = sum(len(g['items']) for g in self.groups)
        font_count = pygame.font.Font(None, 11)
        count_text = font_count.render(f"{total_items} объектов", True, (140, 140, 140))
        screen.blit(count_text, (self.rect.x + 10, self.rect.y + 22))
        
        # Рисуем группы
        y = self.rect.y + self.top_padding - self.scroll_offset
        group_header_height = 28
        item_size = 40
        item_spacing = 4
        cols = self.columns
        
        font_header = pygame.font.Font(None, 14)
        font_label = pygame.font.Font(None, 15)
        font_sub = pygame.font.Font(None, 11)
        
        for group in self.groups:
            # Заголовок группы
            header_rect = pygame.Rect(
                self.rect.x + 5,
                y,
                self.rect.width - 10,
                group_header_height
            )
            
            # Пропускаем, если вне области видимости
            if y + group_header_height > self.rect.y and y < self.rect.bottom:
                # Фон заголовка
                header_color = (55, 55, 70) if group['id'] not in self.collapsed_groups else (50, 50, 55)
                pygame.draw.rect(screen, header_color, header_rect)
                pygame.draw.rect(screen, (70, 70, 80), header_rect, 1)
                
                # Иконка раскрытия
                icon = "▼" if group['id'] not in self.collapsed_groups else "▶"
                text_icon = font_header.render(icon, True, (200, 200, 200))
                screen.blit(text_icon, (header_rect.x + 5, header_rect.y + 6))
                
                # Название группы
                text_header = font_header.render(group['label'], True, (220, 220, 240))
                screen.blit(text_header, (header_rect.x + 25, header_rect.y + 6))
                
                # Количество элементов в группе
                count_text = font_sub.render(f"({len(group['items'])})", True, (140, 140, 150))
                screen.blit(count_text, (header_rect.right - 40, header_rect.y + 8))
            
            y += group_header_height + 2
            
            # Если группа свёрнута - пропускаем её содержимое
            if group['id'] in self.collapsed_groups:
                y += 2
                continue
            
            # Рисуем элементы группы в сетке
            items = group['items']
            rows = (len(items) + cols - 1) // cols
            
            for row in range(rows):
                row_y = y + row * (item_size + item_spacing)
                
                # Пропускаем строки вне области видимости
                if row_y > self.rect.bottom:
                    break
                if row_y + item_size < self.rect.y:
                    continue
                
                for col in range(cols):
                    idx = row * cols + col
                    if idx >= len(items):
                        break
                    
                    item = items[idx]
                    item_rect = pygame.Rect(
                        self.rect.x + 5 + col * (item_size + item_spacing),
                        row_y,
                        item_size,
                        item_size
                    )
                    
                    # Проверяем видимость
                    if item_rect.bottom < self.rect.y or item_rect.top > self.rect.bottom:
                        continue
                    
                    # Фон элемента
                    is_selected = (item['symbol'] == self.selected_symbol)
                    if is_selected:
                        pygame.draw.rect(screen, (80, 80, 160), item_rect)
                    else:
                        pygame.draw.rect(screen, (45, 45, 50), item_rect)
                    
                    pygame.draw.rect(screen, (60, 60, 70), item_rect, 1)
                    
                    # Иконка
                    if item['surface']:
                        icon_rect = item['surface'].get_rect(center=item_rect.center)
                        screen.blit(item['surface'], icon_rect)
                    
                    # Символ под иконкой (если есть место)
                    if item_size > 35:
                        text = font_label.render(item['label'], True, (200, 200, 200))
                        text_rect = text.get_rect(centerx=item_rect.centerx, top=item_rect.bottom + 2)
                        screen.blit(text, text_rect)
            
            y += rows * (item_size + item_spacing) + 4
        
        # Полоса прокрутки
        total_height = self._get_total_height()
        if total_height > self.rect.height:
            bar_height = max(20, int(self.rect.height * (self.rect.height / total_height)))
            scroll_ratio = self.scroll_offset / (total_height - self.rect.height)
            bar_y = self.rect.y + int((self.rect.height - bar_height) * scroll_ratio)
            pygame.draw.rect(screen, (120, 120, 140), (self.rect.right - 10, bar_y, 6, bar_height))