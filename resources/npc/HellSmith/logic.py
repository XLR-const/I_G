import os
import math
import pygame
import types
from random import uniform
from core.particle import Particle

# Подтягиваем настройки проекции из ядра игры
from setting import SCREEN_DIST, HALF_HEIGHT, NUM_RAYS, SCALE, HALF_NUM_RAYS, FOV, HALF_FOV, DELTA_ANGLE, HEIGHT


# ==============================================================================
# 1. СИСТЕМА ПРОЕКЦИИ СНАРЯДОВ С ЧЕСТНЫМ УРОНОМ
# ==============================================================================

class BossProjectile:
    """Виртуальный 3D-спрайт эффекта/снаряда, привязанный к Z-буферу стен"""
    def __init__(self, game, x, y, angle, speed, frames, anim_speed, damage=0):
        self.game = game
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = speed
        self.frames = frames
        self.anim_speed = anim_speed
        self.damage = damage
        self.current_frame = 0
        self.anim_timer = pygame.time.get_ticks()
        self.alive = True

    def update(self, dt):
        if not self.alive:
            return

        # Движение снаряда вперед
        if self.speed > 0:
            self.x += math.cos(self.angle) * self.speed * dt
            self.y += math.sin(self.angle) * self.speed * dt

            # Если влетели в стену — уничтожаем снаряд
            if self.game.map.is_wall(int(self.x), int(self.y)):
                self.on_collision()
                return

        # Крутим кадры анимации эффекта
        now = pygame.time.get_ticks()
        if now - self.anim_timer > self.anim_speed:
            self.anim_timer = now
            self.current_frame += 1
            if self.current_frame >= len(self.frames):
                self.on_animation_end()

    def on_collision(self):
        self.alive = False

    def on_animation_end(self):
        self.current_frame = 0  # По умолчанию зациклено

    def draw(self):
        """Рендеринг снаряда вертикальными полосами со сверкой Z-буфера стен"""
        if not self.alive or not self.frames or self.current_frame >= len(self.frames):
            return

        img = self.frames[self.current_frame]
        raw_w, raw_h = img.get_size()

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

        # Проецируем биллборд на основе скейла Босса HellSmith (1.35)
        proj_height = int((SCREEN_DIST / dist_flat) * 1.35)
        proj_width = int(proj_height * (raw_w / raw_h))

        center_x = (HALF_NUM_RAYS + delta / DELTA_ANGLE) * SCALE
        start_x = int(center_x - proj_width // 2)
        texture_step = raw_w / proj_width if proj_width > 0 else 1.0

        for x in range(start_x, start_x + proj_width, SCALE):
            ray_idx = int(x // SCALE)
            if 0 <= ray_idx < NUM_RAYS:
                if dist_flat < self.game.raycasting.z_buffer[ray_idx]:
                    sub_x = int(x - start_x)
                    if 0 <= sub_x < proj_width:
                        tex_x = int(sub_x * texture_step)
                        if 0 <= tex_x < raw_w:
                            screen_y = HALF_HEIGHT + proj_height // 2 - proj_height
                            slice_surf = img.subsurface(tex_x, 0, 1, raw_h)
                            scaled_slice = pygame.transform.scale(slice_surf, (SCALE, proj_height))
                            self.game.screen.blit(scaled_slice, (x, screen_y))


# ==============================================================================
# 2. УНИКАЛЬНЫЕ СНАРЯДЫ И ЭФФЕКТЫ БОССА С СИСТЕМОЙ УРОНА
# ==============================================================================

class VortexProjectile(BossProjectile):
    """Вихревой снаряд из пушек с плеч (Дальний бой)"""
    def __init__(self, game, x, y, angle, frames, explosion_frames, damage, explosion_sound=None):
        super().__init__(game, x, y, angle, speed=12.0, frames=frames, anim_speed=60, damage=damage)
        self.explosion_frames = explosion_frames
        self.explosion_sound = explosion_sound

    def update(self, dt):
        super().update(dt)
        # Наносим прямой урон, если вихрь физически пересек хитбокс игрока
        if self.alive and math.hypot(self.game.player.x - self.x, self.game.player.y - self.y) < 0.4:
            self.on_collision()

    def on_collision(self):
        self.alive = False
        if self.explosion_sound:
            self.explosion_sound.play()

        # Спавним статический взрыв на месте детонации вихря
        expl = BossProjectile(self.game, self.x, self.y, 0, speed=0, frames=self.explosion_frames, anim_speed=80)
        expl.on_animation_end = lambda: setattr(expl, 'alive', False)

        # Честный урон игроку по радиусу взрыва сферы
        if math.hypot(self.game.player.x - self.x, self.game.player.y - self.y) <= 1.8:
            self.game.player.take_damage(self.damage)

        self.game.level_manager.npcs[0].boss_projectiles.append(expl)


class GroundRocket(BossProjectile):
    """Ракета, бешено вращающаяся на полу из пушки с руки (Средний бой)"""
    def __init__(self, game, x, y, angle, frames, fire_frames, explosion_frames, damage, explosion_sound=None):
        super().__init__(game, x, y, angle, speed=16.0, frames=frames, anim_speed=30, damage=damage)
        self.fire_frames = fire_frames
        self.explosion_frames = explosion_frames
        self.explosion_sound = explosion_sound
        self.flame_spawn_timer = pygame.time.get_ticks()

    def update(self, dt):
        super().update(dt)
        if not self.alive:
            return

        if math.hypot(self.game.player.x - self.x, self.game.player.y - self.y) < 0.4:
            self.on_collision()
            return

        # Оставляем за собой шлейф неподвижного узкого пламени на полу
        now = pygame.time.get_ticks()
        if now - self.flame_spawn_timer > 100:
            self.flame_spawn_timer = now
            flame = BossProjectile(self.game, self.x, self.y, 0, speed=0, frames=self.fire_frames, anim_speed=70)
            flame.on_animation_end = lambda: setattr(flame, 'alive', False)

            if math.hypot(self.game.player.x - self.x, self.game.player.y - self.y) < 0.5:
                self.game.player.take_damage(2)

            for npc in self.game.level_manager.npcs:
                if getattr(npc, 'name', '') == 'HellSmith':
                    npc.boss_projectiles.append(flame)

    def on_collision(self):
        self.alive = False
        if self.explosion_sound:
            self.explosion_sound.play()

        expl = BossProjectile(self.game, self.x, self.y, 0, speed=0, frames=self.explosion_frames, anim_speed=50)
        expl.on_animation_end = lambda: setattr(expl, 'alive', False)

        if math.hypot(self.game.player.x - self.x, self.game.player.y - self.y) <= 1.5:
            self.game.player.take_damage(self.damage)

        for npc in self.game.level_manager.npcs:
            if getattr(npc, 'name', '') == 'HellSmith':
                npc.boss_projectiles.append(expl)


class GroundFireWave(BossProjectile):
    """Огненная лужа от удара молотом, которая СТОИТ НА МЕСТЕ и наносит периодический урон"""
    def __init__(self, game, x, y, frames, damage, fire_sound=None):
        super().__init__(game, x, y, angle=0, speed=0, frames=frames, anim_speed=80, damage=damage)
        self.fire_sound = fire_sound
        if self.fire_sound:
            self.fire_sound.play(loops=-1)

    def update(self, dt):
        super().update(dt)
        if not self.alive:
            return

        # Честный периодический урон каждую секунду горения лужи
        if math.hypot(self.game.player.x - self.x, self.game.player.y - self.y) <= 1.2:
            if self.current_frame % 3 == 0:
                self.game.player.take_damage(self.damage)

    def on_animation_end(self):
        self.alive = False  # Лужа догорела и плавно исчезла
        if self.fire_sound:
            self.fire_sound.stop()


# ==============================================================================
# 3. ПОЛНЫЙ ПЕРЕХВАТ ОБНОВЛЕНИЙ И ИИ БОССА HELLSMITH
# ==============================================================================

def boss_custom_update(self):
    """Полный перехват метода update() у NPC: жесткий контроль анимаций и снарядов"""
    dt = self.game.delta_time
    if dt > 0.033:
        dt = 0.033
    now = pygame.time.get_ticks()

    # 1. ОБНОВЛЕНИЕ ВСЕХ СНАРЯДОВ КУЗНЕЦА
    self.boss_projectiles = [p for p in self.boss_projectiles if p.alive]
    for proj in self.boss_projectiles:
        proj.update(dt)

    # 2. ОБРАБОТКА СМЕРТИ БОССА
    if self.state == "DEAD":
        if hasattr(self, 'sound_fire_loop') and self.sound_fire_loop:
            self.sound_fire_loop.stop()
        self.animator.update()
        self.image = self.animator.current_image
        self._update_sizes()
        return

    # Отсечка дистанции оптимизации ИИ
    dist_to_player = math.hypot(self.x - self.game.player.x, self.y - self.game.player.y)
    if dist_to_player > self.activation_distance:
        return

    # Гасим эффекты урона
    if self.hurt_flash > 0:
        self.hurt_flash -= 1
    if self.shoot_flash > 0:
        self.shoot_flash -= 1

    # 3. АУДИО-ЭМБИЕНТ РЫЧАНИЯ И ОБНАРУЖЕНИЯ
    if self.state in ("IDLE", "PATROL") and hasattr(self, 'sound_idle_growl') and self.sound_idle_growl:
        if now > self.boss_growl_timer:
            self.boss_growl_timer = now + uniform(5000, 9000)
            self.sound_idle_growl.play()

    can_see = self.has_line_of_sight()
    if can_see and dist_to_player <= self.view_distance:
        if hasattr(self, 'sound_sight_phrase') and self.sound_sight_phrase and not self.boss_said_sight_phrase:
            self.boss_said_sight_phrase = True
            self.sound_sight_phrase.play()

    # 4. ЛОГИКА КАСТОМНЫХ АНИМАЦИЙ АТАК
    if self.boss_state in ("MELEE", "HAND", "SHOULDER"):
        if now - self.boss_attack_timer > 150:
            self.boss_attack_timer = now
            self.boss_attack_frame += 1

            # Выстрел 1: Молот (Кадр 2)
            if self.boss_state == "MELEE" and self.boss_attack_frame == 2:
                if hasattr(self, 'sound_melee'):
                    self.sound_melee.play()
                wave = GroundFireWave(
                    self.game,
                    self.game.player.x,
                    self.game.player.y,
                    self.boss_fx_cache["fx_ground_fire"],
                    damage=6,
                    fire_sound=getattr(self, 'sound_fire_loop', None)
                )
                self.boss_projectiles.append(wave)

            # Выстрел 2: Пушка с руки (Кадр 2)
            elif self.boss_state == "HAND" and self.boss_attack_frame == 2:
                if hasattr(self, 'sound_hand'):
                    self.sound_hand.play()
                angle_to_player = math.atan2(self.game.player.y - self.y, self.game.player.x - self.x)
                rocket = GroundRocket(
                    self.game,
                    self.x,
                    self.y,
                    angle_to_player,
                    frames=self.boss_fx_cache["proj_rocket"],
                    fire_frames=self.boss_fx_cache["fx_narrow_flame"],
                    explosion_frames=self.boss_fx_cache["fx_mini_explosion"],
                    damage=18,
                    explosion_sound=getattr(self, 'sound_explosion', None)
                )
                self.boss_projectiles.append(rocket)

            # Выстрел 3: Пушки из-за плеч (Кадр 3)
            elif self.boss_state == "SHOULDER" and self.boss_attack_frame == 3:
                if hasattr(self, 'sound_shoulder'):
                    self.sound_shoulder.play()
                angle_to_player = math.atan2(self.game.player.y - self.y, self.game.player.x - self.x)
                vortex = VortexProjectile(
                    self.game,
                    self.x,
                    self.y,
                    angle_to_player,
                    frames=self.boss_fx_cache["proj_vortex"],
                    explosion_frames=self.boss_fx_cache["fx_big_explosion"],
                    damage=28,
                    explosion_sound=getattr(self, 'sound_explosion', None)
                )
                self.boss_projectiles.append(vortex)

            max_f = 4 if self.boss_state == "SHOULDER" else 3
            if self.boss_attack_frame > max_f:
                self.last_shot = now
                self.boss_state = "CHASE"
                self.state = "CHASE"

            # ЖЕСТКИЙ ПЕРЕХВАТ СПРАЙТА
            action_key = self.boss_state.lower()
            key = f"attack_{action_key}front{self.boss_attack_frame}"
            self.image = self.animator.sprites.get(key, self.image)

            # Обновляем размеры хитбокса наружу для рендерера игры
            if self.image:
                self.sprite_width, self.sprite_height = self.image.get_size()
                self.sprite_ratio = self.sprite_width / self.sprite_height
            return

    # 5. ТРЕХСТУПЕНЧАТЫЙ ВЫБОР РЕЖИМА АТАКИ ИЗ-ЗА ДИСТАНЦИИ
    if can_see and now - self.last_shot >= self.shoot_delay:
        self.boss_attack_timer = now
        self.boss_attack_frame = 1

        if dist_to_player <= 2.2:
            self.boss_state = "MELEE"
            self.state = "ATTACK"
            return
        elif dist_to_player <= 5.5:
            self.boss_state = "HAND"
            self.state = "ATTACK"
            return
        elif dist_to_player <= self.shoot_range:
            self.boss_state = "SHOULDER"
            self.state = "ATTACK"
            return

    # 6. ЕСЛИ КУЗНЕЦ МИРНО ИДЕТ — ВКЛЮЧАЕМ СТАНДАРТНЫЙ АНИМАТОР И ПЕРЕМЕЩЕНИЕ A*
    self.update_state(dt)
    self.animator.update()

    # Синхронизируем базовые переменные для рендерера игры
    self.image = self.animator.current_image
    self.sprite_width = self.animator.sprite_width
    self.sprite_height = self.animator.sprite_height
    self.sprite_ratio = self.animator.sprite_ratio
    self.move_direction = self.animator.move_direction


def boss_custom_draw(self):
    """Метод отрисовки: выводит плоское тело босса, а затем рисует летящие снаряды"""
    self.base_draw_method()
    for proj in self.boss_projectiles:
        proj.draw()


# ==============================================================================
# 4. ГЛОБАЛЬНАЯ ИНИЦИАЛИЗАЦИЯ КУЗНЕЦА ЧЕРЕЗ СИСТЕМУ МОСТИКОВ
# ==============================================================================

def init_logic(self):
    """Вызывается ядром игры один раз при спавне Босса. Собирает HellSmith в памяти"""
    self.boss_state = "CHASE"
    self.boss_attack_timer = 0
    self.boss_attack_frame = 1
    self.boss_projectiles = []
    self.boss_fx_cache = {}
    scale = self.scale

    # Автозагрузчик кадров спецэффектов
    def load_fx_sequence(prefix, count):
        frames = []
        for idx in range(1, count + 1):
            filename = f"{prefix}_{idx}.png"
            path = os.path.join(self.folder_path, filename)
            if os.path.exists(path):
                original = pygame.image.load(path).convert_alpha()
                new_w = int(original.get_width() * scale)
                new_h = int(original.get_height() * scale)
                frames.append(pygame.transform.scale(original, (new_w, new_h)))
        return frames

    self.boss_fx_cache["proj_rocket"] = load_fx_sequence("proj_rocket", 16)
    self.boss_fx_cache["fx_ground_fire"] = load_fx_sequence("fx_ground_fire", 23)
    self.boss_fx_cache["fx_narrow_flame"] = load_fx_sequence("fx_narrow_flame", 13)
    self.boss_fx_cache["fx_mini_explosion"] = load_fx_sequence("fx_mini_explosion", 7)
    self.boss_fx_cache["fx_big_explosion"] = load_fx_sequence("fx_big_explosion", 5)
    self.boss_fx_cache["proj_vortex"] = load_fx_sequence("proj_vortex", 9)

    print(f"[УСПЕХ БОССА] Автозагрузчик импортировал {sum(len(v) for v in self.boss_fx_cache.values())} кадров эффектов.")

    # Догружаем в кэш аниматора фронтальные кадры атак Босса
    for f in range(1, 4):
        self.animator.sprites[f"attack_melee_front_{f}"] = self.animator._load_and_scale_file(
            f"{self.name}attack_melee_front{f}.png", scale
        )
        self.animator.sprites[f"attack_hand_front{f}"] = self.animator._load_and_scale_file(
            f"{self.name}attack_hand_front{f}.png", scale
        )

    for f in range(1, 5):
        self.animator.sprites[f"attack_shoulder_front{f}"] = self.animator._load_and_scale_file(
            f"{self.name}attack_shoulder_front{f}.png", scale
        )

    # Загружаем кастомные аудиофайлы
    try:
        self.sound_melee = pygame.mixer.Sound(os.path.join(self.folder_path, 'sound_melee.wav'))
        self.sound_hand = pygame.mixer.Sound(os.path.join(self.folder_path, 'sound_hand.wav'))
        self.sound_shoulder = pygame.mixer.Sound(os.path.join(self.folder_path, 'sound_shoulder.wav'))
        self.sound_explosion = pygame.mixer.Sound(os.path.join(self.folder_path, 'sound_explosion.wav'))
        self.sound_fire_loop = pygame.mixer.Sound(os.path.join(self.folder_path, 'sound_fire_loop.wav'))
        self.sound_idle_growl = pygame.mixer.Sound(os.path.join(self.folder_path, 'sound_idle_growl.wav'))
        self.sound_sight_phrase = pygame.mixer.Sound(os.path.join(self.folder_path, 'sound_sight_phrase.wav'))

        vol = 0.45
        for s in [self.sound_melee, self.sound_hand, self.sound_shoulder, self.sound_explosion, self.sound_idle_growl]:
            if s:
                s.set_volume(vol)
        if self.sound_fire_loop:
            self.sound_fire_loop.set_volume(vol * 0.6)
        if self.sound_sight_phrase:
            self.sound_sight_phrase.set_volume(vol * 1.3)

    except Exception as e:
        print(f"[БОСС] Аудиофайлы не найдены, применен фолбек: {e}")
        self.sound_melee = self.shoot_sound
        self.sound_hand = self.shoot_sound
        self.sound_shoulder = self.shoot_sound
        self.sound_explosion = self.shoot_sound
        self.sound_fire_loop = None
        self.sound_idle_growl = None
        self.sound_sight_phrase = None

    self.boss_growl_timer = pygame.time.get_ticks() + uniform(2000, 6000)
    self.boss_said_sight_phrase = False

    # ТОТАЛЬНЫЙ ПЕРЕХВАТ МЕТОДОВ ДВИЖКА
    self.base_draw_method = types.MethodType(self.draw.__func__, self)

    # НАМЕРТВО ПЕРЕПИСЫВАЕМ СТАНДАРТНЫЙ МЕТОД UPDATE КЛАССА NPC!
    self.update = types.MethodType(boss_custom_update, self)
    self.draw = types.MethodType(boss_custom_draw, self)