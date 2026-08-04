import os
import math
import random
import pygame
import types

try:
    import setting
    SCREEN_DIST = getattr(setting, 'SCREEN_DIST', 1330)  # Подтянули твою честную константу из логов!
    HALF_HEIGHT = getattr(setting, 'HALF_HEIGHT', 432)
    NUM_RAYS = getattr(setting, 'NUM_RAYS', 768)        # Твой честный Full-HD рэйкаст
    SCALE = getattr(setting, 'SCALE', 2)                # Твой честный масштаб полосы 2px!
    HALF_NUM_RAYS = getattr(setting, 'HALF_NUM_RAYS', 384)
    DELTA_ANGLE = getattr(setting, 'DELTA_ANGLE', 0.0013)
    HALF_FOV = getattr(setting, 'HALF_FOV', 0.52)
    WIDTH = getattr(setting, 'WIDTH', 1536)             # Твое честное разрешение WIDTH
    HEIGHT = getattr(setting, 'HEIGHT', 864)
except:
    SCREEN_DIST, HALF_HEIGHT, NUM_RAYS, SCALE = 1330, 432, 768, 2
    HALF_NUM_RAYS, DELTA_ANGLE, HALF_FOV = 384, 0.0013, 0.52
    WIDTH, HEIGHT = 1536, 864


# ==================================================================
# 🔴 ИСПРАВЛЕННЫЙ КЛАСС КРАСНОЙ ПЛАЗМЫ (STAR) — СИНХРОНИЗИРОВАН С SCALE=2
# ==================================================================

class TermPlasmaBall:
    def __init__(self, game, boss, x, y, angle, speed, fly_frames, explosion_frames, damage):
        self.game = game
        self.boss = boss
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = speed  # Физическая скорость на кадр по паспорту
        self.fly_frames = fly_frames
        self.explosion_frames = explosion_frames
        self.damage = damage
        
        self.current_frame = 0
        self.anim_timer = pygame.time.get_ticks()
        self.anim_speed = 60
        self.alive = True
        self.is_exploding = False
        self.prev_x = x
        self.prev_y = y

    def update(self):
        if not self.alive: 
            return
        now = pygame.time.get_ticks()

        # Анимация DOOM-кадров (STARA0 - STARO0)
        delay = 40 if self.is_exploding else 70
        if now - self.anim_timer > delay:
            self.anim_timer = now
            self.current_frame += 1
            if self.is_exploding:
                if self.current_frame >= len(self.explosion_frames):
                    self.alive = False
                    return
            else:
                if self.fly_frames:
                    self.current_frame %= len(self.fly_frames)

        if self.is_exploding: 
            return

        # ФИЗИЧЕСКИЙ ШАГ: Избавляемся от дефектного dt босса! Летим на честных микрошагах
        sub_steps = 4
        step_size = self.speed / sub_steps
        
        for _ in range(sub_steps):
            self.prev_x = self.x
            self.prev_y = self.y
            
            self.x += math.cos(self.angle) * step_size
            self.y += math.sin(self.angle) * step_size

            # Проверка стен в numeric_grid
            tile_x, tile_y = int(self.x), int(self.y)
            grid = self.game.map.numeric_grid
            if 0 <= tile_x < len(grid) and 0 <= tile_y < len(grid[0]):
                if grid[tile_y][tile_x] > 0:
                    self.trigger_explosion()
                    return

            # Проверка хитбокса игрока
            if math.hypot(self.game.player.x - self.x, self.game.player.y - self.y) < 0.5:
                print(f"💥 [TERM-Плазма] Прямое попадание по игроку! Нанесено: {self.damage} HP")
                if hasattr(self.game.player, 'take_damage'):
                    self.game.player.take_damage(self.damage)
                self.trigger_explosion()
                return

    def trigger_explosion(self):
        if self.is_exploding: 
            return
        if self.explosion_frames:
            self.is_exploding = True
            self.current_frame = 0
            if hasattr(self, 'prev_x'):
                self.x, self.y = self.prev_x, self.prev_y
        else:
            self.alive = False

    def draw(self):
        """Рендерит плазмошар Терминатора без растяжений под Full-HD и SCALE=2"""
        if not self.alive: 
            return
        
        current_deck = self.explosion_frames if self.is_exploding else self.fly_frames
        if not current_deck or self.current_frame >= len(current_deck): 
            return
        
        img = current_deck[self.current_frame]
        raw_w, raw_h = img.get_size()
        
        dx = self.x - self.game.player.x
        dy = self.y - self.game.player.y
        dist = math.hypot(dx, dy)
        if dist < 0.2: 
            return

        delta = math.atan2(dy, dx) - self.game.player.angle
        while delta > math.pi: 
            delta -= math.tau
        while delta < -math.pi: 
            delta += math.tau
        if abs(delta) > HALF_FOV + 0.4: 
            return

        dist_flat = dist * math.cos(delta)
        if dist_flat < 0.2: 
            return

        # Честная плоская проекция тангенса
        screen_x = int(WIDTH // 2 + math.tan(delta) * SCREEN_DIST)
        wall_height = int(SCREEN_DIST / dist_flat)
        
        size_factor = 0.45 if self.is_exploding else 0.3
        proj_height = int(wall_height * size_factor)
        proj_width = int(proj_height * (raw_w / raw_h))
        
        # Компенсатор горизонтального аппаратного скейла окна (0.72)
        proj_width = int(proj_width * 0.72)

        start_x = int(screen_x - proj_width // 2)
        screen_y = HALF_HEIGHT - proj_height // 2

        # Высокоскоростной цельный блайт под SCALE=2 с проверкой центрального луча стен
        center_ray = int(screen_x // SCALE)
        if 0 <= center_ray < NUM_RAYS:
            if dist_flat < self.game.raycasting.z_buffer[center_ray]:
                try:
                    scaled_img = pygame.transform.scale(img, (proj_width, proj_height))
                    self.game.screen.blit(scaled_img, (start_x, screen_y))
                except:
                    pass


# ==================================================================
# 🤖 ИСПРАВЛЕННЫЙ ИИ-ЦИКЛ ОБНОВЛЕНИЯ БОССA TERM
# ==================================================================

def boss_term_isolated_update(self):
    """Изолированный игровой цикл Терминатора с жесткой блокировкой перезаписи кадров"""
    dt = self.game.delta_time
    if dt > 0.033: dt = 0.033
    now = pygame.time.get_ticks()

    # Обновляем локальные снаряды плазмы STAR
    self.boss_projectiles = [p for p in self.boss_projectiles if p.alive]
    for proj in self.boss_projectiles:
        proj.update()

    # Проверка смерти
    if not self.alive or self.hp <= 0:
        self.state = "DEAD"
        self.animator.update()
        self.image = self.animator.current_image
        return

    dist_to_player = math.hypot(self.game.player.x - self.x, self.game.player.y - self.y)
    if self.boss_internal_state == "CHASE" and dist_to_player > self.activation_distance:
        return

    # --- СТEЙТ-МАШИНА АТАК КИБОРГА ---
    if self.boss_internal_state == "ATTACK_MG":
        if now >= self.mg_next_shot_time:
            if hasattr(self, 'sound_mg_fire') and self.sound_mg_fire:
                self.sound_mg_fire.play()
                
            self.mg_shots_left -= 1
            
            # Чередуем кадры вспышки 1 и 2
            self.boss_attack_frame = 2 if self.boss_attack_frame == 1 else 1
            
            if hasattr(self.game.player, 'take_damage'):
                self.game.player.take_damage(15)
            print(f"💥 [TERM-Пулемет] Серия очередей. Осталось выстрелов: {self.mg_shots_left}")

            if self.mg_shots_left > 0:
                self.mg_next_shot_time = now + 140
            else:
                self.boss_internal_state = "CHASE"
                self.state = "CHASE"
                self.last_shot = now
        
        # 🔥 КРИТИЧЕСКИЙ ФИКС: Принудительно вызываем кастомный аниматор боевых кадров 
        # и мгновенно выходим (return) из апдейта, чтобы базовый аниматор ходьбы движка не затер вспышку!
        self.animator.update()
        self.image = self.animator.current_image
        return

    if self.boss_internal_state == "ATTACK_PLASMA":
        if now >= self.plasma_charge_end_time:
            if hasattr(self, 'sound_plasma_fire') and self.sound_plasma_fire:
                self.sound_plasma_fire.play()
                
            print("🔴 [TERM-Плазма] Накопление завершено! Вылет снаряда STAR.")
            self.boss_attack_frame = 1 # Переключаем аниматора на кадр дульного выхлопа залпа
            
            strike_angle = math.atan2(self.game.player.y - self.y, self.game.player.x - self.x)
            ball = TermPlasmaBall(
                game=self.game, boss=self, x=self.x, y=self.y, angle=strike_angle,
                speed=0.12, fly_frames=self.boss_star_fly, explosion_frames=self.boss_star_exp, damage=35
            )
            self.boss_projectiles.append(ball)
            
            self.boss_internal_state = "CHASE"
            self.state = "CHASE"
            self.last_shot = now
        
        # 🔥 КРИТИЧЕСКИЙ ФИКС: Принудительно обновляем боевой кадр зарядки плазмы и выходим
        self.animator.update()
        self.image = self.animator.current_image
        return

    # --- НАВИГАЦИЯ И КУБИК МАРКОВА ---
    if dist_to_player <= self.shoot_range and (now - self.last_shot >= self.shoot_delay):
        self.boss_attack_timer = now
        
        if random.random() < 0.50:
            print("🤖 [Марков ИИ] Запуск пулеметной очереди!")
            self.boss_internal_state = "ATTACK_MG"
            self.state = "ATTACK"
            if hasattr(self, 'sound_mg_start') and self.sound_mg_start:
                self.sound_mg_start.play()
            self.mg_shots_left = 4
            self.mg_next_shot_time = now + 400
            self.boss_attack_frame = 0 # Стартовый кадр наведения стойки
        else:
            print("🤖 [Марков ИИ] Запуск зарядки плазмотрона!")
            self.boss_internal_state = "ATTACK_PLASMA"
            self.state = "ATTACK"
            if hasattr(self, 'sound_plasma_start') and self.sound_plasma_start:
                self.sound_plasma_start.play()
            self.plasma_charge_end_time = now + 600
            self.boss_attack_frame = 0 # Стартовый кадр накопления энергии
    else:
        self.boss_internal_state = "CHASE"
        self.state = "CHASE"
        if hasattr(self, 'update_state'):
            self.update_state(0.016)
        else:
            angle = math.atan2(self.game.player.y - self.y, self.game.player.x - self.x)
            self.x += self.speed * math.cos(angle) * dt
            self.y += self.speed * math.sin(angle) * dt

    # Базовое обновление ходьбы срабатывает ТОЛЬКО когда босс просто бежит за игроком
    self.animator.update()
    self.image = self.animator.current_image
    if self.image:
        self.sprite_width, self.sprite_height = self.image.get_size()
        self.sprite_ratio = self.sprite_width / self.sprite_height


def boss_term_personal_animator_update(self_animator):
    """Кастомный аниматор: жестко привязывает боевые кадры к экрану во время атак"""
    npc = self_animator.npc
    if npc.state == "DEAD":
        self_animator.base_animator_update_func()
        return

    # Если Терминатор атакует, полностью отключаем базовый 8-направленный пересчет
    if npc.boss_internal_state == "ATTACK_MG":
        key = f"shoot_front_mg_{npc.boss_attack_frame}"
        if npc.boss_attack_frame == 0: 
            key = "attack_front_mg_0"
            
        if key in self_animator.sprites:
            self_animator.current_image = self_animator.sprites[key]
            return
            
    elif npc.boss_internal_state == "ATTACK_PLASMA":
        key = "shoot_front_plasma_0" if npc.boss_attack_frame == 1 else "attack_front_plasma_0"
        if key in self_animator.sprites:
            self_animator.current_image = self_animator.sprites[key]
            return

    # Во всех остальных случаях (когда бежит) — пускай работает родной Doom-поворот спрайтов
    self_animator.base_animator_update_func()



def boss_term_custom_draw(self):
    self.base_draw_method()
    for proj in self.boss_projectiles:
        proj.draw()


# ==================================================================
# 🏁 ГЛАВНАЯ ТОЧКА ВХОДА И ЗАГРУЗЧИК ПАКЕТОВ АССЕТOВ БОССA
# ==================================================================

def init_logic(npc):
    """Патчит сущность NPC намертво, превращая её в автономного Терминатора TERM"""
    npc.boss_projectiles = []
    npc.boss_internal_state = "CHASE"
    npc.boss_attack_frame = 0
    npc.boss_attack_timer = 0
    npc.last_shot = 0
    
    # Характеристики из геймдизайнерского паспорта TERM
    npc.hp = 2000
    npc.size = 0.8
    npc.size_mult = 1.4
    npc.speed = 0.04
    npc.activation_distance = 15
    npc.shoot_range = 12
    npc.shoot_delay = 1200
    scale = npc.scale

    # 1. Загрузчик пакетов DOOM-спрайтов STAR для плазмы по честному буквенному алфавиту
    def load_doom_frames(prefix, letters):
        frames = []
        for let in letters:
            filename = f"{prefix}{let}0.png"
            path = os.path.join(npc.folder_path, filename)
            if os.path.exists(path):
                original = pygame.image.load(path).convert_alpha()
                new_w = int(original.get_width() * scale)
                new_h = int(original.get_height() * scale)
                frames.append(pygame.transform.scale(original, (new_w, new_h)))
        return frames

    npc.boss_star_fly = load_doom_frames("STAR", ["A", "B", "C", "D"])
    npc.boss_star_exp = load_doom_frames("STAR", ["E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O"])

    # 2. 🔥 ФИКС КЛЮЧЕЙ: Загружаем файлы TERM_...png, но ключи в словарь пишем БЕЗ префикса TERM_ !
    # Благодаря этому аниматор лисы сможет прочитать их по чистому имени "shoot_front_mg_1"
    def load_single_frame(key_name, file_name):
        path = os.path.join(npc.folder_path, f"{file_name}.png")
        if os.path.exists(path):
            original = pygame.image.load(path).convert_alpha()
            new_w = int(original.get_width() * scale)
            new_h = int(original.get_height() * scale)
            npc.animator.sprites[key_name] = pygame.transform.scale(original, (new_w, new_h))
            print(f"✅ [Ассеты TERM] Кадр '{key_name}' успешно загружен с диска!")

    load_single_frame("attack_front_mg_0", "TERM_attack_front_mg_0")
    load_single_frame("shoot_front_mg_1", "TERM_shoot_front_mg_1")
    load_single_frame("shoot_front_mg_2", "TERM_shoot_front_mg_2")
    load_single_frame("attack_front_plasma_0", "TERM_attack_front_plasma_0")
    load_single_frame("shoot_front_plasma_0", "TERM_shoot_front_plasma_0")

    # 3. Загрузка аудио-пакета босса по паспорту
    try:
        npc.sound_mg_start = pygame.mixer.Sound(os.path.join(npc.folder_path, 'sound_mg_start.wav'))
        npc.sound_mg_fire = pygame.mixer.Sound(os.path.join(npc.folder_path, 'sound_mg_fire.wav'))
        npc.sound_plasma_start = pygame.mixer.Sound(os.path.join(npc.folder_path, 'sound_plasma_start.wav'))
        npc.sound_plasma_fire = pygame.mixer.Sound(os.path.join(npc.folder_path, 'sound_plasma_fire.wav'))
        for s in [npc.sound_mg_start, npc.sound_mg_fire, npc.sound_plasma_start, npc.sound_plasma_fire]:
            if s: 
                s.set_volume(0.15)
    except Exception as e:
        print(f"⚠️ [Аудио-TERM] Не удалось загрузить звуковые вавки: {e}")

    # 4. Аппаратная замена методов MethodType (Полная инкапсуляция)
    npc.base_draw_method = types.MethodType(npc.draw.__func__, npc)
    npc.draw = types.MethodType(boss_term_custom_draw, npc)
    npc.update = types.MethodType(boss_term_isolated_update, npc)
    npc.animator.base_animator_update_func = types.MethodType(npc.animator.update.__func__, npc.animator)
    npc.animator.update = types.MethodType(boss_term_personal_animator_update, npc.animator)
    
    print(f"🤖 [Патч-Успех] Инкапсулированная ИИ-логика Терминатора TERM полностью активирована в ОЗУ движка!\n")