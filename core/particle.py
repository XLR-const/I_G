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

        # НАДЕЖНАЯ НОРМАЛИЗАЦИЯ УГЛА в диапазон от -pi до pi
        delta = math.atan2(math.sin(delta), math.cos(delta))

        # Проверяем, попадает ли частица в поле зрения (FOV)
        if -HALF_FOV < delta < HALF_FOV:
            dist = math.hypot(dx, dy)
            
            # Убираем эффект рыбьего глаза (fish-eye effect)
            dist *= math.cos(delta)

            # Защита от деления на ноль, если частица слишком близко
            if dist > 0.05:
                # Проекция на экран
                screen_x = (delta / FOV + 0.5) * WIDTH
                
                # Рассчитываем Y с учетом вертикального смещения Z и дистанции
                # ВАЖНО: если в игре Z направлен вверх, нужно вычитать ( - self.z * ...), 
                # если вниз — прибавлять. Подправьте знак при необходимости.
                screen_y = HALF_HEIGHT + self.z * (SCREEN_DIST / dist)
                
                # Размер частицы в зависимости от расстояния
                size = int(SCREEN_DIST / (dist * 100))

                # Отрисовка, если частица видна на экране и имеет размер
                if 0 < screen_y < HEIGHT and size > 0:
                    # Ограничиваем координаты экрана разумными пределами, чтобы Pygame не тратил ресурсы
                    if -size < screen_x < WIDTH + size:
                        pygame.draw.circle(self.game.screen, self.color,
                                           (int(screen_x), int(screen_y)), size)
