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
        """Обрабатывает события настроек с поддержкой кнопки полного сброса"""
        import config.user_settings as us
        import pprint
        
        bind_keys = list(us.USER_SETTINGS["KEYBINDS"].keys())
        
        # 🔥 НОВАЯ ДЛИНА МЕНЮ: 2 слайдера + N кнопок + 1 СБРОС + 1 НАЗАД
        options_len = 2 + len(bind_keys) + 2
        
        reset_option_id = options_len - 2  # ID кнопки сброса
        back_option_id = options_len - 1   # ID кнопки назад

        if not hasattr(self, 'waiting_for_key'):
            self.waiting_for_key = False

        if event.type == pygame.KEYDOWN:
            # 1. РЕЖИМ ОЖИДАНИЯ КЛАВИШИ
            if self.waiting_for_key:
                if event.key == pygame.K_ESCAPE:
                    self.waiting_for_key = False
                    if self.swap_sound: self.swap_sound.play()
                    return True
                
                current_bind_idx = self.selected_option - 2
                bind_id = bind_keys[current_bind_idx]
                k_name = pygame.key.name(event.key).upper()
                
                us.USER_SETTINGS["KEYBINDS"][bind_id]["key"] = event.key
                us.USER_SETTINGS["KEYBINDS"][bind_id]["key_name"] = k_name
                
                user_config_path = os.path.join("config", "user_settings.py")
                try:
                    formatted_dict = pprint.pformat(us.USER_SETTINGS, indent=4, width=120, sort_dicts=False)
                    with open(user_config_path, "w", encoding="utf-8") as f:
                        f.write("# Автоматически сгенерированный файл настроек игрока\n")
                        f.write(f"USER_SETTINGS = {formatted_dict}\n")
                except Exception as e:
                    print(f"❌ Ошибка сохранения кнопок: {e}")
                
                self.waiting_for_key = False
                if self.enter_sound: self.enter_sound.play()
                return True

            # 2. ОБЫЧНЫЙ РЕЖИМ НАВИГАЦИИ
            if event.key == pygame.K_UP:
                self.selected_option = (self.selected_option - 1) % options_len
                if self.swap_sound: self.swap_sound.play()
                return True
                
            if event.key == pygame.K_DOWN:
                self.selected_option = (self.selected_option + 1) % options_len
                if self.swap_sound: self.swap_sound.play()
                return True
                
            if event.key == pygame.K_LEFT:
                if self.selected_option == 0:
                    setting.MOUSE_SENSITIVITY = max(0.0005, setting.MOUSE_SENSITIVITY - 0.0005)
                    us.USER_SETTINGS["MOUSE_SENSITIVITY"] = setting.MOUSE_SENSITIVITY
                elif self.selected_option == 1:
                    setting.MASTER_VOLUME = max(0.0, setting.MASTER_VOLUME - 0.1)
                    us.USER_SETTINGS["MASTER_VOLUME"] = setting.MASTER_VOLUME
                    pygame.mixer.music.set_volume(setting.MASTER_VOLUME)
                
                try:
                    formatted_dict = pprint.pformat(us.USER_SETTINGS, indent=4, width=120, sort_dicts=False)
                    with open(os.path.join("config", "user_settings.py"), "w", encoding="utf-8") as f:
                        f.write(f"USER_SETTINGS = {formatted_dict}\n")
                except: pass
                return True
                
            if event.key == pygame.K_RIGHT:
                if self.selected_option == 0:
                    setting.MOUSE_SENSITIVITY = min(0.01, setting.MOUSE_SENSITIVITY + 0.0005)
                    us.USER_SETTINGS["MOUSE_SENSITIVITY"] = setting.MOUSE_SENSITIVITY
                elif self.selected_option == 1:
                    setting.MASTER_VOLUME = min(1.0, setting.MASTER_VOLUME + 0.1)
                    us.USER_SETTINGS["MASTER_VOLUME"] = setting.MASTER_VOLUME
                    pygame.mixer.music.set_volume(setting.MASTER_VOLUME)
                
                try:
                    formatted_dict = pprint.pformat(us.USER_SETTINGS, indent=4, width=120, sort_dicts=False)
                    with open(os.path.join("config", "user_settings.py"), "w", encoding="utf-8") as f:
                        f.write(f"USER_SETTINGS = {formatted_dict}\n")
                except: pass
                return True
                
            if event.key == pygame.K_RETURN:
                if self.enter_sound: self.enter_sound.play()
                
                if 2 <= self.selected_option < reset_option_id:
                    self.waiting_for_key = True
                    
                # 🔥 ОБРАБОТКА НАЖАТИЯ НА КНОПКУ "СБРОС НАСТРОЕК"
                elif self.selected_option == reset_option_id:
                    from config.game_data import DEFAULT_USER_SETTINGS
                    import copy
                    
                    # Глубоко копируем дефолтный словарь из гейм-даты, чтобы изменения не связались ссылками
                    us.USER_SETTINGS = copy.deepcopy(DEFAULT_USER_SETTINGS)
                    
                    # Мгновенно синхронизируем переменные движка в ОЗУ с дефолтными
                    setting.MOUSE_SENSITIVITY = us.USER_SETTINGS["MOUSE_SENSITIVITY"]
                    setting.MASTER_VOLUME = us.USER_SETTINGS["MASTER_VOLUME"]
                    
                    # Физически перезаписываем чистый дефолтный словарь на жесткий диск
                    user_config_path = os.path.join("config", "user_settings.py")
                    try:
                        formatted_dict = pprint.pformat(us.USER_SETTINGS, indent=4, width=120, sort_dicts=False)
                        with open(user_config_path, "w", encoding="utf-8") as f:
                            f.write("# Автоматически сгенерированный файл настроек игрока\n")
                            f.write(f"USER_SETTINGS = {formatted_dict}\n")
                        print("🗑️ [КОНФИГУРАТОР] Настройки успешно сброшены к базовым заводским значениям!")
                    except Exception as e:
                        print(f"❌ Ошибка записи сброса на диск: {e}")
                        
                elif self.selected_option == back_option_id:
                    self.current_state = self.states['MENU']
                return True
                
            if event.key == pygame.K_ESCAPE:
                if self.enter_sound: self.enter_sound.play()
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
        """Обновляет меню настроек: рассчитывает тайминги для мягких Sci-Fi эффектов"""
        now = pygame.time.get_ticks()
        
        # Мягкая пульсация активного пункта (синус от 160 до 255)
        self.menu_pulse = int(207 + 48 * math.sin(now * 0.004))
        
        # Эффект легкого шума терминала (микро-глитч яркости)
        self.hud_glitch = random.choice([0, 0, 0, 0, 12, 0, -8, 0, 0])
        
        # Переключатель режима ожидания новой клавиши
        if not hasattr(self, 'waiting_for_key'):
            self.waiting_for_key = False

    def _draw_options(self, screen):
        """Рисует меню настроек: абсолютное позиционирование по центру высоты экрана"""
        menu_font = self.font_normal
        title_font = self.font_tile

        # 1. ОТРИСОВКА ЗАДНИКА
        if hasattr(self, 'settings_bg') and self.settings_bg is not None:
            screen.blit(self.settings_bg, (0, 0))
        else:
            # Если картинка не найдена — заливаем красивым глубоким Sci-Fi цветом космоса
            screen.fill((10, 16, 26))

        # Накладываем полупрозрачное Sci-Fi затемнение
        dark = pygame.Surface((setting.WIDTH, setting.HEIGHT), pygame.SRCALPHA)
        dark.fill((4, 7, 14, 160)) 
        screen.blit(dark, (0, 0))

        # Кинематографичная виньетка по краям экрана
        vignette = pygame.Surface((setting.WIDTH, setting.HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(vignette, (0, 0, 0, 50), vignette.get_rect(), border_radius=20)
        screen.blit(vignette, (0, 0))

        # Настройки анимаций и пульсации
        pulse_val = getattr(self, 'menu_pulse', 255)
        glitch_val = getattr(self, 'hud_glitch', 0)
        
        text_white = (240, 245, 255)
        text_gray = (150, 160, 170)
        cyan_dim = (0, 120, 220)
        amber_gold = (255, 180, 0)
        
        g_color = max(0, min(255, pulse_val + glitch_val))
        active_color = (0, g_color, 255)  # Неоновый бирюзовый

        # 2. ГОЛОГРАФИЧЕСКИЙ ЛОГОТИП НАСТРОЕК (Мягкий янтарный Glow)
        title_text = "КОНФИГУРАТОР СИСТЕМ"
        tx = setting.WIDTH // 2
        # Жестко фиксируем заголовок у верхнего края (на 8% от высоты экрана)
        ty = int(setting.HEIGHT * 0.08)
        title_brightness = max(0, min(255, 230 + glitch_val))
        
        glow_color = (0, int(title_brightness * 0.4), int(title_brightness * 0.8))
        for ox, oy in [(-2, -2), (2, 2), (-2, 2), (2, -2)]:
            glow_surf = title_font.render(title_text, True, glow_color)
            screen.blit(glow_surf, glow_surf.get_rect(center=(tx + ox, ty + oy)))
        
        title = title_font.render(title_text, True, (255, int(title_brightness * 0.85), 0))
        screen.blit(title, title.get_rect(center=(tx, ty)))

        # Читаем структуру данных из нового изолированного файла настроек
        import config.user_settings as us
        bind_keys = list(us.USER_SETTINGS["KEYBINDS"].keys())
        
        options_len = 2 + len(bind_keys) + 2
        reset_option_id = options_len - 2  
        back_option_id = options_len - 1   

        # 🔥 ЖЕСТКИЙ ФИКС ВЕРСТКИ: Привязываем координаты К ВЫСОТЕ ЭКРАНА вместо CELL_H!
        # Первая строчка начнется строго на 28% от верха экрана, а шаг между ними — 38 пикселей
        start_y = int(setting.HEIGHT * 0.26)  
        row_spacing = 38                     
        
        bx = int(setting.WIDTH * 0.62)
        bar_width = 160

        # ---------------------------------------------------------------------
        # СЛАЙДЕР 0: ЧУВСТВИТЕЛЬНОСТЬ МЫШИ
        # ---------------------------------------------------------------------
        is_sel = (self.selected_option == 0)
        c = active_color if is_sel else text_gray
        txt = menu_font.render(f"ЧУВСТВИТЕЛЬНОСТЬ МЫШИ: {setting.MOUSE_SENSITIVITY:.4f}", True, c)
        screen.blit(txt, txt.get_rect(left=int(setting.WIDTH * 0.15), centery=start_y))
        
        # Шкала
        pygame.draw.rect(screen, (30, 40, 50), (bx, start_y - 4, bar_width, 8))
        norm = (setting.MOUSE_SENSITIVITY - 0.0005) / (0.01 - 0.0005)
        norm = max(0.0, min(1.0, norm))
        hx = bx + int(bar_width * norm)
        pygame.draw.rect(screen, active_color if is_sel else cyan_dim, (bx, start_y - 4, hx - bx, 8))
        pygame.draw.rect(screen, text_white, (hx - 3, start_y - 8, 6, 16))
        
        # Скобочки по бокам
        bracket_color = active_color if is_sel else (60, 75, 90)
        b_l = menu_font.render("[", True, bracket_color)
        screen.blit(b_l, b_l.get_rect(right=bx - 10, centery=start_y))
        b_r = menu_font.render("]", True, bracket_color)
        screen.blit(b_r, b_r.get_rect(left=bx + bar_width + 10, centery=start_y))
        
        # ---------------------------------------------------------------------
        # СЛАЙДЕР 1: ГРОМКОСТЬ ЗВУКА
        # ---------------------------------------------------------------------
        start_y += row_spacing
        is_sel = (self.selected_option == 1)
        c = active_color if is_sel else text_gray
        
        # 🔥 ФИКС БИТОГО СИМВОЛА %: Заменяем знак процента на текстовое обозначение "ЕД"
        vol_val = int(setting.MASTER_VOLUME * 100)
        txt = menu_font.render(f"ГРОМКОСТЬ ЗВУКА: {vol_val} ЕД", True, c)
        screen.blit(txt, txt.get_rect(left=int(setting.WIDTH * 0.15), centery=start_y))
        
        # Шкала
        pygame.draw.rect(screen, (30, 40, 50), (bx, start_y - 4, bar_width, 8))
        hx = bx + int(bar_width * max(0.0, min(1.0, setting.MASTER_VOLUME)))
        pygame.draw.rect(screen, active_color if is_sel else cyan_dim, (bx, start_y - 4, hx - bx, 8))
        pygame.draw.rect(screen, text_white, (hx - 3, start_y - 8, 6, 16))
        
        # Скобочки по бокам
        bracket_color = active_color if is_sel else (60, 75, 90)
        b_l = menu_font.render("[", True, bracket_color)
        screen.blit(b_l, b_l.get_rect(right=bx - 10, centery=start_y))
        b_r = menu_font.render("]", True, bracket_color)
        screen.blit(b_r, b_r.get_rect(left=bx + bar_width + 10, centery=start_y))

        # Разделительная тактическая линия
        start_y += int(row_spacing * 0.8)
        pygame.draw.line(screen, (30, 45, 60), (int(setting.WIDTH * 0.12), start_y), (int(setting.WIDTH * 0.88), start_y), 1)
        
        # Заголовок блока клавиш
        start_y += int(row_spacing * 0.8)
        header_txt = self.font_small.render("КОНФИГУРАЦИЯ КЛАВИШ КОСТЮМА:", True, amber_gold)
        screen.blit(header_txt, header_txt.get_rect(left=int(setting.WIDTH * 0.15), centery=start_y))
        
        # ---------------------------------------------------------------------
        # ДИНАМИЧЕСКИЙ БЛОК ТАБЛИЦЫ КНОПОК ИЗ USER_SETTINGS
        # ---------------------------------------------------------------------
        waiting_key_flag = getattr(self, 'waiting_for_key', False)

        for idx, bind_id in enumerate(bind_keys):
            start_y += row_spacing
            current_opt_global_id = 2 + idx 
            is_sel = (self.selected_option == current_opt_global_id)
            
            action_name = us.USER_SETTINGS["KEYBINDS"][bind_id]["name"]
            key_display_name = us.USER_SETTINGS["KEYBINDS"][bind_id]["key_name"]
            
            c = active_color if is_sel else text_gray
            action_txt = menu_font.render(action_name, True, c)
            screen.blit(action_txt, action_txt.get_rect(left=int(setting.WIDTH * 0.15), centery=start_y))
            
            if is_sel and waiting_key_flag:
                flash_alpha = int(140 + 115 * math.sin(pygame.time.get_ticks() * 0.01))
                key_c = (255, flash_alpha // 2, 0)
                key_txt = menu_font.render("[ НАЖМИ КЛАВИШУ ]", True, key_c)
            else:
                key_c = active_color if is_sel else text_white
                key_txt = menu_font.render(f"[  {key_display_name}  ]", True, key_c)
                
            screen.blit(key_txt, key_txt.get_rect(left=bx, centery=start_y))

        # ---------------------------------------------------------------------
        # КНОПКА СБРОСА: СБРОСИТЬ НАСТРОЙКИ ПО УМОЛЧАНИЮ
        # ---------------------------------------------------------------------
        start_y += int(row_spacing * 1.5) # Даем чуть больше отступа перед финишными кнопками
        is_sel_reset = (self.selected_option == reset_option_id)
        
        if is_sel_reset:
            reset_text = menu_font.render("СБРОСИТЬ НАСТРОЕКИ ПО УМОЛЧАНИЮ", True, active_color)
            reset_rect = reset_text.get_rect(center=(setting.WIDTH // 2, start_y))
            b_l = menu_font.render("[ ", True, active_color)
            screen.blit(b_l, b_l.get_rect(right=reset_rect.left - 10, centery=reset_rect.centery))
            b_r = menu_font.render(" ]", True, active_color)
            screen.blit(b_r, b_r.get_rect(left=reset_rect.right + 10, centery=reset_rect.centery))
        else:
            reset_text = menu_font.render("СБРОСИТЬ НАСТРОЕКИ ПО УМОЛЧАНИЮ", True, (190, 110, 20))
            reset_rect = reset_text.get_rect(center=(setting.WIDTH // 2, start_y))
        screen.blit(reset_text, reset_rect)

        # ---------------------------------------------------------------------
        # КНОПКА ВЫХОДА ОБРАТНО "СОХРАНИТЬ И НАЗАД"
        # ---------------------------------------------------------------------
        start_y += int(row_spacing * 1.2)
        is_sel_back = (self.selected_option == back_option_id)
        
        if is_sel_back:
            back_text = menu_font.render("СОХРАНИТЬ И НАЗАД", True, active_color)
            back_rect = back_text.get_rect(center=(setting.WIDTH // 2, start_y))
            b_l = menu_font.render("[ ", True, active_color)
            screen.blit(b_l, b_l.get_rect(right=back_rect.left - 10, centery=back_rect.centery))
            b_r = menu_font.render(" ]", True, active_color)
            screen.blit(b_r, b_r.get_rect(left=back_rect.right + 10, centery=back_rect.centery))
        else:
            back_text = menu_font.render("СОХРАНИТЬ И НАЗАД", True, text_gray)
            back_rect = back_text.get_rect(center=(setting.WIDTH // 2, start_y))
        screen.blit(back_text, back_rect)

        # ---------------------------------------------------------------------
        # НИЖНЯЯ ПОДСКАЗКА С КЛАВИШАМИ НАВИГАЦИИ
        # ---------------------------------------------------------------------
        tip_str = "UP/DOWN - НАВИГАЦИЯ, ENTER - ПЕРЕНАЗНАЧИТЬ КЛАВИШУ / СБРОСИТЬ, ESC - ВЫХОД"
        if waiting_key_flag:
            tip_str = "СИСТЕМА ОЖИДАЕТ НАЖАТИЯ ЛЮБОЙ КЛАВИШИ НА КЛАВИАТУРЕ..."
            
        tip = self.font_small.render(tip_str, True, (110, 130, 145))
        tip_rect = tip.get_rect(center=(setting.WIDTH // 2, setting.HEIGHT - int(setting.CELL_H * 0.6)))
        screen.blit(tip, tip_rect)

    # ----------------------------------------------------------------------
    # HELPERS
    # ----------------------------------------------------------------------

    def _get_level_time(self):
        """Возвращает время уровня в формате М:СС

        Returns:
            str: Время в формате "М:СС"
        """
        return f"{self.game.level_manager.level_time // 60}:{self.game.level_manager.level_time % 60:02d}"
