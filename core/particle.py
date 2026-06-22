import pygame
import math
from random import uniform
from setting import *


class Particle:
    """Класс частицы для эффектов

    Attributes:
        game: Объект игры
        x: Координата X
        y: Координата Y
        z: Высота
        v_z: Вертикальная скорость
        gravity: Гравитация
        color: Цвет частицы
        speed: Скорость движения
        angle: Угол движения
        life_time: Время жизни в мс
        start_time: Время создания
    """

    def __init__(self, game, pos, color, speed):
        """Инициализирует частицу

        Args:
            game: Объект игры
            pos: Координаты (x, y)
            color: Цвет (r, g, b)
            speed: Скорость движения
        """
        self.game = game
        self.x, self.y = pos
        self.z = 0
        self.v_z = uniform(-0.02, 0.01)
        self.gravity = 0.002
        self.color = color
        self.speed = speed
        self.angle = uniform(0, math.tau)
        self.life_time = 200
        self.start_time = pygame.time.get_ticks()

    def update(self):
        """Обновляет позицию частицы"""
        dt = self.game.delta_time
        self.x += math.cos(self.angle) * self.speed * dt
        self.y += math.sin(self.angle) * self.speed * dt
        self.v_z += self.gravity
        self.z += self.v_z * dt

    def draw(self):
        """Рисует частицу с учётом Z-координаты"""
        dx = self.x - self.game.player.x
        dy = self.y - self.game.player.y
        
        # Угол направления на частицу
        theta = math.atan2(dy, dx)
        
        # Разность углов между взглядом игрока и частицей
        delta = theta - self.game.player.angle
        delta = math.atan2(math.sin(delta), math.cos(delta))

        if -HALF_FOV < delta < HALF_FOV:
            dist = math.hypot(dx, dy)
            
            dist *= math.cos(delta)

            if dist > 0.05:
                screen_x = (delta / FOV + 0.5) * WIDTH
                screen_y = HALF_HEIGHT + self.z * (SCREEN_DIST / dist)

                size = int(SCREEN_DIST / (dist * 100))

                if 0 < screen_y < HEIGHT and size > 0:
                    if -size < screen_x < WIDTH + size:
                        pygame.draw.circle(self.game.screen, self.color,
                                           (int(screen_x), int(screen_y)), size)
