import pygame as pg
from setting import *
import math

class Weapon:
    def __init__(self, game):
        self.game = game
        self.reloading = False
        self.last_shot_time = 0
        self.RELOAD_TIME = 100
        self.recoil = 0

    def fire(self):
        if not self.reloading:
            self.reloading = True
            self.last_shot_time = pg.time.get_ticks()

    def draw(self):
        # 1. Инициализация переменных (чтобы не было ошибок)
        self.recoil = 0
        time_now = pg.time.get_ticks()
        elapsed = time_now - self.last_shot_time

        # 2. Логика анимации отдачи
        if self.reloading:
            if elapsed < self.RELOAD_TIME:
                # Пистолет прыгает вверх
                self.recoil = math.sin(elapsed / self.RELOAD_TIME * math.pi) * 50
            else:
                self.reloading = False
                self.recoil = 0

        # Базовые координаты (с учетом отдачи)
        cx = WIDTH // 2
        by = HEIGHT + self.recoil

        # 3. РИСУЕМ КОРПУС ПИСТОЛЕТА (Тот самый, что тебе понравился)
        # Нижняя часть
        pg.draw.polygon(self.game.screen, (35, 35, 35), [
            (cx - 110, by), (cx + 110, by),
            (cx + 70, by - 350), (cx - 70, by - 350)
        ])
        # Верхняя часть (затвор)
        pg.draw.polygon(self.game.screen, (55, 55, 55), [
            (cx - 70, by - 280), (cx + 70, by - 280),
            (cx + 60, by - 350), (cx - 60, by - 350)
        ])
        # Мушка и детали
        pg.draw.rect(self.game.screen, (20, 20, 20), (cx - 5, by - 365, 10, 15))
        pg.draw.circle(self.game.screen, (10, 10, 10), (cx, int(by - 330)), 12)

        # 4. ВСПЫШКА (Рисуем ПОВЕРХ пистолета)
        if self.reloading and elapsed < 40:
            f_x, f_y = cx, int(by - 360)
            pg.draw.circle(self.game.screen, (255, 255, 100), (f_x, f_y), 50)
            pg.draw.circle(self.game.screen, (255, 255, 255), (f_x, f_y), 20)

        # 5. ПРИЦЕЛ
        pg.draw.circle(self.game.screen, 'red', (WIDTH // 2, HEIGHT // 2), 4, 1)