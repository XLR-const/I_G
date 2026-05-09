import pygame as pg
import math
from setting import *
from random import uniform

class Weapon:
    def __init__(self, game, name, damage, reload_time, is_continuous=False):
        self.game = game
        self.name = name
        
        path = f'resources/player/{self.name}_shot.wav'
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
        self.sound_empty_ammo = pg.mixer.Sound('resources/player/empty.wav')
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
        self.sprite_path = f"resources/weapons/{self.name}.png"
        try:
            original = pygame.image.load(self.sprite_path).convert_alpha()
            # Масштабируем: размер делим на 2 (или подбери свой коэффициент)
            scale_factor = 0.3  # уменьшаем в 2 раза
            new_width = int(original.get_width() * scale_factor)
            new_height = int(original.get_height() * scale_factor)
            self.sprite = pygame.transform.scale(original, (new_width, new_height))
            self.pos = grid_to_pixel(17, 12)
        except:
            self.sprite = None
    
    def draw(self):
        self.update_animation()
        try:
            center_x = (GRID_W // 2) * CELL_W - 0.5 * CELL_W
            bottom_y = HEIGHT + int(80 * self.scale_y) + self.recoil * 2.0
            recoil_offset = 1 * self.recoil
            sprite_rect = self.sprite.get_rect(midbottom=(center_x, bottom_y + recoil_offset))
            self.game.screen.blit(self.sprite, sprite_rect)
            
            if self.reloading and self.elapsed < 50:
                flash_col = 16
                flash_row = 12
                flash_x, flash_y = grid_to_pixel(flash_col, flash_row)
                flash_y += recoil_offset
                
                pygame.draw.circle(self.game.screen, (255, 255, 100), (flash_x, flash_y), self.s(50))
                pygame.draw.circle(self.game.screen, (255, 255, 255), (flash_x, flash_y), self.s(20))
        except:
            center_x = (GRID_W // 2) * CELL_W
            bottom_y = HEIGHT + int(80 * self.scale_y) + self.recoil * 2.0
            
            pg.draw.polygon(self.game.screen, (35, 35, 35), [
                (center_x - self.s(110), bottom_y), (center_x + self.s(110), bottom_y),
                (center_x + self.s(70), bottom_y - self.s(350)), (center_x - self.s(70), bottom_y - self.s(350))
            ])
            pg.draw.polygon(self.game.screen, (55, 55, 55), [
                (center_x - self.s(70), bottom_y - self.s(280)), (center_x + self.s(70), bottom_y - self.s(280)),
                (center_x + self.s(60), bottom_y - self.s(350)), (center_x - self.s(60), bottom_y - self.s(350))
            ])
            pg.draw.rect(self.game.screen, (20, 20, 20), (center_x - self.s(5), bottom_y - self.s(365), self.s(10), self.s(15)))
            pg.draw.circle(self.game.screen, (10, 10, 10), (center_x, int(bottom_y - self.s(330))), self.s(12))
            
            if self.reloading and self.elapsed < 40:
                flash_y = bottom_y - self.s(360)
                pg.draw.circle(self.game.screen, (255, 255, 100), (center_x, flash_y), self.s(50))
                pg.draw.circle(self.game.screen, (255, 255, 255), (center_x, flash_y), self.s(20))

        
class Shotgun(Weapon):
    def __init__(self, game):
        super().__init__(game, "Shotgun", 50, 800)
        self.sprite_path = f"resources/weapons/{self.name}.png"
        try:
            self.sprite = pygame.image.load(self.sprite_path).convert_alpha()
            self.pos = (17, 12)
            self.pos = grid_to_pixel(self.pos[0], self.pos[1])
        except:
            self.sprite = None
                 
    def draw(self):
        self.update_animation()
        try:
            center_x = (GRID_W // 2) * CELL_W + CELL_W * 0.2
            bottom_y = HEIGHT + int(80 * self.scale_y) + self.recoil * 2.0
            recoil_offset = 3.5 * self.recoil
            sprite_rect = self.sprite.get_rect(midbottom=(center_x, bottom_y + recoil_offset))
            self.game.screen.blit(self.sprite, sprite_rect)
            # Вспышка
            if self.reloading and self.elapsed < 50:
                flash_col = 16
                flash_row = 12
                flash_x, flash_y = grid_to_pixel(flash_col, flash_row)
                flash_y += recoil_offset
                
                pygame.draw.circle(self.game.screen, (255, 140, 0), (flash_x, flash_y), self.s(120))
                pygame.draw.circle(self.game.screen, (255, 255, 180), (flash_x, flash_y), self.s(50))
        except:
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
        self.sprite_path = f"resources/weapons/{self.name}.png"
        try:
            original = pygame.image.load(self.sprite_path).convert_alpha()
            scale_factor = 4
            new_width = int(original.get_width() * scale_factor)
            new_height = int(original.get_height() * scale_factor)
            self.sprite = pygame.transform.scale(original, (new_width, new_height))
            self.pos = grid_to_pixel(17, 12)
        except:
            self.sprite = None
    
    def draw(self):
        self.update_animation()
        try:
            center_x = (GRID_W // 2) * CELL_W + CELL_W 
            bottom_y = HEIGHT + int(80 * self.scale_y) + self.recoil * 2.0 - CELL_H * 1
            recoil_offset = 1.5 * self.recoil
            sprite_rect = self.sprite.get_rect(midbottom=(center_x, bottom_y - recoil_offset))
            self.game.screen.blit(self.sprite, sprite_rect)
            
            if self.reloading and self.elapsed < 40:
                flash_col = 17
                flash_row = 12
                flash_x, flash_y = grid_to_pixel(flash_col, flash_row)
                flash_y += recoil_offset
                
                pygame.draw.circle(self.game.screen, (255, 200, 50), (flash_x, flash_y), self.s(80))
                pygame.draw.circle(self.game.screen, (255, 255, 255), (flash_x, flash_y), self.s(30))
        except:
            center_x = (GRID_W // 2) * CELL_W
            bottom_y = HEIGHT + int(120 * self.scale_y) + self.recoil
            shake = math.sin(pygame.time.get_ticks() * 0.3) * 6 if self.reloading else 0
            cx = center_x + shake
            
            pg.draw.polygon(self.game.screen, (30, 30, 30), [
                (cx - self.s(180), bottom_y), (cx + self.s(180), bottom_y),
                (cx + self.s(140), bottom_y - self.s(180)), (cx - self.s(140), bottom_y - self.s(180))
            ])
            
            rot_speed = 0.06 if self.reloading else 0.01
            for i in range(4):
                angle = pygame.time.get_ticks() * rot_speed + i * (math.pi / 2)
                offset = math.cos(angle) * self.s(80)
                thickness = self.s(30) + math.sin(angle) * self.s(10)
                if math.sin(angle) > -0.5:
                    color_val = 50 + int(math.sin(angle) * 20)
                    color_val = min(200, max(30, color_val))
                    color = (color_val, color_val, color_val)
                    pg.draw.rect(self.game.screen, color, 
                                (cx + offset - thickness // 2, bottom_y - self.s(420), thickness, self.s(240)))
                    pg.draw.circle(self.game.screen, (10, 10, 10), 
                                (int(cx + offset), int(bottom_y - self.s(420))), int(thickness // 1.5))
            
            if self.reloading and self.elapsed < 40:
                flash_y = bottom_y - self.s(440)
                pg.draw.circle(self.game.screen, (255, 200, 50), (cx, flash_y), self.s(80))
                pg.draw.circle(self.game.screen, (255, 255, 255), (cx, flash_y), self.s(30))

class PlasmaGun(Weapon):
    def __init__(self, game):
        super().__init__(game, "Plasma Gun", 100, 400)
        self.sprite_path = f"resources/weapons/{self.name}.png"
        try:
            original = pygame.image.load(self.sprite_path).convert_alpha()
            # Увеличиваем плазмаган (было 0.5, стало 0.7)
            scale_factor = 4
            new_width = int(original.get_width() * scale_factor)
            new_height = int(original.get_height() * scale_factor)
            self.sprite = pygame.transform.scale(original, (new_width, new_height))
            self.pos = grid_to_pixel(25, 12)
        except:
            self.sprite = None
    
    def draw(self):
        self.update_animation()
        try:
            center_x = (GRID_W // 2) * CELL_W + CELL_W * 5
            # Смещение по вертикали (подбери под свой спрайт)
            offset_y = -40 
            bottom_y = HEIGHT + offset_y + self.recoil * 2.0 - CELL_H * 1
            recoil_offset = 2.5 * self.recoil
            
            # Используем center вместо midbottom
            sprite_rect = self.sprite.get_rect(center=(center_x, bottom_y + recoil_offset))
            self.game.screen.blit(self.sprite, sprite_rect)
            
            if self.reloading and self.elapsed < 100:
                # Позиция вспышки через cell (col, row)
                flash_col = 18
                flash_row = 13
                flash_x, flash_y = grid_to_pixel(flash_col, flash_row)
                
                # Добавляем смещение отдачи
                flash_y += recoil_offset
                
                pygame.draw.circle(self.game.screen, (200, 0, 255), (flash_x, flash_y), self.s(70))
                pygame.draw.circle(self.game.screen, (255, 100, 255), (flash_x, flash_y), self.s(30))
        except:
            pass

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
        