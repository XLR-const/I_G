import pygame
import setting  # noqa
import sys
import random
from save_system import SaveSystem

class UIManager:
    def __init__(self, game):
        self.game = game
        self.font_tile = pygame.font.Font(None, int(setting.CELL_H * 1.5))
        self.font_normal = pygame.font.Font(None, int(setting.CELL_H * 0.6))
        self.font_small = pygame.font.Font(None, int(setting.CELL_H * 0.4))
        
        self.states = {
            'BOOT': 0,         # загрузка игры
            'MENU': 1,         # главное меню
            'BRIEFING': 2,     # брифинг
            'PLAYING': 3,      # игра
            'PAUSE': 4,        # меню паузы
            'LEVEL_END': 5,    # конец уровня
            'DEAD': 6,         # без сознания хэх
            'CUTSCENE': 7,     # катсцены
            'OPTIONS': 8       # опции
        }
        
        self.current_state = self.states['BOOT']
        self.selected_option = 0
        
        self.load_assets()
    
    def load_assets(self):
        """Загрузка ассетов"""
        self.backgrounds = {}
        try:
            menu_bg = pygame.image.load('resources/ui/main_menu_bg.png').convert_alpha()
            self.backgrounds['menu'] = pygame.transform.scale(menu_bg, (setting.WIDTH, setting.HEIGHT))
        except Exception:
            self.backgrounds['menu'] = None
        try:
            dead_bg = pygame.image.load('resources/ui/dead_bg.png').convert_alpha()
            self.backgrounds['dead'] = pygame.transform.scale(dead_bg, (setting.WIDTH, setting.HEIGHT))
        except Exception:
            self.backgrounds['dead'] = None
    
    def handle_event(self, event):
        """Ретранслятор событий для UI"""
        if self.current_state == self.states['MENU']:
            return self._handle_menu_event(event)
        if self.current_state == self.states['BRIEFING']:
            return self._handle_briefing_event(event)
        if self.current_state == self.states['PAUSE']:
            return self._handle_pause_event(event)
        if self.current_state == self.states['LEVEL_END']:
            return self._handle_level_end_event(event)
        if self.current_state == self.states['DEAD']:
            return self._handle_dead_event(event)
        if self.current_state == self.states['CUTSCENE']:
            return self._handle_cutscene_event(event)
        if self.current_state == self.states['OPTIONS']:
            return self._handle_options_event(event)
        return False

    # ----------------------------------------------------------------------
    # HANDLERS
    # ----------------------------------------------------------------------
    
    def _handle_menu_event(self, event):
        """Обработка ввода в гл меню"""
        options_len = 4
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_DOWN:
                self.selected_option = (self.selected_option + 1) % options_len
                return True
            if event.key == pygame.K_UP:
                self.selected_option = (self.selected_option - 1) % options_len
                return True
            if event.key == pygame.K_RETURN:
                # 0: NEW GAME
                if self.selected_option == 0:
                    self.game.reset_game()
                    self.current_state = self.states['BRIEFING']
                # 1: LOAD GAME
                elif self.selected_option == 1:
                    saved = SaveSystem.load()
                    if saved:
                        self.game.current_level = saved['current_level']
                        self.game.total_kills = saved['total_kills']
                        self.game.load_level(self.game.current_level)
                        self.current_state = self.states['BRIEFING']
                    else:
                        self.game.reset_game()
                        self.current_state = self.states['BRIEFING']
                # 2: OPTIONS
                elif self.selected_option == 2:
                    self.selected_option = 0
                    self.current_state = self.states['OPTIONS']
                # 3: QUIT
                elif self.selected_option == 3:
                    pygame.quit()
                    sys.exit()
                return True
        return False
    
    def _handle_briefing_event(self, event):
        """Обработка событий экрана сводки перед уровнем"""
        if event.type == pygame.KEYDOWN:
            self._start_level()
            return True
        return False
    
    def _handle_pause_event(self, event):
        """Обработка меню паузы"""
        options_len = 4
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.current_state = self.states['PLAYING']
                return True
            if event.key == pygame.K_UP:
                self.selected_option = (self.selected_option - 1) % options_len
                return True
            if event.key == pygame.K_DOWN:
                self.selected_option = (self.selected_option + 1) % options_len
                return True
            if event.key == pygame.K_RETURN:
                if self.selected_option == 0:      # RESUME
                    self.current_state = self.states['PLAYING']
                elif self.selected_option == 1:    # RESTART LEVEL
                    self.game.level_start_time = pygame.time.get_ticks()
                    self.game.load_level(self.game.current_level)
                    self.current_state = self.states['PLAYING']
                elif self.selected_option == 2:    # MAIN MENU
                    self.current_state = self.states['MENU']
                elif self.selected_option == 3:    # QUIT
                    pygame.quit()
                    sys.exit()
                return True
        return False
    
    def _handle_level_end_event(self, event):
        """Обработка конца уровня"""
        if event.type == pygame.KEYDOWN:
            self.game.current_level += 1
            # Save progress (kills and level number, time is just for display)
            SaveSystem.save(self.game.current_level, self.game.total_kills, self._get_level_time())
            self.game.load_level(self.game.current_level)
            self.current_state = self.states['BRIEFING']
            return True
        return False
    
    def _handle_dead_event(self, event):
        """Обработка экрана смерти"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:          # RESTART
                self.game.level_start_time = pygame.time.get_ticks()
                self.game.load_level(self.game.current_level)
                self.current_state = self.states['PLAYING']
                return True
            if event.key == pygame.K_m:          # MAIN MENU
                self.current_state = self.states['MENU']
                return True
        return False
    
    def _handle_cutscene_event(self, event):
        """Обработка катсцены"""
        if event.type == pygame.KEYDOWN:
            self.current_state = self.states['MENU']
            return True
        return False

    def _handle_options_event(self, event):
        """Обработка ввода меню настроек"""
        options_len = 3
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_option = (self.selected_option - 1) % options_len
                return True
            if event.key == pygame.K_DOWN:
                self.selected_option = (self.selected_option + 1) % options_len
                return True
            if event.key == pygame.K_LEFT:
                print("Сработала левая стрелка")
                if self.selected_option == 0:   # sensitivity
                    new_val = max(0.0005, setting.MOUSE_SENSITIVITY - 0.0005)
                    setting.MOUSE_SENSITIVITY = new_val
                elif self.selected_option == 1:   # volume
                    new_val = max(0.0, setting.MASTER_VOLUME - 0.1)
                    setting.MASTER_VOLUME = new_val
                return True
            if event.key == pygame.K_RIGHT:
                print("Сработала правая стрелка")
                if self.selected_option == 0:
                    new_val = min(0.01, setting.MOUSE_SENSITIVITY + 0.0005)
                    setting.MOUSE_SENSITIVITY = new_val
                elif self.selected_option == 1:
                    new_val = min(1.0, setting.MASTER_VOLUME + 0.1)
                    setting.MASTER_VOLUME = new_val
                return True
            if event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                if self.selected_option == 2:   # back
                    self.current_state = self.states['MENU']
                return True
        return False
    
    # ----------------------------------------------------------------------
    # UPDATE LOOPS
    # ----------------------------------------------------------------------
    def update(self):
        """Ретранслятор апдейтов отдельных экранов"""
        if self.current_state == self.states['BOOT']:
            self._update_boot()
        elif self.current_state == self.states['MENU']:
            self._update_menu()
        elif self.current_state == self.states['BRIEFING']:
            self._update_briefing()
        elif self.current_state == self.states['PAUSE']:
            self._update_pause()
        elif self.current_state == self.states['LEVEL_END']:
            self._update_level_end()
        elif self.current_state == self.states['DEAD']:
            self._update_dead()
        elif self.current_state == self.states['CUTSCENE']:
            self._update_cutscene()
        elif self.current_state == self.states['OPTIONS']:
            self._update_options()
    
    def draw(self, screen):
        """Ретранслятор отрисовки по отдельным экранам"""
        if self.current_state == self.states['BOOT']:
            self._draw_boot(screen)
        elif self.current_state == self.states['MENU']:
            self._draw_menu(screen)
        elif self.current_state == self.states['BRIEFING']:
            self._draw_briefing(screen)
        elif self.current_state == self.states['PAUSE']:
            self._draw_pause(screen)
        elif self.current_state == self.states['LEVEL_END']:
            self._draw_level_end(screen)
        elif self.current_state == self.states['DEAD']:
            self._draw_dead(screen)
        elif self.current_state == self.states['CUTSCENE']:
            self._draw_cutscene(screen)
        elif self.current_state == self.states['OPTIONS']:
            self._draw_options(screen)
    
    # ----------------------------------------------------------------------
    # BOOT
    # ----------------------------------------------------------------------
    def _update_boot(self):
        if not hasattr(self, 'boot_start'):
            self.boot_start = pygame.time.get_ticks()
        if pygame.time.get_ticks() - self.boot_start > 2000:
            self.current_state = self.states['MENU']
    
    def _draw_boot(self, screen):
        screen.fill((0, 0, 0))
        text = self.font_tile.render("Loading...", True, (255, 255, 255))
        text_rect = text.get_rect(center=(setting.WIDTH // 2, setting.HEIGHT // 2))
        screen.blit(text, text_rect)
        
        progress = min(1.0, (pygame.time.get_ticks() - self.boot_start) / 2000)
        bar_width = int(setting.WIDTH * 0.4)
        filled = int(bar_width * progress)
        bar_rect = pygame.Rect(setting.WIDTH // 2 - bar_width // 2, setting.HEIGHT // 2 + 50, bar_width, 20)
        pygame.draw.rect(screen, (100, 100, 100), bar_rect)
        pygame.draw.rect(screen, (0, 200, 0), (bar_rect.x, bar_rect.y, filled, 20))
    
    # ----------------------------------------------------------------------
    # MAIN MENU
    # ----------------------------------------------------------------------
    def _update_menu(self):
        pass
    
    def _draw_menu(self, screen):
        if self.backgrounds['menu']:
            screen.blit(self.backgrounds['menu'], (0, 0))
        else:
            screen.fill((20, 40, 20))
        
        # Title
        title = self.font_tile.render("Ilyusha Grate", True, (255, 200, 0))
        title_rect = title.get_rect(center=(setting.WIDTH // 2, int(setting.CELL_H * 2)))
        screen.blit(title, title_rect)
        
        options = ['НОВАЯ ИГРА', 'ЗАГРУЗИТЬ ИГРУ', 'НАСТРОЙКИ', 'ВЫХОД']
        for i, opt in enumerate(options):
            y = setting.HEIGHT // 2 + i * 60
            color = (255, 255, 255) if i == self.selected_option else (150, 150, 150)
            text = self.font_normal.render(opt, True, color)
            text_rect = text.get_rect(center=(setting.WIDTH // 2, y))
            screen.blit(text, text_rect)
            
            if i == self.selected_option:
                # draw little arrow
                arrow_x = text_rect.left - 30
                arrow_y = text_rect.centery
                pygame.draw.line(screen, (255, 200, 0), (arrow_x, arrow_y - 10), (arrow_x + 15, arrow_y), 3)
                pygame.draw.line(screen, (255, 200, 0), (arrow_x, arrow_y + 10), (arrow_x + 15, arrow_y), 3)
    
    # ----------------------------------------------------------------------
    # BRIEFING
    # ----------------------------------------------------------------------
    def _update_briefing(self):
        # No automatic skip, only manual key press
        pass
    
    def _start_level(self):
        self.current_state = self.states['PLAYING']
        self.game.level_start_time = pygame.time.get_ticks()
        self.game.load_level(self.game.current_level)
    
    def _draw_briefing(self, screen):
        screen.fill((0, 0, 0))
        level_num = self.game.current_level
        lines = [
            f"МИССИЯ {level_num}",
            "",
            "ЗАДАЧИ:",
            "- Eliminate all enemy forces",
            "- Find the exit",
            "",
            "Intel suggests heavy resistance in this sector",
            "Proceed with caution, soldier.",
            "",
            "Press any key to continue..."
        ]
        
        for i, line in enumerate(lines):
            y = int(setting.CELL_H * 2) + i * int(setting.CELL_H * 0.6)
            color = (200, 200, 200)
            if 'ЗАДАЧИ' in line or i == 0:
                color = (255, 200, 0)
            font = self.font_tile if line.startswith('МИССИЯ') else self.font_normal
            text = font.render(line, True, color)
            screen.blit(text, (int(setting.CELL_W) * 2, y))
        
        self.__draw_minimap(screen, int(setting.CELL_W * 12), int(setting.CELL_H * 2))
    
    def __draw_minimap(self, screen, x, y):
        try:
            size = int(setting.CELL_H * 4)
            map_w = len(self.game.map.text_map[0])
            map_h = len(self.game.map.text_map)
            cell_size = size // max(map_w, map_h)
            
            for j, row in enumerate(self.game.map.text_map):
                for i, char in enumerate(row):
                    color = (100, 100, 100) if char != '_' and char not in '2345' else (40, 40, 40)
                    if char == 'E':
                        color = (0, 200, 0)
                    rect = pygame.Rect(x + i * cell_size, y + j * cell_size, cell_size - 1, cell_size - 1)
                    pygame.draw.rect(screen, color, rect)
        except Exception:
            pass
    
    # ----------------------------------------------------------------------
    # PAUSE
    # ----------------------------------------------------------------------
    def _update_pause(self):
        pass
    
    def _draw_pause(self, screen):
        dark = pygame.Surface((setting.WIDTH, setting.HEIGHT))
        dark.set_alpha(180)
        dark.fill((0, 0, 0))
        screen.blit(dark, (0, 0))
        
        title = self.font_tile.render("PAUSED", True, (255, 200, 0))
        title_rect = title.get_rect(center=(setting.WIDTH // 2, int(setting.CELL_H * 3)))
        screen.blit(title, title_rect)
        
        options = ['RESUME', 'RESTART LEVEL', 'MAIN MENU', 'QUIT']
        for i, opt in enumerate(options):
            y = setting.HEIGHT // 2 + i * 60
            color = (255, 255, 255) if i == self.selected_option else (150, 150, 150)
            text = self.font_normal.render(opt, True, color)
            text_rect = text.get_rect(center=(setting.WIDTH // 2, y))
            screen.blit(text, text_rect)
    
    # ----------------------------------------------------------------------
    # LEVEL END
    # ----------------------------------------------------------------------
    def _update_level_end(self):
        pass
    
    def _draw_level_end(self, screen):
        screen.fill((0, 0, 0))
        title = self.font_tile.render("MISSION COMPLETE", True, (0, 255, 0))
        title_rect = title.get_rect(center=(setting.WIDTH // 2, int(setting.CELL_H * 3)))
        screen.blit(title, title_rect)
        
        stats = [
            f"ENEMIES KILLED: {self._get_kills_count()}",
            f"TIME: {self._get_level_time()}",
            "",
            "PRESS ANY KEY TO CONTINUE"
        ]
        for i, stat in enumerate(stats):
            y = setting.HEIGHT // 2 + i * 40
            color = (200, 200, 200) if "PRESS" not in stat else (255, 200, 0)
            text = self.font_normal.render(stat, True, color)
            text_rect = text.get_rect(center=(setting.WIDTH // 2, y))
            screen.blit(text, text_rect)
    
    # ----------------------------------------------------------------------
    # DEATH SCREEN
    # ----------------------------------------------------------------------
    def _update_dead(self):
        pass
    
    def _draw_dead(self, screen):
        if self.backgrounds['dead']:
            screen.blit(self.backgrounds['dead'], (0, 0))
        else:
            screen.fill((40, 0, 0))
        
        title = self.font_tile.render("ПОГИБ ЗА ЧЕСТЬ", True, (255, 0, 0))
        title_rect = title.get_rect(center=(setting.WIDTH // 2, int(setting.CELL_H * 2)))
        screen.blit(title, title_rect)
        
        tips = [
            "СОВЕТ: Кармак придумал стрейфы не для того чтобы ты захлебывался кровью",
            "СОВЕТ: Хэдшоты? Не. Не слышали про такое",
            "СОВЕТ: Кончились патроны? Автору некогда было допиливать механику подбора",
            "СОВЕТ: Корпорация Marvin - злейший враг человека",
            "СОВЕТ: Используй укрытия и стрейфы. Ты же не Блацкович"
        ]
        if not hasattr(self, 'current_tip'):
            self.current_tip = random.choice(tips)
        
        tip_text = self.font_small.render(self.current_tip, True, (200, 200, 200))
        tip_rect = tip_text.get_rect(center=(setting.WIDTH // 2, setting.HEIGHT - 100))
        screen.blit(tip_text, tip_rect)
        
        restart = self.font_normal.render("PRESS R TO RESTART", True, (255, 255, 255))
        menu = self.font_normal.render("PRESS M FOR MAIN MENU", True, (255, 255, 255))
        r_rect = restart.get_rect(center=(setting.WIDTH // 2, setting.HEIGHT - 200))
        m_rect = menu.get_rect(center=(setting.WIDTH // 2, setting.HEIGHT - 150))
        screen.blit(restart, r_rect)
        screen.blit(menu, m_rect)
    
    # ----------------------------------------------------------------------
    # CUTSCENE
    # ----------------------------------------------------------------------
    def _update_cutscene(self):
        if not hasattr(self, 'cutscene_start'):
            self.cutscene_start = pygame.time.get_ticks()
        if pygame.time.get_ticks() - self.cutscene_start > 3000:
            self.current_state = self.states['MENU']
    
    def _draw_cutscene(self, screen):
        screen.fill((0, 0, 0))
        text = self.font_tile.render("CUTSCENE", True, (255, 255, 255))
        text_rect = text.get_rect(center=(setting.WIDTH // 2, setting.HEIGHT // 2))
        screen.blit(text, text_rect)
    
    # ----------------------------------------------------------------------
    # OPTIONS
    # ----------------------------------------------------------------------
    def _update_options(self):
        pass
    
    def _draw_options(self, screen):
        screen.fill((20, 20, 40))
        
        # Заголовок
        title = self.font_tile.render("НАСТРОЙКИ", True, (255, 200, 0))
        title_rect = title.get_rect(center=(setting.WIDTH // 2, int(setting.CELL_H * 2)))
        screen.blit(title, title_rect)
        
        start_row = 4
        # 1. Чувствительность мыши
        y_text = int(setting.CELL_H * start_row)
        sens_text = self.font_normal.render(f"ЧУВСТВИТЕЛЬНОСТЬ МЫШИ: {setting.MOUSE_SENSITIVITY:.3f}", True, (200, 200, 200))
        sens_rect = sens_text.get_rect(center=(setting.WIDTH // 2, y_text))
        screen.blit(sens_text, sens_rect)
        
        if self.selected_option == 0:
            bar_width = int(setting.CELL_W * 6)
            bar_x = setting.WIDTH // 2 - bar_width // 2
            bar_y = y_text + int(setting.CELL_H * 0.3)
            pygame.draw.rect(screen, (80, 80, 80), (bar_x, bar_y, bar_width, 8))
            # Normalize value from 0.0005..0.01 to 0..1
            norm = (setting.MOUSE_SENSITIVITY - 0.0005) / (0.01 - 0.0005)
            handle_x = bar_x + int(bar_width * norm)
            pygame.draw.rect(screen, (255, 200, 0), (handle_x - 5, bar_y - 4, 10, 16))
            left_arr = self.font_small.render("<", True, (255, 200, 0))
            right_arr = self.font_small.render(">", True, (255, 200, 0))
            screen.blit(left_arr, (bar_x - 25, bar_y - 8))
            screen.blit(right_arr, (bar_x + bar_width + 15, bar_y - 8))
        
        # 2. Громкость
        y_text = int(setting.CELL_H * (start_row + 1.2))
        vol_text = self.font_normal.render(f"ГРОМКОСТЬ: {int(setting.MASTER_VOLUME * 100)}%", True, (200, 200, 200))
        vol_rect = vol_text.get_rect(center=(setting.WIDTH // 2, y_text))
        screen.blit(vol_text, vol_rect)
        
        if self.selected_option == 1:
            bar_width = int(setting.CELL_W * 6)
            bar_x = setting.WIDTH // 2 - bar_width // 2
            bar_y = y_text + int(setting.CELL_H * 0.3)
            pygame.draw.rect(screen, (80, 80, 80), (bar_x, bar_y, bar_width, 8))
            handle_x = bar_x + int(bar_width * setting.MASTER_VOLUME)
            pygame.draw.rect(screen, (255, 200, 0), (handle_x - 5, bar_y - 4, 10, 16))
            left_arr = self.font_small.render("<", True, (255, 200, 0))
            right_arr = self.font_small.render(">", True, (255, 200, 0))
            screen.blit(left_arr, (bar_x - 25, bar_y - 8))
            screen.blit(right_arr, (bar_x + bar_width + 15, bar_y - 8))
        
        # 3. Кнопка НАЗАД
        y_text = int(setting.CELL_H * (start_row + 2.4))
        color = (255, 255, 255) if self.selected_option == 2 else (150, 150, 150)
        back_text = self.font_normal.render("НАЗАД", True, color)
        back_rect = back_text.get_rect(center=(setting.WIDTH // 2, y_text))
        screen.blit(back_text, back_rect)
        
        # Подсказка
        tip = self.font_small.render("↑/↓ - ВЫБОР, ←/→ - ИЗМЕНИТЬ, ESC/ENTER - НАЗАД", True, (150, 150, 150))
        tip_rect = tip.get_rect(center=(setting.WIDTH // 2, setting.HEIGHT - int(setting.CELL_H * 2)))
        screen.blit(tip, tip_rect)
        
        # Таблица управления
        controls_start_row = 10
        controls = [
            "УПРАВЛЕНИЕ:", "W/A/S/D - ДВИЖЕНИЕ", "МЫШЬ - ПОВОРОТ",
            "ЛКМ / ПРОБЕЛ - СТРЕЛЬБА", "1-4 - СМЕНА ОРУЖИЯ", "ESC - ПАУЗА/ВЫХОД"
        ]
        for i, line in enumerate(controls):
            y = int(setting.CELL_H * (controls_start_row + i * 0.4))
            color = (255, 200, 0) if i == 0 else (180, 180, 180)
            txt = self.font_small.render(line, True, color)
            txt_rect = txt.get_rect(center=(setting.WIDTH // 2, y))
            screen.blit(txt, txt_rect)
    
    # ----------------------------------------------------------------------
    # HELPERS
    # ----------------------------------------------------------------------
    def _get_kills_count(self):
        return self.game.total_kills
    
    def _get_level_time(self):
        return f"{self.game.level_time // 60}:{self.game.level_time % 60:02d}"