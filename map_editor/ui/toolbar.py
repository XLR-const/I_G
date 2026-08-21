# map_editor/ui/toolbar.py
"""Панель объектов - с группами (аккордеон) и поддержкой эмодзи"""

import os
import pygame
from ..config import COLORS, SYMBOL_COLORS, TEXTURES_DIR, NPC_DIR
from config.game_data import SYMBOLS_CONFIG, NPC_CONFIG
from .fonts import font_manager

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class Toolbar:
    """Панель объектов с группами (аккордеон)"""

    def __init__(self, rect):
        self.rect = rect
        
        # ========== ДИНАМИЧЕСКИЕ РАЗМЕРЫ ==========
        self._calculate_dimensions()
        
        # ========== СОСТОЯНИЯ ==========
        self.groups = []
        self.selected_symbol = 'M'
        self.scroll_offset = 0
        self.collapsed_groups = set()
        self.hovered_item = None
        self.hovered_rect = None
        self.tooltip_text = ""
        
        self._build_groups()
        
    def _calculate_dimensions(self):
        """Вычисляет все размеры динамически"""
        self.top_padding = max(25, int(self.rect.height * 0.035))
        self.side_padding = max(4, int(self.rect.width * 0.015))
        
        self.group_header_height = max(22, int(self.rect.height * 0.03))
        self.item_size = max(28, int(min(self.rect.width * 0.18, self.rect.height * 0.07)))
        self.item_spacing = max(2, int(self.item_size * 0.08))
        
        available_width = self.rect.width - self.side_padding * 2
        self.cols = max(2, int(available_width / (self.item_size + self.item_spacing)))
        
        self.font_sizes = {
            'header': max(11, int(self.rect.height * 0.018)),
            'count': max(9, int(self.rect.height * 0.015)),
            'tooltip': max(12, int(self.rect.height * 0.018)),
            'icon': max(16, int(self.rect.height * 0.025)),
            'label': max(9, int(self.rect.height * 0.015)),
            'category': max(10, int(self.rect.height * 0.016)),
        }
    
    def _scale_image(self, surface, target_size):
        """
        Масштабирует изображение с сохранением пропорций
        """
        if surface is None:
            return None
        
        target_width, target_height = target_size
        orig_width, orig_height = surface.get_size()
        
        # Если размеры совпадают
        if orig_width == target_width and orig_height == target_height:
            return surface.copy()
        
        # Проверяем, что размеры валидны
        if orig_width == 0 or orig_height == 0:
            return surface
        
        # Вычисляем коэффициент масштабирования
        # Используем min, чтобы вписать в контейнер
        scale_x = target_width / orig_width
        scale_y = target_height / orig_height
        scale = min(scale_x, scale_y) * 0.85  # 85% от размера контейнера
        
        new_width = max(4, int(orig_width * scale))
        new_height = max(4, int(orig_height * scale))
        
        # Создаем поверхность с прозрачным фоном
        result = pygame.Surface((target_width, target_height), pygame.SRCALPHA)
        result.fill((0, 0, 0, 0))  # Прозрачный фон
        
        try:
            # Используем smoothscale для лучшего качества
            scaled = pygame.transform.smoothscale(surface, (new_width, new_height))
            # Центрируем
            x = (target_width - new_width) // 2
            y = (target_height - new_height) // 2
            result.blit(scaled, (x, y))
        except:
            # Fallback
            result.blit(surface, (target_width // 2 - orig_width // 2,
                                target_height // 2 - orig_height // 2))
        
        return result
        
    def _get_font(self, size_key, bold=False, emoji=False):
        """Возвращает шрифт через менеджер"""
        size = self.font_sizes.get(size_key, 14)
        return font_manager.get_font(size, bold=bold, emoji=emoji)
    
    def _shorten_name(self, name):
        """Сокращает длинные имена для отображения"""
        name = str(name)
        if len(name) > 10:
            return name[:8] + '…'
        return name
    
    def _build_groups(self):
        """Строит группы объектов из конфигов - полностью динамически"""
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
                    'label': self._shorten_name(symbol),
                    'sub': 'стена',
                    'type': 'wall',
                    'full_info': self._get_item_info(symbol, config)
                })
        if wall_items:
            wall_items.sort(key=lambda x: str(x['symbol']))
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
                    'label': self._shorten_name(symbol),
                    'sub': sub,
                    'type': 'door',
                    'full_info': self._get_item_info(symbol, config)
                })
        if door_items:
            door_items.sort(key=lambda x: str(x['symbol']))
            self.groups.append({
                'id': 'doors',
                'label': 'ДВЕРИ',
                'items': door_items,
                'collapsed': False,
                'emoji': '🚪'
            })
        
        # =============================================
        # 3. ОБЪЕКТЫ (спавн, выход, пол)
        # =============================================
        object_items = []
        
        for symbol, config in SYMBOLS_CONFIG.items():
            if config.get('type') == 'player_spawn':
                surf = self._create_surface('S', (120, 100, 0), self.item_size)
                object_items.append({
                    'symbol': symbol,
                    'surface': surf,
                    'label': self._shorten_name(symbol),
                    'sub': 'старт',
                    'type': 'object',
                    'full_info': 'Стартовая позиция игрока'
                })
            elif config.get('type') == 'exit':
                surf = self._create_surface('E', (0, 100, 0), self.item_size)
                object_items.append({
                    'symbol': symbol,
                    'surface': surf,
                    'label': self._shorten_name(symbol),
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
        # 4. ОРУЖИЕ
        # =============================================
        weapon_items = []
        for symbol, config in SYMBOLS_CONFIG.items():
            if config.get('type') == 'item' and config.get('item_type') == 'weapon':
                surf = self._load_texture_or_color(symbol, self.item_size)
                weapon_name = config.get('weapon_name', 'Оружие')
                ammo = config.get('ammo', 0)
                
                weapon_items.append({
                    'symbol': symbol,
                    'surface': surf,
                    'label': self._shorten_name(symbol),
                    'sub': f'{weapon_name} (+{ammo})',
                    'type': 'weapon',
                    'full_info': self._get_item_info(symbol, config)
                })
        if weapon_items:
            weapon_items.sort(key=lambda x: x['sub'])
            self.groups.append({
                'id': 'weapons',
                'label': 'ОРУЖИЕ',
                'items': weapon_items,
                'collapsed': False,
                'emoji': '🔫'
            })
        
        # =============================================
        # 5. КЛЮЧИ
        # =============================================
        key_items = []
        for symbol, config in SYMBOLS_CONFIG.items():
            if config.get('type') == 'item' and config.get('item_type') == 'key':
                surf = self._load_texture_or_color(symbol, self.item_size)
                key_color = config.get('key_color', 'неизвестный')
                
                # Эмодзи для цвета ключа
                color_emoji = {
                    'red': '🔴', 'blue': '🔵', 'yellow': '🟡',
                    'green': '🟢', 'purple': '🟣', 'orange': '🟠',
                }.get(key_color, '🔑')
                
                key_items.append({
                    'symbol': symbol,
                    'surface': surf,
                    'label': self._shorten_name(symbol),
                    'sub': f'{color_emoji} Ключ: {key_color}',
                    'type': 'key',
                    'full_info': self._get_item_info(symbol, config)
                })
        if key_items:
            key_items.sort(key=lambda x: x['sub'])
            self.groups.append({
                'id': 'keys',
                'label': 'КЛЮЧИ',
                'items': key_items,
                'collapsed': False,
                'emoji': '🔑'
            })
        
        # =============================================
        # 6. ДЕКОР
        # =============================================
        decor_items = []
        for symbol, config in SYMBOLS_CONFIG.items():
            if config.get('type') == 'item' and config.get('item_type') == 'decor':
                surf = self._load_texture_or_color(symbol, self.item_size)
                desc = config.get('desc', config.get('description', 'Объект декора'))
                
                decor_items.append({
                    'symbol': symbol,
                    'surface': surf,
                    'label': self._shorten_name(symbol),
                    'sub': desc,
                    'type': 'decor',
                    'full_info': self._get_item_info(symbol, config)
                })
        if decor_items:
            decor_items.sort(key=lambda x: x['sub'])
            self.groups.append({
                'id': 'decor',
                'label': 'ДЕКОР',
                'items': decor_items,
                'collapsed': False,
                'emoji': '🪑'
            })
        
        # =============================================
        # 7. РАСХОДНИКИ (health, armor)
        # =============================================
        consumable_items = []
        for symbol, config in SYMBOLS_CONFIG.items():
            if config.get('type') == 'item' and config.get('item_type') in ['health', 'armor']:
                surf = self._load_texture_or_color(symbol, self.item_size)
                item_type = config.get('item_type')
                amount = config.get('amount', 0)
                
                if item_type == 'health':
                    sub = f'❤️ Аптечка +{amount} HP'
                else:
                    sub = f'🛡️ Броня +{amount}'
                
                consumable_items.append({
                    'symbol': symbol,
                    'surface': surf,
                    'label': self._shorten_name(symbol),
                    'sub': sub,
                    'type': 'consumable',
                    'full_info': self._get_item_info(symbol, config)
                })
        if consumable_items:
            self.groups.append({
                'id': 'consumables',
                'label': 'РАСХОДНИКИ',
                'items': consumable_items,
                'collapsed': False,
                'emoji': '💊'
            })
        
        # =============================================
        # 8. NPC
        # =============================================
        npc_items = []
        for symbol, config in NPC_CONFIG.items():
            name = config.get('name', 'unknown')
            surf = self._load_npc_sprite(name, self.item_size)
            if surf is None:
                surf = self._create_surface(symbol, (100, 0, 0), self.item_size)
            
            is_boss = config.get('class_name') == 'Boss'
            sub = f'{name} {"👑" if is_boss else ""}'
            
            npc_items.append({
                'symbol': symbol,
                'surface': surf,
                'label': self._shorten_name(symbol),
                'sub': sub,
                'type': 'npc',
                'full_info': self._get_npc_info(symbol, config)
            })
        if npc_items:
            npc_items.sort(key=lambda x: x['sub'])
            self.groups.append({
                'id': 'npc',
                'label': 'NPC',
                'items': npc_items,
                'collapsed': False,
                'emoji': '👾'
            })
        
        # =============================================
        # 9. ПРОЧЕЕ (fallback)
        # =============================================
        other_items = []
        for symbol, config in SYMBOLS_CONFIG.items():
            # Пропускаем уже обработанные
            if config.get('type') in ['wall', 'door', 'player_spawn', 'exit']:
                continue
            if config.get('type') == 'item' and config.get('item_type') in ['weapon', 'key', 'decor', 'health', 'armor']:
                continue
            
            surf = self._load_texture_or_color(symbol, self.item_size)
            other_items.append({
                'symbol': symbol,
                'surface': surf,
                'label': self._shorten_name(symbol),
                'sub': config.get('desc', config.get('description', 'объект')),
                'type': 'other',
                'full_info': self._get_item_info(symbol, config)
            })
        
        if other_items:
            other_items.sort(key=lambda x: str(x['symbol']))
            self.groups.append({
                'id': 'other',
                'label': 'ПРОЧЕЕ',
                'items': other_items,
                'collapsed': True,
                'emoji': '📌'
            })
        
        total_items = sum(len(g['items']) for g in self.groups)
        print(f"[Toolbar] Загружено {len(self.groups)} групп, {total_items} объектов")
        for group in self.groups:
            print(f"  {group['emoji']} {group['label']}: {len(group['items'])} объектов")
    
    def _get_item_info(self, symbol, config):
        """Формирует подробную информацию об объекте"""
        item_type = config.get('type', '')
        item_subtype = config.get('item_type', '')
        info_lines = []
        
        if item_type == 'wall':
            info_lines.append(f"🧱 Стена: {symbol}")
            if config.get('breakable'):
                info_lines.append("💥 Разрушаемая")
        
        elif item_type == 'door':
            door_type = config.get('door_type', 'обычная')
            type_map = {
                'normal': '🚪 Обычная',
                'secret': '🕵️ Секретная',
                'locked': '🔒 Запертая',
            }
            info_lines.append(type_map.get(door_type, f'Дверь: {door_type}'))
            if config.get('required_key'):
                info_lines.append(f"🔑 Требуется ключ: {config['required_key']}")
        
        elif item_type == 'item':
            if item_subtype == 'weapon':
                weapon_name = config.get('weapon_name', 'Оружие')
                info_lines.append(f"🔫 {weapon_name}")
                if config.get('ammo'):
                    info_lines.append(f"💥 Патроны: +{config['ammo']}")
                if config.get('damage'):
                    info_lines.append(f"💢 Урон: {config['damage']}")
            
            elif item_subtype == 'key':
                key_color = config.get('key_color', 'неизвестный')
                color_emoji = {'red': '🔴', 'blue': '🔵', 'yellow': '🟡'}.get(key_color, '🔑')
                info_lines.append(f"{color_emoji} Ключ: {key_color}")
            
            elif item_subtype == 'decor':
                desc = config.get('desc', 'Объект декора')
                info_lines.append(f"🪑 {desc}")
                if config.get('ammo'):
                    info_lines.append(f"💪 Прочность: {config['ammo']}")
            
            elif item_subtype == 'health':
                amount = config.get('amount', 25)
                info_lines.append(f"❤️ Аптечка")
                info_lines.append(f"🔄 Восстанавливает: +{amount} HP")
            
            elif item_subtype == 'armor':
                amount = config.get('amount', 25)
                info_lines.append(f"🛡️ Броня")
                info_lines.append(f"🔄 Защита: +{amount}")
        
        elif item_type == 'exit':
            info_lines.append("🚪 Выход с уровня")
        
        elif item_type == 'player_spawn':
            info_lines.append("🎯 Стартовая позиция")
        
        return "\n".join(info_lines) if info_lines else f"Объект: {symbol}"
    
    def _get_npc_info(self, symbol, config):
        """Формирует информацию об NPC"""
        info_lines = []
        name = config.get('name', 'NPC')
        info_lines.append(f"👾 {name}")
        
        if config.get('class_name'):
            info_lines.append(f"📋 Класс: {config['class_name']}")
        if config.get('hp'):
            info_lines.append(f"❤️ HP: {config['hp']}")
        if config.get('damage'):
            info_lines.append(f"💢 Урон: {config['damage']}")
        if config.get('speed'):
            info_lines.append(f"💨 Скорость: {config['speed']}")
        if config.get('shoot_range'):
            info_lines.append(f"🎯 Дальность: {config['shoot_range']}")
        
        return "\n".join(info_lines) if info_lines else "NPC"
    
    def _load_texture_or_color(self, symbol, size):
        config = SYMBOLS_CONFIG.get(symbol, {})
        texture_path = config.get('texture') or config.get('sprite')

        if texture_path:
            full_path = os.path.join(ROOT_DIR, texture_path)
            if os.path.exists(full_path):
                try:
                    surf = pygame.image.load(full_path).convert_alpha()
                    return self._scale_image(surf, (size, size))
                except:
                    pass

        color = SYMBOL_COLORS.get(symbol, (60, 60, 70))
        return self._create_surface(symbol, color, size)

    def _load_npc_sprite(self, name, size):
        try:
            path = os.path.join(NPC_DIR, name, f"{name}_move_front_1.png")
            if os.path.exists(path):
                surf = pygame.image.load(path).convert_alpha()
                return self._scale_image(surf, (size, size))

            path_old = os.path.join(NPC_DIR, name, f"{name}_idle_front.png")
            if os.path.exists(path_old):
                surf = pygame.image.load(path_old).convert_alpha()
                return self._scale_image(surf, (size, size))
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
        font = font_manager.get_font(font_size, bold=True)
        text = font.render(str(symbol)[:2], True, (255, 255, 255))
        text_rect = text.get_rect(center=surf.get_rect().center)
        surf.blit(text, text_rect)
        return surf

    def get_selected_symbol(self):
        return self.selected_symbol

    def handle_click(self, mouse_x, mouse_y):
        """Обрабатывает клик по панели"""
        if not self.rect.collidepoint(mouse_x, mouse_y):
            return False

        self.hovered_item = None
        self.hovered_rect = None
        self.tooltip_text = ""

        header_h = self.group_header_height
        item_size = self.item_size
        spacing = self.item_spacing
        cols = self.cols
        
        current_y = 0
        
        for group_idx, group in enumerate(self.groups):
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
        """Отрисовывает панель с иконками и эмодзи"""
        pygame.draw.rect(screen, COLORS['panel_bg'], self.rect)
        pygame.draw.rect(screen, COLORS['panel_border'], self.rect, 1)
        
        # Заголовок
        font_header = self._get_font('header', bold=True, emoji=True)
        font_count = self._get_font('count', emoji=True)
        
        title_y = self.rect.y + int(self.rect.height * 0.01)
        title = font_header.render("ОБЪЕКТЫ", True, (240, 240, 240))
        screen.blit(title, (self.rect.x + self.side_padding, title_y))
        
        total_items = sum(len(g['items']) for g in self.groups)
        count_text = font_count.render(str(total_items), True, (140, 140, 140))
        count_x = self.rect.right - count_text.get_width() - self.side_padding
        screen.blit(count_text, (count_x, title_y + 2))
        
        y = self.rect.y + self.top_padding - self.scroll_offset
        
        font_icon = self._get_font('icon', emoji=True)
        font_category = self._get_font('category', bold=True, emoji=True)
        font_label = self._get_font('label', emoji=True)
        font_tooltip = self._get_font('tooltip', emoji=True)
        
        for group_idx, group in enumerate(self.groups):
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
                
                # Эмодзи категории
                emoji_text = font_category.render(group['emoji'], True, (220, 220, 240))
                emoji_x = icon_x + text_icon.get_width() + 4
                emoji_y = header_rect.y + (self.group_header_height - emoji_text.get_height()) // 2
                screen.blit(emoji_text, (emoji_x, emoji_y))
                
                # Название категории
                label_x = emoji_x + emoji_text.get_width() + 4
                text_header = font_category.render(group['label'], True, (220, 220, 240))
                text_y = header_rect.y + (self.group_header_height - text_header.get_height()) // 2
                screen.blit(text_header, (label_x, text_y))
                
                # Количество
                count_text = font_count.render(f"({len(group['items'])})", True, (140, 140, 150))
                count_x = header_rect.right - count_text.get_width() - 4
                count_y = header_rect.y + (self.group_header_height - count_text.get_height()) // 2
                screen.blit(count_text, (count_x, count_y))
            
            y += self.group_header_height + 2
            
            if group['id'] in self.collapsed_groups:
                y += 2
                continue
            
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
                    
                    is_hovered = (self.hovered_item and 
                                 self.hovered_item[0] == group_idx and 
                                 self.hovered_item[1] == idx)
                    is_selected = (item['symbol'] == self.selected_symbol)
                    
                    if is_selected:
                        bg_color = (70, 70, 140)
                    elif is_hovered:
                        bg_color = (60, 60, 90)
                    else:
                        bg_color = (40, 40, 45)
                    
                    pygame.draw.rect(screen, bg_color, item_rect)
                    
                    border_color = (120, 120, 180) if is_hovered else (60, 60, 70)
                    if is_selected:
                        border_color = (150, 150, 255)
                    
                    border_width = 2 if (is_hovered or is_selected) else 1
                    pygame.draw.rect(screen, border_color, item_rect, border_width)
                    
                    if is_selected:
                        inner_rect = item_rect.inflate(-4, -4)
                        pygame.draw.rect(screen, (100, 100, 200), inner_rect, 1)
                    
                    if item['surface']:
                        icon_rect = item['surface'].get_rect(center=item_rect.center)
                        screen.blit(item['surface'], icon_rect)
            
            y += rows * (self.item_size + self.item_spacing) + 4
        
        # Полоса прокрутки
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
        
        # Всплывающая подсказка
        if self.hovered_item and self.hovered_rect and self.tooltip_text:
            self._draw_tooltip(screen, font_tooltip)
    
    def _draw_tooltip(self, screen, font):
        """Рисует всплывающую подсказку с поддержкой эмодзи"""
        lines = self.tooltip_text.split('\n')
        
        max_width = 0
        line_surfaces = []
        for line in lines:
            surf = font.render(line, True, (240, 240, 240))
            line_surfaces.append(surf)
            max_width = max(max_width, surf.get_width())
        
        padding = 8
        tooltip_width = max_width + padding * 2
        tooltip_height = len(lines) * (font.get_height() + 2) + padding * 2
        
        tooltip_x = self.hovered_rect.right + 5
        tooltip_y = self.hovered_rect.centery - tooltip_height // 2
        
        if tooltip_x + tooltip_width > self.rect.right:
            tooltip_x = self.hovered_rect.left - tooltip_width - 5
        
        if tooltip_y < self.rect.top:
            tooltip_y = self.rect.top + 5
        if tooltip_y + tooltip_height > self.rect.bottom:
            tooltip_y = self.rect.bottom - tooltip_height - 5
        
        tooltip_rect = pygame.Rect(tooltip_x, tooltip_y, tooltip_width, tooltip_height)
        
        pygame.draw.rect(screen, (30, 30, 40), tooltip_rect)
        pygame.draw.rect(screen, (80, 80, 100), tooltip_rect, 1)
        
        y_offset = tooltip_rect.y + padding
        for surf in line_surfaces:
            x_offset = tooltip_rect.x + padding
            screen.blit(surf, (x_offset, y_offset))
            y_offset += font.get_height() + 2