# map_editor/ui/fonts.py
"""Управление шрифтами для редактора с поддержкой эмодзи"""

import os
import pygame

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FONTS_DIR = os.path.join(ROOT_DIR, 'resources', 'fonts')

# Создаем папку если её нет
os.makedirs(FONTS_DIR, exist_ok=True)


class FontManager:
    """Менеджер шрифтов с поддержкой эмодзи"""
    
    _instance = None
    _fonts = {}
    _emoji_font = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_fonts()
        return cls._instance
    
    def _init_fonts(self):
        """Инициализирует доступные шрифты"""
        self._available_fonts = []
        self._emoji_font_path = None
        
        # 1. Ищем шрифт с эмодзи в папке resources/fonts/
        if os.path.exists(FONTS_DIR):
            for file in os.listdir(FONTS_DIR):
                if file.endswith(('.ttf', '.otf')):
                    if 'emoji' in file.lower() or 'color' in file.lower():
                        self._emoji_font_path = os.path.join(FONTS_DIR, file)
                        break
        
        # 2. Если не нашли - пробуем системные
        if self._emoji_font_path is None:
            emoji_fonts = [
                'Segoe UI Emoji',      # Windows
                'Apple Color Emoji',   # macOS
                'Noto Color Emoji',    # Linux
                'EmojiOne Color',      # Linux
                'Symbola',             # Linux fallback
            ]
            
            for font_name in emoji_fonts:
                try:
                    test_font = pygame.font.SysFont(font_name, 12)
                    test_surf = test_font.render('😀', True, (255, 255, 255))
                    if test_surf.get_width() > 0:
                        self._emoji_font_path = font_name
                        break
                except:
                    continue
        
        # 3. Если всё ещё не нашли - используем обычный шрифт как fallback
        if self._emoji_font_path is None:
            self._emoji_font_path = None
        
        # Собираем основные шрифты для текста
        system_fonts = [
            'Arial',
            'Segoe UI',
            'DejaVu Sans',
            'FreeSans',
            'Helvetica Neue',
            'Arial Unicode MS',
        ]
        
        for font_name in system_fonts:
            try:
                test_font = pygame.font.SysFont(font_name, 12)
                test_surf = test_font.render('Test', True, (255, 255, 255))
                if test_surf.get_width() > 0:
                    self._available_fonts.append(font_name)
            except:
                continue
        
        # Добавляем пользовательские шрифты
        if os.path.exists(FONTS_DIR):
            for file in os.listdir(FONTS_DIR):
                if file.endswith(('.ttf', '.otf')):
                    self._available_fonts.append(os.path.join(FONTS_DIR, file))
        
        if not self._available_fonts:
            self._available_fonts = [None]
        
        print(f"[FontManager] Найден шрифт с эмодзи: {self._emoji_font_path}")
        print(f"[FontManager] Доступные шрифты: {len(self._available_fonts)}")
    
    def get_font(self, size, bold=False, italic=False, emoji=False):
        """Возвращает шрифт с кэшированием"""
        key = (size, bold, italic, emoji)
        
        if key not in self._fonts:
            font = None
            
            if emoji and self._emoji_font_path:
                # Используем шрифт с эмодзи
                try:
                    if isinstance(self._emoji_font_path, str) and os.path.exists(self._emoji_font_path):
                        font = pygame.font.Font(self._emoji_font_path, size)
                    else:
                        font = pygame.font.SysFont(self._emoji_font_path, size, bold, italic)
                except:
                    font = None
            
            # Если не получилось или не нужен эмодзи - используем обычный шрифт
            if font is None:
                for font_source in self._available_fonts:
                    try:
                        if font_source is None:
                            font = pygame.font.Font(None, size)
                        elif isinstance(font_source, str) and os.path.exists(font_source):
                            font = pygame.font.Font(font_source, size)
                        else:
                            font = pygame.font.SysFont(font_source, size, bold, italic)
                        
                        test_surf = font.render('Test', True, (255, 255, 255))
                        if test_surf.get_width() > 0:
                            break
                    except:
                        continue
            
            if font is None:
                font = pygame.font.Font(None, size)
            
            self._fonts[key] = font
        
        return self._fonts[key]
    
    def get_emoji_font(self, size):
        """Быстрый доступ к шрифту с эмодзи"""
        return self.get_font(size, emoji=True)


# Глобальный экземпляр
font_manager = FontManager()