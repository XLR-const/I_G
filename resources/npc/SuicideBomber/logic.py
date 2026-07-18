import os
import math
import pygame
import types

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
# 1. КЛАСС ВИЗУАЛЬНОГО ВЗРЫВА КАМИКАДЗЕ
# ==============================================================================

class BomberExplosionFX:
    def __init__(self, game, x, y, frames):
        self.game = game
        self.x = x
        self.y = y
        self.frames = frames  
        self.current_frame = 0
        self.anim_timer = pygame.time.get_ticks()
        self.alive = True

    def update(self):
        if not self.alive or not self.frames: return
        now = pygame.time.get_ticks()
        if now - self.anim_timer > 60:
            self.anim_timer = now
            self.current_frame += 1
            if self.current_frame >= len(self.frames):
                self.alive = False

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

        proj_height = int((SCREEN_DIST / dist_flat) * 0.6)
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
                        screen_y = HALF_HEIGHT + (proj_height // 2) - proj_height
                        slice_surf = img.subsurface(tex_x, 0, 1, raw_h)
                        scaled_slice = pygame.transform.scale(slice_surf, (SCALE, proj_height))
                        self.game.screen.blit(scaled_slice, (x, screen_y))


# ==============================================================================
# 2. ИЗОЛИРОВАННЫЙ UPDATE ДЛЯ ИИ СМЕРТНИКА
# ==============================================================================

def bomber_isolated_update(self):
    dt = self.game.delta_time
    if dt > 0.033: dt = 0.033
    now = pygame.time.get_ticks()

    if hasattr(self, 'bomber_fx'):
        self.bomber_fx = [fx for fx in self.bomber_fx if fx.alive]
        for fx in self.bomber_fx:
            fx.update()

    # Считываем родное обновление ИИ из ядра npc.py
    self.update_state(dt)
    self.animator.update()
    self.image = self.animator.current_image

    # ПРОГРАММНЫЙ ЦИКЛ СМЕРТИ (Если убит игроком из оружия на подлёте)
    if not self.alive or self.hp <= 0:
        self.state = "DEAD"
        # 🔥 ФИКС КРАСНОГО ЭФФЕКТА: Гасим флеш боли при гибели, чтобы труп не горел красным вечно!
        self.hurt_flash = 0
        return

    if self.hurt_flash > 0: self.hurt_flash -= 1

    # ОТЛОВ СТЕЙТА ПОГОНИ ИЗ ЯДРА
    if self.state in ("CHASE", "WALK"):
        # 🔥 ФИКС ЗВУКА: Вместо loops=-1 пускаем одиночный пронзительный вопль по таймеру раз в 900 мс!
        # Такой звук идет обычным одиночным эффектом, и ядро игры не способно его заглушить.
        if hasattr(self, 'sound_run') and self.sound_run:
            if now - getattr(self, 'bomber_cry_timer', 0) > 900:
                self.bomber_cry_timer = now
                self.sound_run.play()

    # ТРИГГЕР САМОВЗРЫВА В УПОР
    dist_to_player = math.hypot(self.game.player.x - self.x, self.game.player.y - self.y)
    if self.state == "ATTACK" or dist_to_player <= 0.6:
        self.alive = False
        self.hp = 0
        self.state = "DEAD"
        self.hurt_flash = 0 # Снимаем красноту в момент бабаха
        
        # Воспроизводим звук взрыва shot.wav
        if hasattr(self, 'sound_shot') and self.sound_shot:
            self.sound_shot.play()

        # Наносим урон игроку
        self.game.player.take_damage(45)

        # Спавним визуальные 3D-частицы взрыва
        if hasattr(self, 'bomber_expl_frames') and self.bomber_expl_frames:
            fx = BomberExplosionFX(self.game, self.x, self.y, self.bomber_expl_frames)
            self.bomber_fx.append(fx)
        return

    if self.image:
        self.sprite_width, self.sprite_height = self.image.get_size()
        self.sprite_ratio = self.sprite_width / self.sprite_height


def bomber_custom_draw(self):
    self.base_draw_method()
    if hasattr(self, 'bomber_fx'):
        for fx in self.bomber_fx:
            fx.draw()


# ==============================================================================
# 3. ТОЧКА ВХОДА ИНИЦИАЛИЗАЦИИ КАМИКАДЗЕ ЧЕРЕЗ СКРИПТЫ ДВИЖКА
# ==============================================================================

def init_logic(npc):
    npc.bomber_fx = []
    npc.bomber_cry_timer = 0
    scale = npc.scale
    
    npc.bomber_expl_frames = []
    for idx in range(1, 8):
        path = os.path.join(npc.folder_path, f"fx_mini_explosion_{idx}.png")
        if os.path.exists(path):
            original = pygame.image.load(path)
            npc.bomber_expl_frames.append(pygame.transform.scale(original, (int(original.get_width() * scale), int(original.get_height() * scale))))

    # Загружаем аудио один раз честно со склада
    try:
        npc.sound_run = pygame.mixer.Sound(os.path.join(npc.folder_path, 'run.wav'))
        npc.sound_shot = pygame.mixer.Sound(os.path.join(npc.folder_path, 'shot.wav'))
        
        npc.sound_run.set_volume(npc.sound_volume * 1.2)  
        npc.sound_shot.set_volume(npc.sound_volume * 1.4)  
    except Exception as e:
        print(f"[КАМИКАДЗЕ] Ошибка загрузки воплей: {e}")
        npc.sound_run = None
        npc.sound_shot = npc.shoot_sound

    npc.base_draw_method = types.MethodType(npc.draw.__func__, npc)
    npc.draw = types.MethodType(bomber_custom_draw, npc)
    npc.update = types.MethodType(bomber_isolated_update, npc)

    print(f"[УСПЕХ] Камикадзе SuicideBomber переведен на таймерные одиночные вопли.")
