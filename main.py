import pygame
import sys
import math
from setting import *
from core.map import Map
from core.player import Player
from rendering.raycasting import RayCasting
from rendering.renderer import Renderer
from core.weapon import Weapon, Pistol, Shotgun, MachineGun, PlasmaGun
from core.weapon import Particle
from core.npc import NPC, Solder, Jaggernaut, Kamikaze, Boss, Lightning
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
        self.save_system = SaveSystem()
        self.total_kills = 0

        self.console = DevConsole(self)

        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        self.ui_manager = UIManager(self)
        self.level_manager = LevelManager(self)

        self.raycasting = RayCasting(self)
        self.renderer = Renderer(self)
        self.pathfinder = PathFinder(self)

        self.current_level = 1
        self.load_level(self.current_level)

    def load_level(self, level_num):
        import time
        start_total = time.time()

        print(f"\n{'=' * 60}")
        print(f"ЗАГРУЗКА УРОВНЯ {level_num}")
        print(f"{'=' * 60}")


        level_data = self.level_manager.load_level(level_num)
        if not level_data:
            print("ОШИБКА: JSON не загружен")
            self.game_over()
            return

        if hasattr(self, 'raycasting'):
            self.raycasting.texture_cache.clear()

        self.particles = []
        self.total_kills = 0

        self.map = Map(self, level_data['map_data'], level_data.get('doors', []))
        print(f"Карта: {self.map.width}x{self.map.height}, стен: {len(self.map.world_map)}")

        background = level_data.get('background', {})
        self.renderer.set_background(background)

        self.exit_pos = self.map.get_exit_pos()
        print(f"Выход: {self.exit_pos}")

        if hasattr(self, 'player'):
            self.player.x, self.player.y = level_data['player_start']
            self.player.hp = 100
        else:
            self.player = Player(self)
            self.player.x, self.player.y = level_data['player_start']
        print(f"Игрок на ({self.player.x}, {self.player.y})")

        self.inventory = []
        for weapon_name in level_data.get('inventory', ['Pistol']):
            if weapon_name == 'Pistol':
                self.inventory.append(Pistol(self))
            elif weapon_name == 'Shotgun':
                self.inventory.append(Shotgun(self))
            elif weapon_name == 'Machine Gun':
                self.inventory.append(MachineGun(self))
            elif weapon_name == 'Plasma Gun':
                self.inventory.append(PlasmaGun(self))

        self.current_weapon_index = 0
        self.weapon = self.inventory[0]

        starting_ammo = level_data.get('starting_ammo', {})
        for gun in self.inventory:
            gun.ammo = starting_ammo.get(gun.name, 0)
        print(f"Оружие: {[w.name for w in self.inventory]}")

        self.npcs = []
        npc_positions = list(self.map.npc_positions)
        print(f"Создание NPC: {len(npc_positions)} шт.")

        for i, (npc_x, npc_y, npc_type) in enumerate(npc_positions):
            x, y = npc_x + 0.5, npc_y + 0.5

            try:
                if npc_type == 'Solder':
                    self.npcs.append(Solder(self, pos=(x, y)))
                elif npc_type == 'Kamikaze':
                    self.npcs.append(Kamikaze(self, pos=(x, y)))
                elif npc_type == 'Jaggernaut':
                    self.npcs.append(Jaggernaut(self, pos=(x, y)))
                elif npc_type == 'Boss':
                    self.npcs.append(Boss(self, pos=(x, y)))
                elif npc_type == 'Lightning':
                    self.npcs.append(Lightning(self, pos=(x, y)))
                else:
                    continue
            except Exception as e:
                print(f"Ошибка создания NPC {npc_type}: {e}")
                continue

        for npc in self.npcs:
            try:
                npc.generate_waypoints_auto(4)
                npc.state = "PATROL"
            except Exception as e:
                print(f"Ошибка waypoints: {e}")
                npc.waypoints = []
                npc.state = "IDLE"

        print(f"Уровень {level_num} загружен за {time.time() - start_total:.2f}с")
        print(f"{'=' * 60}\n")

    def next_level(self):
        self.level_time = (pygame.time.get_ticks() - self.level_start_time) // 1000
        self.save_system.save(self.current_level, self.total_kills, self.level_time)
        self.ui_manager.current_state = self.ui_manager.states['LEVEL_END']

    def check_exit(self):
        if not hasattr(self, 'exit_pos') or self.exit_pos is None:
            return

        player_cell = (int(self.player.x), int(self.player.y))
        exit_cell = (int(self.exit_pos[0]), int(self.exit_pos[1]))


        if player_cell == exit_cell:
            self.ui_manager.current_state = self.ui_manager.states['LEVEL_END']
            self.next_level()

    def game_over(self):
        pygame.quit()

    def reset_game(self):
        self.save_system.delete()
        self.total_kills = 0
        self.level_time = 0
        self.current_level = 1
        self.load_level(self.current_level)

    def play_music(self):
        current_state = self.ui_manager.current_state

        if current_state == self.ui_manager.states['MENU']:
            if not hasattr(self, 'current_music') or self.current_music != 'menu':
                try:
                    pygame.mixer.music.load('resources/ui_sounds/main_menu_song.wav')
                    pygame.mixer.music.set_volume(0.4)
                    pygame.mixer.music.play(-1)
                    self.current_music = 'menu'
                except Exception as e:
                    pass

        elif current_state == self.ui_manager.states['PLAYING'] and self.current_level == 1:
            if not hasattr(self, 'current_music') or self.current_music != 'level1':
                try:
                    pygame.mixer.music.load('resources/level_music/level_1.wav')
                    pygame.mixer.music.set_volume(0.5)
                    pygame.mixer.music.play(-1)
                    self.current_music = 'level1'
                except Exception as e:
                    pass

        elif current_state == self.ui_manager.states['BRIEFING']:
            if not hasattr(self, 'current_music') or current_state != 'briefing':
                try:
                    pygame.mixer.music.load('resources/ui_sounds/briefing.wav')
                    pygame.mixer.music.set_volume(0.5)
                    pygame.mixer.music.play(-1)
                    self.current_music = 'briefing'
                except Exception as e:
                    pass

        elif current_state in (self.ui_manager.states['DEAD'], self.ui_manager.states['LEVEL_END']):
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
                if hasattr(self, 'current_music'):
                    delattr(self, 'current_music')

    def update(self):
        self.player.update()
        self.check_exit()

        mouse_buttons = pygame.mouse.get_pressed()
        if mouse_buttons[0]:
            if self.weapon.is_continuous and not self.weapon.reloading:
                self.weapon.fire()

        for door in self.map.doors:
            door.update()

        self.particles = [p for p in self.particles if pygame.time.get_ticks() - p.start_time < p.life_time]
        for p in self.particles:
            p.update()

        for npc in self.npcs:
            npc.update()

        self.delta_time = self.clock.tick(FPS)
        self.player.update_regen()
        pygame.display.set_caption(f'FPS: {self.clock.get_fps():.1f}')

    def draw(self):
        self.renderer.draw_background()
        self.raycasting.ray_cast()
        self.renderer.draw_fps()

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

    def check_events(self):
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
                        self.current_weapon_index = 0
                    if event.key == pygame.K_2:
                        self.current_weapon_index = 1
                    if event.key == pygame.K_3:
                        self.current_weapon_index = 2
                    if event.key == pygame.K_4:
                        self.current_weapon_index = 3

                    if self.current_weapon_index < len(self.inventory):
                        self.weapon = self.inventory[self.current_weapon_index]
                    else:
                        self.current_weapon_index = 0

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 4:
                        self.current_weapon_index = (self.current_weapon_index + 1) % len(self.inventory)
                    if event.button == 5:
                        self.current_weapon_index = (self.current_weapon_index - 1) % len(self.inventory)
                    self.weapon = self.inventory[self.current_weapon_index]

                if self.console.active:
                    self.console.handle_event(event)
                    return

                if event.type == pygame.KEYDOWN and event.key == pygame.K_BACKQUOTE:
                    self.console.toggle()

    def run(self):
        while True:
            self.check_events()
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