import os
import math
import pygame
import types
from random import uniform

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


# ==============================================================================
# 1. ПОДСИСТЕМА АВТОНОМНЫХ 3D-СНАРЯДОВ БОССА
# ==============================================================================

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
        if not self.alive:
            return
        dt = self.game.delta_time
        if dt > 0.033:
            dt = 0.033

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
        if self.explosion_frames:
            self.is_exploding = True
            self.speed = 0
            self.current_frame = 0
            if self.explosion_sound:
                self.explosion_sound.play()
        else:
            self.alive = False

    def draw(self):
        if not self.alive or not self.frames:
            return
        current_deck = self.explosion_frames if self.is_exploding else self.frames
        if not current_deck or self.current_frame >= len(current_deck):
            return

        img = current_deck[self.current_frame]
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

        current_size = 0.6 if self.is_exploding else self.size_mult
        proj_height = int((SCREEN_DIST / dist_flat) * current_size)
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


class HighMortarRocket:
    """Новый изолированный класс для навесной ракеты из пушки руки (HAND)"""
    def __init__(self, game, boss, start_x, start_y, target_dist, angle, frames, explosion_frames, fire_frames, damage, explosion_sound=None):
            # ИСПРАВЛЕНИЕ: Добавили explosion_sound=None в самый конец списка аргументов!
            self.game = game
            self.boss = boss
            self.x = start_x
            self.y = start_y
            self.start_x = start_x
            self.start_y = start_y
            self.angle = angle
            self.speed = 7.0           
            self.frames = frames       
            self.explosion_frames = explosion_frames
            self.fire_frames = fire_frames
            self.damage = damage
            self.explosion_sound = explosion_sound  # Запоминаем кастомный звук взрыва ракеты
            
            self.target_dist = target_dist
            self.z = 0.0               
            self.current_frame = 0
            self.anim_timer = pygame.time.get_ticks()
            self.alive = True
            self.in_air = True        # Флаг: пока летит по воздуху — анимация заморожена

    def update(self):
        if not self.alive: return
        dt = self.game.delta_time
        if dt > 0.033: dt = 0.033

        # ФАЗА 1: ЛЕТИТ В ВОЗДУХЕ ПО ДУГЕ
        if self.in_air:
            self.x += math.cos(self.angle) * self.speed * dt
            self.y += math.sin(self.angle) * self.speed * dt

            # Считаем пройденный процент пути до точки назначения
            dist_travelled = math.hypot(self.x - self.start_x, self.y - self.start_y)
            progress = dist_travelled / self.target_dist if self.target_dist > 0 else 1.0

            if progress >= 1.0 or self.game.map.is_wall(int(self.x), int(self.y)):
                # Ракетка упала на пол! Останавливаем полет и включаем кручение
                self.in_air = False
                self.speed = 0
                self.z = 0.0
                self.current_frame = 0
                self.anim_timer = pygame.time.get_ticks()
            else:
                # Синусоида параболы поднимает биллборд ракеты вверх
                self.z = math.sin(progress * math.pi) * 1.5
                self.current_frame = 0 # Замораживаем на 1-м кадре в воздухе
            return

        # ФАЗА 2: УПАЛА И БЕШЕНО КРУТИТСЯ НА ЗЕМЛЕ (ЗАДЕРЖКА ВЗРЫВА)
        now = pygame.time.get_ticks()
        if now - self.anim_timer > 35:
            self.anim_timer = now
            self.current_frame += 1
            # Прокрутила все 16 кадров на полу — взрывается!
            if self.current_frame >= len(self.frames):
                self.trigger_detonation()

    def trigger_detonation(self):
        self.alive = False
        
        # Включаем кастомный звук бабаха
        if hasattr(self.boss, 'sound_explosion') and self.boss.sound_explosion:
            self.boss.sound_explosion.play()

        # 1. РАЗОВЫЙ ПЛОТНЫЙ УРОН ВЗРЫВА (Радиус окружности — 1.2 клетки)
        dist_to_player = math.hypot(self.game.player.x - self.x, self.game.player.y - self.y)
        if dist_to_player <= 1.2:
            self.game.player.take_damage(self.damage)

        # 2. Спавним визуальный мини-взрыв на 7 кадров через твой список снарядов Босса
        if self.explosion_frames:
            # Создаем фейковый BossBallProjectile с нулевой скоростью для анимации взрыва
            expl = BossBallProjectile(self.game, self.boss, self.x, self.y, 0, speed=0, frames=self.explosion_frames, damage=0)
            expl.on_animation_end = lambda: setattr(expl, 'alive', False)
            self.boss.boss_projectiles.append(expl)

        # 3. ПОДЖОГ ЗЕМЛИ: Спавним лужу высокопериодичного огня (23 кадра fx_ground_fire)
        if self.fire_frames:
            fire_wave = GroundFireWave(self.game, self.boss, self.x, self.y, self.fire_frames, damage=4)
            self.boss.boss_projectiles.append(fire_wave)

    def draw(self):
        """Рендеринг биллборда ракеты с учетом высоты параболы self.z"""
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

        proj_height = int((SCREEN_DIST / dist_flat) * 0.4) 
        proj_width = int(proj_height * (raw_w / raw_h))
        center_x = (HALF_NUM_RAYS + delta / DELTA_ANGLE) * SCALE
        start_x = int(center_x - proj_width // 2)
        texture_step = raw_w / proj_width if proj_width > 0 else 1.0

        # Смещаем вертикальные полосы вверх, пока ракета летит по дуге в воздухе
        z_offset = int((self.z * SCREEN_DIST) / dist_flat) if dist_flat > 0 else 0

        for x in range(start_x, start_x + proj_width, SCALE):
            ray_idx = int(x // SCALE)
            if 0 <= ray_idx < NUM_RAYS and dist_flat < self.game.raycasting.z_buffer[ray_idx]:
                sub_x = int(x - start_x)
                if 0 <= sub_x < proj_width:
                    tex_x = int(sub_x * texture_step)
                    if 0 <= tex_x < raw_w:
                        screen_y = HALF_HEIGHT + proj_height // 2 - proj_height - z_offset
                        slice_surf = img.subsurface(tex_x, 0, 1, raw_h)
                        scaled_slice = pygame.transform.scale(slice_surf, (SCALE, proj_height))
                        self.game.screen.blit(scaled_slice, (x, screen_y))


class GroundFireWave(BossBallProjectile):
    """Огненная лужа: высокопериодичный тикающий урон по окружности радиусом 2.0 клетки"""
    def __init__(self, game, boss, x, y, frames, damage):
        # Передаем параметры в твой базовый класс, выставляя размер лужи побольше (0.8)
        super().__init__(game, boss, x, y, angle=0, speed=0, frames=frames, damage=damage)
        self.size_mult = 0.8
        self.anim_speed = 80

    def update(self):
        if not self.alive: return
        
        # Окружность поражения радиусом 2.0 клетки
        dist_to_player = math.hypot(self.game.player.x - self.x, self.game.player.y - self.y)
        if dist_to_player <= 2.0:
            # Наносим тикающий урон очень часто — каждый 3-й кадр горения
            if self.current_frame % 3 == 0:
                self.game.player.take_damage(self.damage)

        # Смена кадров горения до 23 кадра
        now = pygame.time.get_ticks()
        if now - self.anim_timer > self.anim_speed:
            self.anim_timer = now
            self.current_frame += 1
            if self.current_frame >= len(self.frames):
                self.alive = False  # Пламя полностью потухло



# ==============================================================================
# 2. ЛИЧНЫЙ, НЕЗАВИСИМЫЙ МЕТОД ОБНОВЛЕНИЯ АНИМАЦИЙ ДЛЯ АНИМАТОРA БОССА
# ==============================================================================

def boss_personal_animator_update(self_animator):
    """ПОЛНАЯ ЗАМЕНА МЕТОДА update() У ОБЪЕКТА NPCAnimator БОССА.
    Базовый код аниматора ядра отключен на 100%. Мы сами полностью управляем графикой!"""
    npc = self_animator.npc

    # Если Босс мертв — запускаем оригинальный цикл падения трупа
    if npc.state == "DEAD":
        self_animator.base_animator_update_func()
        return

    # В режиме атак — аниматор Босса забирает текстуру замаха
    if npc.boss_internal_state in ("MELEE_ATTACK", "HAND_ATTACK", "SHOULDER_ATTACK"):
        prefix = "shoulder" if npc.boss_internal_state == "SHOULDER_ATTACK" else "hand"
        key = f"attack_{prefix}_front_{npc.boss_attack_frame}"

        self_animator.current_image = self_animator.sprites.get(key, npc.image)
        return

    # Если Босс просто идет — возвращаем стандартный 8-ракурсный перебор ног
    self_animator.base_animator_update_func()


# ==============================================================================
# 3. ПОЛНОСТЬЮ ЧИСТЫЙ И ИЗОЛИРОВАННЫЙ UPDATE ДЛЯ СУЩНОСТИ БОССА
# ==============================================================================

def boss_total_isolated_update(self):
    """Независимый ИИ Босса с хитрым чередованием атак и защитой от затирания"""
    dt = self.game.delta_time
    if dt > 0.033: dt = 0.033
    now = pygame.time.get_ticks()

    # 1. Обновляем летящие ракеты и взрывы
    self.boss_projectiles = [p for p in self.boss_projectiles if p.alive]
    for proj in self.boss_projectiles:
        proj.update()

    # 2. Обработка смерти Босса
    if not self.alive or self.hp <= 0:
        self.state = "DEAD"
        self.animator.update()
        self.image = self.animator.current_image
        if self.image:
            self.sprite_width, self.sprite_height = self.image.get_size()
            self.sprite_ratio = self.sprite_width / self.sprite_height
        return

    # Оптимизация дистанции ИИ
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

    # ==========================================================================
    # СТРУКТУРА ЛОКАЛЬНОГО КОНЕЧНОГО АВТОМАТА БОССА
    # ==========================================================================
    
    # СИТУАЦИЯ А: ФАЗА ВЕДЕНИЯ КАСТОМНОГО ОГНЯ (Когда босс застывает и машет пушками)
    if self.boss_internal_state in ("HAND_ATTACK", "SHOULDER_ATTACK"):
        self.animator._calculate_direction()
        self.move_direction = self.animator.move_direction

        if now - self.boss_attack_timer > 150:
            self.boss_attack_timer = now
            self.boss_attack_frame += 1

            # Залп наплечных пушек (Дальний бой, вылет прямого вихря на 3-м кадре)
            if self.boss_internal_state == "SHOULDER_ATTACK" and self.boss_attack_frame == 3:
                vortex_frames = getattr(self, 'boss_fireball_frames', [])
                if vortex_frames:
                    # ИСПРАВЛЕНИЕ: Передали обязательный аргумент boss_explosion_frames на его законное место!
                    ball = BossBallProjectile(
                        self.game, self, self.x, self.y, 
                        math.atan2(self.game.player.y - self.y, self.game.player.x - self.x), 
                        speed=4.5, 
                        frames=vortex_frames, 
                        explosion_frames=getattr(self, 'boss_explosion_frames', []), # Добавили
                        damage=25
                    )
                    self.boss_projectiles.append(ball)

            # Выстрел из руки (Средний бой, вылет параболической ракеты на 2-м кадре)
            elif self.boss_internal_state == "HAND_ATTACK" and self.boss_attack_frame == 2:
                rocket_frames = getattr(self, 'boss_rocket_frames', [])
                if rocket_frames:
                    angle = math.atan2(self.game.player.y - self.y, self.game.player.x - self.x)
                    ball = HighMortarRocket(
                        self.game, self, self.x, self.y, target_dist=dist_to_player, angle=angle, 
                        frames=rocket_frames, 
                        explosion_frames=getattr(self, 'boss_mini_explosion_frames', []), 
                        fire_frames=getattr(self, 'boss_ground_fire_frames', []), 
                        damage=20, explosion_sound=getattr(self, 'sound_explosion', None)
                    )
                    self.boss_projectiles.append(ball)

            max_f = 4 if self.boss_internal_state == "SHOULDER_ATTACK" else 3
            if self.boss_attack_frame > max_f:
                self.last_shot = now  
                self.boss_internal_state = "CHASE"
                self.state = "CHASE"

        # Принудительно заставляем наш изолированный аниматор удерживать картинку замаха
        self.animator.update()
        self.image = self.animator.current_image

    # ФАЗА ВЫБОРА АТАК И НАВИГАЦИИ ПО КАРТЕ ЧЕРЕЗ БРОСОК КУБИКА 50/50%
    else:
        if can_see and dist_to_player <= self.shoot_range and (now - self.last_shot >= self.shoot_delay):
            self.boss_attack_timer = now
            self.boss_attack_frame = 1
            
            # В упор (< 3.0 клеток) — гарантированно выжигает пол ракетой под ногами ГГ!
            if dist_to_player <= 3.0:
                self.boss_internal_state = "HAND_ATTACK"
                self.state = "ATTACK"
                if hasattr(self, 'sound_hand') and self.sound_hand: self.sound_hand.play()
            else:
                # На дистанции — честный бросок кубика вероятности 50 на 50%! [Example 5]
                from random import random
                if random() < 0.5:
                    self.boss_internal_state = "HAND_ATTACK"
                    self.state = "ATTACK"
                    if hasattr(self, 'sound_hand') and self.sound_hand: self.sound_hand.play()
                else:
                    self.boss_internal_state = "SHOULDER_ATTACK"
                    self.state = "ATTACK"
                    if hasattr(self, 'sound_shoulder') and self.sound_shoulder: self.sound_shoulder.play()
        else:
            # Если Босс не готов стрелять — он просто мирно преследует игрока по A*
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


# ==============================================================================
# 4. ТОЧКА ВХОДА ИНИЦИАЛИЗАЦИИ БОССА
# ==============================================================================

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
    
    # 1. Загружаем 3 кадра атаки пушкой с руки (HAND)
    for f in range(1, 4):
        key = f"attack_hand_front_{f}"
        filename = f"{npc.name}_attack_hand_front_{f}.png"
        path = os.path.join(npc.folder_path, filename)

        if os.path.exists(path):
            # Загружаем НАПРЯМУЮ с диска по полному пути, минуя базовый аниматор ядра!
            original = pygame.image.load(path)
            new_w = int(original.get_width() * scale)
            new_h = int(original.get_height() * scale)
            
            # Сохраняем честный отмасштабированный HD-кадр в колоду спрайтов Босса
            npc.animator.sprites[key] = pygame.transform.scale(original, (new_w, new_h))
            print(f"  ✅ Загружен боевой кадр рук: {key}")
        else:
            print(f"  ❌ КРИТИЧЕСКАЯ ОШИБКА: Файл потерялся: {path}")
            npc.animator.sprites[key] = npc.animator.sprites.get("move_front_1")

    # 2. Загружаем 4 кадра атаки пушками из-за плеч (SHOULDER)
    for f in range(1, 5):
        key = f"attack_shoulder_front_{f}"
        filename = f"{npc.name}_attack_shoulder_front_{f}.png"
        path = os.path.join(npc.folder_path, filename)

        if os.path.exists(path):
            original = pygame.image.load(path)
            new_w = int(original.get_width() * scale)
            new_h = int(original.get_height() * scale)
            
            npc.animator.sprites[key] = pygame.transform.scale(original, (new_w, new_h))
            print(f"  ✅ Загружен боевой кадр плеч: {key}")
        else:
            print(f"  ❌ КРИТИЧЕСКАЯ ОШИБКА: Файл потерялся: {path}")
            npc.animator.sprites[key] = npc.animator.sprites.get("move_front_1")
            
    print("-" * 60)

    try:
        npc.sound_shoulder = pygame.mixer.Sound(os.path.join(npc.folder_path, 'sound_shoulder.wav'))
        npc.sound_hand = pygame.mixer.Sound(os.path.join(npc.folder_path, 'sound_hand.wav'))
        npc.sound_explosion = pygame.mixer.Sound(os.path.join(npc.folder_path, 'sound_explosion.wav'))
        npc.sound_idle_growl = pygame.mixer.Sound(os.path.join(npc.folder_path, 'sound_idle_growl.wav'))
        npc.sound_sight_phrase = pygame.mixer.Sound(os.path.join(npc.folder_path, 'sound_sight_phrase.wav'))

        vol = 0.45
        for s in [npc.sound_shoulder, npc.sound_hand, npc.sound_explosion, npc.sound_idle_growl]:
            if s:
                s.set_volume(vol)
        if npc.sound_sight_phrase:
            npc.sound_sight_phrase.set_volume(vol * 1.3)

    except Exception as e:
        print(f"[БОСС] Аудио не найдено, фолбек: {e}")
        npc.sound_shoulder = npc.shoot_sound
        npc.sound_hand = npc.shoot_sound
        npc.sound_explosion = npc.shoot_sound
        npc.sound_idle_growl = None
        npc.sound_sight_phrase = None

    npc.boss_growl_timer = pygame.time.get_ticks() + uniform(2000, 6000)
    npc.boss_said_sight_phrase = False

    # ПОЛНЫЙ ДВУХСТОРОННИЙ ПЕРЕХВАТ СУЩНОСТИ И ЕЕ ГРАФИКИ
    npc.base_draw_method = types.MethodType(npc.draw.__func__, npc)
    npc.draw = types.MethodType(boss_custom_draw, npc)

    # 1. Заменяем метод update самого Босса (ИИ изолирован)
    npc.update = types.MethodType(boss_total_isolated_update, npc)

    # 2. Заменяем метод update лично у АНИМАТОРA Босса (Графика изолирована!)
    npc.animator.base_animator_update_func = types.MethodType(npc.animator.update.__func__, npc.animator)
    npc.animator.update = types.MethodType(boss_personal_animator_update, npc.animator)

    print(f"[УСПЕХ БОССА] Личный независимый Аниматор и ИИ HellSmith полностью запущены.")
    
    # Скопируй эти строчки в самый низ своего init_logic:
    def load_local_fx(prefix, count):
        frames = []
        for idx in range(1, count + 1):
            path = os.path.join(self.folder_path, f"{prefix}_{idx}.png")
            if os.path.exists(path):
                original = pygame.image.load(path)
                frames.append(pygame.transform.scale(original, (int(original.get_width() * self.scale), int(original.get_height() * self.scale))))
        return frames

    self.boss_mini_explosion_frames = load_local_fx("fx_mini_explosion", 7)
    self.boss_ground_fire_frames = load_local_fx("fx_ground_fire", 23)

    