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
        if self.is_exploding: return
        if self.explosion_frames:
            self.is_exploding = True
            self.current_frame = 0
            if hasattr(self, 'prev_x'):
                self.x, self.y = self.prev_x, self.prev_y
            
            # 🔥 ВОТ ЭТОТ ФИКС ОЗВУЧИТ ВЗРЫВ:
            # Пытаемся вызвать глобальный звук взрыва оружия игрока (звук плазмы RGTX), 
            # который гарантированно загружен в память движка!
            try:
                if hasattr(self.game, 'weapon' ) and self.game.weapon and hasattr(self.game.weapon, 'sound'):
                    self.game.weapon.sound.play()
            except:
                pass
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
    """Изолированный цикл Терминатора: принудительно сбрасывает зависшие системные флаги боли движка"""
    now = pygame.time.get_ticks()

    # 🔥 ГЛАВНЫЙ СИНХРОНИЗАЦИОННЫЙ ФИКС: СМЫВАЕМ ЗАВИСШИЙ ФЛАГ БОЛИ ИЗ ПАМЯТИ
    # Так как базовый update() у Терминатора отключен, мы принудительно гасим 
    # абсолютно все возможные флаги боли твоего движка, если с момента получения урона прошло более 200 мс!
    # Это позволит Терминатору моргнуть красным от Базуки, но мгновенно вернуть стальной цвет.
    
    # 1. Если в твоем движке используется таймер боли (например, pain_timer или hurt_timer)
    for timer_attr in ['pain_timer', 'hurt_timer', 'pain_duration']:
        if hasattr(self, timer_attr):
            val = getattr(self, timer_attr)
            # Если это отметка времени get_ticks(), проверяем кулдаун в 200 мс
            if isinstance(val, (int, float)) and val > 100000 and now - val > 200:
                # Обнуляем таймер, чтобы движок понял, что боль прошла!
                setattr(self, timer_attr, 0)
            elif isinstance(val, (int, float)) and val <= 100: # если это счетчик кадров
                setattr(self, timer_attr, 0)

    # 2. Если в твоем движке используются чистые булевы флаги (True/False)
    for flag_attr in ['pain', 'hurt', 'hit', 'is_hit', 'was_hit', 'red', 'flash_red']:
        if hasattr(self, flag_attr):
            # Если босс сейчас стреляет из пулемета или плазмы, принудительно гасим флаг,
            # так как анимация атаки имеет высший приоритет над залипанием боли!
            if self.boss_internal_state in ["ATTACK_MG", "ATTACK_PLASMA"]:
                setattr(self, flag_attr, False)
                
    # 3. Синхронизируем базовый стейт: если урон нанесся, но босс завис в стейте боли "PAIN"/"HURT",
    # а таймеры очереди требуют стрелять — насильно возвращаем его в рабочий стейт
    if self.state in ["PAIN", "HURT", "HIT"] and self.boss_internal_state in ["ATTACK_MG", "ATTACK_PLASMA"]:
        self.state = "ATTACK"

    # Твоя стабильная логика обновления локальных снарядов
    self.boss_projectiles = [p for p in self.boss_projectiles if p.alive]
    for proj in self.boss_projectiles:
        proj.update()

    # Обработка смерти босса
    if not self.alive or self.hp <= 0:
        self.state = "DEAD"
        if hasattr(self, 'animator'):
            self.animator.update()
            self.image = self.animator.current_image
        return

    dist_to_player = math.hypot(self.game.player.x - self.x, self.game.player.y - self.y)
    
    # Флаг, блокирующий движение во время ведения огня
    attack_in_progress = False
    
    # Сюда мы запишем имя кастомного боевого кадра, если босс атакует
    custom_sprite_key = None

    # --- СТEЙТ-МАШИНА БОЕВЫХ РЕЖИМOВ ---
    # АТАКА №1: Очередь пулемета (4 быстрых выстрела хитскана через 140 мс)
    if self.boss_internal_state == "ATTACK_MG":
        attack_in_progress = True
        
        # Определяем, какой чистый кадр пулемета сейчас должен быть на экране
        custom_sprite_key = f"shoot_front_mg_{self.boss_attack_frame}"
        if self.boss_attack_frame == 0: 
            custom_sprite_key = "attack_front_mg_0"

        if now >= self.mg_next_shot_time:
            self.mg_shots_left -= 1
            
            # Чередуем кадры дульного пламени пулемета (1 и 2)
            self.boss_attack_frame = 2 if self.boss_attack_frame == 1 else 1

            is_visible = getattr(self, 'can_see', True)
            if hasattr(self, 'ray_cast'): is_visible = self.ray_cast()
            elif hasattr(self, 'check_visibility'): is_visible = self.check_visibility()

            if is_visible:
                if hasattr(self, 'sound_mg_fire') and self.sound_mg_fire:
                    self.sound_mg_fire.play()
                if hasattr(self.game.player, 'take_damage'):
                    self.game.player.take_damage(8) # Безопасный урон пули
                print(f"💥 [TERM-Пулемет] Очередь! Пуль осталось: {self.mg_shots_left}")

            if self.mg_shots_left > 0:
                self.mg_next_shot_time = now + 140
            else:
                self.boss_internal_state = "CHASE"
                self.state = "CHASE"
                self.last_shot = now
                attack_in_progress = False

    # АТАКА №2: Залп тяжелой красной плазмой (Снаряд STAR)
    elif self.boss_internal_state == "ATTACK_PLASMA":
        attack_in_progress = True
        
        # Определяем, какой чистый кадр плазмотрона сейчас должен быть на экране
        custom_sprite_key = "shoot_front_plasma_0" if self.boss_attack_frame == 1 else "attack_front_plasma_0"

        if now >= self.plasma_charge_end_time:
            if hasattr(self, 'sound_plasma_fire') and self.sound_plasma_fire:
                self.sound_plasma_fire.play()
                
            print("🔴 [TERM-Плазма] Вылет красной сферы STAR.")
            self.boss_attack_frame = 1 
            
            strike_angle = math.atan2(self.game.player.y - self.y, self.game.player.x - self.x)
            ball = TermPlasmaBall(
                game=self.game, boss=self, x=self.x, y=self.y, angle=strike_angle,
                speed=0.12, fly_frames=self.boss_star_fly, explosion_frames=self.boss_star_exp, damage=35
            )
            self.boss_projectiles.append(ball)
            
            self.boss_internal_state = "CHASE"
            self.state = "CHASE"
            self.last_shot = now
            attack_in_progress = False

    # --- НАВИГАЦИЯ И КУБИК МАРКОВА (ЕСЛИ БОСС НЕ ЗАНЯТ СТРЕЛЬБОЙ) ---
    if not attack_in_progress:
        if dist_to_player <= self.shoot_range and (now - self.last_shot >= self.shoot_delay):
            self.boss_attack_timer = now
            
            # Кубик Маркова 50% / 50%
            if random.random() < 0.50:
                print("🤖 [Марков ИИ] Выброшено 50% -> Пулеметный шквал!")
                self.boss_internal_state = "ATTACK_MG"
                self.state = "ATTACK"
                if hasattr(self, 'sound_mg_start') and self.sound_mg_start:
                    self.sound_mg_start.play()
                self.mg_shots_left = 4
                self.mg_next_shot_time = now + 400
                self.boss_attack_frame = 0 
            else:
                print("🤖 [Марков ИИ] Выброшено 50% -> Энергозаряд плазмотрона!")
                self.boss_internal_state = "ATTACK_PLASMA"
                self.state = "ATTACK"
                if hasattr(self, 'sound_plasma_start') and self.sound_plasma_start:
                    self.sound_plasma_start.play()
                self.plasma_charge_end_time = now + 600
                self.boss_attack_frame = 0 
        else:
            # Преследование игрока по каньону
            self.boss_internal_state = "CHASE"
            self.state = "CHASE"
            if hasattr(self, 'update_state'):
                self.update_state(0.016)
            else:
                angle = math.atan2(self.game.player.y - self.y, self.game.player.x - self.x)
                self.x += self.speed * math.cos(angle)
                self.y += self.speed * math.sin(angle)

    # ==================================================================
    # 🔥 ЖЕСТКИЙ ПРИНУДИТЕЛЬНЫЙ ФИКС ПОКРАСНЕНИЯ (ПЕРЕХВАТ СВОЙСТВА self.image)
    # ==================================================================
    # Если босс прямо сейчас ведет огонь, мы ХАРДКОДНО записываем чистый, неиспорченный клон 
    # боевого кадра из словаря sprites прямо в self.image, полностью затирая любые 
    # попытки базового рендерера оставить маску боли!
    if attack_in_progress and custom_sprite_key and hasattr(self, 'animator') and custom_sprite_key in self.animator.sprites:
        self.image = self.animator.sprites[custom_sprite_key].copy()
    else:
        # Если босс просто бежит, пускай спокойно тикает базовый аниматор 8-направленных поворотов
        if hasattr(self, 'animator'):
            self.animator.update()
            self.image = self.animator.current_image

    # Обновляем физические размеры для проекционных лучей стен
    if self.image:
        self.sprite_width, self.sprite_height = self.image.get_size()
        self.sprite_ratio = self.sprite_width / self.sprite_height


def boss_term_personal_animator_update(self_animator):
    """Кастомный аниматор Терминатора с глубокой лог-диагностикой для отлова покраснения"""
    print("Аниматор работает")
    npc = self_animator.npc
    now = pygame.time.get_ticks()

    if npc.state == "DEAD":
        self_animator.base_animator_update_func()
        return

    # ==================================================================
    # 🔍 СИСТЕМА ДИАТНОСТИКИ КРАСНOГО ЗАЛИПАНИЯ (БЬЕТ РАЗ В 500 МС ПРИ АТАКЕ)
    # ==================================================================
    if npc.boss_internal_state in ["ATTACK_MG", "ATTACK_PLASMA"] and (not hasattr(npc, 'last_log_time') or now - npc.last_log_time > 500):
        npc.last_log_time = now
        print(f"\n🚨 [МЕТРИКА ПОКРАСНЕНИЯ] Сканирую свойства босса TERM:")
        print(f"  -> Системный стейт (npc.state): '{npc.state}'")
        print(f"  -> Внутренний ИИ-стейт (npc.boss_internal_state): '{npc.boss_internal_state}'")
        
        # Сканируем вообще ВСЕ возможные скрытые флаги боли из твоего базового движка NPC
        possible_hurt_flags = ['pain', 'hurt', 'hit', 'is_hit', 'was_hit', 'damage', 'take_damage', 'red', 'flash_red']
        found_flags = {f: getattr(npc, f, 'НЕТУ') for f in possible_hurt_flags}
        print(f"  -> Поиск флагов боли в объекте NPC: {found_flags}")
        
        # Проверяем, есть ли скрытые свойства у самого аниматора (таймеры или альфа-каналы маски)
        anim_flags = ['pain_duration', 'hurt_timer', 'red_alpha', 'alpha', 'color_tint']
        found_anim = {f: getattr(self_animator, f, 'НЕТУ') for f in anim_flags}
        print(f"  -> Поиск флагов в объекте Аниматора: {found_anim}")
        
        # Проверяем, не подменяется ли глобальный стейт аниматора (например, self_animator.state)
        if hasattr(self_animator, 'state'):
            print(f"  -> Стейт самого аниматора (self_animator.state): '{self_animator.state}'")
        print(f"  -> Текущий обрабатываемый кадр атаки (boss_attack_frame): {npc.boss_attack_frame}\n")

    # Режим боли: даем отработать базовому движку, чтобы он попробовал смыть цвет
    if getattr(npc, 'pain', False) or npc.state in ["PAIN", "HURT", "HIT"]:
        self_animator.base_animator_update_func()
        return

    # Логика подмены кадров атаки пулемета
    if npc.boss_internal_state == "ATTACK_MG":
        key = f"shoot_front_mg_{npc.boss_attack_frame}"
        if npc.boss_attack_frame == 0: 
            key = "attack_front_mg_0"
            
        if key in self_animator.sprites:
            self_animator.current_image = self_animator.sprites[key].copy()
            return
            
    # Логика подмены кадров атаки плазмотрона
    elif npc.boss_internal_state == "ATTACK_PLASMA":
        key = "shoot_front_plasma_0" if npc.boss_attack_frame == 1 else "attack_front_plasma_0"
        if key in self_animator.sprites:
            self_animator.current_image = self_animator.sprites[key].copy()
            return

    self_animator.base_animator_update_func()


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
        
        # Выставляем хорошую, отчетливую громкость для финального босса
        for s in [npc.sound_mg_start, npc.sound_mg_fire, npc.sound_plasma_start, npc.sound_plasma_fire]:
            if s: s.set_volume(0.4)
        print("🎵 [Аудио-TERM] Все 4 звуковых файла .wav успешно инициализированы!")
    except Exception as e:
        print(f"⚠️ [Аудио-TERM] Ошибка инициализации звуков (проверь наличие .wav файлов): {e}")

    # 4. Аппаратная замена методов MethodType (Полная инкапсуляция)
    npc.base_draw_method = types.MethodType(npc.draw.__func__, npc)
    npc.draw = types.MethodType(boss_term_custom_draw, npc)
    npc.update = types.MethodType(boss_term_isolated_update, npc)
    npc.animator.base_animator_update_func = types.MethodType(npc.animator.update.__func__, npc.animator)
    npc.animator.update = types.MethodType(boss_term_personal_animator_update, npc.animator)
    
    print(f"🤖 [Патч-Успех] Инкапсулированная ИИ-логика Терминатора TERM полностью активирована в ОЗУ движка!\n")