"""Главный класс редактора"""

import os
import json
import pygame
from .config import *
from .ui import Canvas, InfoPanel
from .ui.toolbar import Toolbar
from .tools import Brush, Eraser


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
        self.selected_symbol = 'M'
        self.has_changes = False

        self._setup_ui()
        self._setup_tools()

        if level_file:
            self.load_level(level_file)

    def _setup_ui(self):
        canvas_rect = pygame.Rect(0, 0, WINDOW_WIDTH - 250, WINDOW_HEIGHT - 60)
        self.canvas = Canvas(canvas_rect)

        info_rect = pygame.Rect(0, WINDOW_HEIGHT - 60, WINDOW_WIDTH - 250, 60)
        self.info_panel = InfoPanel(info_rect)

        toolbar_rect = pygame.Rect(WINDOW_WIDTH - 250, 0, 250, WINDOW_HEIGHT - 60)
        self.toolbar = Toolbar(toolbar_rect)

    def _setup_tools(self):
        self.brush = Brush(self)
        self.eraser = Eraser(self)
        self.current_tool = 'brush'  # 'brush' или 'eraser'

    def _on_change(self):
        """Вызывается при изменении карты"""
        self.has_changes = True
        self._auto_save()

    def _auto_save(self):
        """Автосохранение с бэкапом"""
        if self.current_file and self.grid:
            self._create_backup()
            self.save_level(self.current_file)

    def _create_backup(self):
        """Создаёт бэкап текущего уровня"""
        if not self.current_file or not self.grid:
            return

        # Создаём папку для бэкапов
        backup_dir = os.path.join(os.path.dirname(self.current_file), 'levels_backup')
        os.makedirs(backup_dir, exist_ok=True)

        # Имя бэкапа
        base_name = os.path.basename(self.current_file)
        name, ext = os.path.splitext(base_name)
        backup_path = os.path.join(backup_dir, f"{name}_backup{ext}")

        try:
            # Загружаем текущие данные
            with open(self.current_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Обновляем карту
            data['map'] = self.grid

            # Сохраняем бэкап
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"[Бэкап] Ошибка: {e}")

    def load_level(self, file_path):
        if not os.path.exists(file_path):
            print(f"[Ошибка] Файл не найден: {file_path}")
            return False

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.grid = data.get('map', [])
            self.current_file = file_path
            self.has_changes = False

            self.canvas.set_grid(self.grid)

            filename = os.path.basename(file_path)
            pygame.display.set_caption(f"Map Editor — {filename}")

            print(f"[Успех] Загружен уровень: {file_path}")
            print(f"  Размер: {len(self.grid[0])}x{len(self.grid)}")

            return True

        except Exception as e:
            print(f"[Ошибка] Не удалось загрузить уровень: {e}")
            return False

    def save_level(self, file_path=None):
        if file_path is None:
            file_path = self.current_file

        if not file_path or not self.grid:
            return False

        try:
            data = {}
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

            data['map'] = self.grid

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self.has_changes = False
            print(f"[Сохранено] {file_path}")
            return True

        except Exception as e:
            print(f"[Ошибка] Сохранение: {e}")
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
                if event.key == pygame.K_b:
                    self.current_tool = 'brush'
                    print("[Инструмент] Кисть")
                if event.key == pygame.K_e:
                    self.current_tool = 'eraser'
                    print("[Инструмент] Ластик")

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos

                # ============================================================
                # 1. СКРОЛЛ НА ПАНЕЛИ ОБЪЕКТОВ (приоритет)
                # ============================================================
                if self.toolbar.rect.collidepoint(mx, my):
                    if event.button == 4:  # Колесо вверх
                        self.toolbar.scroll(-30)
                        continue
                    elif event.button == 5:  # Колесо вниз
                        self.toolbar.scroll(30)
                        continue

                # ============================================================
                # 2. КЛИК ПО ПАНЕЛИ ОБЪЕКТОВ
                # ============================================================
                if self.toolbar.handle_click(mx, my):
                    self.selected_symbol = self.toolbar.get_selected_symbol()
                    print(f"[Выбран] '{self.selected_symbol}'")
                    continue

                # ============================================================
                # 3. ЗУМ НА КАРТЕ (если мышь над картой)
                # ============================================================
                if self.canvas.rect.collidepoint(mx, my):
                    if event.button == 4:  # Колесо вверх — зум
                        self.canvas.zoom_in()
                        continue
                    elif event.button == 5:  # Колесо вниз — зум
                        self.canvas.zoom_out()
                        continue

                # ============================================================
                # 4. DRAG КАРТЫ
                # ============================================================
                if event.button == 2:  # Средняя кнопка
                    self.canvas.start_drag(mx, my)
                    continue

                # ============================================================
                # 5. КИСТЬ / ЛАСТИК
                # ============================================================
                if event.button == 1:  # ЛКМ
                    cell = self.canvas.get_cell_at(mx, my)
                    if cell:
                        x, y = cell
                        if self.current_tool == 'brush':
                            self.brush.apply(x, y)
                elif event.button == 3:  # ПКМ
                    cell = self.canvas.get_cell_at(mx, my)
                    if cell:
                        x, y = cell
                        self.eraser.apply(x, y)

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 2:
                    self.canvas.end_drag()

            elif event.type == pygame.MOUSEMOTION:
                mx, my = event.pos
                self.canvas.update_drag(mx, my)

                # Кисть при зажатой ЛКМ
                if pygame.mouse.get_pressed()[0]:
                    cell = self.canvas.get_cell_at(mx, my)
                    if cell:
                        x, y = cell
                        if self.current_tool == 'brush':
                            self.brush.apply(x, y)

                # Ластик при зажатой ПКМ
                if pygame.mouse.get_pressed()[2]:
                    cell = self.canvas.get_cell_at(mx, my)
                    if cell:
                        x, y = cell
                        self.eraser.apply(x, y)

                # Обновляем информацию
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
        self.toolbar.draw(self.screen)

        # Информация в заголовке
        font_small = pygame.font.Font(None, 12)
        tool_name = "Кисть" if self.current_tool == 'brush' else "Ластик"
        info = f"Инструмент: {tool_name}  |  Объект: '{self.selected_symbol}'"
        if self.has_changes:
            info += "  |  * (изменено)"

        text = font_small.render(info, True, COLORS['text_dim'])
        self.screen.blit(text, (10, WINDOW_HEIGHT - 25))  # ← ИСПРАВЛЕНО

        pygame.display.flip()

    def run(self):
        while self.running:
            self._handle_events()
            self._draw()
            self.clock.tick(60)

        pygame.quit()
