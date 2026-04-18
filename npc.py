import pygame
import math
from setting import *
from random import uniform
from weapon import Particle


class NPC:
    def __init__(self, game, pos=(8.5, 7.5)):
        self.game = game
        self.x, self.y = pos[0] + 0.5, pos[1] + 0.5
        self.alive = True
        # движение
        self.speed = 0.1
        self.radius = 0.35 # радиус коллизии
        
        # автомат действия
        self.state = "IDLE" # IDLE, ATTACK, PATROL, CHASE, DEAD, HURT
        self.state_timer = 0
        
        # shoot
        self.damage = 10
        self.shoot_delay = 800
        self.last_shot = 0
        self.shoot_range = 5.0 # дистанция аттаки
        self.shoot_flash = 0
        self.shoot_sound = pygame.mixer.Sound('resources/pistol_shot.wav')
        self.shoot_sound.set_volume(0.2)
        
        # patrol
        self.waypoints = []
        self.current_waypoint = 0
        self.idle_duration = 1500 # время бездействия
        self.flocking_enabled = True
        
        self.hurt_flash = 0
        self.size = 0.3
        self.hp = 100
        self.color = (245, 100, 0)
        
        # СПРАЙТЫ
        self.image = pygame.image.load('resources/npc/solder.png').convert_alpha()
        self.sprite_width, self.sprite_height = self.image.get_size()
        self.sprite_ratio = self.sprite_width / self.sprite_height
        
    def get_damage(self, damage):
        if not self.alive:
            return
        else:
            self.hp -= damage
            self.hurt_flash = 8
            self.state = "HURT"
            self.state_timer = pygame.time.get_ticks() + 300
            if self.hp <= 0:
                self.alive = False
                self.color = (50, 50, 50)
                
            for _ in range(15):
                dx = self.game.player.x - self.x
                dy = self.game.player.y - self.y
                dist = math.hypot(dx, dy)
                
                # Точка появления: чуть ближе к игроку от центра NPC
                p_x = self.x + (dx / dist) * 0.1 + uniform(-0.1, 0.1)
                p_y = self.y + (dy / dist) * 0.1 + uniform(-0.1, 0.1)
                self.game.particles.append(Particle(self.game, (p_x, p_y), (200, 0, 0), uniform(0.002, 0.005)))
    
    def update(self):
        if not self.alive:
            return 
        
        dt = self.game.delta_time
        if dt > 0.033:
            dt = 0.033
            
        if self.hurt_flash > 0:
            self.hurt_flash -= 1
        if self.shoot_flash > 0:
            self.shoot_flash -= 1
        
        self.update_state(dt)
    
    def check_hit(self):
        pass
    
    def draw(self):
        if not self.alive:
            # Add other dead sprite
            return
        """
        # ===== ВИЗУАЛЬНАЯ ОТЛАДКА =====
        # Рисуем красный кружок на 2D карте (если ты её включаешь)
        if hasattr(self.game, 'map'):
            screen_x = self.x * TILE
            screen_y = self.y * TILE
            pygame.draw.circle(self.game.screen, (255, 0, 0), (int(screen_x), int(screen_y)), 10)
        
        # Рисуем линию к игроку для отладки LOS
        if self.has_line_of_sight():
            start = (int(self.x * TILE), int(self.y * TILE))
            end = (int(self.game.player.x * TILE), int(self.game.player.y * TILE))
            pygame.draw.line(self.game.screen, (0, 255, 0), start, end, 2)
        else:
            start = (int(self.x * TILE), int(self.y * TILE))
            end = (int(self.game.player.x * TILE), int(self.game.player.y * TILE))
            pygame.draw.line(self.game.screen, (255, 0, 0), start, end, 2)
        """
        
        dx = self.x - self.game.player.x
        dy = self.y - self.game.player.y
        distance = math.hypot(dx, dy)
        
        theta = math.atan2(dy, dx)
        delta = theta - self.game.player.angle
        delta = (delta + math.pi) % math.tau - math.pi
        
        # Если NPC за спиной — не рисуем
        if math.cos(delta) <= 0 or distance < 0.2:
            return

        # Убираем рыбий глаз и считаем проекцию
        dist_flat = distance * math.cos(delta)
        # Защита от 0
        if dist_flat < 0.2:
            return
        
        proj_height = int(SCREEN_DIST / (dist_flat + 0.0001))
        if proj_height > HEIGHT * 2:
            proj_height = HEIGHT * 2
        proj_width = int(proj_height * self.sprite_ratio)
        
        # Позиция центра на экране
        center_x = (HALF_NUM_RAYS + delta / DELTA_ANGLE) * SCALE
        
        # Collision render
        """
        # Определяем границы NPC на экране
        start_x = int(center_x - proj_height // 2)
        end_x = int(center_x + proj_height // 2)

        # РИСУЕМ ПОЛОСКАМИ
        # Проходим по всем экранным координатам, которые занимает NPC
        for screen_x in range(start_x, end_x, SCALE):
            ray_idx = int(screen_x // SCALE)
            
            # Проверяем, попадает ли полоска в экран
            if 0 <= ray_idx < NUM_RAYS:
                # ГЛАВНОЕ: сравниваем дистанцию этой полоски с Z-буфером стены
                if dist_flat < self.game.raycasting.z_buffer[ray_idx]:
                    # Рисуем вертикальную линию (одну полоску спрайта)
                    pygame.draw.line(self.game.screen, self.color,
                                 (screen_x, HALF_HEIGHT - proj_height // 2),
                                 (screen_x, HALF_HEIGHT + proj_height // 2),
                                 SCALE)
        """

        if self.hurt_flash > 0:
            # Создаём красную версию спрайта
            img = self.image.copy()
            # Накладываем красный слой поверх
            red_surface = pygame.Surface(img.get_size())
            red_surface.fill((255, 0, 0))
            img.blit(red_surface, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        else:
            img = self.image
        
        # SPRITE RENDER
        img = pygame.transform.scale(img, (proj_width, proj_height))
        
    
        # Создаём копию спрайта для вспышки (если нужно поверх)
        if self.shoot_flash > 0:
            # Создаём жёлто-белый круг в центре спрайта
            flash_surface = pygame.Surface((proj_width, proj_height), pygame.SRCALPHA)
            
            # Яркость вспышки: максимальная в начале, затухает к концу
            intensity = min(255, self.shoot_flash * 40)  # 6*40=240, 5*40=200 и т.д.
            
            # Рисуем большой круг в центре
            center_flash_x = proj_width // 2
            center_flash_y = proj_height // 2
            radius = min(proj_width, proj_height) // 2
            
            # Внешнее свечение (жёлтое)
            pygame.draw.circle(flash_surface, (255, 200, 50, intensity), 
                            (center_flash_x, center_flash_y), radius)
            # Внутреннее свечение (белое)
            pygame.draw.circle(flash_surface, (255, 255, 200, intensity), 
                            (center_flash_x, center_flash_y), radius // 2)
            
            # Накладываем вспышку на спрайт (режим сложения цветов)
            img.blit(flash_surface, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        
        # Отрисовка полосками для Z-буфера
        start_x = int(center_x - proj_width // 2)
        for x in range(start_x, start_x + proj_width, SCALE):
            ray_idx = int(x // SCALE)
            if 0 <= ray_idx < NUM_RAYS:
                if dist_flat < self.game.raycasting.z_buffer[ray_idx]:
                    # Вырезаем нужную вертикальную полоску из отмасштабированной картинки
                    # area = (x_внутри_картинки, y_внутри_картинки, ширина_полоски, высота)
                    sub_x = int((x - start_x))
                    if 0 <= sub_x < proj_width:
                        self.game.screen.blit(img, (x, HALF_HEIGHT - proj_height // 2), 
                                              (sub_x, 0, SCALE, proj_height))
        
    # AI: проверка видимости ray и line of sight
    # Algos Ray Casting LOS
    def has_line_of_sight(self):
        
        dx = self.game.player.x - self.x
        dy = self.game.player.y - self.y
        distance = math.hypot(dx, dy)
        
        if distance > 12:
            return False
        
        # разделяем луч в проверке на отрезки
        steps = int(distance * 20)# 20 точек луча на клетку карты
        for step in range(steps):
            t = step / steps # Коэф пропорции до конца луча
            # Проверяем клетку на карте
            check_x = int(self.x + dx * t)
            check_y = int(self.y + dy * t)
            if self.game.map.is_wall(check_x, check_y):
                return False
        return True
    
    # Sliding Collision
    def check_collision(self, x, y):
        """коллизия NPC по отношению к карте  в точке (х, у)"""
        # проверка углов нпс
        for offset_x, offset_y in [(-self.radius, self.radius),
                                   (self.radius, self.radius),
                                   (-self.radius, -self.radius),
                                   (self.radius, -self.radius)]:
            check_x = int(x + offset_x)
            check_y = int(y + offset_y)
            
            if self.game.map.is_wall(check_x, check_y):
                return True
            
            for other in self.game.npcs:
                if other is not self and other.alive:
                    dist = math.hypot(x - other.x, y - other.y)
                    if dist < self.radius + other.radius:
                        return True
        return False
    
    def try_move(self, dx, dy):
        new_x = self.x + dx
        new_y = self.y + dy
        
        if not self.check_collision(new_x, self.y):
            self.x = new_x
        if not self.check_collision(self.x, new_y):
            self.y = new_y
            
    def shoot(self):
        now = pygame.time.get_ticks()
        if now - self.last_shot >= self.shoot_delay:
            self.last_shot = now
            self.shoot_flash = 12
            self.shoot_sound.play()
            self.game.player.hp -= self.damage
            
            # Flash fire
            for _ in range(8):
                self.game.particles.append(Particle(
                    self.game, (self.x + uniform(-0.1, 0.1),
                                self.y + uniform(-0.1, 0.1)),
                    (255, 200, 50),
                    uniform(0.003, 0.005)
                ))
    
    # Algos Finite State Machine(FSM)
    def update_state(self, dt):
        """принятие решения о движении NPC 
        в зависимости от его состояния 
        и положения игрока на карте"""
        
        distance_to_player = math.hypot(self.x - self.game.player.x, self.y - self.game.player.y)
        can_see = self.has_line_of_sight()
        #can_see = False
        # ЕСЛИ ПОЛУЧИЛ УРОН
        if self.state == "HURT":
            if pygame.time.get_ticks() > self.state_timer:
                if can_see:
                    self.state = "CHASE"
                else:
                    self.state = "IDLE"
        
        # ПРАВИЛА ПЕРЕХОДОВ ИЗ СОСТОЯНИЙ
        if not can_see:
            # либо патруль либо холд
            if self.state in ("ATTACK", "CHASE"):
                self.state = "IDLE"
                self.state_timer = pygame.time.get_ticks() + self.idle_duration
        else:
            # преследование или атака
            if distance_to_player <= self.shoot_range:
                self.state = "ATTACK"
            else:
                self.state = "CHASE"
                
        # ДЕЙСТВИЯ ПО ПЕРЕХОДАМ
        if self.state == "IDLE":
            if self.state_timer and pygame.time.get_ticks() > self.state_timer:
                if self.waypoints:
                    self.state = "PATROL"
                    self.current_waypoint = 0
                    
        elif self.state == "PATROL":
            if not self.waypoints:  # ЕСЛИ НЕТ ТОЧЕК
                self.state = "IDLE"  # ПЕРЕХОДИМ В IDLE
                return
            target_x, target_y = self.waypoints[self.current_waypoint]
            dx = target_x - self.x
            dy = target_y - self.y
            dist = math.hypot(dx, dy)
            
            if dist < 0.2:
                self.current_waypoint = (self.current_waypoint + 1) % len(self.waypoints)
                self.state = "IDLE"
                self.state_timer = pygame.time.get_ticks() + 500
            else:
                if dist > 0.01:
                    move_x = (dx / dist) * self.speed * dt
                    move_y = (dy / dist) * self.speed * dt
                    self.try_move(move_x, move_y)
            if can_see:
                self.state = "CHASE"
        
        elif self.state == "CHASE":
            # Boids alg
            # ПОИСК СОСЕДЕЙ ДЛЯ СТАИ
            
            neighbors = []
            for other in self.game.npcs:
                if other is not self and other.alive:
                    dist = math.hypot(self.x - other.x, self.y - other.y)
                    if dist < 3.0:  # радиус стаи 3 клетки
                        neighbors.append(other)
            
            # --- СИЛА СТАИ (BOID FLOCKING) ---
            if self.flocking_enabled:
                flock_x, flock_y = self.get_flocking_force(neighbors, dt)
            else:
                flock_x, flock_y = 0, 0
            
            # --- ДВИЖЕНИЕ К ИГРОКУ ---
            to_player_x = self.game.player.x - self.x
            to_player_y = self.game.player.y - self.y
            player_dist = math.hypot(to_player_x, to_player_y)
            if player_dist > 0.01:
                to_player_x /= player_dist
                to_player_y /= player_dist
            
            # --- СУММИРУЕМ ВСЕ СИЛЫ ---
            move_x = (to_player_x * self.speed * dt) + (flock_x * self.speed * dt)
            move_y = (to_player_y * self.speed * dt) + (flock_y * self.speed * dt)
            
            # --- ОТТАЛКИВАНИЕ ОТ ДРУГИХ NPC (SEPARATION) ---
            for other in self.game.npcs:
                if other is not self and other.alive:
                    dist = math.hypot(self.x - other.x, self.y - other.y)
                    if dist < 0.8:
                        angle = math.atan2(self.y - other.y, self.x - other.x)
                        force = (0.8 - dist) * 0.5
                        move_x += math.cos(angle) * force * dt * self.speed
                        move_y += math.sin(angle) * force * dt * self.speed
            
            self.try_move(move_x, move_y)
            
            if distance_to_player <= self.shoot_range and can_see:
                self.state = "ATTACK"
                
        elif self.state == "ATTACK":
            self.shoot()
            if distance_to_player > self.shoot_range or not can_see:
                self.state = "CHASE"
        
        
    # Algos Waypoint Auto Generation
    def generate_waypoints_auto(self, num_points=4):
        waypoints = []
        
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        
        for dx, dy in directions:
            for dist in range(2, 6):
                check_x = int(self.x) + dx * dist
                check_y = int(self.y) + dy * dist
                height_map = len(self.game.map.text_map)
                width_map = len(self.game.map.text_map[0])
                
                if (0 <= check_x < width_map and 0 <= check_y < height_map):  # размер твоей карты
                    if not self.game.map.is_wall(check_x, check_y):
                        # Добавляем точку с центром в клетке
                        waypoints.append((check_x + 0.5, check_y + 0.5))
                        break  # нашли точку в этом направлении
        # Если точек меньше 2, добавляем случайные вокруг
        while len(waypoints) < num_points:
            rand_x = self.x + uniform(-3, 3)
            rand_y = self.y + uniform(-3, 3)
            if 1 < rand_x < 9 and 1 < rand_y < 17:
                if not self.game.map.is_wall(int(rand_x), int(rand_y)):
                    waypoints.append((rand_x, rand_y))
        
        self.waypoints = waypoints[:num_points]
    
    
    # Algos Boids Algorithm (Craig Reynolds, 1986)            
    def get_flocking_force(self, neighbors, dt):
        """Возвращает силу для выравнивания и слияния с соседями"""
        if not neighbors:
            return (0, 0)
        
        # ALIGNMENT — среднее направление соседей
        avg_dx = 0
        avg_dy = 0
        
        # COHESION — средняя позиция соседей
        avg_px = 0
        avg_py = 0
        
        for other in neighbors:
            # Направление движения соседа (вектор к игроку или патруля)
            if other.state == "CHASE":
                other_dx = other.game.player.x - other.x
                other_dy = other.game.player.y - other.y
            elif other.waypoints:
                tx, ty = other.waypoints[other.current_waypoint]
                other_dx = tx - other.x
                other_dy = ty - other.y
            else:
                other_dx = 0
                other_dy = 0
            
            # Нормализуем
            other_dist = math.hypot(other_dx, other_dy)
            if other_dist > 0.01:
                avg_dx += other_dx / other_dist
                avg_dy += other_dy / other_dist
            
            # Позиция для cohesion
            avg_px += other.x
            avg_py += other.y
        
        count = len(neighbors)
        avg_dx /= count
        avg_dy /= count
        avg_px /= count
        avg_py /= count
        
        # Alignment (сила 0.3)
        align_force_x = avg_dx * 0.3
        align_force_y = avg_dy * 0.3
        
        # Cohesion — двигаемся к центру стаи (сила 0.2)
        to_center_x = avg_px - self.x
        to_center_y = avg_py - self.y
        center_dist = math.hypot(to_center_x, to_center_y)
        if center_dist > 0.01:
            to_center_x /= center_dist
            to_center_y /= center_dist
        cohesion_force_x = to_center_x * 0.2
        cohesion_force_y = to_center_y * 0.2
        
        return (align_force_x + cohesion_force_x, align_force_y + cohesion_force_y)
    