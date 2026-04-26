import pygame as pg
import math
from setting import *
from random import uniform

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
        self.ammo = 0
        self.last_shot_time = 0
        self.recoil = 0
        self.is_continuous = is_continuous
        self.scale_x = CELL_W / 60
        self.scale_y = CELL_H / 60
        self.sound_empty_ammo = pg.mixer.Sound('resources/empty.wav')
        self.sound_empty_ammo.set_volume(0.2)

    def fire(self):
        if not self.reloading and self.ammo > 0:
            self.reloading = True
            self.last_shot_time = pg.time.get_ticks()
            self.sound.play()
            self.ammo -= 1
            
            # Walls
            hit_x, hit_y, dist, side = self.get_hit_pos()
            
            # NPC
            for npc in self.game.npcs:
                if not npc.alive:
                    continue
                
                # Вектор от игрока к NPC
                dx = npc.x - self.game.player.x
                dy = npc.y - self.game.player.y
                dist_npc = math.hypot(dx, dy)
                
                # Угол на NPC
                theta = math.atan2(dy, dx)
                # Разница с углом взгляда игрока
                delta = theta - self.game.player.angle
                delta = (delta + math.pi) % math.tau - math.pi
                
                
                view_width = npc.size / dist_npc 
    
                if abs(delta) < view_width and dist_npc < dist and math.cos(delta) > 0:
                    npc.get_damage(self.damage)
                
            
            # Particle effect
            for _ in range(10):
                p_pos = (hit_x + uniform(-0.02, 0.02), hit_y + uniform(-0.02, 0.02))
                self.game.particles.append(Particle(self.game, p_pos, (255, 200, 50), uniform(0.001, 0.005)))
        if self.ammo == 0:
            self.sound_empty_ammo.play()

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
    # DDA alg        
    def get_hit_pos(self):
        
        ox, oy = self.game.player.x, self.game.player.y
        x_map, y_map = int(ox), int(oy)
        
        angle = self.game.player.angle
        sin_a = math.sin(angle)
        cos_a = math.cos(angle)

        delta_dist_x = abs(1 / cos_a) if cos_a != 0 else 1e30
        delta_dist_y = abs(1 / sin_a) if sin_a != 0 else 1e30

        if cos_a < 0:
            step_x = -1
            side_dist_x = (ox - x_map) * delta_dist_x
        else:
            step_x = 1
            side_dist_x = (x_map + 1.0 - ox) * delta_dist_x

        if sin_a < 0:
            step_y = -1
            side_dist_y = (oy - y_map) * delta_dist_y
        else:
            step_y = 1
            side_dist_y = (y_map + 1.0 - oy) * delta_dist_y

        # Цикл DDA до первой стены
        side = 0
        while True:
            if side_dist_x < side_dist_y:
                side_dist_x += delta_dist_x
                x_map += step_x
                side = 0
            else:
                side_dist_y += delta_dist_y
                y_map += step_y
                side = 1
            
            # Проверяем карту
            if (x_map, y_map) in self.game.map.world_map:
                break

        # 5. Считаем финальную дистанцию
        if side == 0:
            dist = side_dist_x - delta_dist_x
        else:
            dist = side_dist_y - delta_dist_y

        # Точные координаты точки удара на карте
        hit_x = ox + dist * cos_a
        hit_y = oy + dist * sin_a

        return hit_x, hit_y, dist, side

    def s(self, x, y=None):
        """Универсальный метод масштабирования
        эталонных координат"""
        if y is None:
            return int(x * self.scale_x)
        return (int(x * self.scale_x), int(y * self.scale_y))


class Pistol(Weapon):
    def __init__(self, game):
        super().__init__(game, "Pistol", 10, 150)
    # 10 урона и 150 мс перезарядки
    def draw(self):
        self.update_animation()
        
        # Получаем центр экрана через сетку
        cx = int((GRID_W // 2) * CELL_W)  # 15.5 * CELL_W
        cy = int((GRID_H // 2) * CELL_H)  # 8.5 * CELL_H
        
        # Базовая позиция: от нижнего края экрана
        # Оригинал: by = HEIGHT + self.recoil
        # Переводим: от нижнего края отступаем 0 клеток (HEIGHT = GRID_H * CELL_H)
        bottom_y = GRID_H * CELL_H + self.recoil
        
        # Оригинальные значения и их перевод в клетки:
        # 110 пикселей = 110 / CELL_W клеток (CELL_W = 60 при 1920/32)
        # 350 пикселей = 350 / CELL_H клеток (CELL_H = 60 при 1080/18)
        
        # Корпус пистолета
        # Оригинал: (cx - 110, by), (cx + 110, by), (cx + 70, by - 350), (cx - 70, by - 350)
        offset_bottom = int(110 * CELL_W / 60)      # коэффициент от оригинального CELL_W (60)
        offset_top = int(70 * CELL_W / 60)
        height = int(350 * CELL_H / 60)              # оригинальная высота 350 при CELL_H=60
        
        pg.draw.polygon(self.game.screen, (35, 35, 35), [
            (cx - offset_bottom, bottom_y), 
            (cx + offset_bottom, bottom_y),
            (cx + offset_top, bottom_y - height), 
            (cx - offset_top, bottom_y - height)
        ])
        
        # Затвор
        # Оригинал: (cx - 70, by - 280), (cx + 70, by - 280), (cx + 60, by - 350), (cx - 60, by - 350)
        slide_offset_bottom = int(70 * CELL_W / 60)
        slide_offset_top = int(60 * CELL_W / 60)
        slide_y = int(280 * CELL_H / 60)
        
        pg.draw.polygon(self.game.screen, (55, 55, 55), [
            (cx - slide_offset_bottom, bottom_y - slide_y),
            (cx + slide_offset_bottom, bottom_y - slide_y),
            (cx + slide_offset_top, bottom_y - height),
            (cx - slide_offset_top, bottom_y - height)
        ])
        
        # Детали (Мушка, Дуло)
        # Оригинал: (cx - 5, by - 365, 10, 15)
        sight_w = int(10 * CELL_W / 60)
        sight_h = int(15 * CELL_H / 60)
        sight_x = cx - sight_w // 2
        sight_y = bottom_y - int(365 * CELL_H / 60)
        pg.draw.rect(self.game.screen, (20, 20, 20), (sight_x, sight_y, sight_w, sight_h))
        
        # Оригинал: (cx, int(by - 330)), 12
        muzzle_y = bottom_y - int(330 * CELL_H / 60)
        muzzle_r = int(12 * CELL_W / 60)
        pg.draw.circle(self.game.screen, (10, 10, 10), (cx, muzzle_y), muzzle_r)

        # Вспышка
        if self.reloading and self.elapsed < 40:
            flash_y = bottom_y - int(360 * CELL_H / 60)
            flash_r_big = int(50 * CELL_W / 60)
            flash_r_small = int(20 * CELL_W / 60)
            pg.draw.circle(self.game.screen, (255, 255, 100), (cx, flash_y), flash_r_big)
            pg.draw.circle(self.game.screen, (255, 255, 255), (cx, flash_y), flash_r_small)

        
class Shotgun(Weapon):
    def __init__(self, game):
        super().__init__(game, "Shotgun", 50, 800)    
    def draw(self):
        self.update_animation()
        
        # Центр экрана = начало 16-й клетки (индекс 16)
        center_x = (GRID_W // 2) * CELL_W
        # Для дробовика смещение вниз: оригинал HEIGHT + 80
        # 80 пикселей = 80 / 60 = 1.33 клетки
        bottom_y = HEIGHT + int(80 * self.scale_y) + self.recoil * 2.0
        
        # 1. ДЕРЕВЯННОЕ ЦЕВЬЕ (нижняя часть)
        WOOD_COLOR = (100, 50, 20)
        pg.draw.polygon(self.game.screen, WOOD_COLOR, [
            (center_x - self.s(220), bottom_y),
            (center_x + self.s(220), bottom_y),
            (center_x + self.s(170), bottom_y - self.s(180)),
            (center_x - self.s(170), bottom_y - self.s(180))
        ])
        
        # Тень на дереве для объема
        pg.draw.polygon(self.game.screen, (70, 35, 15), [
            (center_x - self.s(170), bottom_y - self.s(180)),
            (center_x + self.s(170), bottom_y - self.s(180)),
            (center_x + self.s(150), bottom_y - self.s(210)),
            (center_x - self.s(150), bottom_y - self.s(210))
        ])
        
        # 2. СОПРИКАСАЮЩИЕСЯ СТВОЛЫ (Металл)
        # Левый ствол (вплотную к центру)
        pg.draw.polygon(self.game.screen, (50, 50, 50), [
            (center_x - self.s(90), bottom_y - self.s(200)),
            (center_x, bottom_y - self.s(200)),
            (center_x, bottom_y - self.s(400)),
            (center_x - self.s(75), bottom_y - self.s(400))
        ])
        
        # Правый ствол (вплотную к центру)
        pg.draw.polygon(self.game.screen, (60, 60, 60), [
            (center_x, bottom_y - self.s(200)),
            (center_x + self.s(90), bottom_y - self.s(200)),
            (center_x + self.s(75), bottom_y - self.s(400)),
            (center_x, bottom_y - self.s(400))
        ])
        
        # Разделительная линия между стволами для четкости
        pg.draw.line(self.game.screen, (20, 20, 20), 
                    (center_x, bottom_y - self.s(200)), 
                    (center_x, bottom_y - self.s(400)), 2)
        
        # 3. ДУЛЬНЫЕ СРЕЗЫ
        pg.draw.circle(self.game.screen, (10, 10, 10), 
                      (center_x - self.s(42), bottom_y - self.s(395)), self.s(28))
        pg.draw.circle(self.game.screen, (10, 10, 10), 
                      (center_x + self.s(42), bottom_y - self.s(395)), self.s(28))
        
        # 4. МОЩНАЯ ВСПЫШКА
        if self.reloading and self.elapsed < 50:
            flash_y = bottom_y - self.s(410)
            pg.draw.circle(self.game.screen, (255, 140, 0), 
                          (center_x, flash_y), self.s(120))
            pg.draw.circle(self.game.screen, (255, 255, 180), 
                          (center_x, flash_y), self.s(50))
        


class MachineGun(Weapon):
    def __init__(self, game):
        super().__init__(game, "Machine Gun", 10, 90, True)

    def draw(self):
        self.update_animation()
        
        time = pg.time.get_ticks()
        # Скорость вращения: быстро при стрельбе, медленно в покое
        rot_speed = 0.06 if self.reloading else 0.01
        
        # Тряска при стрельбе: 6 пикселей в клетки
        shake = math.sin(time * 0.3) * (6 * self.scale_x) if self.reloading else 0
        # Центр экрана = начало 16-й клетки
        center_x = (GRID_W // 2) * CELL_W + shake
        # Смещение вниз: 120 пикселей = 2 клетки
        bottom_y = HEIGHT + int(120 * self.scale_y) + self.recoil

        # 1. МАССИВНЫЙ КОРПУС (Задняя часть)
        pg.draw.polygon(self.game.screen, (30, 30, 30), [
            (center_x - self.s(180), bottom_y),
            (center_x + self.s(180), bottom_y),
            (center_x + self.s(140), bottom_y - self.s(180)),
            (center_x - self.s(140), bottom_y - self.s(180))
        ])

        # 2. БЛОК ГИГАНТСКИХ СТВОЛОВ (4 штуки для массивности)
        for i in range(4):
            angle = time * rot_speed + i * (math.pi / 2)
            offset = math.cos(angle) * self.s(80)
            # Эффект перспективы для толщины ствола
            thickness = self.s(30) + math.sin(angle) * self.s(10)
            
            # Рисуем ствол только если он на переднем плане
            if math.sin(angle) > -0.5:
                # Цвет с градиентом для объема
                color_val = 50 + int(math.sin(angle) * 20)
                color = (color_val, color_val, color_val)
                
                # Сами трубы стволов
                pg.draw.rect(self.game.screen, color, 
                            (int(center_x + offset - thickness // 2), 
                             bottom_y - self.s(420), 
                             int(thickness), 
                             self.s(240)))
                
                # Массивные дульные срезы
                pg.draw.circle(self.game.screen, (10, 10, 10), 
                              (int(center_x + offset), 
                               bottom_y - self.s(420)), 
                              int(thickness // 1.5))
                # Блик на срезе для металла
                pg.draw.circle(self.game.screen, (80, 80, 80), 
                              (int(center_x + offset - 5 * self.scale_x), 
                               bottom_y - self.s(425)), 
                              int(thickness // 4))

        # 3. ВСПЫШКА (Яркая и широкая)
        if self.reloading and self.elapsed < 40:
            flash_y = bottom_y - self.s(440)
            pg.draw.circle(self.game.screen, (255, 200, 50), 
                          (int(center_x), flash_y), self.s(80))
            pg.draw.circle(self.game.screen, (255, 255, 255), 
                          (int(center_x), flash_y), self.s(30))

        # Прицел (центр экрана)
        pg.draw.circle(self.game.screen, 'red', 
                      (WIDTH // 2, HEIGHT // 2), 4, 1)

class PlasmaGun(Weapon):
    def __init__(self, game):
        super().__init__(game, "Plasma Gun", 100, 400)

    def draw(self):
        self.update_animation()
        
        # Центр экрана = начало 16-й клетки
        center_x = (GRID_W // 2) * CELL_W
        # Смещение вниз: 80 пикселей = 1.33 клетки
        bottom_y = HEIGHT + int(80 * self.scale_y) + self.recoil

        # ФУТУРИСТИЧНЫЙ КОРПУС
        pg.draw.polygon(self.game.screen, (20, 40, 80), [
            (center_x - self.s(150), bottom_y),
            (center_x + self.s(150), bottom_y),
            (center_x + self.s(100), bottom_y - self.s(350)),
            (center_x - self.s(100), bottom_y - self.s(350))
        ])
        
        # Светящаяся плазменная трубка
        plasma_color = (0, 255, 255) if not self.reloading else (255, 0, 255)
        pg.draw.rect(self.game.screen, plasma_color, 
                    (center_x - self.s(20), bottom_y - self.s(300), self.s(40), self.s(150)), 0, 5)

        # Вспышка при выстреле
        if self.reloading and self.elapsed < 100:
            flash_y = bottom_y - self.s(370)
            pg.draw.circle(self.game.screen, (200, 0, 255), 
                          (center_x, flash_y), self.s(70))

class Particle:
    def __init__(self, game, pos, color, speed):
        self.game = game
        self.x, self.y = pos
        # gravity
        self.z = 0
        self.v_z = uniform(-0.02, 0.01)
        self.gravity = 0.002
        self.color = color
        self.speed = speed
        self.angle = uniform(0, math.tau)
        self.life_time = 200
        self.start_time = pg.time.get_ticks()
        
    def update(self):
        dt = self.game.delta_time
        self.x += math.cos(self.angle) * self.speed * dt
        self.y += math.sin(self.angle) * self.speed * dt
        
        # Oz
        self.v_z += self.gravity
        self.z += self.v_z * dt
        
    def draw(self):
        dx = self.x - self.game.player.x
        dy = self.y - self.game.player.y
        theta = math.atan2(dy, dx)
        delta = theta - self.game.player.angle
        
        if dx > 0 and self.game.player.angle > math.pi: delta += math.tau
        elif dx < 0 and self.game.player.angle < math.pi: delta -= math.tau
        
        if -HALF_FOV < delta < HALF_FOV:
            dist = math.hypot(dx, dy)
            dist *= math.cos(delta)
            
            if dist > 0.1:
                screen_x = (delta / FOV + 0.5) * WIDTH
                
                # МАГИЯ: Смещаем Y в зависимости от Z и дистанции
                # Мы делим z на dist, чтобы чем дальше искра, тем меньше было её смещение
                screen_y = HALF_HEIGHT + self.z * (SCREEN_DIST / dist)
                
                size = int(SCREEN_DIST / (dist * 100)) 
                
                # Рисуем только если искра не улетела за пределы экрана по вертикали
                if 0 < screen_y < HEIGHT and size > 0:
                    pg.draw.circle(self.game.screen, self.color, (int(screen_x), int(screen_y)), size)
        