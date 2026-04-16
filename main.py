import pygame
import sys
from setting import *
from map import Map
from player import Player
from raycasting import RayCasting
from renderer import Renderer
from weapon import Weapon, Pistol, Shotgun, MachineGun, PlasmaGun
from weapon import Particle
from npc import NPC

class Game:
    def __init__(self):
        pygame.init()
        pygame.mouse.set_visible(False)
        #pygame.event.set_grab(True)
        #self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.screen = pygame.display.set_mode(RES, pygame.FULLSCREEN)
        self.clock = pygame.time.Clock() 
        self.delta_time = 1
        self.font = pygame.font.SysFont('Arial', 30, bold=True)

        # Звук пистолета
        pygame.mixer.init()
        self.shot_sound = pygame.mixer.Sound('resources/pistol_shot.wav')
        self.shot_sound.set_volume(0.2)
        self.new_game()
        
        # Particles
        self.particles = []

    def new_game(self):
        self.map = Map(self)
        self.player = Player(self)
        self.raycasting = RayCasting(self)
        self.renderer = Renderer(self)
        # Guns
        self.inventory = [Pistol(self), Shotgun(self), MachineGun(self), PlasmaGun(self)]
        
        self.current_weapon_index = 0
        self.weapon = self.inventory[self.current_weapon_index]
        # NPC
        self.npcs = [NPC(self, pos=(p[0] + 0.5, p[1] + 0.5)) for p in self.map.npc_positions]
        
    def update(self):
        self.player.update()
        # Проверка зажатой ЛКМ для автоматического оружия
        mouse_buttons = pygame.mouse.get_pressed()
        if mouse_buttons[0]: # 0 - это левая кнопка
            if self.weapon.is_continuous and not self.weapon.reloading:
                self.weapon.fire()
                # self.shot_sound.play() # Если есть звук

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
        #self.map.draw()
        #self.player.draw()
        self.npcs.sort(key=lambda npc: math.hypot(npc.x - self.player.x, npc.y - self.player.y), reverse=True)
        for npc in self.npcs:
            npc.draw()
        
        for p in self.particles:
            p.draw()
        self.weapon.draw()
        self.renderer.draw_crosshair()
        
        
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
                self.weapon = self.inventory[self.current_weapon_index]

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
