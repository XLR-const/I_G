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

        self.dialog_active = False
        self.dialog_choice = None

        self.grid = []
        self.current_file = None
        self.selected_symbol = 'M'
        self.has_changes = False
        self._saving = False  # защита от множественных сохранений

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
        self.current_tool = 'brush'

    def _on_change(self):
        """Вызывается при изменении карты"""
        if not self._saving:
            self.has_changes = True
            self._auto_save()

    def _auto_save(self):
        """Пишет изменения ТОЛЬКО в бэкап, не трогая основной файл"""
        if self._saving or not self.current_file or not self.grid or not self.has_changes:
            return

        self._saving = True
        self._create_backup()  # Делаем резервную копию
        # Строку self.save_level(self.current_file) ОТСЮДА УДАЛЯЕМ!
        self._saving = False


    def _create_backup(self):
        if not self.current_file or not self.grid:
            return

        backup_dir = os.path.join(os.path.dirname(self.current_file), 'levels_backup')
        os.makedirs(backup_dir, exist_ok=True)

        base_name = os.path.basename(self.current_file)
        name, ext = os.path.splitext(base_name)
        backup_path = os.path.join(backup_dir, f"{name}_backup{ext}")

        try:
            with open(self.current_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            data['map'] = self.grid

            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"[Бэкап] Ошибка: {e}")

    def _clear_backups(self):
        if not self.current_file:
            return

        backup_dir = os.path.join(os.path.dirname(self.current_file), 'levels_backup')
        if not os.path.exists(backup_dir):
            return

        base_name = os.path.basename(self.current_file)
        name, _ = os.path.splitext(base_name)

        for f in os.listdir(backup_dir):
            if f.startswith(name) and f.endswith('_backup.json'):
                try:
                    os.remove(os.path.join(backup_dir, f))
                except:
                    pass

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
            self._clear_backups()

            print(f"[Сохранено] {file_path}")
            return True

        except Exception as e:
            print(f"[Ошибка] Сохранение: {e}")
            return False

    def _open_dialog(self):
        """Открывает диалог сохранения"""
        if self.has_changes and self.current_file:
            self.dialog_active = True
            self.dialog_choice = None
        else:
            self.running = False

    def _draw_dialog(self):
        """Рисует диалог сохранения"""
        # Затемнение
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Окно диалога
        dialog_rect = pygame.Rect(
            WINDOW_WIDTH // 2 - 220,
            WINDOW_HEIGHT // 2 - 80,
            440, 160
        )
        pygame.draw.rect(self.screen, (50, 50, 60), dialog_rect)
        pygame.draw.rect(self.screen, (100, 100, 120), dialog_rect, 2)

        font = pygame.font.Font(None, 24)
        font_small = pygame.font.Font(None, 18)

        # Заголовок
        title = font.render("Сохранить изменения?", True, (255, 255, 255))
        title_rect = title.get_rect(center=(dialog_rect.centerx, dialog_rect.y + 30))
        self.screen.blit(title, title_rect)

        # Кнопки
        y = dialog_rect.y + 70
        options = [
            ("[Y] Да, сохранить и выйти", (dialog_rect.x + 30, y)),
            ("[N] Нет, выйти без сохранения", (dialog_rect.x + 30, y + 25)),
            ("[ESC] Отмена", (dialog_rect.x + 30, y + 50)),
        ]

        for text, pos in options:
            rendered = font_small.render(text, True, (200, 200, 200))
            self.screen.blit(rendered, pos)

    def _handle_events(self):
        for event in pygame.event.get():
            # === ДИАЛОГ ===
            if self.dialog_active:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_y:
                        self.dialog_choice = 'save'
                        self.dialog_active = False
                    elif event.key == pygame.K_n:
                        self.dialog_choice = 'discard'
                        self.dialog_active = False
                    elif event.key == pygame.K_ESCAPE:
                        self.dialog_choice = 'cancel'
                        self.dialog_active = False
                continue  # Важно: пропускаем остальные события, пока открыт диалог


            # === ОБЫЧНЫЕ СОБЫТИЯ ===
            if event.type == pygame.QUIT:
                self._open_dialog()
                continue

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self._open_dialog()
                    continue

                if event.key == pygame.K_s and (event.mod & pygame.KMOD_CTRL):
                    if self.current_file:
                        self.save_level(self.current_file)
                    continue

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

                if self.toolbar.rect.collidepoint(mx, my):
                    if event.button == 4:
                        self.toolbar.scroll(-30)
                        continue
                    elif event.button == 5:
                        self.toolbar.scroll(30)
                        continue

                if self.toolbar.handle_click(mx, my):
                    self.selected_symbol = self.toolbar.get_selected_symbol()
                    print(f"[Выбран] '{self.selected_symbol}'")
                    continue

                if self.canvas.rect.collidepoint(mx, my):
                    if event.button == 4:
                        self.canvas.zoom_in()
                        continue
                    elif event.button == 5:
                        self.canvas.zoom_out()
                        continue

                if event.button == 2:
                    self.canvas.start_drag(mx, my)
                    continue

                if event.button == 1:
                    cell = self.canvas.get_cell_at(mx, my)
                    if cell:
                        x, y = cell
                        if self.current_tool == 'brush':
                            self.brush.apply(x, y)
                elif event.button == 3:
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

                if pygame.mouse.get_pressed()[0]:
                    cell = self.canvas.get_cell_at(mx, my)
                    if cell:
                        x, y = cell
                        if self.current_tool == 'brush':
                            self.brush.apply(x, y)

                if pygame.mouse.get_pressed()[2]:
                    cell = self.canvas.get_cell_at(mx, my)
                    if cell:
                        x, y = cell
                        self.eraser.apply(x, y)

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

        # Информация внизу
        font_small = pygame.font.Font(None, 12)
        tool_name = "Кисть" if self.current_tool == 'brush' else "Ластик"
        info = f"Инструмент: {tool_name}  |  Объект: '{self.selected_symbol}'"
        if self.has_changes:
            info += "  |  * (изменено)"

        text = font_small.render(info, True, COLORS['text_dim'])
        self.screen.blit(text, (10, WINDOW_HEIGHT - 25))

        # Диалог поверх всего
        if self.dialog_active:
            self._draw_dialog()

        pygame.display.flip()

    def run(self):
        while self.running:
            self._handle_events()

            # Обрабатываем результат диалога
            if not self.dialog_active and self.dialog_choice is not None:
                if self.dialog_choice == 'save':
                    if self.current_file:
                        self.save_level(self.current_file)
                    self.running = False
                elif self.dialog_choice == 'discard':
                    self.running = False
                elif self.dialog_choice == 'cancel':
                    self.dialog_choice = None  # Сбрасываем выбор и продолжаем работу

            self._draw()
            self.clock.tick(60)

        pygame.quit()
