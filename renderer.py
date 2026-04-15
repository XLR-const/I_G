import pygame
from setting import *
class Renderer:
    def __init__(self, game):
        self.game = game
    def draw_background(self):
        # Потолок (темно-серый)
        pygame.draw.rect(self.game.screen, (20, 20, 20), (0, 0, WIDTH, HALF_HEIGHT))
        # Пол (чуть светлее)
        pygame.draw.rect(self.game.screen, (40, 40, 40), (0, HALF_HEIGHT, WIDTH, HEIGHT))
