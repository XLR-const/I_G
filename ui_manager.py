import pygame
from setting import *
import sys
import random
from save_system import SaveSystem

class UIManager:
    def __init__(self, game):
        self.game = game
        self.font_tile = pygame.font.Font(None, int(CELL_H * 1.5))
        self.font_normal = pygame.font.Font(None, int(CELL_H * 0.6))
        self.font_small = pygame.font.Font(None, int(CELL_H * 0.4))
        
        self.states = {
            'BOOT': 0, # загрузка игры
            'MENU': 1, # главное меню
            'BRIEFING': 2, # брифинг
            'PLAYING': 3, # игра
            'PAUSE': 4, # меню паузы
            'LEVEL_END': 5, # конец уровня
            'DEAD': 6, # без сознания хэх
            'CUTSCENE': 7 # катсцены
        }
        
        self.current_state = self.states['BOOT']
        self.selected_option = 0
        
        self.load_assets()
    
    def load_assets(self):
        """Загрузка ассетов"""
        self.backgrounds = {}
        try:
            menu_bg = pygame.image.load('resources/ui/main_menu_bg.png').convert_alpha()
            self.backgrounds['menu'] = pygame.transform.scale(menu_bg, (WIDTH, HEIGHT))
        except:
            self.backgrounds['menu'] = None
        try:
            dead_bg = pygame.image.load('resources/ui/dead_bg.png').convert_alpha()
            self.backgrounds['dead'] = pygame.transform.scale(dead_bg, (WIDTH, HEIGHT))
        except:
            self.backgrounds['dead'] = None
    
    def handle_event(self, event):
        """Ретранслятор событий для UI
        по типу там кнопок меню и т.д."""
        if self.current_state == self.states['MENU']:
            return self._handle_menu_event(event)
        elif self.current_state == self.states['BRIEFING']:
            return self._handle_briefing_event(event)
        elif self.current_state == self.states['PAUSE']:
            return self._handle_pause_event(event)
        elif self.current_state == self.states['LEVEL_END']:
            return self._handle_level_end_event(event)
        elif self.current_state == self.states['DEAD']:
            return self._handle_dead_event(event)
        elif self.current_state == self.states['CUTSCENE']:
            return self._handle_cutscene_event(event)
        return False
    
    def _handle_menu_event(self, event):
        """Обработка ввода в гл меню"""
        options = {
            'NEW_GAME': 0,
            'LOAD GAME': 1,
            'OPTIONS': 2,
            'QUIT': 3}
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_DOWN:
                self.selected_option = (self.selected_option + 1) % len(options)
                return True
            elif event.key == pygame.K_UP:
                self.selected_option = (self.selected_option - 1) % len(options)
                return True
            elif event.key == pygame.K_RETURN:
                # 0 situation
                if self.selected_option == 0:
                    self.game.reset_game()
                    self.current_state = self.states['BRIEFING']
                elif self.selected_option == 1:
                    saved = SaveSystem.load()
                    if saved:
                        self.game.current_level = saved['current_level']
                        self.game.total_kills = saved['total_kills']
                        self.game.load_level(self.game.current_level)
                        self.current_state = self.states['BRIEFING']
                    else:
                        self.game.reset_game()
                        # Load level and tick уже в reset_game
                        self.current_state = self.states['BRIEFING']
                # 3 situation
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
        options = ['RESUME', 'RESTART LEVEL', 'MAIN MENU', 'QUIT']
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.current_state = self.states['PLAYING']
                return True
            elif event.key == pygame.K_UP:
                self.selected_option = (self.selected_option - 1) % len(options)
                return True
            elif event.key == pygame.K_DOWN:
                self.selected_option = (self.selected_option + 1) % len(options)
                return True
            elif event.key == pygame.K_RETURN:
                if self.selected_option == 0:
                    self.current_state = self.states['PLAYING']
                elif self.selected_option == 1:
                    self.game.level_start_time = pygame.time.get_ticks()
                    self.game.load_level(self.game.current_level)
                    self.current_state = self.states['PLAYING']
                elif self.selected_option == 2:
                    self.current_state = self.states['MENU']
                elif self.selected_option == 3:  # ← ДОБАВЬ ЭТО
                    pygame.quit()
                    sys.exit()
                return True
        return False
    
    def _handle_level_end_event(self, event):
        """Обработка конца уровня"""
        if event.type == pygame.KEYDOWN:
            '''if hasattr(self, 'briefing_start'):
                delattr(self, 'briefing_start')'''
            self.game.current_level += 1
            SaveSystem.save(self.game.current_level,
                            self.game.total_kills,
                            self._get_level_time())
            self.game.load_level(self.game.current_level)
            self.current_state = self.states['BRIEFING']
            return True
        return False
    
    def _handle_dead_event(self, event):
        """Обработка экрана смерти"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                self.game.level_start_time = pygame.time.get_ticks()
                self.game.load_level(self.game.current_level)
                self.current_state = self.states['PLAYING']
                return True
            elif event.key == pygame.K_m:
                self.current_state = self.states['MENU']
                return True
        return False
    
    def _handle_cutscene_event(self, event):
        """Обработка катсцены"""
        if event.type == pygame.KEYDOWN:
            self.current_state = self.states['MENU']
            return True
        return False
    
    def update(self):
        """Ретранслятор апдейтов отдельных экранов:
        анимации и таймеры где есть"""
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
    
    # ===BOOT===        
    def _update_boot(self):
        """Обновление экрана загрузки игры"""
        if not hasattr(self, 'boot_start'):
            self.boot_start = pygame.time.get_ticks()
        # Отсчитваем время искусственного задержки
        if pygame.time.get_ticks() - self.boot_start > 2000:
            self.current_state = self.states['MENU']
    
    def _draw_boot(self, screen):
        """Отрисовка экрана загрузки игры"""
        screen.fill((0, 0, 0))
        text = self.font_tile.render("Loading...", True, (255, 255, 255))
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2))
        
        # Прогресс бар
        progress = (pygame.time.get_ticks() - self.boot_start) / 2000
        if progress > 1:
            progress = 1
        bar_width = int(WIDTH * progress * 0.4)
        pygame.draw.rect(screen, (100, 100, 100),
                         (WIDTH//2 - 200, HEIGHT//2 + 50, WIDTH*0.4, 20))
        pygame.draw.rect(screen, (0, 200, 0), 
                         (WIDTH//2 - 200, HEIGHT//2 + 50, bar_width, 20))
    
    # ===MAIN MENU===
    def _update_menu(self):
        """Обновление меню (таймеры, анимации) - без обработки событий"""
        pass  # Всё что связано с вводом — в handle_event
    
    def _draw_menu(self, screen):
            if self.backgrounds['menu']:
                screen.blit(self.backgrounds['menu'], (0, 0))
            else:
                screen.fill((20, 40, 20))
            
            # название игры
            title = self.font_tile.render("Ilyusha Grate", True, (255, 200, 0))
            screen.blit(title, (WIDTH//2 - title.get_width()//2, int(CELL_H * 2)))
            
            # Пункты меню
            options = ['NEW GAME', 'LOAD GAME', 'OPTIONS', 'QUIT']
            for i, option in enumerate(options):
                y = HEIGHT//2 + i * 60
                color = (255, 255, 255) if i == self.selected_option else (150, 150, 150)
                text = self.font_normal.render(option, True, color)
                screen.blit(text, (WIDTH//2 - text.get_width()//2, y))
                
                if i == self.selected_option:
                    pygame.draw.line(screen, (255, 200, 0), 
                                (WIDTH//2 - text.get_width()//2 - 20, y + text.get_height()//2),
                                (WIDTH//2 - text.get_width()//2 - 5, y + text.get_height()//2), 3)
                    
    # ===BRIEFING===
    def _update_briefing(self):
        '''if not hasattr(self, 'briefing_start'):
            self.briefing_start = pygame.time.get_ticks()
        
        elapsed = pygame.time.get_ticks() - self.briefing_start
        
        if elapsed > 5000:
            print("Авто-переход в игру")  # ← отладка
            self._start_level()
            delattr(self, 'briefing_start')'''
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
            y = int(CELL_H * 2) + i * int(CELL_H * 0.6)
            if 'ЗАДАЧИ' not in line and i != 0:
                color = (200, 200, 200)
            else:
                color = (255, 200, 0)

            if line.startswith('МИССИЯ'):
                text = self.font_tile.render(line, True, color)
            else:
                text = self.font_normal.render(line, True, color)
            screen.blit(text, (int(CELL_W) * 2, y))
        self.__draw_minimap(screen, int(CELL_W * 12), int(CELL_H * 2))
    
    def __draw_minimap(self, screen, x, y):
        """Рисует мини-карту уровня из JSON"""
        try:
            size = int(CELL_H * 4)
            cell_size = size // max(len(self.game.map.text_map[0]), len(self.game.map.text_map))
            
            for j, row in enumerate(self.game.map.text_map):
                for i, char in enumerate(row):
                    color = (100, 100, 100) if char != '_' and char not in '2345' else (40, 40, 40)
                    if char == 'E':
                        color = (0, 200, 0)
                    pygame.draw.rect(screen, color, 
                                   (x + i * cell_size, y + j * cell_size, cell_size - 1, cell_size - 1))
        except:
            pass
    
    # ===PAUSE MENU===
    def _update_pause(self):
        """Обновление паузы (таймеры) - без обработки событий"""
        pass
    
    def _draw_pause(self, screen):
        """Рисуем экран паузы"""
        dark = pygame.Surface((WIDTH, HEIGHT))
        dark.set_alpha(180)
        dark.fill((0, 0, 0))
        screen.blit(dark, (0, 0))
        
        title = self.font_tile.render("PAUSED", True, (255, 200, 0))
        screen.blit(title, (WIDTH//2 - title.get_width()//2, int(CELL_H * 3)))
        
        options = ['RESUME', 'RESTART LEVEL', 'MAIN MENU', 'QUIT']
        for i, option in enumerate(options):
            y = HEIGHT//2 + i * 60
            color = (255, 255, 255) if i == self.selected_option else (150, 150, 150)
            text = self.font_normal.render(option, True, color)
            screen.blit(text, (WIDTH//2 - text.get_width()//2, y))
            
    # ===LEVEL END===
    def _update_level_end(self):
        """Обновление конца уровня (таймеры) - без обработки событий"""
        pass
        
    def _draw_level_end(self, screen):
        """Рисуем экран конца уровня"""
        screen.fill((0, 0, 0))
        
        text = self.font_tile.render("MISSION COMPLETE", True, (0, 255, 0))
        screen.blit(text, (WIDTH//2 - text.get_width()//2, int(CELL_H * 3)))
        stats = [
            f"ENEMIES KILLED: {self._get_kills_count()}",
            f"TIME: {self._get_level_time()}",
            "",
            "PRESS ANY KEY TO CONTINUE"
        ]
        
        for i, stat in enumerate(stats):
            y = HEIGHT//2 + i * 40
            color = (200, 200, 200) if "PRESS" not in stat else (255, 200, 0)
            text = self.font_normal.render(stat, True, color)
            screen.blit(text, (WIDTH//2 - text.get_width()//2, y))
        
    # ===DEATH SCREEN===
    def _update_dead(self):
        """Обновление экрана смерти (таймеры) - без обработки событий"""
        
    
    def _draw_dead(self, screen):
        if self.backgrounds['dead']:
            screen.blit(self.backgrounds['dead'], (0, 0))
        else:
            screen.fill((40, 0, 0))
        
        # Текст смерти
        text = self.font_tile.render("ПОГИБ ЗА ЧЕСТЬ", True, (255, 0, 0))
        screen.blit(text, (WIDTH//2 - text.get_width()//2, int(CELL_H * 2)))
        
        # Совет
        tips = [
            "СОВЕТ: Кармак придумал стрейфы не для того чтобы ты захлебывался кровью",
            "СОВЕТ: Хэдшоты? Не. Не слышали про такое",
            "СОВЕТ: Кончились патроны? Автору некогда было допиливать механику подбора",
            "СОВЕТ: Корпорация Marvin - злейший враг человека",
            "СОВЕТ: Используй укрытия и стрейфы. Ты же не Блацкович"
        ]
        if not hasattr(self, 'current_tip'):
            self.current_tip = random.choice(tips)
        
        tip = self.font_small.render(self.current_tip, True, (200, 200, 200))
        screen.blit(tip, (WIDTH//2 - tip.get_width()//2, HEIGHT - 100))
        
        # Кнопки
        restart = self.font_normal.render("PRESS R TO RESTART", True, (255, 255, 255))
        menu = self.font_normal.render("PRESS M FOR MAIN MENU", True, (255, 255, 255))
        screen.blit(restart, (WIDTH//2 - restart.get_width()//2, HEIGHT - 200))
        screen.blit(menu, (WIDTH//2 - menu.get_width()//2, HEIGHT - 150))
        
    # ===CUTSCENE(заглушка пока)===
    def _play_cutscene(self, video_path):
        """Воспроизведение видео (если есть)"""
        self.current_state = self.states['CUTSCENE']
        # Здесь можно использовать pygame-movie или просто показывать картинки
        self.cutscene_frames = []
        # Для простоты: показываем статичную картинку 3 секунды
    
    def _update_cutscene(self):
        if not hasattr(self, 'cutscene_start'):
            self.cutscene_start = pygame.time.get_ticks()
        
        if pygame.time.get_ticks() - self.cutscene_start > 3000:
            self.current_state = self.states['MENU']
    
    def _draw_cutscene(self, screen):
        screen.fill((0, 0, 0))
        text = self.font_tile.render("CUTSCENE", True, (255, 255, 255))
        screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2))
        
    # ===HELPERS FUNC===
    def _get_kills_count(self):
        return self.game.total_kills

    def _get_level_time(self):
        return f"{self.game.level_time // 60}:{self.game.level_time % 60:02d}"
