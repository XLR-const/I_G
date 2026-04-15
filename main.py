import pygame
import sys
from setting import *
from map import Map
from player import Player
from raycasting import RayCasting
from renderer import Renderer
from weapon import Weapon

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

    def new_game(self):
        self.map = Map(self)
        self.player = Player(self)
        self.raycasting = RayCasting(self)
        self.renderer = Renderer(self)
        self.weapon = Weapon(self)

    def update(self):
        self.player.update()
        self.delta_time = self.clock.tick(FPS)
        pygame.display.set_caption(f'FPS: {self.clock.get_fps() :.1f}')

    def draw(self):
        #self.screen.fill('black') # Очистка экрана перед каждым кадром
        self.renderer.draw_background()
        self.raycasting.ray_cast()
        self.renderer.draw_fps()
        #self.map.draw()
        #self.player.draw()
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
                if event.button == 1 and not self.weapon.reloading:
                    self.weapon.fire()
                    self.shot_sound.play()

    def run(self):
        while True:
            self.check_events()
            self.update()
            self.draw()


game = Game()
game.run()
