"""Главный класс редактора"""

import os
import json
import pygame
from .config import *
from .ui import Canvas, InfoPanel


class MapEditor:
    """Редактор карт"""

    def __init__(self, level_file=None):
        pygame.init()
        pygame.display.set_caption("Map Editor — Загрузите уровень")

        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True

        self.grid = []
        self.current_file = None

        self._setup_ui()

        # Загружаем уровень если передан
        if level_file:
            self.load_level(level_file)

    def _setup_ui(self):
        canvas_rect = pygame.Rect(0, 0, WINDOW_WIDTH - 250, WINDOW_HEIGHT - 60)
        self.canvas = Canvas(canvas_rect)

        info_rect = pygame.Rect(0, WINDOW_HEIGHT - 60, WINDOW_WIDTH - 250, 60)
        self.info_panel = InfoPanel(info_rect)

        self.toolbar_rect = pygame.Rect(WINDOW_WIDTH - 250, 0, 250, WINDOW_HEIGHT - 60)

    def load_level(self, file_path):
        """Загружает уровень из JSON"""
        if not os.path.exists(file_path):
            print(f"[Ошибка] Файл не найден: {file_path}")
            return False

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.grid = data.get('map', [])
            self.current_file = file_path

            self.canvas.set_grid(self.grid)

            filename = os.path.basename(file_path)
            pygame.display.set_caption(f"Map Editor — {filename}")

            print(f"[Успех] Загружен уровень: {file_path}")
            print(f"  Размер: {len(self.grid[0])}x{len(self.grid)}")

            return True

        except Exception as e:
            print(f"[Ошибка] Не удалось загрузить уровень: {e}")
            return False

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                if event.key == pygame.K_0 and (event.mod & pygame.KMOD_CTRL):
                    self.canvas._center_view()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:  # Колесо вверх — приблизить
                    self.canvas.zoom_in()
                elif event.button == 5:  # Колесо вниз — отдалить
                    self.canvas.zoom_out()
                elif event.button == 2:  # Средняя кнопка — начать drag
                    self.canvas.start_drag(event.pos[0], event.pos[1])

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 2:
                    self.canvas.end_drag()

            elif event.type == pygame.MOUSEMOTION:
                mx, my = event.pos
                self.canvas.update_drag(mx, my)

                cell = self.canvas.get_cell_at(mx, my)
                symbol = None
                if cell:
                    x, y = cell
                    if 0 <= y < len(self.grid) and 0 <= x < len(self.grid[0]):
                        symbol = self.grid[y][x]
                self.info_panel.update(cell, symbol)
                self.canvas.update_hover(mx, my)

    def _draw(self):
        self.screen.fill(COLORS['background'])

        self.canvas.draw(self.screen)
        self.info_panel.draw(self.screen)

        # Панель объектов (заглушка)
        pygame.draw.rect(self.screen, COLORS['panel_bg'], self.toolbar_rect)
        pygame.draw.rect(self.screen, COLORS['panel_border'], self.toolbar_rect, 1)

        font = pygame.font.Font(None, 20)
        text = font.render("Легенда (будет здесь)", True, COLORS['text_dim'])
        text_rect = text.get_rect(center=self.toolbar_rect.center)
        self.screen.blit(text, text_rect)

        # Подсказки
        font_small = pygame.font.Font(None, 12)
        tips = [
            "Колесо мыши — зум",
            "Средняя кнопка — панорамирование",
            "Ctrl+0 — сброс масштаба"
        ]
        y = self.toolbar_rect.bottom - len(tips) * 20 - 10
        for tip in tips:
            text = font_small.render(tip, True, COLORS['text_dim'])
            self.screen.blit(text, (self.toolbar_rect.x + 10, y))
            y += 20

        pygame.display.flip()

    def run(self):
        while self.running:
            self._handle_events()
            self._draw()
            self.clock.tick(60)

        pygame.quit()
