# map_editor/ui/toolbar.py
"""Панель объектов - иконки с всплывающими подсказками"""

import os
import pygame
from ..config import COLORS, SYMBOL_COLORS, TEXTURES_DIR, NPC_DIR
from config.game_data import SYMBOLS_CONFIG, NPC_CONFIG

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class Toolbar:
    """Панель объектов с иконками и tooltip'ами"""

    def __init__(self, rect):
        self.rect = rect
        
        # ========== ДИНАМИЧЕСКИЕ РАЗМЕРЫ ==========
        self._calculate_dimensions()
        
        # ========== СОСТОЯНИЯ ==========
        self.groups = []
        self.selected_symbol = 'M'
        self.scroll_offset = 0
        self.collapsed_groups = set()
        
        # Для подсветки и тултипов
        self.hovered_item = None  # (group_index, item_index)
        self.hovered_rect = None
        self.tooltip_text = ""
        self.tooltip_rect = None
        
        self._build_groups()
        
    def _calculate_dimensions(self):
        """Вычисляет все размеры динамически"""
        # Паддинги
        self.top_padding = max(25, int(self.rect.height * 0.035))
        self.side_padding = max(4, int(self.rect.width * 0.015))
        
        # Размеры элементов
        self.group_header_height = max(22, int(self.rect.height * 0.03))
        self.item_size = max(28, int(min(self.rect.width * 0.18, self.rect.height * 0.07)))
        self.item_spacing = max(2, int(self.item_size * 0.08))
        
        # Количество колонок
        available_width = self.rect.width - self.side_padding * 2
        self.cols = max(2, int(available_width / (self.item_size + self.item_spacing)))
        
        # Размеры шрифтов
        self.font_sizes = {
            'header': max(11, int(self.rect.height * 0.018)),
            'count': max(9, int(self.rect.height * 0.015)),
            'tooltip': max(13, int(self.rect.height * 0.02)),
            'icon': max(14, int(self.rect.height * 0.022)),
            'emoji': max(14, int(self.rect.height * 0.022)),
        }
        
        # Цвета для разных типов
        self.border_colors = {
            'wall': (100, 100, 120),
            'door': (150, 120, 80),
            'item': (80, 150, 80),
            'npc': (150, 80, 150),
            'object': (120, 120, 80),
            'default': (70, 70, 80),
        }
        
    def _get_font(self, size_key):
        """Возвращает шрифт нужного размера с кэшированием"""
        if not hasattr(self, '_font_cache'):
            self._font_cache = {}
        
        size = self.font_sizes.get(size_key, 14)
        if size not in self._font_cache:
            self._font_cache[size] = pygame.font.Font(None, size)
        return self._font_cache[size]
        
    def _build_groups(self):
        """Строит группы объектов из конфигов"""
        self.groups = []
        
        # =============================================
        # 1. СТЕНЫ
        # =============================================
        wall_items = []
        for symbol, config in SYMBOLS_CONFIG.items():
            if config.get('type') == 'wall':
                surf = self._load_texture_or_color(symbol, self.item_size)
                wall_items.append({
                    'symbol': symbol,
                    'surface': surf,
                    'label': symbol,
                    'sub': 'стена',
                    'type': 'wall',
                    'full_info': self._get_item_info(symbol, config)
                })
        if wall_items:
            wall_items.sort(key=lambda x: x['label'])
            self.groups.append({
                'id': 'walls',
                'label': 'СТЕНЫ',
                'items': wall_items,
                'collapsed': False,
                'emoji': '🧱'
            })
        
        # =============================================
        # 2. ДВЕРИ
        # =============================================
        door_items = []
        for symbol, config in SYMBOLS_CONFIG.items():
            if config.get('type') == 'door':
                surf = self._load_texture_or_color(symbol, self.item_size)
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
                    'sub': sub,
                    'type': 'door',
                    'full_info': self._get_item_info(symbol, config)
                })
        if door_items:
            door_items.sort(key=lambda x: x['label'])
            self.groups.append({
                'id': 'doors',
                'label': 'ДВЕРИ',
                'items': door_items,
                'collapsed': False,
                'emoji': '🚪'
            })
        
        # =============================================
        # 3. ОБЪЕКТЫ
        # =============================================
        object_items = []
        
        for symbol, config in SYMBOLS_CONFIG.items():
            if config.get('type') == 'player_spawn':
                surf = self._create_surface(symbol, (120, 100, 0), self.item_size)
                object_items.append({
                    'symbol': symbol,
                    'surface': surf,
                    'label': symbol,
                    'sub': 'старт',
                    'type': 'object',
                    'full_info': 'Стартовая позиция игрока'
                })
            elif config.get('type') == 'exit':
                surf = self._create_surface(symbol, (0, 100, 0), self.item_size)
                object_items.append({
                    'symbol': symbol,
                    'surface': surf,
                    'label': symbol,
                    'sub': 'выход',
                    'type': 'object',
                    'full_info': 'Выход с уровня'
                })
        
        # Пол (пустота)
        surf = self._create_surface('_', (20, 20, 25), self.item_size)
        object_items.append({
            'symbol': '_',
            'surface': surf,
            'label': '_',
            'sub': 'пустота',
            'type': 'object',
            'full_info': 'Пустая клетка (пол)'
        })
        
        if object_items:
            self.groups.append({
                'id': 'objects',
                'label': 'ОБЪЕКТЫ',
                'items': object_items,
                'collapsed': False,
                'emoji': '📦'
            })
        
        # =============================================
        # 4. ПРЕДМЕТЫ
        # =============================================
        item_items = []
        for symbol, config in SYMBOLS_CONFIG.items():
            if config.get('type') == 'item':
                surf = self._load_texture_or_color(symbol, self.item_size)
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
                    'sub': sub,
                    'type': 'item',
                    'full_info': self._get_item_info(symbol, config)
                })
        if item_items:
            item_items.sort(key=lambda x: x['label'])
            self.groups.append({
                'id': 'items',
                'label': 'ПРЕДМЕТЫ',
                'items': item_items,
                'collapsed': False,
                'emoji': '💊'
            })
        
        # =============================================
        # 5. NPC
        # =============================================
        npc_items = []
        for symbol, config in NPC_CONFIG.items():
            name = config.get('name', 'unknown')
            surf = self._load_npc_sprite(name, self.item_size)
            if surf is None:
                surf = self._create_surface(symbol, (100, 0, 0), self.item_size)
            
            is_boss = config.get('class_name') == 'Boss'
            sub = f'{name} {"(БОСС)" if is_boss else ""}'
            
            npc_items.append({
                'symbol': symbol,
                'surface': surf,
                'label': symbol,
                'sub': sub,
                'type': 'npc',
                'full_info': self._get_npc_info(symbol, config)
            })
        if npc_items:
            npc_items.sort(key=lambda x: x['label'])
            self.groups.append({
                'id': 'npc',
                'label': 'NPC',
                'items': npc_items,
                'collapsed': False,
                'emoji': '👾'
            })
        
        total_items = sum(len(g['items']) for g in self.groups)
        print(f"[Toolbar] Загружено {len(self.groups)} групп, {total_items} объектов")

    def _get_item_info(self, symbol, config):
        """Формирует подробную информацию об объекте"""
        item_type = config.get('type', '')
        info_lines = []
        
        if item_type == 'wall':
            info_lines.append(f"Стена")
            if config.get('breakable'):
                info_lines.append("Разрушаемая")
        
        elif item_type == 'door':
            door_type = config.get('door_type', 'обычная')
            info_lines.append(f"Дверь: {door_type}")
            if config.get('required_key'):
                info_lines.append(f"Требуется ключ: {config['required_key']}")
        
        elif item_type == 'item':
            if config.get('item_type') == 'health':
                info_lines.append(f"Аптечка +{config.get('amount', 25)} HP")
            elif config.get('item_type') == 'armor':
                info_lines.append(f"Броня +{config.get('amount', 25)}")
            elif config.get('weapon_name'):
                info_lines.append(f"Оружие: {config['weapon_name']}")
                if config.get('ammo'):
                    info_lines.append(f"Боеприпасы: +{config['ammo']}")
            elif config.get('key_color'):
                info_lines.append(f"Ключ: {config['key_color']}")
        
        elif item_type == 'exit':
            info_lines.append("Выход с уровня")
        
        elif item_type == 'player_spawn':
            info_lines.append("Стартовая позиция")
        
        return "\n".join(info_lines) if info_lines else "Объект"

    def _get_npc_info(self, symbol, config):
        """Формирует информацию об NPC"""
        info_lines = []
        name = config.get('name', 'NPC')
        info_lines.append(f"Имя: {name}")
        
        if config.get('class_name'):
            info_lines.append(f"Класс: {config['class_name']}")
        
        if config.get('health'):
            info_lines.append(f"HP: {config['health']}")
        
        if config.get('damage'):
            info_lines.append(f"Урон: {config['damage']}")
        
        return "\n".join(info_lines)

    def _load_texture_or_color(self, symbol, size):
        """Загружает текстуру или создаёт цветной квадрат"""
        config = SYMBOLS_CONFIG.get(symbol, {})
        texture_path = config.get('texture') or config.get('sprite')

        if texture_path:
            full_path = os.path.join(ROOT_DIR, texture_path)
            if os.path.exists(full_path):
                try:
                    surf = pygame.image.load(full_path).convert_alpha()
                    return pygame.transform.scale(surf, (size, size))
                except:
                    pass

        color = SYMBOL_COLORS.get(symbol, (60, 60, 70))
        return self._create_surface(symbol, color, size)

    def _load_npc_sprite(self, name, size):
        """Загружает спрайт NPC"""
        try:
            path = os.path.join(NPC_DIR, name, f"{name}_move_front_1.png")
            if os.path.exists(path):
                surf = pygame.image.load(path).convert_alpha()
                return pygame.transform.scale(surf, (size, size))

            path_old = os.path.join(NPC_DIR, name, f"{name}_idle_front.png")
            if os.path.exists(path_old):
                surf = pygame.image.load(path_old).convert_alpha()
                return pygame.transform.scale(surf, (size, size))
        except:
            pass
        return None

    def _create_surface(self, symbol, color, size):
        """Создаёт поверхность с символом"""
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        surf.fill((*color, 255))
        
        border_width = max(1, int(size * 0.03))
        pygame.draw.rect(surf, (80, 80, 90), surf.get_rect(), border_width)
        
        font_size = max(10, int(size * 0.6))
        font = pygame.font.Font(None, font_size)
        text = font.render(symbol, True, (255, 255, 255))
        text_rect = text.get_rect(center=surf.get_rect().center)
        surf.blit(text, text_rect)
        return surf

    def get_selected_symbol(self):
        return self.selected_symbol

    def handle_click(self, mouse_x, mouse_y):
        """Обрабатывает клик по панели"""
        if not self.rect.collidepoint(mouse_x, mouse_y):
            return False

        # Сбрасываем hover
        self.hovered_item = None
        self.hovered_rect = None
        self.tooltip_text = ""

        header_h = self.group_header_height
        item_size = self.item_size
        spacing = self.item_spacing
        cols = self.cols
        
        current_y = 0
        
        for group_idx, group in enumerate(self.groups):
            # Заголовок группы
            header_rect = pygame.Rect(
                self.rect.x + self.side_padding,
                self.rect.y + self.top_padding + current_y - self.scroll_offset,
                self.rect.width - self.side_padding * 2,
                header_h
            )
            
            if header_rect.collidepoint(mouse_x, mouse_y):
                if group['id'] in self.collapsed_groups:
                    self.collapsed_groups.remove(group['id'])
                else:
                    self.collapsed_groups.add(group['id'])
                return True
            
            if group['id'] in self.collapsed_groups:
                current_y += header_h + 2
                continue
            
            items = group['items']
            rows = (len(items) + cols - 1) // cols
            
            for row in range(rows):
                for col in range(cols):
                    idx = row * cols + col
                    if idx >= len(items):
                        break
                    
                    item_rect = pygame.Rect(
                        self.rect.x + self.side_padding + col * (item_size + spacing),
                        self.rect.y + self.top_padding + current_y + header_h + row * (item_size + spacing) - self.scroll_offset,
                        item_size,
                        item_size
                    )
                    
                    if item_rect.collidepoint(mouse_x, mouse_y):
                        self.selected_symbol = items[idx]['symbol']
                        print(f"[Toolbar] Выбран объект: '{self.selected_symbol}'")
                        return True
            
            current_y += header_h + rows * (item_size + spacing) + 4
        
        return False

    def update_hover(self, mouse_x, mouse_y):
        """Обновляет состояние наведения"""
        if not self.rect.collidepoint(mouse_x, mouse_y):
            self.hovered_item = None
            self.hovered_rect = None
            self.tooltip_text = ""
            return

        header_h = self.group_header_height
        item_size = self.item_size
        spacing = self.item_spacing
        cols = self.cols
        
        current_y = 0
        
        for group_idx, group in enumerate(self.groups):
            if group['id'] in self.collapsed_groups:
                current_y += header_h + 2
                continue
            
            items = group['items']
            rows = (len(items) + cols - 1) // cols
            
            for row in range(rows):
                for col in range(cols):
                    idx = row * cols + col
                    if idx >= len(items):
                        break
                    
                    item_rect = pygame.Rect(
                        self.rect.x + self.side_padding + col * (item_size + spacing),
                        self.rect.y + self.top_padding + current_y + header_h + row * (item_size + spacing) - self.scroll_offset,
                        item_size,
                        item_size
                    )
                    
                    if item_rect.collidepoint(mouse_x, mouse_y):
                        self.hovered_item = (group_idx, idx)
                        self.hovered_rect = item_rect.copy()
                        self.tooltip_text = items[idx]['full_info']
                        return
            
            current_y += header_h + rows * (item_size + spacing) + 4
        
        self.hovered_item = None
        self.hovered_rect = None
        self.tooltip_text = ""

    def scroll(self, delta):
        total_height = self._get_total_height()
        max_scroll = max(0, total_height - self.rect.height + 10)
        self.scroll_offset = max(0, min(max_scroll, self.scroll_offset + delta))

    def _get_total_height(self):
        total = 0
        header_h = self.group_header_height
        item_size = self.item_size
        spacing = self.item_spacing
        cols = self.cols
        
        for group in self.groups:
            total += header_h + 2
            if group['id'] not in self.collapsed_groups:
                items = group['items']
                rows = (len(items) + cols - 1) // cols
                total += rows * (item_size + spacing) + 4
        
        return total + self.top_padding

    def draw(self, screen):
        """Отрисовывает панель с иконками"""
        # Фон панели
        pygame.draw.rect(screen, COLORS['panel_bg'], self.rect)
        pygame.draw.rect(screen, COLORS['panel_border'], self.rect, 1)
        
        # ========== ЗАГОЛОВОК ==========
        font_header = self._get_font('header')
        font_count = self._get_font('count')
        
        title_y = self.rect.y + int(self.rect.height * 0.01)
        title = font_header.render("ОБЪЕКТЫ", True, (240, 240, 240))
        screen.blit(title, (self.rect.x + self.side_padding, title_y))
        
        total_items = sum(len(g['items']) for g in self.groups)
        count_text = font_count.render(f"{total_items}", True, (140, 140, 140))
        count_x = self.rect.right - count_text.get_width() - self.side_padding
        screen.blit(count_text, (count_x, title_y + 2))
        
        # ========== ГРУППЫ ==========
        y = self.rect.y + self.top_padding - self.scroll_offset
        
        font_icon = self._get_font('icon')
        font_emoji = self._get_font('emoji')
        
        for group_idx, group in enumerate(self.groups):
            # Заголовок группы
            header_rect = pygame.Rect(
                self.rect.x + self.side_padding,
                y,
                self.rect.width - self.side_padding * 2,
                self.group_header_height
            )
            
            if y + self.group_header_height > self.rect.y and y < self.rect.bottom:
                is_collapsed = group['id'] in self.collapsed_groups
                header_color = (55, 55, 70) if not is_collapsed else (50, 50, 55)
                pygame.draw.rect(screen, header_color, header_rect)
                pygame.draw.rect(screen, (70, 70, 80), header_rect, 1)
                
                # Иконка раскрытия
                icon = "▾" if not is_collapsed else "▸"
                text_icon = font_icon.render(icon, True, (200, 200, 200))
                icon_x = header_rect.x + 4
                icon_y = header_rect.y + (self.group_header_height - text_icon.get_height()) // 2
                screen.blit(text_icon, (icon_x, icon_y))
                
                # Эмодзи и название
                emoji_text = font_emoji.render(group['emoji'], True, (220, 220, 240))
                emoji_x = icon_x + text_icon.get_width() + 4
                emoji_y = header_rect.y + (self.group_header_height - emoji_text.get_height()) // 2
                screen.blit(emoji_text, (emoji_x, emoji_y))
                
                text_header = font_header.render(group['label'], True, (220, 220, 240))
                text_x = emoji_x + emoji_text.get_width() + 4
                text_y = header_rect.y + (self.group_header_height - text_header.get_height()) // 2
                screen.blit(text_header, (text_x, text_y))
                
                # Количество
                count_text = font_count.render(f"({len(group['items'])})", True, (140, 140, 150))
                count_x = header_rect.right - count_text.get_width() - 4
                count_y = header_rect.y + (self.group_header_height - count_text.get_height()) // 2
                screen.blit(count_text, (count_x, count_y))
            
            y += self.group_header_height + 2
            
            if group['id'] in self.collapsed_groups:
                y += 2
                continue
            
            # ===== ИКОНКИ В СЕТКЕ =====
            items = group['items']
            cols = self.cols
            rows = (len(items) + cols - 1) // cols
            
            for row in range(rows):
                row_y = y + row * (self.item_size + self.item_spacing)
                
                if row_y > self.rect.bottom:
                    break
                if row_y + self.item_size < self.rect.y:
                    continue
                
                for col in range(cols):
                    idx = row * cols + col
                    if idx >= len(items):
                        break
                    
                    item = items[idx]
                    item_rect = pygame.Rect(
                        self.rect.x + self.side_padding + col * (self.item_size + self.item_spacing),
                        row_y,
                        self.item_size,
                        self.item_size
                    )
                    
                    if item_rect.bottom < self.rect.y or item_rect.top > self.rect.bottom:
                        continue
                    
                    # Проверяем, наведён ли этот элемент
                    is_hovered = (self.hovered_item and 
                                 self.hovered_item[0] == group_idx and 
                                 self.hovered_item[1] == idx)
                    is_selected = (item['symbol'] == self.selected_symbol)
                    
                    # ===== ОТРИСОВКА ИКОНКИ =====
                    # Фон
                    if is_selected:
                        bg_color = (70, 70, 140)
                    elif is_hovered:
                        bg_color = (60, 60, 90)
                    else:
                        bg_color = (40, 40, 45)
                    
                    pygame.draw.rect(screen, bg_color, item_rect)
                    
                    # Рамка (подсветка при наведении)
                    border_color = (120, 120, 180) if is_hovered else (60, 60, 70)
                    if is_selected:
                        border_color = (150, 150, 255)
                    
                    border_width = 2 if (is_hovered or is_selected) else 1
                    pygame.draw.rect(screen, border_color, item_rect, border_width)
                    
                    # Двойная рамка для выбранного
                    if is_selected:
                        inner_rect = item_rect.inflate(-4, -4)
                        pygame.draw.rect(screen, (100, 100, 200), inner_rect, 1)
                    
                    # Иконка
                    if item['surface']:
                        icon_rect = item['surface'].get_rect(center=item_rect.center)
                        screen.blit(item['surface'], icon_rect)
            
            y += rows * (self.item_size + self.item_spacing) + 4
        
        # ========== ПОЛОСА ПРОКРУТКИ ==========
        total_height = self._get_total_height()
        if total_height > self.rect.height:
            scroll_bar_width = max(3, int(self.rect.width * 0.02))
            bar_height = max(20, int(self.rect.height * (self.rect.height / total_height)))
            scroll_ratio = self.scroll_offset / (total_height - self.rect.height)
            bar_y = self.rect.y + int((self.rect.height - bar_height) * scroll_ratio)
            
            bar_rect = pygame.Rect(
                self.rect.right - scroll_bar_width - 2,
                self.rect.y + 2,
                scroll_bar_width,
                self.rect.height - 4
            )
            pygame.draw.rect(screen, (40, 40, 45), bar_rect)
            pygame.draw.rect(screen, (120, 120, 140), 
                           (bar_rect.x, bar_y, scroll_bar_width, bar_height))
        
        # ========== ВСПЛЫВАЮЩАЯ ПОДСКАЗКА ==========
        if self.hovered_item and self.hovered_rect and self.tooltip_text:
            self._draw_tooltip(screen)

    def _draw_tooltip(self, screen):
        """Рисует всплывающую подсказку"""
        font = self._get_font('tooltip')
        
        # Разбиваем текст на строки
        lines = self.tooltip_text.split('\n')
        
        # Вычисляем размер тултипа
        max_width = 0
        line_surfaces = []
        for line in lines:
            surf = font.render(line, True, (240, 240, 240))
            line_surfaces.append(surf)
            max_width = max(max_width, surf.get_width())
        
        padding = 8
        tooltip_width = max_width + padding * 2
        tooltip_height = len(lines) * (font.get_height() + 2) + padding * 2
        
        # Позиционируем тултип справа от иконки
        tooltip_x = self.hovered_rect.right + 5
        tooltip_y = self.hovered_rect.centery - tooltip_height // 2
        
        # Проверяем, не вылезает ли за границы
        if tooltip_x + tooltip_width > self.rect.right:
            tooltip_x = self.hovered_rect.left - tooltip_width - 5
        
        if tooltip_y < self.rect.top:
            tooltip_y = self.rect.top + 5
        if tooltip_y + tooltip_height > self.rect.bottom:
            tooltip_y = self.rect.bottom - tooltip_height - 5
        
        tooltip_rect = pygame.Rect(tooltip_x, tooltip_y, tooltip_width, tooltip_height)
        
        # Фон тултипа
        pygame.draw.rect(screen, (30, 30, 40), tooltip_rect)
        pygame.draw.rect(screen, (80, 80, 100), tooltip_rect, 1)
        
        # Текст
        y_offset = tooltip_rect.y + padding
        for surf in line_surfaces:
            x_offset = tooltip_rect.x + padding
            screen.blit(surf, (x_offset, y_offset))
            y_offset += font.get_height() + 2