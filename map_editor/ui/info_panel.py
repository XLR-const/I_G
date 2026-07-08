"""Панель информации о клетке"""

import pygame
from ..config import COLORS, OBJECT_TYPES


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

    def update(self, cell_pos, symbol):
        """Обновляет информацию о клетке"""
        if cell_pos:
            self.cell_x, self.cell_y = cell_pos
            self.symbol = symbol
        else:
            self.cell_x = None
            self.cell_y = None
            self.symbol = None

    def update_status(self, tool, selected_symbol, has_changes):
        """Обновляет статусную информацию"""
        self.tool = tool
        self.selected_symbol = selected_symbol
        self.has_changes = has_changes

    def draw(self, screen):
        """Отрисовывает панель информации"""
        pygame.draw.rect(screen, COLORS['info_bg'], self.rect)

        font = pygame.font.Font(None, 16)

        # Левая часть: координаты, символ, тип
        left_text = ""
        if self.cell_x is not None:
            type_name = self._get_type_name(self.symbol)
            left_text = f"({self.cell_x}, {self.cell_y})  Символ: '{self.symbol}'  Тип: {type_name}"
        else:
            left_text = "Наведите на клетку"

        text_left = font.render(left_text, True, COLORS['text'])
        screen.blit(text_left, (self.rect.x + 12, self.rect.y + 10))

        # Правая часть: инструмент, объект, изменения
        right_text = f"Инструмент: {self.tool.upper()}  |  Объект: '{self.selected_symbol}'"
        if self.has_changes:
            right_text += "  |  * (изменено)"

        text_right = font.render(right_text, True, COLORS['text_dim'])
        # Правая часть прижата к правому краю
        right_x = self.rect.right - text_right.get_width() - 12
        screen.blit(text_right, (right_x, self.rect.y + 10))

    def _get_type_name(self, symbol):
        """Возвращает название типа объекта"""
        if not symbol:
            return "—"
        if symbol == 'M':
            return "Стена"
        for type_name, symbols in OBJECT_TYPES.items():
            if symbol in symbols:
                return type_name.capitalize()
        return "Неизвестно"
