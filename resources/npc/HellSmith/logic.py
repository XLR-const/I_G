import os
import math
import pygame
import types
from random import uniform, random

# Динамически извлекаем константы рейкастинга из игры
try:
    import setting
    SCREEN_DIST = getattr(setting, 'SCREEN_DIST', 800)
    HALF_HEIGHT = getattr(setting, 'HALF_HEIGHT', 384)
    NUM_RAYS = getattr(setting, 'NUM_RAYS', 120)
    SCALE = getattr(setting, 'SCALE', 8)
    HALF_NUM_RAYS = getattr(setting, 'HALF_NUM_RAYS', 60)
    DELTA_ANGLE = getattr(setting, 'DELTA_ANGLE', 0.008)
    HALF_FOV = getattr(setting, 'HALF_FOV', 0.52)
except:
    SCREEN_DIST, HALF_HEIGHT, NUM_RAYS, SCALE = 800, 384, 120, 8
    HALF_NUM_RAYS, DELTA_ANGLE, HALF_FOV = 60, 0.008, 0.52


class BossBallProjectile:
    """Огненный шар, который плавно летит, крутит анимацию и взрывается об стены"""
    def __init__(self, game, boss, x, y, angle, speed, frames, explosion_frames, damage, size_mult=0.4, anim_speed=60, explosion_sound=None):
        self.game = game
        self.boss = boss
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = speed
        self.frames = frames
        self.explosion_frames = explosion_frames
        self.explosion_sound = explosion_sound
        self.damage = damage
        self.size_mult = size_mult
        self.anim_speed = anim_speed

        self.current_frame = 0
        self.anim_timer = pygame.time.get_ticks()
        self.alive = True
        self.is_exploding = False

    def update(self):
        if not self.alive: return
        dt = self.game.delta_time
        if dt > 0.033: dt = 0.033

        if not self.is_exploding:
            self.x += math.cos(self.angle) * self.speed * dt
            self.y += math.sin(self.angle) * self.speed * dt

            if self.game.map.is_wall(int(self.x), int(self.y)):
                self.trigger_explosion()
                return

            if math.hypot(self.game.player.x - self.x, self.game.player.y - self.y) < 0.4:
                self.game.player.take_damage(self.damage)
                self.trigger_explosion()
                return

        now = pygame.time.get_ticks()
        if now - self.anim_timer > self.anim_speed:
            self.anim_timer = now
            self.current_frame += 1
            if self.is_exploding:
                if self.current_frame >= len(self.explosion_frames):
                    self.alive = False
            else:
                self.current_frame %= len(self.frames)

    def trigger_explosion(self):
        sound_to_play = self.explosion_sound if self.explosion_sound else getattr(self.boss, 'sound_explosion', None)
        if self.explosion_frames:
            self.is_exploding = True
            self.speed = 0
            self.current_frame = 0
            if sound_to_play: sound_to_play.play()
        else:
            self.alive = False
            if sound_to_play: sound_to_play.play()

    def draw(self):
        if not self.alive or not self.frames: return
        current_deck = self.explosion_frames if self.is_exploding else self.frames
        if not current_deck or self.current_frame >= len(current_deck): return

        img = current_deck[self.current_frame]
        raw_w, raw_h = img.get_size()

        dx, dy = self.x - self.game.player.x, self.y - self.game.player.y
        dist = math.hypot(dx, dy)
        if dist < 0.2: return

        theta = math.atan2(dy, dx)
        delta = theta - self.game.player.angle
        delta = (delta + math.pi) % math.tau - math.pi
        if abs(delta) > HALF_FOV: return

        dist_flat = dist * math.cos(delta)
        if dist_flat < 0.2: return

        current_size = 0.6 if self.is_exploding else self.size_mult
        proj_height = int((SCREEN_DIST / dist_flat) * current_size)
        proj_width = int(proj_height * (raw_w / raw_h))

        center_x = (HALF_NUM_RAYS + delta / DELTA_ANGLE) * SCALE
        start_x = int(center_x - proj_width // 2)
        texture_step = raw_w / proj_width if proj_width > 0 else 1.0

        for x in range(start_x, start_x + proj_width, SCALE):
            ray_idx = int(x // SCALE)
            if 0 <= ray_idx < NUM_RAYS and dist_flat < self.game.raycasting.z_buffer[ray_idx]:
                sub_x = int(x - start_x)
                if 0 <= sub_x < proj_width:
                    tex_x = int(sub_x * texture_step)
                    if 0 <= tex_x < raw_w:
                        screen_y = HALF_HEIGHT + proj_height // 2 - proj_height
                        slice_surf = img.subsurface(tex_x, 0, 1, raw_h)
                        scaled_slice = pygame.transform.scale(slice_surf, (SCALE, proj_height))
                        self.game.screen.blit(scaled_slice, (x, screen_y))


class HighMortarRocket:
    """Изолированный класс для навесной ракеты из пушки руки (HAND)"""
    def __init__(self, game, boss, start_x, start_y, target_dist, angle, frames, explosion_frames, fire_frames, damage, explosion_sound=None):
        self.game = game
        self.boss = boss
        self.x = start_x
        self.y = start_y
        self.start_x = start_x
        self.start_y = start_y
        self.angle = angle
        
        self.speed = 6.0           
        self.frames = frames       
        self.explosion_frames = explosion_frames
        self.fire_frames = fire_frames
        self.damage = damage
        self.explosion_sound = explosion_sound  
        
        self.target_dist = target_dist if target_dist > 0.5 else 3.0
        self.z = 0.0               
        self.current_frame = 0
        self.alive = True
        self.in_air = True        
        
        self.flight_start_time = pygame.time.get_ticks()
        self.total_flight_duration = max(300, min(1500, int(self.target_dist * 150))) 
        self.anim_timer = pygame.time.get_ticks()

    def update(self):
        if not self.alive: return
        dt = self.game.delta_time
        if dt > 0.033: dt = 0.033
        now = pygame.time.get_ticks()

        if getattr(self, 'in_air', True):
            self.x += math.cos(self.angle) * self.speed * dt
            self.y += math.sin(self.angle) * self.speed * dt

            current_dist_travelled = math.hypot(self.x - self.start_x, self.y - self.start_y)
            progress = current_dist_travelled / self.target_dist if self.target_dist > 0 else 1.0

            if now - self.flight_start_time > 2000:
                progress = 1.0

            if progress >= 1.0 or self.game.map.is_wall(int(self.x), int(self.y)):
                self.in_air = False
                self.speed = 0
                self.z = 0.0
                self.current_frame = 0
                self.anim_timer = pygame.time.get_ticks()
                self.land_x = self.x
                self.land_y = self.y
                print(f"[Ракета] Приземлилась в ({self.land_x:.2f}, {self.land_y:.2f})")
            else:
                self.z = math.sin(progress * math.pi) * 1.5
                self.current_frame = 0
            return

        if now - self.anim_timer > 120:
            self.anim_timer = now
            self.current_frame += 1
            if self.current_frame >= len(self.frames):
                self.trigger_detonation()

    def trigger_detonation(self):
        self.alive = False
        lx = getattr(self, 'land_x', self.x)
        ly = getattr(self, 'land_y', self.y)

        sound_to_play = self.explosion_sound if self.explosion_sound else getattr(self.boss, 'sound_explosion', None)
        if sound_to_play: sound_to_play.play()

        dist_to_player = math.hypot(self.game.player.x - lx, self.game.player.y - ly)
        if dist_to_player <= 1.2:
            self.game.player.take_damage(self.damage)

        if self.explosion_frames:
            expl = BossBallProjectile(self.game, self.boss, lx, ly, angle=0, speed=0, frames=self.explosion_frames, explosion_frames=[], damage=0, size_mult=0.6, anim_speed=60)
            def custom_expl_update(self_expl):
                now_ex = pygame.time.get_ticks()
                if now_ex - self_expl.anim_timer > self_expl.anim_speed:
                    self_expl.anim_timer = now_ex
                    self_expl.current_frame += 1
                    if self_expl.current_frame >= len(self_expl.frames):
                        self_expl.alive = False
            expl.update = types.MethodType(custom_expl_update, expl)
            self.boss.boss_projectiles.append(expl)

        if self.fire_frames:
            fire_wave = GroundFireWave(self.game, self.boss, lx, ly, self.fire_frames, damage=4)
            self.boss.boss_projectiles.append(fire_wave)

    def draw(self):
        if not self.alive or not self.frames or self.current_frame >= len(self.frames): return
        
        img = self.frames[self.current_frame]
        raw_w, raw_h = img.get_size()
        dx, dy = self.x - self.game.player.x, self.y - self.game.player.y
        dist = math.hypot(dx, dy)
        if dist < 0.2: return

        theta = math.atan2(dy, dx)
        delta = theta - self.game.player.angle
        delta = (delta + math.pi) % math.tau - math.pi
        if abs(delta) > HALF_FOV: return
        dist_flat = dist * math.cos(delta)
        if dist_flat < 0.2: return

        proj_height = int((SCREEN_DIST / dist_flat) * 0.11) 
        proj_width = int(int(proj_height * (raw_w / raw_h)) * 0.7)

        center_x = (HALF_NUM_RAYS + delta / DELTA_ANGLE) * SCALE
        start_x = int(center_x - proj_width // 2)
        texture_step = raw_w / proj_width if proj_width > 0 else 1.0

        z_offset = int((self.z * SCREEN_DIST) / dist_flat) if dist_flat > 0 else 0

        for x in range(start_x, start_x + proj_width, SCALE):
            ray_idx = int(x // SCALE)
            if 0 <= ray_idx < NUM_RAYS and dist_flat < self.game.raycasting.z_buffer[ray_idx]:
                sub_x = int(x - start_x)
                if 0 <= sub_x < proj_width:
                    tex_x = int(sub_x * texture_step)
                    if 0 <= tex_x < raw_w:
                        screen_y = HALF_HEIGHT + (proj_height // 2) - z_offset
                        slice_surf = img.subsurface(tex_x, 0, 1, raw_h)
                        scaled_slice = pygame.transform.scale(slice_surf, (SCALE, proj_height))
                        self.game.screen.blit(scaled_slice, (x, screen_y))

class GroundFireWave:
    """Полностью независимый класс огненной лужи: лежит строго на полу и наносит тикающий урон"""
    def __init__(self, game, boss, x, y, frames, damage):
        self.game = game
        self.boss = boss
        self.fixed_x = x  
        self.fixed_y = y  
        self.frames = frames
        self.damage = damage
        self.size_mult = 0.8
        self.anim_speed = 80
        
        self.current_frame = 0
        self.anim_timer = pygame.time.get_ticks()
        self.alive = True
        self.z = 0.0

    def update(self):
        if not self.alive: return
        
        dist_to_player = math.hypot(self.game.player.x - self.fixed_x, self.game.player.y - self.fixed_y)
        if dist_to_player <= 2.0:
            if self.current_frame % 3 == 0:
                self.game.player.take_damage(self.damage)

        now = pygame.time.get_ticks()
        if now - self.anim_timer > self.anim_speed:
            self.anim_timer = now
            self.current_frame += 1
            if self.current_frame >= len(self.frames):
                self.alive = False

    def draw(self):
        if not self.alive or not self.frames or self.current_frame >= len(self.frames): return
        
        img = self.frames[self.current_frame]
        raw_w, raw_h = img.get_size()
        
        dx, dy = self.fixed_x - self.game.player.x, self.fixed_y - self.game.player.y
        dist = math.hypot(dx, dy)
        if dist < 0.2: return

        theta = math.atan2(dy, dx)
        delta = theta - self.game.player.angle
        delta = (delta + math.pi) % math.tau - math.pi
        if abs(delta) > HALF_FOV: return
        
        dist_flat = dist * math.cos(delta)
        if dist_flat < 0.2: return

        proj_height = int((SCREEN_DIST / dist_flat) * self.size_mult) 
        proj_width = int(proj_height * (raw_w / raw_h))
        center_x = (HALF_NUM_RAYS + delta / DELTA_ANGLE) * SCALE
        start_x = int(center_x - proj_width // 2)
        texture_step = raw_w / proj_width if proj_width > 0 else 1.0

        for x in range(start_x, start_x + proj_width, SCALE):
            ray_idx = int(x // SCALE)
            if 0 <= ray_idx < NUM_RAYS and dist_flat < self.game.raycasting.z_buffer[ray_idx]:
                sub_x = int(x - start_x)
                if 0 <= sub_x < proj_width:
                    tex_x = int(sub_x * texture_step)
                    if 0 <= tex_x < raw_w:
                        # 🔥 ФИКС: Отрезаем высоту, чтобы спрайт костра стоял подошвой на полу
                        screen_y = HALF_HEIGHT + proj_height // 2 - proj_height
                        
                        slice_surf = img.subsurface(tex_x, 0, 1, raw_h)
                        scaled_slice = pygame.transform.scale(slice_surf, (SCALE, proj_height))
                        self.game.screen.blit(scaled_slice, (x, screen_y))

def boss_personal_animator_update(self_animator):
    npc = self_animator.npc
    if npc.state == "DEAD":
        self_animator.base_animator_update_func()
        return

    if npc.boss_internal_state in ("MELEE_ATTACK", "HAND_ATTACK", "SHOULDER_ATTACK"):
        prefix = "shoulder" if npc.boss_internal_state == "SHOULDER_ATTACK" else "hand"
        key = f"attack_{prefix}_front_{npc.boss_attack_frame}"
        self_animator.current_image = self_animator.sprites.get(key, npc.image)
        return

    self_animator.base_animator_update_func()


def boss_total_isolated_update(self):
    dt = self.game.delta_time
    if dt > 0.033: dt = 0.033
    now = pygame.time.get_ticks()

    self.boss_projectiles = [p for p in self.boss_projectiles if p.alive]
    for proj in self.boss_projectiles:
        proj.update()

    if not self.alive or self.hp <= 0:
        self.state = "DEAD"
        self.animator.update()
        self.image = self.animator.current_image
        if self.image:
            self.sprite_width, self.sprite_height = self.image.get_size()
            self.sprite_ratio = self.sprite_width / self.sprite_height
        return

    dist_to_player = math.hypot(self.game.player.x - self.x, self.game.player.y - self.y)
    if dist_to_player > self.activation_distance: return

    if self.hurt_flash > 0: self.hurt_flash -= 1
    if self.shoot_flash > 0: self.shoot_flash -= 1

    if self.boss_internal_state == "CHASE" and hasattr(self, 'sound_idle_growl') and self.sound_idle_growl:
        if now > self.boss_growl_timer:
            self.boss_growl_timer = now + uniform(5000, 9000)
            self.sound_idle_growl.play()

    can_see = self.has_line_of_sight()
    if can_see and dist_to_player <= self.view_distance:
        if hasattr(self, 'sound_sight_phrase') and self.sound_sight_phrase and not self.boss_said_sight_phrase:
            self.boss_said_sight_phrase = True
            self.sound_sight_phrase.play()

    if self.boss_internal_state in ("HAND_ATTACK", "SHOULDER_ATTACK"):
        self.animator._calculate_direction()
        self.move_direction = self.animator.move_direction

        if now - self.boss_attack_timer > 150:
            self.boss_attack_timer = now
            self.boss_attack_frame += 1

            if self.boss_internal_state == "SHOULDER_ATTACK" and self.boss_attack_frame == 3:
                vortex_frames = getattr(self, 'boss_fireball_frames', [])
                if vortex_frames:
                    ball = BossBallProjectile(
                        self.game, self, self.x, self.y, 
                        math.atan2(self.game.player.y - self.y, self.game.player.x - self.x), 
                        speed=4.5, frames=vortex_frames, 
                        explosion_frames=getattr(self, 'boss_explosion_frames', []), damage=25
                    )
                    self.boss_projectiles.append(ball)

                        # Атака: Средний бой (HAND, вылет ПЯТИ параболических ракет веером на 2-м кадре)
            elif self.boss_internal_state == "HAND_ATTACK" and self.boss_attack_frame == 2:
                rocket_frames = getattr(self, 'boss_rocket_frames', [])
                if rocket_frames:
                    base_angle = math.atan2(self.game.player.y - self.y, self.game.player.x - self.x)
                    
                    # 🔥 ЗАПУСКАЕМ ВЕЕРНЫЙ ЗАЛП ИЗ 5 РАКЕТ ПО ОБЛАСТИ
                    for _ in range(5):
                        # Добавляем случайный разброс угла вылета (примерно +-15 градусов в радианах)
                        random_angle_offset = uniform(-0.25, 0.22)
                        final_angle = base_angle + random_angle_offset
                        
                        # Добавляем случайный разброс дистанции приземления (в радиусе +-1.5 клеток от ГГ)
                        # max(1.0, ...) защищает от падения ракеты прямо внутрь хитбокса самого Босса
                        random_dist_offset = uniform(-1.5, 1.5)
                        final_target_dist = max(1.0, dist_to_player + random_dist_offset)
                        
                        ball = HighMortarRocket(
                            game=self.game, 
                            boss=self, 
                            start_x=self.x, 
                            start_y=self.y,
                            target_dist=final_target_dist, 
                            angle=final_angle, 
                            frames=rocket_frames,
                            explosion_frames=getattr(self, 'boss_mini_explosion_frames', []),
                            fire_frames=getattr(self, 'boss_ground_fire_frames', []), 
                            damage=15, # Снизили разовый урон до 15, так как ракет летит много
                            explosion_sound=getattr(self, 'sound_explosion', None)
                        )
                        self.boss_projectiles.append(ball)


            max_f = 4 if self.boss_internal_state == "SHOULDER_ATTACK" else 3
            if self.boss_attack_frame > max_f:
                self.last_shot = now  
                self.boss_internal_state = "CHASE"
                self.state = "CHASE"

        self.animator.update()
        self.image = self.animator.current_image

    else:
        if can_see and dist_to_player <= self.shoot_range and (now - self.last_shot >= self.shoot_delay):
            self.boss_attack_timer = now
            self.boss_attack_frame = 1
            if dist_to_player <= 3.0:
                self.boss_internal_state = "HAND_ATTACK"
                self.state = "ATTACK"
                if hasattr(self, 'sound_hand') and self.sound_hand: self.sound_hand.play()
            else:
                if random() < 0.5:
                    self.boss_internal_state = "HAND_ATTACK"
                    self.state = "ATTACK"
                    if hasattr(self, 'sound_hand') and self.sound_hand: self.sound_hand.play()
                else:
                    self.boss_internal_state = "SHOULDER_ATTACK"
                    self.state = "ATTACK"
                    if hasattr(self, 'sound_shoulder') and self.sound_shoulder: self.sound_shoulder.play()
        else:
            self.update_state(dt)
            self.animator.update()
            self.image = self.animator.current_image
            self.move_direction = self.animator.move_direction

    if self.image:
        self.sprite_width, self.sprite_height = self.image.get_size()
        self.sprite_ratio = self.sprite_width / self.sprite_height


def boss_custom_draw(self):
    self.base_draw_method()
    for proj in self.boss_projectiles:
        proj.draw()


def init_logic(npc):
    """Главная точка входа. Намертво изолирует ИИ и Аниматор Босса от базового ядра"""
    npc.boss_projectiles = []
    npc.boss_fireball_frames = []
    npc.boss_rocket_frames = []
    npc.boss_explosion_frames = []

    npc.boss_internal_state = "CHASE"
    npc.boss_attack_frame = 1
    npc.boss_attack_timer = 0

    scale = npc.scale

    def load_local_frames(prefix, count):
        frames = []
        for idx in range(1, count + 1):
            filename = f"{prefix}_{idx}.png"
            path = os.path.join(npc.folder_path, filename)
            if os.path.exists(path):
                original = pygame.image.load(path)
                new_w = int(original.get_width() * scale)
                new_h = int(original.get_height() * scale)
                frames.append(pygame.transform.scale(original, (new_w, new_h)))
        return frames

    npc.boss_fireball_frames = load_local_frames("proj_vortex", 9)
    npc.boss_rocket_frames = load_local_frames("proj_rocket", 16)
    npc.boss_explosion_frames = load_local_frames("fx_big_explosion", 5)

    print(f"\n[УСПЕХ] Начинаем тотальную изолированную загрузку спрайтов атак Босса...")
    
    for f in range(1, 4):
        key = f"attack_hand_front_{f}"
        filename = f"{npc.name}_attack_hand_front_{f}.png"
        path = os.path.join(npc.folder_path, filename)
        if os.path.exists(path):
            original = pygame.image.load(path)
            new_w, new_h = int(original.get_width() * scale), int(original.get_height() * scale)
            npc.animator.sprites[key] = pygame.transform.scale(original, (new_w, new_h))
        else:
            npc.animator.sprites[key] = npc.animator.sprites.get("move_front_1")

    for f in range(1, 5):
        key = f"attack_shoulder_front_{f}"
        filename = f"{npc.name}_attack_shoulder_front_{f}.png"
        path = os.path.join(npc.folder_path, filename)
        if os.path.exists(path):
            original = pygame.image.load(path)
            new_w, new_h = int(original.get_width() * scale), int(original.get_height() * scale)
            npc.animator.sprites[key] = pygame.transform.scale(original, (new_w, new_h))
        else:
            npc.animator.sprites[key] = npc.animator.sprites.get("move_front_1")

    try:
        npc.sound_shoulder = pygame.mixer.Sound(os.path.join(npc.folder_path, 'sound_shoulder.wav'))
        npc.sound_hand = pygame.mixer.Sound(os.path.join(npc.folder_path, 'sound_hand.wav'))
        npc.sound_explosion = pygame.mixer.Sound(os.path.join(npc.folder_path, 'sound_explosion.wav'))
        npc.sound_idle_growl = pygame.mixer.Sound(os.path.join(npc.folder_path, 'sound_idle_growl.wav'))
        npc.sound_sight_phrase = pygame.mixer.Sound(os.path.join(npc.folder_path, 'sound_sight_phrase.wav'))

        vol = 0.45
        for s in [npc.sound_shoulder, npc.sound_hand, npc.sound_explosion, npc.sound_idle_growl]:
            if s: s.set_volume(vol)
        if npc.sound_sight_phrase: npc.sound_sight_phrase.set_volume(vol * 1.3)
    except Exception as e:
        npc.sound_shoulder = npc.shoot_sound
        npc.sound_hand = npc.shoot_sound
        npc.sound_explosion = npc.shoot_sound
        npc.sound_idle_growl = None
        npc.sound_sight_phrase = None

    npc.boss_growl_timer = pygame.time.get_ticks() + uniform(2000, 6000)
    npc.boss_said_sight_phrase = False

    npc.base_draw_method = types.MethodType(npc.draw.__func__, npc)
    npc.draw = types.MethodType(boss_custom_draw, npc)
    npc.update = types.MethodType(boss_total_isolated_update, npc)

    npc.animator.base_animator_update_func = types.MethodType(npc.animator.update.__func__, npc.animator)
    npc.animator.update = types.MethodType(boss_personal_animator_update, npc.animator)

    # 🔥 НАШИ ИСПРАВЛЕННЫЕ ОТСТУПЫ: Эффекты теперь железно загружаются в сущность npc
    npc.boss_mini_explosion_frames = load_local_frames("fx_mini_explosion", 7)
    npc.boss_explosion_frames = load_local_frames("fx_big_explosion", 5) 
    npc.boss_ground_fire_frames = load_local_frames("fx_ground_fire", 23)

    print(f"[УСПЕХ БОССА] Личный независимый Аниматор, ИИ HellSmith и спецэффекты полностью запущены.")
