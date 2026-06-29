"""Главный файл

Содержит класс Game и точку входа в мейн цикл.
"""

import pygame
import sys
import math
from setting import *
from rendering.raycasting import RayCasting
from rendering.renderer import Renderer
from utils.pathfinding import PathFinder
from utils.level_manager import LevelManager
from utils.music_manager import MusicManager
from ui.ui_manager import UIManager
from utils.save_system import SaveSystem
from ui.console import DevConsole
from utils.intro_player import IntroPlayer


class Game:
    """Главный класс игры

    Управляет игровым циклом, загрузкой уровней и компонентами.

    Attributes:
        screen: Экран pygame
        clock: Часы для FPS
        delta_time: Время между кадрами
        font: Шрифт для отладки
        save_system: Система сохранений
        raycasting: Система рейкастинга
        renderer: Рендерер интерфейса
        pathfinder: Система поиска пути
        ui_manager: Менеджер UI
        console: Консоль разработчика
        music_manager: Менеджер музыки
        level_manager: Менеджер уровней
        player: Игрок
        map: Карта
        npcs: Список NPC
        inventory: Инвентарь игрока
        weapon: Текущее оружие
        particles: Список частиц
        exit_pos: Позиция выхода
        total_kills: Общее количество убийств
        current_level: Текущий уровень
        level_start_time: Время начала уровня
    """

    def __init__(self):
        """Инициализирует игру"""
        pygame.mouse.set_visible(False)
        self.screen = pygame.display.set_mode(RES, pygame.SCALED | pygame.FULLSCREEN)
        self.clock = pygame.time.Clock()
        self.delta_time = 1
        self.font = pygame.font.SysFont('Arial', 30, bold=True)

        self.save_system = SaveSystem()
        self.raycasting = RayCasting(self)
        self.renderer = Renderer(self)
        self.pathfinder = PathFinder(self)

        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        self.ui_manager = UIManager(self)
        self.console = DevConsole(self)

        self.music_manager = MusicManager()

        self.level_manager = LevelManager(self)

        self.player = None
        self.map = None
        self.npcs = []
        self.inventory = []
        self.weapon = None
        self.particles = []
        self.exit_pos = None
        self.total_kills = 0
        self.current_level = 1
        self.level_start_time = 0

        # Катсцена
        self.intro_player = IntroPlayer(self)

        # Загружаем уровень
        self.load_level(self.current_level)

    def load_level(self, level_num):
        """Загружает уровень через LevelManager и обновляет ссылки

        Args:
            level_num: Номер уровня
        """
        self.level_manager.load_level(level_num)

        self.player = self.level_manager.player
        self.map = self.level_manager.map
        self.npcs = self.level_manager.npcs
        self.inventory = self.level_manager.inventory
        self.weapon = self.level_manager.weapon
        self.particles = self.level_manager.particles
        self.exit_pos = self.level_manager.exit_pos
        self.total_kills = self.level_manager.total_kills
        self.current_level = self.level_manager.current_level
        self.level_start_time = self.level_manager.level_start_time

    def update(self):
        """Обновляет состояние игры"""
        self.player.update()
        self.level_manager.check_exit()

        for door in self.map.doors:
            door.update()

        self.particles = [p for p in self.particles
                          if pygame.time.get_ticks() - p.start_time < p.life_time]
        for p in self.particles:
            p.update()

        for npc in self.npcs:
            npc.update()

        self.weapon.update_animation()

        mouse_buttons = pygame.mouse.get_pressed()
        if mouse_buttons[0]:
            if self.weapon.is_continuous and not self.weapon.reloading:
                self.weapon.fire()

        self.delta_time = self.clock.tick(FPS)
        self.player.update_regen()
        pygame.display.set_caption(f'FPS: {self.clock.get_fps():.1f}')

    def draw(self):
        """Отрисовывает игру"""
        self.renderer.draw_background()
        self.raycasting.ray_cast()
        self.renderer.draw_fps()

        self.npcs.sort(key=lambda npc: math.hypot(
            npc.x - self.player.x, npc.y - self.player.y), reverse=True)
        for npc in self.npcs:
            npc.draw()
            if npc.alive:
                if not getattr(npc, 'is_boss', False):
                    self.renderer.draw_npc_health(npc)
                else:
                    npc.draw_boss_hud()

        for p in self.particles:
            p.draw()

        self.weapon.draw()
        self.renderer.draw_interface()
        self.renderer.draw_crosshair()
        self.console.draw(self.screen)

        pygame.display.flip()

    def handle_events(self):
        """Обрабатывает события pygame"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # КАТСЦЕНА - пропуск
            if self.intro_player.is_active():
                if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    self.intro_player.skip()
                    return
                # Обновляем статус
                self.intro_player.update()
                return
            
            handled = self.ui_manager.handle_event(event)

            if not handled and self.ui_manager.current_state == self.ui_manager.states['PLAYING']:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.ui_manager.current_state = self.ui_manager.states['PAUSE']
                    self.ui_manager.selected_option = 0

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        if not self.weapon.reloading and not self.weapon.is_continuous:
                            self.weapon.fire()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.weapon.fire()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1:
                        self.level_manager.current_weapon_index = 0
                    if event.key == pygame.K_2 and len(self.inventory) > 1:
                        self.level_manager.current_weapon_index = 1
                    if event.key == pygame.K_3 and len(self.inventory) > 2:
                        self.level_manager.current_weapon_index = 2
                    if event.key == pygame.K_4 and len(self.inventory) > 3:
                        self.level_manager.current_weapon_index = 3

                    if self.level_manager.current_weapon_index < len(self.inventory):
                        self.weapon = self.inventory[self.level_manager.current_weapon_index]

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 4:
                        self.level_manager.current_weapon_index = (
                            self.level_manager.current_weapon_index + 1
                        ) % len(self.inventory)
                    if event.button == 5:
                        self.level_manager.current_weapon_index = (
                            self.level_manager.current_weapon_index - 1
                        ) % len(self.inventory)
                    self.weapon = self.inventory[self.level_manager.current_weapon_index]

                if self.console.active:
                    self.console.handle_event(event)
                    return

                if event.type == pygame.KEYDOWN and event.key == pygame.K_BACKQUOTE:
                    self.console.toggle()

    def run(self):
        """Главный игровой цикл"""
        while True:
            self.handle_events()
            self.ui_manager.update()
            
            if self.intro_player.is_active():
                self.ui_manager.draw(self.screen)
                pygame.display.flip()
                self.clock.tick(FPS)
                continue

            self.music_manager.update(self.ui_manager.current_state, self.current_level)

            if self.ui_manager.current_state == self.ui_manager.states['PLAYING']:
                self.update()
                self.draw()
            else:
                self.ui_manager.draw(self.screen)
                pygame.display.flip()

            self.delta_time = self.clock.tick(FPS)

    def run_dev_mode(self):
        """Режим разработки - без UI, сразу в игру"""
        # Принудительно в игру
        self.ui_manager.current_state = self.ui_manager.states['PLAYING']
        self.current_level = DEV_LEVEL
        self.load_level(self.current_level)
        
        print("\n" + "="*50)
        print("🔧 РЕЖИМ РАЗРАБОТКИ")
        print(f"📁 Уровень: {self.current_level}")
        print(f"🎯 NPC: {len(self.npcs)}")
        print("="*50 + "\n")
        
        while True:
            # Обработка событий для DEV режима
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                if event.type == pygame.KEYDOWN:
                    # F1-F5 - смена уровня
                    if event.key == pygame.K_F1:
                        self.current_level = 1
                        self.load_level(1)
                        print(f"📁 Уровень {self.current_level}")
                    if event.key == pygame.K_F2:
                        self.current_level = 2
                        self.load_level(2)
                        print(f"📁 Уровень {self.current_level}")
                    if event.key == pygame.K_F3:
                        self.current_level = 3
                        self.load_level(3)
                        print(f"📁 Уровень {self.current_level}")
                    if event.key == pygame.K_F4:
                        self.current_level = 4
                        self.load_level(4)
                        print(f"📁 Уровень {self.current_level}")
                    if event.key == pygame.K_F5:
                        self.current_level = 5
                        self.load_level(5)
                        print(f"📁 Уровень {self.current_level}")
                    
                    # F5 - рестарт текущего уровня
                    if event.key == pygame.K_F5:
                        self.load_level(self.current_level)
                        print("🔄 Рестарт")
                    
                    # ESC - выход
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    
                    # Смена оружия
                    if event.key == pygame.K_1:
                        self.level_manager.current_weapon_index = 0
                    if event.key == pygame.K_2 and len(self.inventory) > 1:
                        self.level_manager.current_weapon_index = 1
                    if event.key == pygame.K_3 and len(self.inventory) > 2:
                        self.level_manager.current_weapon_index = 2
                    if event.key == pygame.K_4 and len(self.inventory) > 3:
                        self.level_manager.current_weapon_index = 3
                    if self.level_manager.current_weapon_index < len(self.inventory):
                        self.weapon = self.inventory[self.level_manager.current_weapon_index]
                
                # Стрельба
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        if not self.weapon.reloading and not self.weapon.is_continuous:
                            self.weapon.fire()
                
                # Колёсико мыши
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 4:
                        self.level_manager.current_weapon_index = (
                            self.level_manager.current_weapon_index + 1
                        ) % len(self.inventory)
                    if event.button == 5:
                        self.level_manager.current_weapon_index = (
                            self.level_manager.current_weapon_index - 1
                        ) % len(self.inventory)
                    self.weapon = self.inventory[self.level_manager.current_weapon_index]
            
            # Обновление и отрисовка
            self.update()
            self.draw()
            
            self.delta_time = self.clock.tick(FPS)

if __name__ == "__main__":
    game = Game()
    
    if DEV_MODE:
        game.run_dev_mode()
    else:
        game.run()
