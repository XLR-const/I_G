import pygame
import sys
import math
from setting import *
from rendering.raycasting import RayCasting
from rendering.renderer import Renderer
from utils.pathfinding import PathFinder
from utils.level_manager import LevelManager
from ui.ui_manager import UIManager
from utils.save_system import SaveSystem
from ui.console import DevConsole


class Game:
    def __init__(self):
        pygame.mouse.set_visible(False)
        self.screen = pygame.display.set_mode(RES, pygame.SCALED | pygame.FULLSCREEN)
        self.clock = pygame.time.Clock()
        self.delta_time = 1
        self.font = pygame.font.SysFont('Arial', 30, bold=True)
        
        # Системы
        self.save_system = SaveSystem()
        self.raycasting = RayCasting(self)
        self.renderer = Renderer(self)
        self.pathfinder = PathFinder(self)
        
        # UI
        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        self.ui_manager = UIManager(self)
        self.console = DevConsole(self)
        
        # Level Manager (все данные уровня теперь внутри)
        self.level_manager = LevelManager(self)
        
        # Ссылки на объекты уровня (для удобства)
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
        
        # Загружаем первый уровень
        self.load_level(self.current_level)

    
    def load_level(self, level_num):
        """Загружает уровень через LevelManager и обновляет ссылки"""
        self.level_manager.load_level(level_num)
        
        # Обновляем ссылки после загрузки
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
        self.player.update()
        self.level_manager.check_exit()
        
        # Обновление дверей
        for door in self.map.doors:
            door.update()
        
        # Обновление частиц
        self.particles = [p for p in self.particles if pygame.time.get_ticks() - p.start_time < p.life_time]
        for p in self.particles:
            p.update()
        
        # Обновление NPC
        for npc in self.npcs:
            npc.update()
        
        # Обновление оружия
        self.weapon.update_animation()
        # Проверка зажатой ЛКМ для автоматического оружия
        mouse_buttons = pygame.mouse.get_pressed()
        if mouse_buttons[0]:
            if self.weapon.is_continuous and not self.weapon.reloading:
                self.weapon.fire()
        
        self.delta_time = self.clock.tick(FPS)
        self.player.update_regen()
        pygame.display.set_caption(f'FPS: {self.clock.get_fps():.1f}')

    def draw(self):
        self.renderer.draw_background()
        self.raycasting.ray_cast()
        self.renderer.draw_fps()

        # Сортировка NPC по глубине
        self.npcs.sort(key=lambda npc: math.hypot(npc.x - self.player.x, npc.y - self.player.y), reverse=True)
        for npc in self.npcs:
            npc.draw()

        for p in self.particles:
            p.draw()

        self.weapon.draw()
        self.renderer.draw_interface()
        self.renderer.draw_crosshair()
        self.console.draw(self.screen)

        pygame.display.flip()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

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
                    if event.key == pygame.K_2:
                        self.level_manager.current_weapon_index = 1
                    if event.key == pygame.K_3:
                        self.level_manager.current_weapon_index = 2
                    if event.key == pygame.K_4:
                        self.level_manager.current_weapon_index = 3

                    if self.level_manager.current_weapon_index < len(self.inventory):
                        self.weapon = self.inventory[self.level_manager.current_weapon_index]

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 4:
                        self.level_manager.current_weapon_index = (self.level_manager.current_weapon_index + 1) % len(self.inventory)
                    if event.button == 5:
                        self.level_manager.current_weapon_index = (self.level_manager.current_weapon_index - 1) % len(self.inventory)
                    self.weapon = self.inventory[self.level_manager.current_weapon_index]

                if self.console.active:
                    self.console.handle_event(event)
                    return

                if event.type == pygame.KEYDOWN and event.key == pygame.K_BACKQUOTE:
                    self.console.toggle()

    def play_music(self):
        current_state = self.ui_manager.current_state

        if current_state == self.ui_manager.states['MENU']:
            if not hasattr(self, 'current_music') or self.current_music != 'menu':
                try:
                    pygame.mixer.music.load('resources/ui_sounds/main_menu_song.wav')
                    pygame.mixer.music.set_volume(0.4)
                    pygame.mixer.music.play(-1)
                    self.current_music = 'menu'
                except:
                    pass

        elif current_state == self.ui_manager.states['PLAYING'] and self.current_level == 1:
            if not hasattr(self, 'current_music') or self.current_music != 'level1':
                try:
                    pygame.mixer.music.load('resources/level_music/level_1.wav')
                    pygame.mixer.music.set_volume(0.5)
                    pygame.mixer.music.play(-1)
                    self.current_music = 'level1'
                except:
                    pass

        elif current_state == self.ui_manager.states['BRIEFING']:
            if not hasattr(self, 'current_music') or self.current_music != 'briefing':
                try:
                    pygame.mixer.music.load('resources/ui_sounds/briefing.wav')
                    pygame.mixer.music.set_volume(0.5)
                    pygame.mixer.music.play(-1)
                    self.current_music = 'briefing'
                except:
                    pass

        elif current_state in (self.ui_manager.states['DEAD'], self.ui_manager.states['LEVEL_END']):
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
                if hasattr(self, 'current_music'):
                    delattr(self, 'current_music')

    def run(self):
        while True:
            self.handle_events()
            self.ui_manager.update()
            self.play_music()

            if self.ui_manager.current_state == self.ui_manager.states['PLAYING']:
                self.update()
                self.draw()
            else:
                self.ui_manager.draw(self.screen)
                pygame.display.flip()

            self.delta_time = self.clock.tick(FPS)


if __name__ == "__main__":
    game = Game()
    game.run()