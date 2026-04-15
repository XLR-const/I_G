import pygame as pg
import math
from setting import *


class Weapon:
    def __init__(self, game, name, damage, reload_time, is_continuous=False):
        self.game = game
        self.name = name
        
        path = f'resources/{self.name}_shot.wav'
        self.sound = pg.mixer.Sound(path)
        self.sound.set_volume(0.2)
        self.damage = damage
        self.reload_time = reload_time
        self.reloading = False
        self.last_shot_time = 0
        self.recoil = 0
        self.is_continuous = is_continuous

    def fire(self):
        if not self.reloading:
            self.reloading = True
            self.last_shot_time = pg.time.get_ticks()
            self.sound.play()

    def update_animation(self):
        if self.reloading:
            self.elapsed = pg.time.get_ticks() - self.last_shot_time
            if self.elapsed < self.reload_time:
                self.recoil = math.sin(self.elapsed / self.reload_time * math.pi) * 50
            else:
                self.reloading = False
                self.recoil = 0
        else:
            self.elapsed = 9999

class Pistol(Weapon):
    def __init__(self, game):
        super().__init__(game, "Pistol", 10, 150)

    def draw(self):
        self.update_animation()
        cx, by = WIDTH // 2, HEIGHT + self.recoil

        # ТВОЯ ЛЮБИМАЯ МОДЕЛЬ (Корпус)
        pg.draw.polygon(self.game.screen, (35, 35, 35), [
            (cx - 110, by), (cx + 110, by),
            (cx + 70, by - 350), (cx - 70, by - 350)
        ])
        # Затвор
        pg.draw.polygon(self.game.screen, (55, 55, 55), [
            (cx - 70, by - 280), (cx + 70, by - 280),
            (cx + 60, by - 350), (cx - 60, by - 350)
        ])
        # Детали (Мушка, Дуло)
        pg.draw.rect(self.game.screen, (20, 20, 20), (cx - 5, by - 365, 10, 15))
        pg.draw.circle(self.game.screen, (10, 10, 10), (cx, int(by - 330)), 12)

        # ВОЗВРАЩАЕМ ВСПЫШКУ
        if self.reloading and self.elapsed < 40:
            f_x, f_y = cx, int(by - 360)
            pg.draw.circle(self.game.screen, (255, 255, 100), (f_x, f_y), 50)
            pg.draw.circle(self.game.screen, (255, 255, 255), (f_x, f_y), 20)

        # Прицел
        pg.draw.circle(self.game.screen, 'red', (WIDTH // 2, HEIGHT // 2), 4, 1)
class Shotgun(Weapon):
    def __init__(self, game):
        # Урон 50, перезарядка 800мс
        super().__init__(game, "Shotgun", 50, 800)

    def draw(self):
        self.update_animation()
        # Опускаем модель чуть ниже и усиливаем отдачу
        cx, by = WIDTH // 2, HEIGHT + 80 + self.recoil * 2.0 

        # 1. ДЕРЕВЯННОЕ ЦЕВЬЕ (нижняя часть)
        # Цвет темного дерева (коричневый)
        WOOD_COLOR = (100, 50, 20)
        pg.draw.polygon(self.game.screen, WOOD_COLOR, [
            (cx - 220, by), (cx + 220, by),
            (cx + 170, by - 180), (cx - 170, by - 180)
        ])
        # Тень на дереве для объема
        pg.draw.polygon(self.game.screen, (70, 35, 15), [
            (cx - 170, by - 180), (cx + 170, by - 180),
            (cx + 150, by - 210), (cx - 150, by - 210)
        ])

        # 2. СОПРИКАСАЮЩИЕСЯ СТВОЛЫ (Металл)
        # Левый ствол (вплотную к центру)
        pg.draw.polygon(self.game.screen, (50, 50, 50), [
            (cx - 90, by - 200), (cx, by - 200),
            (cx, by - 400), (cx - 75, by - 400)
        ])
        # Правый ствол (вплотную к центру)
        pg.draw.polygon(self.game.screen, (60, 60, 60), [
            (cx, by - 200), (cx + 90, by - 200),
            (cx + 75, by - 400), (cx, by - 400)
        ])
        
        # Разделительная линия между стволами для четкости
        pg.draw.line(self.game.screen, (20, 20, 20), (cx, by - 200), (cx, by - 400), 2)

        # 3. ДУЛЬНЫЕ СРЕЗЫ
        pg.draw.circle(self.game.screen, (10, 10, 10), (cx - 42, int(by - 395)), 28)
        pg.draw.circle(self.game.screen, (10, 10, 10), (cx + 42, int(by - 395)), 28)

        # 4. МОЩНАЯ ВСПЫШКА
        if self.reloading and self.elapsed < 50:
            f_y = int(by - 410)
            pg.draw.circle(self.game.screen, (255, 140, 0), (cx, f_y), 120)
            pg.draw.circle(self.game.screen, (255, 255, 180), (cx, f_y), 50)

        # Прицел
        pg.draw.circle(self.game.screen, 'red', (WIDTH // 2, HEIGHT // 2), 4, 1)

class MachineGun(Weapon):
    def __init__(self, game):
        # Очень быстрая перезарядка (90мс) для эффекта очереди
        super().__init__(game, "Machine Gun", 5, 90, True)

    def draw(self):
        self.update_animation()
        # Постоянная мелкая тряска при стрельбе
        shake = math.sin(pg.time.get_ticks() * 0.1) * 5 if self.reloading else 0
        cx, by = WIDTH // 2 + shake, HEIGHT + 100 + self.recoil

        # ТРИ СТВОЛА (Миниган)
        for i in [-40, 0, 40]:
            pg.draw.polygon(self.game.screen, (60, 60, 60), [
                (cx + i - 20, by - 150), (cx + i + 20, by - 150),
                (cx + i + 15, by - 400), (cx + i - 15, by - 400)
            ])
            pg.draw.circle(self.game.screen, (10, 10, 10), (int(cx + i), int(by - 400)), 15)

        if self.reloading and self.elapsed < 40:
            pg.draw.circle(self.game.screen, (255, 255, 150), (cx, int(by - 420)), 60)

class PlasmaGun(Weapon):
    def __init__(self, game):
        super().__init__(game, "Plasma Gun", 30, 400)

    def draw(self):
        self.update_animation()
        cx, by = WIDTH // 2, HEIGHT + 80 + self.recoil

        # ФУТУРИСТИЧНЫЙ КОРПУС
        pg.draw.polygon(self.game.screen, (20, 40, 80), [
            (cx - 150, by), (cx + 150, by),
            (cx + 100, by - 350), (cx - 100, by - 350)
        ])
        # Светящаяся плазменная трубка
        plasma_color = (0, 255, 255) if not self.reloading else (255, 0, 255)
        pg.draw.rect(self.game.screen, plasma_color, (cx - 20, by - 300, 40, 150), 0, 5)

        if self.reloading and self.elapsed < 100:
            pg.draw.circle(self.game.screen, (200, 0, 255), (cx, int(by - 370)), 70)
