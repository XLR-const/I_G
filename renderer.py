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

    def draw_fps(self):
        # Получаем текущее значение FPS
        fps = str(int(self.game.clock.get_fps()))
        # Создаем поверхность с текстом
        fps_render = self.game.font.render(fps, True, (0, 255, 0)) # Зеленый цвет
        # Рисуем в левом верхнем углу
        self.game.screen.blit(fps_render, (10, 10))
    
    def draw_crosshair(self):
        pygame.draw.circle(self.game.screen, 'red', (WIDTH // 2, HEIGHT // 2), 4, 1)