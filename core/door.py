import pygame
import math
from setting import *


class Door:
    """Класс двери с анимацией открытия и закрытия

    Attributes:
        game: Объект игры
        x: Координата X
        y: Координата Y
        state: Состояние двери (CLOSED, OPENING, OPENED, CLOSING)
        open_progress: Прогресс открытия (0.0 - 1.0)
        speed: Скорость открытия/закрытия
        trigger_distance: Дистанция срабатывания
        close_delay: Задержка перед закрытием в мс
        close_timer: Таймер закрытия
        color: Цвет двери (fallback)
        frame: Кадр анимации
    """

    def __init__(self, game, x, y):
        """Инициализирует дверь

        Args:
            game: Объект игры
            x: Координата X
            y: Координата Y
        """
        self.game = game
        self.x = x
        self.y = y
        self.state = "CLOSED"
        self.open_progress = 0.0
        self.speed = 0.05
        self.trigger_distance = 1.5
        self.close_delay = 1000
        self.close_timer = 0

        self.color = WALL_COLORS['W']
        self.frame = 0

    def update(self):
        """Обновляет состояние двери"""
        dx = self.game.player.x - self.x
        dy = self.game.player.y - self.y
        dist = math.hypot(dx, dy)

        if self.state == "CLOSED":
            if dist < self.trigger_distance:
                self.state = "OPENING"

        elif self.state == "OPENING":
            self.open_progress += self.speed
            if self.open_progress >= 1.0:
                self.open_progress = 1.0
                self.state = "OPEN"
                self.close_timer = pygame.time.get_ticks() + self.close_delay

        elif self.state == "OPEN":
            if dist > self.trigger_distance * 1.5:
                if pygame.time.get_ticks() > self.close_timer:
                    self.state = "CLOSING"

        elif self.state == "CLOSING":
            self.open_progress -= self.speed
            if self.open_progress <= 0.0:
                self.open_progress = 0.0
                self.state = "CLOSED"

    def is_wall(self):
        """Проверяет, является ли дверь стеной

        Returns:
            bool: True если дверь закрыта или закрывается
        """
        return self.state == "CLOSED" or self.state == "CLOSING"

    def get_texture_offset(self):
        """Возвращает смещение текстуры для анимации

        Returns:
            float: Прогресс открытия (0.0 - 1.0)
        """
        if self.state == "OPENING":
            return self.open_progress
        elif self.state == "CLOSING":
            return self.open_progress
        elif self.state == "OPEN":
            return 1.0
        else:
            return 0.0
