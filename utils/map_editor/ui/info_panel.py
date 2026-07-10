"""Панель информации о клетке"""

import pygame
from ..config import COLORS, OBJECT_TYPES, FONT_SMALL


class InfoPanel:
    """Отображает информацию о текущей клетке и статус"""

    def __init__(self, rect):
        self.rect = rect
        self.cell_x = None
        self.cell_y = None
        self.symbol = None
        self.tool = 'BRUSH'
        self.selected_symbol = 'M'
        self.has_changes = False
        self.font = FONT_SMALL

    def update(self, cell_pos, symbol):
        if cell_pos:
            self.cell_x, self.cell_y = cell_pos
            self.symbol = symbol
        else:
            self.cell_x = None
            self.cell_y = None
            self.symbol = None

    def update_status(self, tool, selected_symbol, has_changes):
        self.tool = tool
        self.selected_symbol = selected_symbol
        self.has_changes = has_changes

    def draw(self, screen):
        pygame.draw.rect(screen, COLORS['info_bg'], self.rect)

        # Левая часть
        left_text = ""
        if self.cell_x is not None:
            type_name = self._get_type_name(self.symbol)
            left_text = f"({self.cell_x}, {self.cell_y})  Символ: '{self.symbol}'  Тип: {type_name}"
        else:
            left_text = "Наведите на клетку"

        text_left = self.font.render(left_text, True, COLORS['text'])
        screen.blit(text_left, (self.rect.x + 12, self.rect.y + 10))

        # Правая часть
        right_text = f"Инструмент: {self.tool.upper()}  |  Объект: '{self.selected_symbol}'"
        if self.has_changes:
            right_text += "  |  * (изменено)"

        text_right = self.font.render(right_text, True, COLORS['text_dim'])
        right_x = self.rect.right - text_right.get_width() - 12
        screen.blit(text_right, (right_x, self.rect.y + 10))

    def _get_type_name(self, symbol):
        if not symbol:
            return "—"
        for type_name, symbols in OBJECT_TYPES.items():
            if symbol in symbols:
                return type_name.capitalize()
        return "Неизвестно"
