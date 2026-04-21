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


class Pistol(Weapon):
    def __init__(self, game):
        super().__init__(game, "Pistol", 10, 150)
    # 10 урона и 150 мс перезарядки
    def draw(self):
        self.update_animation()
        cx, by = WIDTH // 2, HEIGHT + self.recoil

        
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
        # Быстрая стрельба (90мс) и флаг автоматического огня (True)
        super().__init__(game, "Machine Gun", 15, 90, True)

    def draw(self):
        self.update_animation()
        
        time = pg.time.get_ticks()
        # Скорость вращения: быстро при стрельбе, медленно в покое
        rot_speed = 0.06 if self.reloading else 0.01
        
        # Тряска при стрельбе
        shake = math.sin(time * 0.3) * 6 if self.reloading else 0
        cx, by = WIDTH // 2 + shake, HEIGHT + 120 + self.recoil

        # 1. МАССИВНЫЙ КОРПУС (Задняя часть)
        pg.draw.polygon(self.game.screen, (30, 30, 30), [
            (cx - 180, by), (cx + 180, by),
            (cx + 140, by - 180), (cx - 140, by - 180)
        ])

        # 2. БЛОК ГИГАНТСКИХ СТВОЛОВ (4 штуки для массивности)
        # Увеличиваем разлет (80) и базовую толщину (30)
        for i in range(4):
            angle = time * rot_speed + i * (math.pi / 2)
            offset = math.cos(angle) * 80
            # Эффект перспективы для толщины ствола
            thickness = 30 + math.sin(angle) * 10
            
            # Рисуем ствол только если он на переднем плане
            if math.sin(angle) > -0.5:
                # Цвет с градиентом для объема
                color_val = 50 + int(math.sin(angle) * 20)
                color = (color_val, color_val, color_val)
                
                # Сами трубы стволов
                pg.draw.rect(self.game.screen, color, 
                             (cx + offset - thickness // 2, by - 420, thickness, 240))
                
                # Массивные дульные срезы
                pg.draw.circle(self.game.screen, (10, 10, 10), 
                               (int(cx + offset), int(by - 420)), int(thickness // 1.5))
                # Блик на срезе для металла
                pg.draw.circle(self.game.screen, (80, 80, 80), 
                               (int(cx + offset - 5), int(by - 425)), int(thickness // 4))

        # 3. ВСПЫШКА (Яркая и широкая)
        if self.reloading and self.elapsed < 40:
            f_y = int(by - 440)
            pg.draw.circle(self.game.screen, (255, 200, 50), (cx, f_y), 80)
            pg.draw.circle(self.game.screen, (255, 255, 255), (cx, f_y), 30)

        # Прицел
        pg.draw.circle(self.game.screen, 'red', (WIDTH // 2, HEIGHT // 2), 4, 1)

class PlasmaGun(Weapon):
    def __init__(self, game):
        super().__init__(game, "Plasma Gun", 100, 400)

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
        