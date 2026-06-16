import pygame
import math
from random import uniform
from setting import *
from config.game_data import NPC_CONFIG
from core.particle import Particle

class NPC:
    def __init__(self, game, npc_type, pos=(8.5, 7.5)):
        self.game = game
        self.npc_type = npc_type
        
        # Читаем параметры из конфига
        config = NPC_CONFIG.get(npc_type, {})
        self.name = config.get('name', 'unknown')
        self.speed = config.get('speed', 0.3)
        self.radius = config.get('radius', 0.35)
        self.size = 0.3
        self.hp = config.get('hp', 100)
        self.damage = config.get('damage', 10)
        self.shoot_range = config.get('shoot_range', 5.0)
        self.shoot_delay = config.get('shoot_delay', 800)
        
        self.x, self.y = pos
        self.alive = True
        self.active = True
        self.activation_distance = 15
        
        self.state = "IDLE"
        self.state_timer = 0
        
        self.last_shot = 0
        self.shoot_flash = 0
        
        sound_path = config.get('sound', 'resources/npc/npc_rifle.wav')
        sound_volume = config.get('sound_volume', 0.2)
        self.shoot_sound = pygame.mixer.Sound(sound_path)
        self.shoot_sound.set_volume(sound_volume)
        
        self.waypoints = []
        self.current_waypoint = 0
        self.idle_duration = 500
        
        self.hurt_flash = 0
        
        self.image = None
        self.sprite_width = 0
        self.sprite_height = 0
        self.sprite_ratio = 0
        self.move_direction = "front"
        self.last_x = self.x
        self.last_y = self.y
        self.sprites = {}
        
        self.load_all_sprites()
        
        self.path = []
        self.last_path_update = 0
        self.current_target_index = 0
        
        self._last_los_check = 0
        self._cached_los = True

    def load_all_sprites(self):
        base = f"resources/npc/{self.name}/{self.name}"
        directions = ["right", "left", "front", "back"]
        scale_factor = 0.1
        
        for direction in directions:
            key = f"IDLE_{direction}"
            path = f"{base}_idle_{direction}.png"
            try:
                original = pygame.image.load(path).convert_alpha()
                new_w = int(original.get_width() * scale_factor)
                new_h = int(original.get_height() * scale_factor)
                self.sprites[key] = pygame.transform.scale(original, (new_w, new_h))
            except:
                self.sprites[key] = pygame.Surface((50, 80))
                self.sprites[key].fill((150, 150, 150))
        
        for direction in directions:
            key = f"MOVE_{direction}"
            path = f"{base}_move_{direction}.png"
            try:
                original = pygame.image.load(path).convert_alpha()
                new_w = int(original.get_width() * scale_factor)
                new_h = int(original.get_height() * scale_factor)
                self.sprites[key] = pygame.transform.scale(original, (new_w, new_h))
            except:
                self.sprites[key] = self.sprites.get(f"IDLE_{direction}")
        
        try:
            original = pygame.image.load(f"{base}_shoot.png").convert_alpha()
            new_w = int(original.get_width() * scale_factor)
            new_h = int(original.get_height() * scale_factor)
            self.sprites["ATTACK"] = pygame.transform.scale(original, (new_w, new_h))
        except:
            self.sprites["ATTACK"] = pygame.Surface((50, 80))
            self.sprites["ATTACK"].fill((255, 200, 0))
        
        self.image = self.sprites.get("IDLE_front")
        self.sprite_width, self.sprite_height = self.image.get_size()
        self.sprite_ratio = self.sprite_width / self.sprite_height

    def get_damage(self, damage):
        if not self.alive:
            return
        self.hp -= damage
        self.hurt_flash = 8
        self.state = "HURT"
        self.state_timer = pygame.time.get_ticks() + 300
        if self.hp <= 0:
            self.alive = False
            self.game.total_kills += 1
            for _ in range(20):
                self.game.particles.append(Particle(
                    self.game,
                    (self.x + uniform(-0.2, 0.2), self.y + uniform(-0.2, 0.2)),
                    (150, 0, 0),
                    uniform(0.002, 0.006)
                ))

    def update(self):
        if not self.alive:
            return
        
        dx = self.game.player.x - self.x
        dy = self.game.player.y - self.y
        dist = math.hypot(dx, dy)
        
        if dist > self.activation_distance:
            return
        
        dt = self.game.delta_time
        if dt > 0.033:
            dt = 0.033
        
        if self.hurt_flash > 0:
            self.hurt_flash -= 1
        if self.shoot_flash > 0:
            self.shoot_flash -= 1
        
        self.update_state(dt)
        
        dx_move = self.x - self.last_x
        dy_move = self.y - self.last_y
        if dx_move != 0 or dy_move != 0:
            if abs(dx_move) > abs(dy_move):
                self.move_direction = "right" if dx_move < 0 else "left"
            else:
                self.move_direction = "front" if dy_move < 0 else "back"
        
        self.last_x = self.x
        self.last_y = self.y
        
        if self.state == "ATTACK":
            self.image = self.sprites.get("ATTACK", self.sprites.get("IDLE_front"))
        elif self.state in ("PATROL", "CHASE"):
            key = f"MOVE_{self.move_direction}"
            self.image = self.sprites.get(key, self.sprites.get("IDLE_front"))
        else:
            key = f"IDLE_{self.move_direction}"
            self.image = self.sprites.get(key, self.sprites.get("IDLE_front"))
        
        self.sprite_width, self.sprite_height = self.image.get_size()
        self.sprite_ratio = self.sprite_width / self.sprite_height

    def has_line_of_sight(self):
        now = pygame.time.get_ticks()
        if now - self._last_los_check < 150:
            return self._cached_los
        self._last_los_check = now
        
        x1, y1 = int(self.x), int(self.y)
        x2, y2 = int(self.game.player.x), int(self.game.player.y)
        
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        
        x, y = x1, y1
        while (x, y) != (x2, y2):
            if self.game.map.is_wall(x, y):
                self._cached_los = False
                return False
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy
        
        self._cached_los = True
        return True

    def try_move(self, dx, dy):
        if not self.alive:
            return
        new_x = self.x + dx
        new_y = self.y + dy
        
        for offset_x, offset_y in [(-self.radius, self.radius), (self.radius, self.radius),
                                   (-self.radius, -self.radius), (self.radius, -self.radius)]:
            if self.game.map.is_wall(int(new_x + offset_x), int(self.y + offset_y)):
                new_x = self.x
            if self.game.map.is_wall(int(self.x + offset_x), int(new_y + offset_y)):
                new_y = self.y
        
        self.x = new_x
        self.y = new_y

    def shoot(self):
        now = pygame.time.get_ticks()
        if now - self.last_shot >= self.shoot_delay:
            self.last_shot = now
            self.shoot_flash = 12
            self.shoot_sound.play()
            self.game.player.take_damage(self.damage)
            for _ in range(8):
                self.game.particles.append(Particle(
                    self.game,
                    (self.x + uniform(-0.1, 0.1), self.y + uniform(-0.1, 0.1)),
                    (255, 200, 50),
                    uniform(0.003, 0.005)
                ))

    def generate_waypoints_auto(self, num_points=4):
        waypoints = []
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        
        for dx, dy in directions:
            for dist in range(2, 6):
                check_x = int(self.x) + dx * dist
                check_y = int(self.y) + dy * dist
                if (0 <= check_x < self.game.level_manager.map.width and 0 <= check_y < self.game.level_manager.map.height):
                    if not self.game.map.is_wall(check_x, check_y):
                        waypoints.append((check_x + 0.5, check_y + 0.5))
                        break
        
        max_attempts = 100
        attempts = 0
        while len(waypoints) < num_points and attempts < max_attempts:
            attempts += 1
            rand_x = self.x + uniform(-3, 3)
            rand_y = self.y + uniform(-3, 3)
            if 1 < rand_x < self.game.map.width - 1 and 1 < rand_y < self.game.map.height - 1:
                if not self.game.map.is_wall(int(rand_x), int(rand_y)):
                    waypoints.append((rand_x, rand_y))
        
        self.waypoints = waypoints[:num_points]

    def update_state(self, dt):
        if self.hp <= 0:
            if self.state != "DEAD":
                self.state = "DEAD"
                self.alive = False
            return
        
        dist_to_player = math.hypot(self.x - self.game.player.x, self.y - self.game.player.y)
        can_see = self.has_line_of_sight()
        
        if self.state == "HURT":
            if pygame.time.get_ticks() > self.state_timer:
                if can_see:
                    self.state = "CHASE"
                else:
                    self.state = "PATROL" if self.waypoints else "IDLE"
            return
        
        if can_see:
            if dist_to_player <= self.shoot_range:
                if self.state != "ATTACK":
                    self.state = "ATTACK"
            else:
                if self.state != "CHASE":
                    self.state = "CHASE"
        else:
            if self.state in ("ATTACK", "CHASE"):
                if self.waypoints:
                    self.state = "PATROL"
                    self.current_waypoint = 0
                else:
                    self.state = "IDLE"
                    self.state_timer = pygame.time.get_ticks() + self.idle_duration
        
        if self.state == "IDLE":
            if self.state_timer and pygame.time.get_ticks() > self.state_timer:
                if self.waypoints:
                    self.state = "PATROL"
                    self.current_waypoint = 0
        
        elif self.state == "PATROL":
            if not self.waypoints:
                self.state = "IDLE"
                return
            target_x, target_y = self.waypoints[self.current_waypoint]
            dx = target_x - self.x
            dy = target_y - self.y
            dist = math.hypot(dx, dy)
            if dist < 0.2:
                self.current_waypoint = (self.current_waypoint + 1) % len(self.waypoints)
            else:
                if dist > 0.01:
                    move_x = (dx / dist) * self.speed * dt
                    move_y = (dy / dist) * self.speed * dt
                    self.try_move(move_x, move_y)
        
        elif self.state == "CHASE":
            now = pygame.time.get_ticks()
            if now - self.last_path_update >= 200:
                self.last_path_update = now
                path = self.game.pathfinder.a_star((self.x, self.y), (self.game.player.x, self.game.player.y))
                if path:
                    self.path = [(x + 0.5, y + 0.5) for x, y in path]
                    self.current_target_index = 0
            
            if self.path and self.current_target_index < len(self.path):
                target_x, target_y = self.path[self.current_target_index]
                dx = target_x - self.x
                dy = target_y - self.y
                dist = math.hypot(dx, dy)
                if dist < 0.6:
                    self.current_target_index += 1
                else:
                    move_x = (dx / dist) * self.speed * dt
                    move_y = (dy / dist) * self.speed * dt
                    self.try_move(move_x, move_y)
            else:
                dx = self.game.player.x - self.x
                dy = self.game.player.y - self.y
                dist = math.hypot(dx, dy)
                if dist > 0.01:
                    move_x = (dx / dist) * self.speed * dt
                    move_y = (dy / dist) * self.speed * dt
                    self.try_move(move_x, move_y)
            
            if dist_to_player <= self.shoot_range and self.has_line_of_sight():
                self.state = "ATTACK"
        
        elif self.state == "ATTACK":
            if self.has_line_of_sight():
                self.shoot()
            if dist_to_player > self.shoot_range or not self.has_line_of_sight():
                self.state = "CHASE"

    def draw(self):
        if not self.alive:
            return
        
        dx = self.x - self.game.player.x
        dy = self.y - self.game.player.y
        dist = math.hypot(dx, dy)
        
        if dist < 0.2:
            return
        
        theta = math.atan2(dy, dx)
        delta = theta - self.game.player.angle
        delta = (delta + math.pi) % math.tau - math.pi
        
        if abs(delta) > HALF_FOV:
            return
        
        dist_flat = dist * math.cos(delta)
        if dist_flat < 0.2:
            return
        
        proj_height = int(SCREEN_DIST / dist_flat)
        proj_width = int(proj_height * self.sprite_ratio)
        
        if proj_height > HEIGHT * 2:
            proj_height = HEIGHT * 2
            proj_width = int(proj_height * self.sprite_ratio)
        
        center_x = (HALF_NUM_RAYS + delta / DELTA_ANGLE) * SCALE
        
        if self.hurt_flash > 0:
            img = self.image.copy()
            red_surface = pygame.Surface(img.get_size())
            red_surface.fill((255, 0, 0))
            img.blit(red_surface, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        else:
            img = self.image
        
        if self.shoot_flash > 0:
            flash_surface = pygame.Surface((proj_width, proj_height), pygame.SRCALPHA)
            intensity = min(255, self.shoot_flash * 40)
            center_flash_x = proj_width // 2
            center_flash_y = proj_height // 2
            radius = min(proj_width, proj_height) // 2
            pygame.draw.circle(flash_surface, (255, 200, 50, intensity), 
                             (center_flash_x, center_flash_y), radius)
            img.blit(flash_surface, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        
        img = pygame.transform.scale(img, (proj_width, proj_height))
        
        start_x = int(center_x - proj_width // 2)
        for x in range(start_x, start_x + proj_width, SCALE):
            ray_idx = int(x // SCALE)
            if 0 <= ray_idx < NUM_RAYS:
                if dist_flat < self.game.raycasting.z_buffer[ray_idx]:
                    sub_x = int((x - start_x))
                    if 0 <= sub_x < proj_width:
                        self.game.screen.blit(img, (x, HALF_HEIGHT - proj_height // 2), 
                                             (sub_x, 0, SCALE, proj_height))


class Solder(NPC):
    def __init__(self, game, pos=(8.5, 7.5)):
        super().__init__(game, '2', pos)


class Kamikaze(NPC):
    def __init__(self, game, pos=(8.5, 7.5)):
        super().__init__(game, '3', pos)

    def shoot(self):
        """Взрыв вместо выстрела"""
        if not self.alive:
            return
        
        now = pygame.time.get_ticks()
        if now - self.last_shot >= self.shoot_delay:
            self.last_shot = now
            self.shoot_flash = 12
            self.shoot_sound.play()
            self.game.player.take_damage(self.damage)
            
            for _ in range(30):
                self.game.particles.append(Particle(
                    self.game,
                    (self.x + uniform(-0.3, 0.3), self.y + uniform(-0.3, 0.3)),
                    (255, 100, 0),
                    uniform(0.005, 0.02)
                ))
            
            self.alive = False


class Jaggernaut(NPC):
    def __init__(self, game, pos=(8.5, 7.5)):
        super().__init__(game, '4', pos)


class Lightning(NPC):
    def __init__(self, game, pos=(8.5, 7.5)):
        super().__init__(game, '5', pos)


class Boss(NPC):
    def __init__(self, game, pos=(8.5, 7.5)):
        super().__init__(game, '6', pos)