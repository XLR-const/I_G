import os
import math
import random
import pygame
import types

# Подтягиваем честные Full-HD константы твоего рейкастер-движка из логов
try:
    import setting
    SCREEN_DIST = getattr(setting, 'SCREEN_DIST', 1330.215) 
    HALF_HEIGHT = getattr(setting, 'HALF_HEIGHT', 432)
    NUM_RAYS = getattr(setting, 'NUM_RAYS', 768)       
    SCALE = getattr(setting, 'SCALE', 2)               
    HALF_NUM_RAYS = getattr(setting, 'HALF_NUM_RAYS', 384)
    DELTA_ANGLE = getattr(setting, 'DELTA_ANGLE', 0.0013)
    HALF_FOV = getattr(setting, 'HALF_FOV', 0.52)
    WIDTH = getattr(setting, 'WIDTH', 1536)            
    HEIGHT = getattr(setting, 'HEIGHT', 864)
except:
    SCREEN_DIST, HALF_HEIGHT, NUM_RAYS, SCALE = 1330.215, 432, 768, 2
    HALF_NUM_RAYS, DELTA_ANGLE, HALF_FOV = 384, 0.0013, 0.52
    WIDTH, HEIGHT = 1536, 864

# ==================================================================
# 🔴 ЛОКАЛЬНЫЙ АВТОНОМНЫЙ КЛАСС СНАРЯДА КРАСНОЙ ПЛАЗМЫ (STAR)
# ==================================================================
class TermPlasmaBall:
    def __init__(self, game, boss, x, y, angle, speed, fly_frames, explosion_frames, damage):
        self.game = game
        self.boss = boss
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = speed 
        self.fly_frames = fly_frames
        self.explosion_frames = explosion_frames
        self.damage = damage
        
        self.current_frame = 0
        self.anim_timer = pygame.time.get_ticks()
        self.alive = True
        self.is_exploding = False

    def update(self):
        if not self.alive: 
            return
        now = pygame.time.get_ticks()

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

        # Шаг баллистики на микрошагах sub-stepping
        sub_steps = 4
        step_size = self.speed / sub_steps
        
        for _ in range(sub_steps):
            self.prev_x = self.x
            self.prev_y = self.y
            
            self.x += math.cos(self.angle) * step_size
            self.y += math.sin(self.angle) * step_size

            # Коллизия со стенами
            tile_x, tile_y = int(self.x), int(self.y)
            grid = self.game.map.numeric_grid
            if 0 <= tile_x < len(grid) and 0 <= tile_y < len(grid):
                if grid[tile_y][tile_x] > 0:
                    self.trigger_explosion()
                    return

            # Коллизия с игроком
            if math.hypot(self.game.player.x - self.x, self.game.player.y - self.y) < 0.5:
                print(f"💥 [TERM-Плазма] Попадание по игроку! Нанесено: {self.damage} HP")
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
        if not self.alive: 
            return
        current_deck = self.explosion_frames if self.is_exploding else self.fly_frames
        if not current_deck or self.current_frame >= len(current_deck): 
            return
        
        img = current_deck[self.current_frame]
        raw_w, raw_h = img.get_size()
        
        dx, dy = self.x - self.game.player.x, self.y - self.game.player.y
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

        screen_x = int(WIDTH // 2 + math.tan(delta) * SCREEN_DIST)
        wall_height = int(SCREEN_DIST / dist_flat)
        
        size_factor = 0.45 if self.is_exploding else 0.3
        proj_height = int(wall_height * size_factor)
        proj_width = int(proj_height * (raw_w / raw_h))
        proj_width = int(proj_width * 0.72)

        start_x = int(screen_x - proj_width // 2)
        screen_y = HALF_HEIGHT - proj_height // 2

        center_ray = int(screen_x // SCALE)
        if 0 <= center_ray < NUM_RAYS:
            if dist_flat < self.game.raycasting.z_buffer[center_ray]:
                try:
                    scaled_img = pygame.transform.scale(img, (proj_width, proj_height))
                    self.game.screen.blit(scaled_img, (start_x, screen_y))
                except:
                    pass


# ==================================================================
# 🤖 ПОЛНОСТЬЮ ПЕРЕХВАЧЕННЫЙ КОРНЕВOЙ ЦИКЛ ОБНОВЛЕНИЯ БОССA TERM
# ==================================================================
def boss_term_isolated_update(self):
    """Кастомный корневой апдейт: заменяет метод NPC.update() со страницы 10 PDF, 
    полностью решая баги смерти и зависания красной маски боли"""
    now = pygame.time.get_ticks()
    dt = self.game.delta_time
    if dt > 0.033: 
        dt = 0.033

    # 🔥 ФИКС БАГА СМЕРТИ №1: Локальные снаряды STAR продолжают лететь и 
    # анимироваться, даже если сам Терминатор уже убит и лежит на полу коридора!
    self.boss_projectiles = [p for p in self.boss_projectiles if p.alive]
    for proj in self.boss_projectiles:
        proj.update()

    # 🔥 ФИКС БАГА СМЕРТИ №2: Если здоровье обнулилось — принудительно гасим 
    # маску боли (hurt_flash = 0) и даем оригинальному аниматору прокрутить 
    # кадры падения трупа на пол из страниц 4-5 твоей доки!
    if self.state == "DEAD" or self.hp <= 0:
        self.state = "DEAD"
        self.hurt_flash = 0
        self.shoot_flash = 0
        
        # Синхронизируем состояние с оригинальным 8-ракурсным аниматором ядра
        self.animator.update()
        self.image = self.animator.current_image
        return

    # --- СНИЖЕНИЕ ТАЙМЕРOВ ЭФФЕКТOВ (КОПИЯ СТРАНИЦЫ 10 ТВОЕГО PDF) ---
    # Принудительно уменьшаем счетчик вспышки боли на каждом кадре игры, 
    # гарантируя, что красный цвет СМOЕТСЯ вовремя, несмотря на очереди атак!
    if self.hurt_flash > 0: 
        self.hurt_flash -= 1
    if self.shoot_flash > 0: 
        self.shoot_flash -= 1

    dist_to_player = math.hypot(self.game.player.x - self.x, self.game.player.y - self.y)
    
    # Флаг ведения огня
    attack_in_progress = False

    # --- СТEЙТ-МАШИНА БОЕВЫХ РЕЖИМOВ КИБОРГА ---
    # АТАКА №1: Очередь пулемета (4 быстрых хитскан выстрела)
    if self.boss_internal_state == "ATTACK_MG":
        attack_in_progress = True
        self.state = "SHOOT" # Переключаем стейт для аниматора твоего ядра
        self.shoot_flash = 4

        if now >= self.mg_next_shot_time:
            self.mg_shots_left -= 1
            
            # Чередуем кадры дульного пламени пулемета (1 и 2)
            self.boss_attack_frame = 2 if self.boss_attack_frame == 1 else 1

            # Честная проверка видимости через DDA-лучи твоего движка стен
            is_visible = getattr(self, 'can_see', True)
            if hasattr(self, 'ray_cast'): 
                is_visible = self.ray_cast()
            elif hasattr(self, 'check_visibility'): 
                is_visible = self.check_visibility()

            if is_visible:
                if hasattr(self, 'sound_mg_fire') and self.sound_mg_fire:
                    self.sound_mg_fire.play()
                if hasattr(self.game.player, 'take_damage'):
                    self.game.player.take_damage(8) # Умеренный урон пули
                print(f"💥 [TERM-Пулемет] Выстрел очереди! Пуль осталось: {self.mg_shots_left}")

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
        self.state = "SHOOT"
        self.shoot_flash = 4

        if now >= self.plasma_charge_end_time:
            if hasattr(self, 'sound_plasma_fire') and self.sound_plasma_fire:
                self.sound_plasma_fire.play()
                
            print("🔴 [TERM-Плазма] Накопление завершено! Вылет снаряда STAR.")
            self.boss_attack_frame = 1 
            
            strike_angle = math.atan2(self.game.player.y - self.y, self.game.player.x - self.x)
            ball = TermPlasmaBall(
                game=self.game, 
                boss=self, 
                x=self.x, 
                y=self.y, 
                angle=strike_angle,
                speed=0.12, 
                fly_frames=self.boss_star_fly, 
                explosion_frames=self.boss_star_exp, 
                damage=35
            )
            self.boss_projectiles.append(ball)
            
            self.boss_internal_state = "CHASE"
            self.state = "CHASE"
            self.last_shot = now
            attack_in_progress = False

    # --- НАВИГАЦИЯ, ПРЕСЛЕДOВАНИЕ И КУБИК МАРКОВА ---
    if not attack_in_progress:
        # Если босс находится в ступоре от боли HURT со страницы 12 PDF, ждем таймер
        if self.state == "HURT":
            if now > self.state_timer:
                self.state = "CHASE"
            return

        if dist_to_player <= self.shoot_range and (now - self.last_shot >= self.shoot_delay):
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
            # Преследование и бег за игроком (Вызываем оригинальный update_state из страницы 12 PDF)
            self.boss_internal_state = "CHASE"
            if hasattr(self, 'update_state'):
                self.update_state(dt)
        
        # Синхронизируем состояние с оригинальным 8-ракурсным аниматором твоего ядра
        self.animator.update()
        
        # Записываем готовый кадр в системное свойство отображения движка
        self.image = self.animator.current_image
        if self.image:
            self.sprite_width, self.sprite_height = self.image.get_size()
            self.sprite_ratio = self.sprite_width / self.sprite_height


# ==================================================================
# 🎨 ИСПРАВЛЕННЫЙ ИНКАПСУЛИРОВАННЫЙ АНИМАТОР БOЕВЫХ КАДРOВ
# ==================================================================
def boss_term_personal_animator_update(self_animator):
    npc = self_animator.npc
    if npc.state == "DEAD":
        self_animator.base_animator_update_func()
        return

    # Если Терминатор ведет огонь, подменяем стандартную ходьбу на кадры вспышек
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

    # В режиме бега пускай работает оригинальный 8-ракурсный Doom-поворот твоего ядра!
    self_animator.base_animator_update_func()


def boss_term_custom_draw(self):
    self.base_draw_method()
    # Отрисовываем все летящие красные сферы босса в общем цикле рендерера
    for proj in self.boss_projectiles:
        proj.draw()
        
def boss_term_empty_perform_attack(self):
    """Пустая заглушка-заглушка: намертво блокирует вызов дефолтной стрельбы пулями со страницы 9 PDF, 
    не давая ядру сбрасывать Марковские стейты Терминатора в базовый SHOOT!"""
    pass



# ==================================================================
# 🏁 ТОЧКА ВХОДА ДИНАМИЧЕСКOГО ПАТЧА ИИ И АССЕТОВ БОССA TERM
# ==================================================================
def init_logic(npc):
    npc.boss_projectiles = []
    npc.boss_internal_state = "CHASE"
    npc.boss_attack_frame = 0
    npc.last_shot = 0
    scale = npc.scale
    
    # Загрузчик пакетов DOOM-спрайтов STAR для плазмы по буквам алфавита
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
    
    # Загрузчик одиночных боевых кадров пулемета и плазмы Терминатора
    def load_single_frame(key_name, file_name):
        path = os.path.join(npc.folder_path, f"{file_name}.png")
        if os.path.exists(path):
            original = pygame.image.load(path).convert_alpha()
            new_w = int(original.get_width() * scale)
            new_h = int(original.get_height() * scale)
            npc.animator.sprites[key_name] = pygame.transform.scale(original, (new_w, new_h))

    load_single_frame("attack_front_mg_0", "TERM_attack_front_mg_0")
    load_single_frame("shoot_front_mg_1", "TERM_shoot_front_mg_1")
    load_single_frame("shoot_front_mg_2", "TERM_shoot_front_mg_2")
    load_single_frame("attack_front_plasma_0", "TERM_attack_front_plasma_0")
    load_single_frame("shoot_front_plasma_0", "TERM_shoot_front_t_plasma_0")
    
    # Инициализация звукового аудио-пакета босса
    try:
        npc.sound_mg_start = pygame.mixer.Sound(os.path.join(npc.folder_path, 'sound_mg_start.wav'))
        npc.sound_mg_fire = pygame.mixer.Sound(os.path.join(npc.folder_path, 'sound_mg_fire.wav'))
        npc.sound_plasma_start = pygame.mixer.Sound(os.path.join(npc.folder_path, 'sound_plasma_start.wav'))
        npc.sound_plasma_fire = pygame.mixer.Sound(os.path.join(npc.folder_path, 'sound_plasma_fire.wav'))
        for s in [npc.sound_mg_start, npc.sound_mg_fire, npc.sound_plasma_start, npc.sound_plasma_fire]:
            if s: 
                s.set_volume(0.4)
    except:
        pass
    
    # 🔥 ЧИСТЫЙ ПЕРЕХВАТ ОБНОВЛЕНИЯ ЯДРА НАМЕРТВО:
    # Заменяем дефектный npc.update на наш кастомный метод MethodType.
    # Теперь и сброс красного цвета боли, и покадровая смерть трупа будут работать идеально!
    # ==================================================================
    # 4. Аппаратная замена методов MethodType (Полная инкапсуляция)
    # ==================================================================
    npc.base_draw_method = types.MethodType(npc.draw.__func__, npc)
    npc.draw = types.MethodType(boss_term_custom_draw, npc)
    npc.update = types.MethodType(boss_term_isolated_update, npc)
    
    # 🔥 ГЛАВНЫЙ ФИКС БОЕВОГО ЗАСТЫВАНИЯ:
    # Перегружаем оригинальный метод perform_attack со страницы 9-14 твоего PDF!
    # Теперь ядро не сможет насильно впихнуть боссу дефолтную стрельбу пулями штурмовиков.
    npc.perform_attack = types.MethodType(boss_term_empty_perform_attack, npc)
    
    npc.animator.base_animator_update_func = types.MethodType(npc.animator.update.__func__, npc.animator)
    npc.animator.update = types.MethodType(boss_term_personal_animator_update, npc.animator)

    print(f"🤖 [Патч-Успех] Кастомный ИИ, звуки, снаряды STAR и блокиратор perform_attack успешно внедрены в TERM!\n")
