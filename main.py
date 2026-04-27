import pygame
import sys
from setting import *
from map import Map
from player import Player
from raycasting import RayCasting
from renderer import Renderer
from weapon import Weapon, Pistol, Shotgun, MachineGun, PlasmaGun
from weapon import Particle
from npc import NPC, Solder, Jaggernaut, Kamikaze, Boss, Lightning
from pathfinding import PathFinder
from level_manager import LevelManager

class Game:
    def __init__(self):
        pygame.mouse.set_visible(False)
        #pygame.event.set_grab(True)
        #self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.screen = pygame.display.set_mode(RES, pygame.SCALED | pygame.FULLSCREEN)
        self.clock = pygame.time.Clock() 
        self.delta_time = 1
        self.font = pygame.font.SysFont('Arial', 30, bold=True)
        

        self.level_manager = LevelManager(self)
        self.current_level = 1
        self.load_level(self.current_level)
        
        
    """
    def new_game(self):
        self.map = Map(self)
        self.player = Player(self)
        self.raycasting = RayCasting(self)
        self.renderer = Renderer(self)
        self.load_level(self.current_level)
        # Guns
        self.inventory = [Pistol(self), Shotgun(self), MachineGun(self), PlasmaGun(self)]
        gun_ammo = {
                "Pistol": 20,
                "Shotgun": 10,
                "Machine Gun": 100,
                "Plasma Gun": 5
        }
        for gun in self.inventory:
            gun.ammo = gun_ammo[gun.name]
            
        self.current_weapon_index = 0
        self.weapon = self.inventory[self.current_weapon_index]
        
        
        # NPC
        #self.npcs = [NPC(self, pos=(p[0] + 0.5, p[1] + 0.5)) for p in self.map.npc_positions]
        self.npcs = []
        for npc in self.map.npc_positions:
            if npc[-1] == '2':
                self.npcs.append(Solder(self, pos=(npc[0] + 0.5, npc[1] + 0.5)))
            if npc[-1] == '3':
                self.npcs.append(Kamikaze(self, pos=(npc[0] + 0.5, npc[1] + 0.5)))
            if npc[-1] == '4':
                self.npcs.append(Jaggernaut(self, pos=(npc[0] + 0.5, npc[1] + 0.5)))
            if npc[-1] == '5':
                self.npcs.append(Boss(self, pos=(npc[0] + 0.5, npc[1] + 0.5)))
        for npc in self.npcs:
            npc.generate_waypoints_auto(4)
            npc.state = "PATROL"
        self.pathfinder = PathFinder(self)
    """ 
          
    def load_level(self, level_num):
        '''Вся инициализация здесь'''
        level_data = self.level_manager.load_level(level_num)
        if not level_data:
            self.game_over()
            return
        # Очистка кэша тектур
        if hasattr(self, 'renderer'):
            self.raycasting.texture_cache.clear()
        # партикли 
        self.particles = []
        
        # карта
        self.map = Map(self, level_data['map_data'], level_data['doors'])
        self.exit_pos = self.map.get_exit_pos()
        
        # NPC
        self.npcs = []
        for npc_x, npc_y, npc_type in self.map.npc_positions:
            x, y = npc_x + 0.5, npc_y + 0.5
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
        
        for npc in self.npcs:
            npc.generate_waypoints_auto(4)
            npc.state = "PATROL"
        
        # игрок
        if hasattr(self, 'player'):
            self.player.x, self.player.y = level_data['player_start']
        else:
            self.player = Player(self)
            self.player.x, self.player.y = level_data['player_start']
            
        # оружие
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
        # fill ammo
        starting_ammo = level_data.get('starting_ammo', {})
        for gun in self.inventory:
            if gun.name in starting_ammo:
                gun.ammo = starting_ammo[gun.name]
            else:
                gun.ammo = 0
        
        
        # Raycasting + render
        if not hasattr(self, 'raycasting'):
            self.raycasting = RayCasting(self)
            self.renderer = Renderer(self)
            self.pathfinder = PathFinder(self)
            
        # Close
        #self.exit_pos = level_data.get('exit', (-1, -1))
    
        
    def next_level(self):
        self.current_level += 1
        self.load_level(self.current_level)
        
    def check_exit(self):
        if not hasattr(self, 'exit_pos') or self.exit_pos is None:
            return
        
        # Проверяем расстояние до выхода (можно по клеткам)
        player_cell = (int(self.player.x), int(self.player.y))
        exit_cell = (int(self.exit_pos[0]), int(self.exit_pos[1]))
        
        if player_cell == exit_cell:
            self.next_level()
            
    def game_over(self):
        pygame.quit()

            
            
    def update(self):
        self.player.update()
        self.check_exit()
        # Проверка зажатой ЛКМ для автоматического оружия
        mouse_buttons = pygame.mouse.get_pressed()
        if mouse_buttons[0]: # 0 - это левая кнопка
            if self.weapon.is_continuous and not self.weapon.reloading:
                self.weapon.fire()
                # self.shot_sound.play() # Если есть звук

        for door in self.map.doors:
            door.update()
        self.particles = [p for p in self.particles if pygame.time.get_ticks() - p.start_time < p.life_time]
        for p in self.particles:
            p.update()
        for npc in self.npcs:
            npc.update()
        self.delta_time = self.clock.tick(FPS)
        pygame.display.set_caption(f'FPS: {self.clock.get_fps() :.1f}')

    def draw(self):
        #self.screen.fill('black') # Очистка экрана перед каждым кадром
        self.renderer.draw_background()
        self.raycasting.ray_cast()
        self.renderer.draw_fps()
        #self.player.draw()
        self.npcs.sort(key=lambda npc: math.hypot(npc.x - self.player.x, npc.y - self.player.y), reverse=True)
        for npc in self.npcs:
            npc.draw()
        
        for p in self.particles:
            p.draw()
        self.weapon.draw()
        self.renderer.draw_interface()
        self.renderer.draw_crosshair()
        #self.renderer.draw_line_of_cells()
        
        
        pygame.display.flip()

    def check_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Теперь проверяем КНОПКУ (1 - левая) и статус перезарядки
                if event.button == 1:
                    if not self.weapon.reloading and not self.weapon.is_continuous:
                        self.weapon.fire()
            # Альтернативгая стрельба
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
                # Обновляем ссылку на активное оружие
                if self.current_weapon_index < len(self.inventory):
                    self.weapon = self.inventory[self.current_weapon_index]
                else:
                    self.current_weapon_index = 0

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4: # Колесо вверх
                    self.current_weapon_index = (self.current_weapon_index + 1) % len(self.inventory)
                if event.button == 5: # Колесо вниз
                    self.current_weapon_index = (self.current_weapon_index - 1) % len(self.inventory)
                self.weapon = self.inventory[self.current_weapon_index]


    def run(self):
        while True:
            self.check_events()
            self.update()
            self.draw()


game = Game()
game.run()
