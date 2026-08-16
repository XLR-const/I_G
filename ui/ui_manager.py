import pygame
import setting
import sys
import random
from utils.save_system import SaveSystem
from config.game_data import ACTS_SEQUENCE
import os
import math


class UIManager:
    """Менеджер пользовательского интерфейса

    Управляет всеми экранами: меню, пауза, брифинг, смерть, конец уровня.

    Attributes:
        game: Объект игры
        font_tile_path: Путь для шрифта заголовка
        font_path: Путь для шрифта
        font_tile: Шрифт для заголовков
        font_normal: Основной шрифт
        font_small: Мелкий шрифт
        states: Словарь состояний UI
        current_state: Текущее состояние
        selected_option: Выбранный пункт меню
        briefing_images: Словарь картинок брифингов
        backgrounds: Словарь фонов
        swap_sound: Звук переключения
        enter_sound: Звук выбора
    """

    def __init__(self, game):
        """Инициализирует UI менеджер

        Args:
            game: Объект игры
        """
        self.game = game
        self.font_path = 'resources/fonts/Fy.ttf'
        self.font_tile_path = 'resources/fonts/Evolve.otf'
        self.font_tile = pygame.font.Font(self.font_tile_path, int(setting.CELL_H * 2))
        self.font_normal = pygame.font.Font(self.font_path, int(setting.CELL_H * 0.6))
        self.font_small = pygame.font.Font(self.font_path, int(setting.CELL_H * 0.4))

        self.states = {
            'BOOT': 0,
            'MENU': 1,
            'BRIEFING': 2,
            'PLAYING': 3,
            'PAUSE': 4,
            'LEVEL_END': 5,
            'DEAD': 6,
            'CUTSCENE': 7,
            'OPTIONS': 8
        }

        self.current_state = self.states['BOOT']
        self.selected_option = 0

        self.briefing_images = {}
        self.backgrounds = {}
        self.swap_sound = None
        self.enter_sound = None

        self.load_assets()

    def load_assets(self):
        """Загружает все ассеты UI"""
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


        # Брифинги
        self.briefing_images = {}
        briefings_base_path = "resources/briefings"
        
        # 1. Сначала обрабатываем наш дебаг-акт для dev_mode, если он используется
        all_acts = list(ACTS_SEQUENCE)
        if "act_test" not in all_acts:
            all_acts.append("act_test")

        # 2. Сканируем папки для каждого акта
        for act in all_acts:
            act_folder = os.path.join(briefings_base_path, act)
            
            if os.path.exists(act_folder):
                # Ищем все файлы вида level_X.png в папке акта
                for filename in os.listdir(act_folder):
                    if filename.startswith("level_") and filename.endswith(".png"):
                        try:
                            # Вытаскиваем номер уровня из имени файла (н-р из "level_1.png" берем 1)
                            level_num = int(filename.split("_")[1].split(".")[0])
                            
                            path = os.path.join(act_folder, filename)
                            img = pygame.image.load(path).convert()
                            img = pygame.transform.scale(img, (setting.WIDTH, setting.HEIGHT))
                            
                            # 🔥 КРИТИЧЕСКИЙ ФИКС: Сохраняем в словарь под составным ключом (акт, уровень)
                            self.briefing_images[(act, level_num)] = img
                            print(f"  --> Успешно: брифинг для {act} -> Уровень {level_num}")
                        except Exception as e:
                            print(f"  ❌ Ошибка парсинга файла {filename} в акте {act}: {e}")
                            pass
            else:
                print(f"  ⚠️ Папка брифингов для акта '{act}' не найдена на диске")


        try:
            self.swap_sound = pygame.mixer.Sound('resources/ui_sounds/swap.wav')
            self.swap_sound.set_volume(0.1)
        except Exception:
            self.swap_sound = None

        try:
            self.enter_sound = pygame.mixer.Sound('resources/ui_sounds/enter.wav')
            self.enter_sound.set_volume(0.1)
        except Exception:
            self.enter_sound = None

    def handle_event(self, event):
        """Обрабатывает события UI

        Args:
            event: Событие pygame

        Returns:
            bool: True если событие обработано
        """
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
            return False
        if self.current_state == self.states['OPTIONS']:
            return self._handle_options_event(event)
        return False

    # ----------------------------------------------------------------------
    # HANDLERS
    # ----------------------------------------------------------------------

    def _handle_menu_event(self, event):
        """Обрабатывает события главного меню

        Args:
            event: Событие pygame

        Returns:
            bool: True если событие обработано
        """
        options_len = 4

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected_option = (self.selected_option + 1) % options_len
                if self.swap_sound:
                    self.swap_sound.play()
                return True
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected_option = (self.selected_option - 1) % options_len
                if self.swap_sound:
                    self.swap_sound.play()
                return True
            if event.key == pygame.K_RETURN:
                if self.selected_option == 0:
                    self.enter_sound.play()
                    self.game.level_manager.reset_game()
                    self.game.intro_player.play()
                    return True
                elif self.selected_option == 1:
                    saved = SaveSystem.load()
                    if saved:
                        self.game.current_level = int(saved['current_level'])
                        self.game.total_kills = int(saved['total_kills'])
                        self.game.level_manager.current_level = self.game.current_level
                        self.game.level_manager.load_level(self.game.current_level)
                        self.current_state = self.states['BRIEFING']
                    else:
                        self.game.level_manager.reset_game()
                        self.current_state = self.states['BRIEFING']
                elif self.selected_option == 2:
                    self.selected_option = 0
                    self.current_state = self.states['OPTIONS']
                elif self.selected_option == 3:
                    pygame.quit()
                    sys.exit()
                return True
        return False

    def _handle_briefing_event(self, event):
        """Обрабатывает события экрана брифинга

        Args:
            event: Событие pygame

        Returns:
            bool: True если событие обработано
        """
        if event.type == pygame.KEYDOWN:
            self._start_level()
            return True
        return False

    def _handle_pause_event(self, event):
        """Обрабатывает события меню паузы

        Args:
            event: Событие pygame

        Returns:
            bool: True если событие обработано
        """
        options_len = 4

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.current_state = self.states['PLAYING']
                return True
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected_option = (self.selected_option - 1) % options_len
                if self.swap_sound:
                    self.swap_sound.play()
                return True
            if event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected_option = (self.selected_option + 1) % options_len
                if self.swap_sound:
                    self.swap_sound.play()
                return True
            if event.key == pygame.K_RETURN:
                if self.enter_sound:
                    self.enter_sound.play()
                if self.selected_option == 0:
                    self.current_state = self.states['PLAYING']
                elif self.selected_option == 1:
                    self.game.level_start_time = pygame.time.get_ticks()
                    self.game.load_level(self.game.current_level)
                    self.current_state = self.states['PLAYING']
                elif self.selected_option == 2:
                    self.current_state = self.states['MENU']
                elif self.selected_option == 3:
                    pygame.quit()
                    sys.exit()
                return True
        return False

    def _handle_level_end_event(self, event):
        """Обрабатывает события экрана конца уровня

        Args:
            event: Событие pygame

        Returns:
            bool: True если событие обработано
        """
        if event.type == pygame.KEYDOWN:
            self.game.load_level(self.game.level_manager.current_level)
            self.current_state = self.states['BRIEFING']
            return True
        return False

    def _handle_dead_event(self, event):
        """Обрабатывает события экрана смерти

        Args:
            event: Событие pygame

        Returns:
            bool: True если событие обработано
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                self.game.level_start_time = pygame.time.get_ticks()
                self.game.load_level(self.game.current_level)
                self.current_state = self.states['PLAYING']
                return True
            if event.key == pygame.K_m:
                self.current_state = self.states['MENU']
                return True
        return False

    def _handle_cutscene_event(self, event):
        """Обрабатывает события катсцены

        Args:
            event: Событие pygame

        Returns:
            bool: True если событие обработано
        """
        if event.type == pygame.KEYDOWN:
            self.current_state = self.states['MENU']
            return True
        return False

    def _handle_options_event(self, event):
        """Обрабатывает события меню настроек

        Args:
            event: Событие pygame

        Returns:
            bool: True если событие обработано
        """
        options_len = 3

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_option = (self.selected_option - 1) % options_len
                if self.swap_sound:
                    self.swap_sound.play()
                return True
            if event.key == pygame.K_DOWN:
                self.selected_option = (self.selected_option + 1) % options_len
                if self.swap_sound:
                    self.swap_sound.play()
                return True
            if event.key == pygame.K_LEFT:
                if self.selected_option == 0:
                    new_val = max(0.0005, setting.MOUSE_SENSITIVITY - 0.0005)
                    setting.MOUSE_SENSITIVITY = new_val
                elif self.selected_option == 1:
                    new_val = max(0.0, setting.MASTER_VOLUME - 0.1)
                    setting.MASTER_VOLUME = new_val
                return True
            if event.key == pygame.K_RIGHT:
                if self.selected_option == 0:
                    new_val = min(0.01, setting.MOUSE_SENSITIVITY + 0.0005)
                    setting.MOUSE_SENSITIVITY = new_val
                elif self.selected_option == 1:
                    new_val = min(1.0, setting.MASTER_VOLUME + 0.1)
                    setting.MASTER_VOLUME = new_val
                return True
            if event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                if self.enter_sound:
                    self.enter_sound.play()
                if self.selected_option == 2:
                    self.current_state = self.states['MENU']
                return True
        return False

    # ----------------------------------------------------------------------
    # UPDATE LOOPS
    # ----------------------------------------------------------------------

    def update(self):
        """Обновляет состояние UI"""
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
            pass
        elif self.current_state == self.states['OPTIONS']:
            self._update_options()

    def draw(self, screen):
        """Отрисовывает текущий UI экран

        Args:
            screen: Экран pygame
        """
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
        """Обновляет экран загрузки: считает тайминги"""
        if not hasattr(self, 'boot_start'):
            self.boot_start = pygame.time.get_ticks()
            
        # Задаем общее время загрузки в 2500 мс (2.5 секунды), чтобы логи успели пробежать
        self.boot_duration = 2500
        
        if pygame.time.get_ticks() - self.boot_start > self.boot_duration:
            self.current_state = self.states['MENU']

    def _draw_boot(self, screen):
        """Рисует стилизованный Sci-Fi экран инициализации BIOS/HUD"""
        # Гарантируем, что boot_start инициализирован во избежание ZeroDivisionError
        if not hasattr(self, 'boot_start'):
            self.boot_start = pygame.time.get_ticks()
            
        now = pygame.time.get_ticks()
        elapsed = now - self.boot_start
        duration = getattr(self, 'boot_duration', 2500)
        progress = min(1.0, elapsed / duration)
        
        # 1. СТРОГИЙ ЧЕРНЫЙ ФОН ТЕРМИНАЛА
        screen.fill((10, 12, 16))
        
        # Цветовая палитра военного HUD
        neon_blue = (0, 140, 255)
        neon_cyan = (0, 255, 210)
        dark_metal = (35, 45, 55)
        text_gray = (160, 175, 185)

        # 2. ИМИТАЦИЯ СИСТЕМНЫХ ЛОГОВ (БЕГУЩИЕ СТРОКИ)
        # Массив логов с таймингами их появления на экране (в долях прогресса)
        boot_logs = [
            (0.00, "INITIALIZING BOOT PROTOCOL..."),
            (0.12, "CORE ENGINE: STABLE (VER 2.5D_ALPHA)"),
            (0.25, "RAYCASTING MATRIX... LOADED"),
            (0.38, "Z-BUFFER MATRIX... ALLOCATED"),
            (0.50, "MAPPING REYKASTER GRID... OK"),
            (0.65, "CACHING TEXTURES & SPRITES... OK"),
            (0.78, "CONNECTING DATA-DRIVEN ACT SEQUENCER..."),
            (0.90, "TACTICAL HUD VISOR... INITIALIZED"),
            (0.98, "SYSTEMS ONLINE. WELCOME, OPERATOR.")
        ]
        
        log_y_start = int(setting.HEIGHT * 0.15)
        log_spacing = 30
        
        # Выводим на экран только те строки, до которых дошел прогресс времени
        for log_trigger_progress, log_text in boot_logs:
            if progress >= log_trigger_progress:
                # Последняя появившаяся строка горит неоновым бирюзовым, остальные — серым текстом
                is_latest = (log_trigger_progress == max(t for t, _ in boot_logs if progress >= t))
                color = neon_cyan if is_latest else text_gray
                
                # Добавляем к последней строке мигающий курсор "_"
                display_text = log_text
                if is_latest and (now // 250) % 2 == 0 and progress < 0.98:
                    display_text += "_"
                    
                log_surf = self.font_normal.render(display_text, True, color)
                screen.blit(log_surf, (int(setting.WIDTH * 0.1), log_y_start))
                log_y_start += log_spacing

        # 3. ЦЕНТРАЛЬНЫЙ СТАТУС ЗАГРУЗКИ
        # Пишем крупным шрифтом статус по центру экрана
        status_str = f"LOADING SYSTEM... {int(progress * 100)}%"
        if progress >= 1.0:
            status_str = "SYSTEMS ONLINE"
            
        status_text = self.font_tile.render(status_str, True, neon_blue)
        status_rect = status_text.get_rect(center=(setting.WIDTH // 2, setting.HEIGHT // 2 + 60))
        screen.blit(status_text, status_rect)

        # 4. 🔥 НОВЫЙ Sci-Fi ПРОГРЕСС-БАР С СЕГМЕНТАМИ
        bar_width = int(setting.WIDTH * 0.5)
        bar_height = 14
        bx = setting.WIDTH // 2 - bar_width // 2
        by = status_rect.bottom + 25
        
        # Задняя рамка-подложка
        pygame.draw.rect(screen, dark_metal, (bx, by, bar_width, bar_height), 1)
        
        # Рисуем заполнение в виде дискретных Sci-Fi блоков (черточек), а не сплошной полосой
        num_segments = 25  # Сколько всего блоков в полоске
        segments_to_fill = int(num_segments * progress)
        segment_width = (bar_width - (num_segments - 1) * 3) // num_segments
        
        for seg in range(num_segments):
            seg_x = bx + seg * (segment_width + 3)
            # Если этот сегмент должен быть заполнен по времени
            if seg < segments_to_fill:
                # Первые сегменты синие, финальные переходят в сочную бирюзу
                seg_color = neon_cyan if seg > num_segments * 0.7 else neon_blue
                pygame.draw.rect(screen, seg_color, (seg_x, by + 2, segment_width, bar_height - 4))
            else:
                # Неактивные сегменты еле заметны на фоне
                pygame.draw.rect(screen, (20, 25, 35), (seg_x, by + 2, segment_width, bar_height - 4))
                
        # 5. Мягкие Sci-Fi уголки по краям экрана для сохранения общей стилистики HUD
        margin, length = 20, 15
        
        # Левый верхний угол
        pygame.draw.line(screen, dark_metal, (margin, margin), (margin + length, margin), 1)
        pygame.draw.line(screen, dark_metal, (margin, margin), (margin, margin + length), 1)
        
        # Правый верхний угол (Фикс: теперь строго передается цвет dark_metal)
        pygame.draw.line(screen, dark_metal, (setting.WIDTH - margin, margin), (setting.WIDTH - margin - length, margin), 1)
        pygame.draw.line(screen, dark_metal, (setting.WIDTH - margin, margin), (setting.WIDTH - margin, margin + length), 1)



    # ----------------------------------------------------------------------
    # MAIN MENU
    # ----------------------------------------------------------------------

    def _update_menu(self):
        """Обновляет главное меню: рассчитывает тайминги для мягких Sci-Fi эффектов"""
        now = pygame.time.get_ticks()
        
        # Мягкая пульсация активного пункта (синус от 160 до 255)
        self.menu_pulse = int(207 + 48 * math.sin(now * 0.004))
        
        # Эффект легкого шума терминала (микро-глитч яркости голограммы)
        self.hud_glitch = random.choice([0, 0, 0, 0, 12, 0, -8, 0, 0])

    def _draw_menu(self, screen):
        """Рисует главное меню: исправлен контраст цветов и фикс сложения кортежей"""
        # 1. Отрисовка базового задника
        if self.backgrounds.get('menu'):
            screen.blit(self.backgrounds['menu'], (0, 0))
        else:
            screen.fill((10, 12, 16))

        # 2. Мягкая виньетка по краям экрана для увеличения контраста текста
        vignette = pygame.Surface((setting.WIDTH, setting.HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(vignette, (0, 0, 0, 45), vignette.get_rect(), border_radius=20)
        screen.blit(vignette, (0, 0))

        # 3. ЛОГОТИП ИГРЫ (С неоновым Sci-Fi свечением плазмы)
        title_text = "Ilyusha Grate"
        
        # Разделяем координаты центра логотипа на X и Y
        tx = setting.WIDTH // 2
        ty = int(setting.CELL_H * 1.5)
        
        glitch_val = getattr(self, 'hud_glitch', 0)
        pulse_val = getattr(self, 'menu_pulse', 255)
        logo_y_brightness = max(0, min(255, 230 + glitch_val))
        
        # Размытый неоновый Glow-ореол под логотипом (Фикс: попиксельный сдвиг без сложения кортежей)
        glow_color = (0, int(logo_y_brightness * 0.4), int(logo_y_brightness * 0.8))
        for ox, oy in [(-2, -2), (2, 2), (-2, 2), (2, -2)]:
            glow_surf = self.font_tile.render(title_text, True, glow_color)
            screen.blit(glow_surf, glow_surf.get_rect(center=(tx + ox, ty + oy)))

        # Тень под логотипом
        title_shadow = self.font_tile.render(title_text, True, (15, 20, 30))
        screen.blit(title_shadow, title_shadow.get_rect(center=(tx + 2, ty + 2)))
        
        # Сам логотип (Твой оригинальный шрифт font_tile)
        title = self.font_tile.render(title_text, True, (255, int(logo_y_brightness * 0.85), 0))
        screen.blit(title, title.get_rect(center=(tx, ty)))

        # 4. НАСТРОЙКА ЦЕНТРОВКИ И КОНТРАСТНЫХ ЦВЕТОВ ПУНКТОВ
        menu_center_x = int(setting.WIDTH * 0.70) 
        options = ['НОВАЯ ИГРА', 'ЗАГРУЗИТЬ ПОСЛЕДНЮЮ ИГРУ', 'НАСТРОЙКИ', 'ВЫХОД']
        
        for i, opt in enumerate(options):
            # Шаг по вертикали под твой родной размер
            y = setting.HEIGHT // 2 + i * 60
            
            if i == self.selected_option:
                # 🔷 АКТИВНЫЙ ПУНКТ: Яркий неоновый бирюзовый
                g_color = max(0, min(255, pulse_val + glitch_val))
                color = (0, g_color, 255)
                
                text = self.font_normal.render(opt, True, color)
                text_rect = text.get_rect(center=(menu_center_x, y))
                
                # Квадратные скобки [ ]
                bracket_l = self.font_normal.render("[ ", True, color)
                bracket_l_rect = bracket_l.get_rect(right=text_rect.left - 15, centery=text_rect.centery)
                
                bracket_r = self.font_normal.render(" ]", True, color)
                bracket_r_rect = bracket_r.get_rect(left=text_rect.right + 15, centery=text_rect.centery)
                
                screen.blit(bracket_l, bracket_l_rect)
                screen.blit(bracket_r, bracket_r_rect)
            else:
                # ⚪ КОНТРАСТНЫЙ ЦВЕТ: Светло-серый тактический металл (Больше не сливается со скалами!)
                color = (220, 225, 230)
                
                text = self.font_normal.render(opt, True, color)
                text_rect = text.get_rect(center=(menu_center_x, y))

            # Выводим оригинальный резкий пиксельный текст на экран
            screen.blit(text, text_rect)


    # ----------------------------------------------------------------------
    # BRIEFING
    # ----------------------------------------------------------------------

    def _update_briefing(self):
        """Обновляет экран брифинга"""
        pass

    def _start_level(self):
        """Запускает уровень"""
        self.current_state = self.states['PLAYING']
        self.game.level_start_time = pygame.time.get_ticks()
        self.game.load_level(self.game.current_level)

    def _draw_briefing(self, screen):
        """Рисует экран брифинга"""
        screen.fill((0, 0, 0))
        level_num = self.game.current_level
        act_name = self.game.level_manager.get_current_act_name()
        
        briefing_key = (act_name, level_num)

        if briefing_key in self.briefing_images:
            screen.blit(self.briefing_images[briefing_key], (0, 0))


            """font = pygame.font.Font(None, 36)
            text = font.render("Нажмите на любую кнопку...", True, (255, 255, 255))
            text_rect = text.get_rect(center=(setting.WIDTH // 2, setting.HEIGHT - setting.CELL_H))

            bg = pygame.Surface((text.get_width() + 20, text.get_height() + 10))
            bg.set_alpha(128)
            bg.fill((0, 0, 0))
            screen.blit(bg, (text_rect.x - 10, text_rect.y - 5))
            screen.blit(text, text_rect)"""
        else:
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

            self._draw_minimap(screen, int(setting.CELL_W * 12), int(setting.CELL_H * 2))

    def _draw_minimap(self, screen, x, y):
        """Рисует миникарту на экране брифинга

        Args:
            screen: Экран pygame
            x: Координата X
            y: Координата Y
        """
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
        """Обновляет меню паузы: рассчитывает тайминги для мягких Sci-Fi эффектов"""
        now = pygame.time.get_ticks()
        
        # Мягкая пульсация активного пункта (синус)
        self.pause_pulse = int(207 + 48 * math.sin(now * 0.004))
        
        # Микро-глитч яркости голограммы
        self.pause_glitch = random.choice([0, 0, 0, 0, 12, 0, -8, 0, 0])

    def _draw_pause(self, screen):
        """Рисует минималистичное меню паузы поверх яркого фона базы"""
        menu_font = self.font_normal
        title_font = self.font_tile

        # 1. ЗАГРУЗКА И КЭШИРОВАНИЕ ФОНА НАПРЯМУЮ С ДИСКА
        if not hasattr(self, '_pause_bg_cached'):
            bg_path = "resources/ui/main_menu_bg.png"
            if os.path.exists(bg_path):
                try:
                    img = pygame.image.load(bg_path).convert()
                    self._pause_bg_cached = pygame.transform.scale(img, (setting.WIDTH, setting.HEIGHT))
                except:
                    self._pause_bg_cached = None
            else:
                self._pause_bg_cached = None

        # Отрисовка фона
        if self._pause_bg_cached:
            screen.blit(self._pause_bg_cached, (0, 0))
        else:
            screen.fill((10, 12, 16))

        # 🔥 ФИКС 1: ДЕЛАЕМ ФОН ЯРЧЕ
        # Снижаем плотность альфа-канала с 195 до 110. 
        # Теперь база и персонаж будут видны четко, сочно и контрастно!
        dark = pygame.Surface((setting.WIDTH, setting.HEIGHT), pygame.SRCALPHA)
        dark.fill((4, 7, 14, 110)) 
        screen.blit(dark, (0, 0))

        # Кинематографичная легкая виньетка по краям
        vignette = pygame.Surface((setting.WIDTH, setting.HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(vignette, (0, 0, 0, 50), vignette.get_rect(), border_radius=30)
        screen.blit(vignette, (0, 0))

        # Цвет линий тактических уголков шлема
        blue_line = (0, 140, 255)

        # 🔥 ФИКС 2: ВСЕ ЛИШНИЕ ОБЪЕКТЫ (РАДАР, ЛУЧИ, СИНУСОИДЫ) ПОЛНОСТЬЮ УДАЛЕНЫ

        # Оставляем только аккуратные тонкие Sci-Fi уголки по краям экрана для сохранения HUD-стилистики
        margin, length = 25, 20
        pygame.draw.line(screen, blue_line, (margin, margin), (margin + length, margin), 1)
        pygame.draw.line(screen, blue_line, (margin, margin), (margin, margin + length), 1)
        pygame.draw.line(screen, blue_line, (setting.WIDTH - margin, margin), (setting.WIDTH - margin - length, margin), 1)
        pygame.draw.line(screen, blue_line, (setting.WIDTH - margin, margin), (setting.WIDTH - margin, margin + length), 1)

        # 2. ЗАГЛУШКА-ЗАГОЛОВОК "ПАУЗА"
        title_text = "ПАУЗА"
        tx, ty = setting.WIDTH // 2, int(setting.CELL_H * 2.5)
        
        glitch_val = getattr(self, 'pause_glitch', 0)
        pulse_val = getattr(self, 'pause_pulse', 255)
        title_brightness = max(0, min(255, 230 + glitch_val))
        
        # Эффект мягкого свечения под заголовком
        glow_color = (int(title_brightness * 0.9), int(title_brightness * 0.7), 0)
        for ox, oy in [(-2, -2), (2, 2), (-2, 2), (2, -2)]:
            glow_surf = title_font.render(title_text, True, glow_color)
            screen.blit(glow_surf, glow_surf.get_rect(center=(tx + ox, ty + oy)))

        title_shadow = title_font.render(title_text, True, (5, 5, 10))
        screen.blit(title_shadow, title_shadow.get_rect(center=(tx + 3, ty + 3)))
        
        title = title_font.render(title_text, True, (255, int(title_brightness * 0.8), 0))
        screen.blit(title, title.get_rect(center=(tx, ty)))

        # 3. ОТРИСОВКА ПУНКТОВ МЕНЮ (Твой родной резкий пиксельный шрифт)
        menu_center_x = setting.WIDTH // 2
        options = ['ПРОДОЛЖИТЬ', 'ПЕРЕЗАПУСТИТЬ УРОВЕНЬ', 'ГЛАВНОЕ МЕНЮ', 'ВЫХОД']

        for i, opt in enumerate(options):
            y = setting.HEIGHT // 2 + i * 60
            
            if i == self.selected_option:
                # 🔷 Активный пункт: Неоновый бирюзовый с легким мерцанием
                g_color = max(0, min(255, pulse_val + glitch_val))
                color = (0, g_color, 255)
                
                text = menu_font.render(opt, True, color)
                text_rect = text.get_rect(center=(menu_center_x, y))
                
                # Строгие квадратные скобки вокруг активной строки
                bracket_l = menu_font.render("[ ", True, color)
                bracket_l_rect = bracket_l.get_rect(right=text_rect.left - 15, centery=text_rect.centery)
                
                bracket_r = menu_font.render(" ]", True, color)
                bracket_r_rect = bracket_r.get_rect(left=text_rect.right + 15, centery=text_rect.centery)
                
                screen.blit(bracket_l, bracket_l_rect)
                screen.blit(bracket_r, bracket_r_rect)
            else:
                # ⚪ Неактивные пункты: Контрастный светло-серый стальной HUD-цвет
                color = (190, 200, 210)
                text = menu_font.render(opt, True, color)
                text_rect = text.get_rect(center=(menu_center_x, y))

            screen.blit(text, text_rect)



    # ----------------------------------------------------------------------
    # LEVEL END
    # ----------------------------------------------------------------------

    def _update_level_end(self):
        """Обновляет экран конца уровня"""
        pass

    def _draw_level_end(self, screen):
        """Рисует экран конца уровня"""
        screen.fill((0, 0, 0))
        title = self.font_tile.render("МИССИЯ ПРОЙДЕНА", True, (0, 255, 0))
        title_rect = title.get_rect(center=(setting.WIDTH // 2, int(setting.CELL_H * 3)))
        screen.blit(title, title_rect)

        stats = [
            f"УБИТО: {self.game.level_manager.total_kills}",
            f"ВРЕМЯ: {self._get_level_time()}",
            "",
            "НАЖМИТЕ ЛЮБУЮ КЛАВИШУ ДЛЯ ПРОДОЛЖЕНИЯ"
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
        """Обновляет экран смерти"""
        pass

    def _draw_dead(self, screen):
        """Рисует экран смерти"""
        if self.backgrounds.get('dead'):
            screen.blit(self.backgrounds['dead'], (0, 0))
        else:
            screen.fill((40, 0, 0))

        title = self.font_tile.render("ПОГИБ В БОЮ", True, (255, 0, 0))
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

        restart = self.font_normal.render("нажми R для перезапуска", True, (255, 255, 255))
        menu = self.font_normal.render("нажми M для главного меню", True, (255, 255, 255))
        r_rect = restart.get_rect(center=(setting.WIDTH // 2, setting.HEIGHT - 200))
        m_rect = menu.get_rect(center=(setting.WIDTH // 2, setting.HEIGHT - 150))
        screen.blit(restart, r_rect)
        screen.blit(menu, m_rect)

    # ----------------------------------------------------------------------
    # CUTSCENE
    # ----------------------------------------------------------------------

    def _update_cutscene(self):
        """Обновляет катсцену"""
        if not hasattr(self, 'cutscene_start'):
            self.cutscene_start = pygame.time.get_ticks()
        if pygame.time.get_ticks() - self.cutscene_start > 3000:
            self.current_state = self.states['MENU']

    def _draw_cutscene(self, screen):
        """Рисует строчку скипа катсцены"""
        screen.fill((0, 0, 0))
        font = pygame.font.Font(None, 36)
        text = font.render("Нажмите на любую кнопку", True, (200, 200, 200))
        screen.blit(text, (screen.get_width() // 2 - 150, screen.get_height() - 100))

    # ----------------------------------------------------------------------
    # OPTIONS
    # ----------------------------------------------------------------------

    def _update_options(self):
        """Обновляет меню настроек"""
        pass

    def _draw_options(self, screen):
        """Рисует меню настроек"""
        screen.fill((20, 20, 40))

        title = self.font_tile.render("НАСТРОЙКИ", True, (255, 200, 0))
        title_rect = title.get_rect(center=(setting.WIDTH // 2, int(setting.CELL_H * 2)))
        screen.blit(title, title_rect)

        start_row = 4

        y_text = int(setting.CELL_H * start_row)
        sens_text = self.font_normal.render(
            f"ЧУВСТВИТЕЛЬНОСТЬ МЫШИ: {setting.MOUSE_SENSITIVITY:.3f}",
            True, (200, 200, 200)
        )
        sens_rect = sens_text.get_rect(center=(setting.WIDTH // 2, y_text))
        screen.blit(sens_text, sens_rect)

        if self.selected_option == 0:
            bar_width = int(setting.CELL_W * 6)
            bar_x = setting.WIDTH // 2 - bar_width // 2
            bar_y = y_text + int(setting.CELL_H * 0.3)
            pygame.draw.rect(screen, (80, 80, 80), (bar_x, bar_y, bar_width, 8))
            norm = (setting.MOUSE_SENSITIVITY - 0.0005) / (0.01 - 0.0005)
            handle_x = bar_x + int(bar_width * norm)
            pygame.draw.rect(screen, (255, 200, 0), (handle_x - 5, bar_y - 4, 10, 16))
            left_arr = self.font_small.render("<", True, (255, 200, 0))
            right_arr = self.font_small.render(">", True, (255, 200, 0))
            screen.blit(left_arr, (bar_x - 25, bar_y - 8))
            screen.blit(right_arr, (bar_x + bar_width + 15, bar_y - 8))

        y_text = int(setting.CELL_H * (start_row + 1.2))
        vol_text = self.font_normal.render(
            f"ГРОМКОСТЬ: {int(setting.MASTER_VOLUME * 100)}%",
            True, (200, 200, 200)
        )
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

        y_text = int(setting.CELL_H * (start_row + 2.4))
        color = (255, 255, 255) if self.selected_option == 2 else (150, 150, 150)
        back_text = self.font_normal.render("НАЗАД", True, color)
        back_rect = back_text.get_rect(center=(setting.WIDTH // 2, y_text))
        screen.blit(back_text, back_rect)

        tip = self.font_small.render(
            "↑/↓ - ВЫБОР, ←/→ - ИЗМЕНИТЬ, ESC/ENTER - НАЗАД",
            True, (150, 150, 150)
        )
        tip_rect = tip.get_rect(center=(setting.WIDTH // 2, setting.HEIGHT - int(setting.CELL_H * 2)))
        screen.blit(tip, tip_rect)

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

    def _get_level_time(self):
        """Возвращает время уровня в формате М:СС

        Returns:
            str: Время в формате "М:СС"
        """
        return f"{self.game.level_manager.level_time // 60}:{self.game.level_manager.level_time % 60:02d}"
