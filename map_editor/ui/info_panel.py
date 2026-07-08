"""Панель информации о клетке"""

import pygame
from ..config import COLORS, OBJECT_TYPES


class InfoPanel:
    """Отображает информацию о текущей клетке"""

    def __init__(self, rect):
        self.rect = rect
        self.cell_x = None
        self.cell_y = None
        self.symbol = None

    def update(self, cell_pos, symbol):
        """Обновляет информацию о клетке"""
        if cell_pos:
            self.cell_x, self.cell_y = cell_pos
            self.symbol = symbol
        else:
            self.cell_x = None
            self.cell_y = None
            self.symbol = None

    def draw(self, screen):
        """Отрисовывает панель информации"""
        pygame.draw.rect(screen, COLORS['info_bg'], self.rect)

        font = pygame.font.Font(None, 16)

        if self.cell_x is not None:
            lines = [
                f"Координаты: ({self.cell_x}, {self.cell_y})",
                f"Символ: '{self.symbol}'",
                f"Тип: {self._get_type_name(self.symbol)}"
            ]
        else:
            lines = ["Наведите на клетку"]

        for i, line in enumerate(lines):
            color = COLORS['text'] if i == 0 else COLORS['text_dim']
            text = font.render(line, True, color)
            screen.blit(text, (self.rect.x + 10, self.rect.y + 10 + i * 20))

    def _get_type_name(self, symbol):
        """Возвращает название типа объекта"""
        if not symbol:
            return "—"
        for type_name, symbols in OBJECT_TYPES.items():
            if symbol in symbols:
                return type_name.capitalize()
        return "Неизвестно"