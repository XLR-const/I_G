"""Панель инструментов"""

import pygame


class ToolsPanel:
    """Панель с инструментами (сверху)"""

    def __init__(self, rect):
        self.rect = rect
        self.tools = []
        self.selected_index = 0
        self.tool_width = 80
        self.tool_height = rect.height - 8
        self.tool_start_x = 130  # отступ слева под заголовок

        self._build_tools()

    def _build_tools(self):
        """Собирает инструменты"""
        self.tools = [
            {'id': 'brush', 'label': 'Кисть', 'icon': '🖌'},
            {'id': 'eraser', 'label': 'Ластик', 'icon': '🧹'},
            {'id': 'select', 'label': 'Выделение', 'icon': '▭'},
            {'id': 'fill', 'label': 'Заливка', 'icon': '⬛'},
        ]

    def get_selected_tool(self):
        """Возвращает ID выбранного инструмента"""
        if 0 <= self.selected_index < len(self.tools):
            return self.tools[self.selected_index]['id']
        return 'brush'

    def handle_click(self, mouse_x, mouse_y):
        """Обрабатывает клик по панели"""
        if not self.rect.collidepoint(mouse_x, mouse_y):
            return False

        # Относительная позиция от начала кнопок
        rel_x = mouse_x - self.rect.x - self.tool_start_x

        # Проверяем, что клик в области кнопок
        if rel_x < 0:
            return False

        index = rel_x // (self.tool_width + 4)  # +4 на отступ между кнопками

        if 0 <= index < len(self.tools):
            self.selected_index = index
            print(f"[Инструмент] {self.tools[index]['label']}")
            return True

        return False

    def draw(self, screen):
        """Отрисовывает панель"""
        # Фон
        pygame.draw.rect(screen, (45, 45, 50), self.rect)
        pygame.draw.rect(screen, (80, 80, 90), self.rect, 1)

        # Заголовок слева
        font_title = pygame.font.Font(None, 18)
        title = font_title.render("Инструменты:", True, (200, 200, 200))
        screen.blit(title, (self.rect.x + 8, self.rect.y + 14))

        # Кнопки
        x = self.rect.x + self.tool_start_x
        font_icon = pygame.font.Font(None, 24)
        font_label = pygame.font.Font(None, 13)

        for i, tool in enumerate(self.tools):
            rect = pygame.Rect(x, self.rect.y + 4, self.tool_width, self.tool_height)

            # Фон кнопки
            if i == self.selected_index:
                pygame.draw.rect(screen, (80, 80, 160), rect)
            else:
                pygame.draw.rect(screen, (50, 50, 55), rect)
            pygame.draw.rect(screen, (70, 70, 80), rect, 1)

            # Иконка
            icon_text = font_icon.render(tool['icon'], True, (255, 255, 255))
            screen.blit(icon_text, (rect.x + rect.width//2 - icon_text.get_width()//2, rect.y + 4))

            # Название
            label_text = font_label.render(tool['label'], True, (200, 200, 200))
            screen.blit(label_text, (rect.x + rect.width//2 - label_text.get_width()//2, rect.y + 30))

            x += self.tool_width + 4
