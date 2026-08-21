"""
Изолированное окно свойств уровня с динамической версткой без хардкода
"""

import os
import pygame

from ..config import COLORS
from config.game_data import WEAPON_CONFIG

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class InputField:
    """Интерактивный инпут для ввода чисел с динамической позицией"""
    
    def __init__(self, width, height, text=""):
        self.rect = pygame.Rect(0, 0, width, height)
        self.text = text
        self.active = False
        self.color = (100, 100, 150)

    def handle_event(self, event, mouse_pos):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(mouse_pos):
                self.active = True
                self.color = (180, 180, 255)
            else:
                self.active = False
                self.color = (100, 100, 150)
        
        if self.active and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                if event.unicode.isdigit() and len(self.text) < 3:
                    self.text += event.unicode

    def draw(self, screen, font, x, y):
        self.rect.x = x
        self.rect.y = y
        pygame.draw.rect(screen, self.color, self.rect, 2, 4)
        txt_surf = font.render(self.text, True, (255, 255, 255))
        screen.blit(txt_surf, (self.rect.x + 5, self.rect.y + 5))


class LevelPropertiesWindow:
    """Масштабируемое модальное окно настроек метаданных уровня"""
    
    def __init__(self, editor):
        self.editor = editor
        self.screen = editor.screen
        self.clock = editor.clock
        self.running = True
        
        # Размеры окна теперь рассчитываются от размера экрана редактора
        screen_w, screen_h = self.screen.get_size()
        win_w = int(screen_w * 0.9)
        win_h = int(screen_h * 0.9)
        self.rect = pygame.Rect(
            (screen_w - win_w) // 2,
            (screen_h - win_h) // 2,
            win_w, win_h
        )
        
        self.font_title = pygame.font.Font(None, 28)
        self.font_section = pygame.font.Font(None, 20)
        self.font_ui = pygame.font.Font(None, 16)
        
        # Локальные копии данных
        self.local_inventory = list(editor.inventory)
        self.local_ammo = dict(editor.starting_ammo)
        self.local_bg = dict(editor.background_data)
        
        if self.local_bg.get("floor_color") is None: self.local_bg["floor_color"] = [40, 40, 40]
        if self.local_bg.get("ceiling_color") is None: self.local_bg["ceiling_color"] = [128, 128, 128]

        # Инпуты RGB (без жестких координат, позиция задается при draw)
        self.inputs = {
            "floor_r": InputField(40, 22, str(self.local_bg["floor_color"][0])),
            "floor_g": InputField(40, 22, str(self.local_bg["floor_color"][1])),
            "floor_b": InputField(40, 22, str(self.local_bg["floor_color"][2])),
            "ceil_r": InputField(40, 22, str(self.local_bg["ceiling_color"][0])),
            "ceil_g": InputField(40, 22, str(self.local_bg["ceiling_color"][1])),
            "ceil_b": InputField(40, 22, str(self.local_bg["ceiling_color"][2]))
        }
        
        # Динамические инпуты патронов для пушек
        self.ammo_inputs = {}
        self.weapons = list(WEAPON_CONFIG.keys()) if WEAPON_CONFIG else ["KNIFE", "COLT", "SHOTGUN", "MACHINEGUN"]
        
        for wpn in self.weapons:
            val = str(self.local_ammo.get(wpn, 0))
            self.ammo_inputs[wpn] = InputField(45, 22, val)
        
        # Текстуры и расчет колонок под ширину окон
        self.textures = []
        self._scan_textures()
        
        # Кнопки Применить / Отмена в правом нижнем углу окна
        self.btn_apply = pygame.Rect(self.rect.right - 250, self.rect.bottom - 45, 110, 32)
        self.btn_cancel = pygame.Rect(self.rect.right - 130, self.rect.bottom - 45, 110, 32)
        
        # Переменные для динамического скролла инвентаря оружия
        self.inv_scroll = 0

    def _scan_textures(self):
        target_dir = os.path.join(ROOT_DIR, "resources", "textures")
        if os.path.exists(target_dir):
            for file in os.listdir(target_dir):
                if file.lower().endswith('.png'):
                    rel_path = f"resources/textures/{file}"
                    try:
                        img = pygame.image.load(os.path.join(target_dir, file)).convert_alpha()
                        preview = pygame.transform.scale(img, (36, 36))
                        self.textures.append({
                            "path": rel_path,
                            "name": file,
                            "surf": preview
                        })
                    except:
                        pass

    def _handle_events(self):
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                self.editor.running = False
            
            # Перехват скролла мыши для списка оружия
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:  # Скролл вверх
                    self.inv_scroll = max(0, self.inv_scroll - 20)
                elif event.button == 5:  # Скролл вниз
                    self.inv_scroll += 20
            
            # События инпутов RGB
            for field in self.inputs.values():
                field.handle_event(event, mouse_pos)
            
            # События инпутов патронов
            for wpn, field in self.ammo_inputs.items():
                if wpn in self.local_inventory and wpn != "KNIFE":
                    field.handle_event(event, mouse_pos)
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.btn_cancel.collidepoint(mouse_pos):
                    self.running = False
                
                elif self.btn_apply.collidepoint(mouse_pos):
                    def get_rgb(r_in, g_in, b_in):
                        r = min(255, int(r_in.text) if r_in.text else 0)
                        g = min(255, int(g_in.text) if g_in.text else 0)
                        b = min(255, int(b_in.text) if b_in.text else 0)
                        return [r, g, b]
                    
                    if self.local_bg["floor_texture"] is None:
                        self.local_bg["floor_color"] = get_rgb(
                            self.inputs["floor_r"],
                            self.inputs["floor_g"],
                            self.inputs["floor_b"]
                        )
                    
                    if self.local_bg["ceiling_texture"] is None:
                        self.local_bg["ceiling_color"] = get_rgb(
                            self.inputs["ceil_r"],
                            self.inputs["ceil_g"],
                            self.inputs["ceil_b"]
                        )
                    
                    for wpn in self.local_inventory:
                        if wpn == "KNIFE":
                            self.local_ammo[wpn] = 1
                        else:
                            txt = self.ammo_inputs[wpn].text
                            self.local_ammo[wpn] = int(txt) if txt else 0
                    
                    self.editor.inventory = self.local_inventory
                    self.editor.starting_ammo = self.local_ammo
                    self.editor.background_data = self.local_bg
                    self.editor._on_change()
                    self.running = False
                
                # Динамический расчет кликов по колонкам интерфейса
                # Внутренние отступы секций
                pad = 15
                sec_w = (self.rect.width - pad * 4) // 3
                sec_h = self.rect.height - 110
                x_inv = self.rect.x + pad
                x_floor = x_inv + sec_w + pad
                x_ceil = x_floor + sec_w + pad
                
                # Клик по чекбоксам инвентаря оружия (с учетом скролла)
                y_wpn = self.rect.y + 120 - self.inv_scroll
                for wpn in self.weapons:
                    chk_rect = pygame.Rect(x_inv + 10, y_wpn, sec_w - 20, 30)
                    if chk_rect.collidepoint(mouse_pos) and (self.rect.y + 110 <= mouse_pos[1] <= self.rect.y + 110 + sec_h):

                        if wpn in self.local_inventory:
                            if len(self.local_inventory) > 1:
                                self.local_inventory.remove(wpn)
                        else:
                            self.local_inventory.append(wpn)
                    y_wpn += 35
                
                # Динамический клик по сетке ТЕКСТУР ПОЛА
                cols_count = max(1, (sec_w - 20) // 42)
                for t_idx, tx in enumerate(self.textures):
                    row, col = t_idx // cols_count, t_idx % cols_count
                    t_rect = pygame.Rect(x_floor + 10 + col * 42, self.rect.y + 120 + row * 42, 38, 38)
                    if t_rect.collidepoint(mouse_pos):
                        self.local_bg["floor_texture"] = tx["path"]
                        self.local_bg["floor_color"] = None
                
                # Динамический клик по сетке ТЕКСТУР ПОТОЛКА
                for t_idx, tx in enumerate(self.textures):
                    row, col = t_idx // cols_count, t_idx % cols_count
                    t_rect = pygame.Rect(x_ceil + 10 + col * 42, self.rect.y + 120 + row * 42, 38, 38)
                    if t_rect.collidepoint(mouse_pos):
                        self.local_bg["ceiling_texture"] = tx["path"]
                        self.local_bg["ceiling_color"] = None
                
                # Кнопки "Включить RGB" (смещены под сетки текстур)
                grid_rows = (len(self.textures) + cols_count - 1) // cols_count
                grid_end_y = self.rect.y + 120 + grid_rows * 42 + 15
                
                btn_reset_floor = pygame.Rect(x_floor + 10, grid_end_y, 120, 25)
                if btn_reset_floor.collidepoint(mouse_pos):
                    self.local_bg["floor_texture"] = None
                    self.local_bg["floor_color"] = [40, 40, 40]
                
                btn_reset_ceil = pygame.Rect(x_ceil + 10, grid_end_y, 120, 25)
                if btn_reset_ceil.collidepoint(mouse_pos):
                    self.local_bg["ceiling_texture"] = None
                    self.local_bg["ceiling_color"] = [128, 128, 128]

    def _draw(self):
        overlay = pygame.Surface(self.screen.get_size())
        overlay.set_alpha(150)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        pygame.draw.rect(self.screen, (35, 35, 45), self.rect, 0, 8)
        pygame.draw.rect(self.screen, (70, 70, 90), self.rect, 2, 8)
        
        pygame.draw.rect(self.screen, (45, 45, 60), (self.rect.x, self.rect.y, self.rect.width, 45), 0, 8)
        self.screen.blit(
            self.font_title.render("Свойства уровня и метаданные карты", True, (255, 255, 255)),
            (self.rect.x + 20, self.rect.y + 12)
        )
        
        # Масштабируемый расчет ширины трех колонок
        pad = 15
        sec_w = (self.rect.width - pad * 4) // 3
        sec_h = self.rect.height - 110
        x_inv = self.rect.x + pad
        x_floor = x_inv + sec_w + pad
        x_ceil = x_floor + sec_w + pad
        y_content = self.rect.y + 60
        
        # --- КОЛОНКА 1: ИНВЕНТАРЬ (С поддержкой скролла рабочей зоны) ---
        pygame.draw.rect(self.screen, (45, 45, 55), (x_inv, y_content, sec_w, sec_h), 0, 4)
        self.screen.blit(
            self.font_section.render("Стартовое снаряжение", True, (200, 200, 250)),
            (x_inv + 15, y_content + 15)
        )
        
        # Создаем маску-клип, чтобы текст пушек не вылезал за границы карточки при прокрутке
        inv_clip = pygame.Rect(x_inv, y_content + 45, sec_w, sec_h - 55)
        old_clip = self.screen.get_clip()
        self.screen.set_clip(inv_clip)
        
        y_wpn = y_content + 50 - self.inv_scroll
        for wpn in self.weapons:
            has_wpn = wpn in self.local_inventory
            chk_txt = f"[X]  {wpn}" if has_wpn else f"[ ]  {wpn}"
            color = (150, 255, 150) if has_wpn else (160, 160, 160)
            self.screen.blit(self.font_ui.render(chk_txt, True, color), (x_inv + 15, y_wpn + 4))
            
            if has_wpn and wpn != "KNIFE":
                self.ammo_inputs[wpn].draw(self.screen, self.font_ui, x_inv + sec_w - 95, y_wpn)
                self.screen.blit(
                    self.font_ui.render("пат.", True, (130, 130, 140)),
                    (x_inv + sec_w - 40, y_wpn + 4)
                )
            y_wpn += 35
        
        self.screen.set_clip(old_clip)
        
        # Вычисляем, сколько колонок текстур поместится в ширину окна
        cols_count = max(1, (sec_w - 20) // 42)
        
        # --- КОЛОНКА 2: ПАРАМЕТРЫ ПОЛА ---
        pygame.draw.rect(self.screen, (40, 45, 40), (x_floor, y_content, sec_w, sec_h), 0, 4)
        self.screen.blit(
            self.font_section.render("Параметры ПОЛА", True, (180, 255, 180)),
            (x_floor + 15, y_content + 15)
        )
        
        # Сетка картинок
        for t_idx, tx in enumerate(self.textures):
            row, col = t_idx // cols_count, t_idx % cols_count
            tx_rect = pygame.Rect(x_floor + 15 + col * 42, y_content + 50 + row * 42, 38, 38)
            self.screen.blit(tx["surf"], tx_rect)
            if self.local_bg.get("floor_texture") == tx["path"]:
                pygame.draw.rect(self.screen, (255, 255, 255), tx_rect.inflate(4, 4), 2, 2)
        
        # Динамический сдвиг блока RGB под сетку текстур
        grid_rows = (len(self.textures) + cols_count - 1) // cols_count
        rgb_start_y = y_content + 50 + grid_rows * 42 + 20
        
        btn_rf = pygame.Rect(x_floor + 15, rgb_start_y, 120, 24)
        pygame.draw.rect(self.screen, (60, 80, 60), btn_rf, 0, 4)
        self.screen.blit(
            self.font_ui.render("Включить RGB", True, (255, 255, 255)),
            (btn_rf.x + 18, btn_rf.y + 5)
        )
        
        if self.local_bg.get("floor_texture"):
            self.screen.blit(
                self.font_ui.render("RGB заблокирован (выбрана текстура)", True, (140, 140, 140)),
                (x_floor + 15, rgb_start_y + 35)
            )
        else:
            pygame.draw.rect(self.screen, (255, 255, 255), btn_rf, 1, 4)
            self.screen.blit(
                self.font_ui.render("R:                   G:                   B:", True, (255, 255, 255)),
                (x_floor + 15, rgb_start_y + 38)
            )
            self.inputs["floor_r"].draw(self.screen, self.font_ui, x_floor + 35, rgb_start_y + 35)
            self.inputs["floor_g"].draw(self.screen, self.font_ui, x_floor + 105, rgb_start_y + 35)
            self.inputs["floor_b"].draw(self.screen, self.font_ui, x_floor + 175, rgb_start_y + 35)
        
        # --- КОЛОНКА 3: ПАРАМЕТРЫ ПОТОЛКА ---
        pygame.draw.rect(self.screen, (45, 40, 40), (x_ceil, y_content, sec_w, sec_h), 0, 4)
        self.screen.blit(
            self.font_section.render("Параметры ПОТОЛКА", True, (255, 180, 180)),
            (x_ceil + 15, y_content + 15)
        )
        
        # Сетка картинок
        for t_idx, tx in enumerate(self.textures):
            row, col = t_idx // cols_count, t_idx % cols_count
            tx_rect = pygame.Rect(x_ceil + 15 + col * 42, y_content + 50 + row * 42, 38, 38)
            self.screen.blit(tx["surf"], tx_rect)
            if self.local_bg.get("ceiling_texture") == tx["path"]:
                pygame.draw.rect(self.screen, (255, 255, 255), tx_rect.inflate(4, 4), 2, 2)
        
        # Динамический сдвиг блока RGB под сетку текстур потолка
        btn_rc = pygame.Rect(x_ceil + 15, rgb_start_y, 120, 24)
        pygame.draw.rect(self.screen, (80, 60, 60), btn_rc, 0, 4)
        self.screen.blit(
            self.font_ui.render("Включить RGB", True, (255, 255, 255)),
            (btn_rc.x + 18, btn_rc.y + 5)
        )
        
        if self.local_bg.get("ceiling_texture"):
            self.screen.blit(
                self.font_ui.render("RGB заблокирован (выбрана текстура)", True, (140, 140, 140)),
                (x_ceil + 15, rgb_start_y + 35)
            )
        else:
            pygame.draw.rect(self.screen, (255, 255, 255), btn_rc, 1, 4)
            self.screen.blit(
                self.font_ui.render("R:                   G:                   B:", True, (255, 255, 255)),
                (x_ceil + 15, rgb_start_y + 38)
            )
            self.inputs["ceil_r"].draw(self.screen, self.font_ui, x_ceil + 35, rgb_start_y + 35)
            self.inputs["ceil_g"].draw(self.screen, self.font_ui, x_ceil + 105, rgb_start_y + 35)
            self.inputs["ceil_b"].draw(self.screen, self.font_ui, x_ceil + 175, rgb_start_y + 35)
        
        # Нижние кнопки управления окном
        pygame.draw.rect(self.screen, (50, 120, 50), self.btn_apply, 0, 4)
        self.screen.blit(
            self.font_section.render("Применить", True, (255, 255, 255)),
            (self.btn_apply.x + 18, self.btn_apply.y + 8)
        )
        
        pygame.draw.rect(self.screen, (100, 50, 50), self.btn_cancel, 0, 4)
        self.screen.blit(
            self.font_section.render("Отмена", True, (255, 255, 255)),
            (self.btn_cancel.x + 28, self.btn_cancel.y + 8)
        )

    def run(self):
        while self.running:
            self._handle_events()
            self._draw()
            pygame.display.flip()
            self.clock.tick(60)