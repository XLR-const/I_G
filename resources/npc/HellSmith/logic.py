import os
import math
import pygame
import types
from random import uniform

# ==============================================================================
# 1. НЕЗАВИСИМЫЙ КЛАСС ЛЕТЯЩЕГО 3D-ФАЕРБОЛА БОССА
# ==============================================================================

class BossBallProjectile:
    """Огненный шар, который плавно летит, крутит анимацию и взрывается об стены"""
    def __init__(self, game, boss, x, y, angle, speed, frames, explosion_frames, damage, explosion_sound=None):
        self.game = game
        self.boss = boss  
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = speed
        self.frames = frames  
        self.explosion_frames = explosion_frames  
        self.explosion_sound = explosion_sound  # ЗАПОМИНАЕМ ЗВУК ВЗРЫВА
        self.damage = damage
        
        self.current_frame = 0
        self.anim_timer = pygame.time.get_ticks()
        self.alive = True
        self.is_exploding = False 

    def update(self):
        if not self.alive: return
        
        dt = self.game.delta_time
        if dt > 0.033: dt = 0.033

        # Если шар еще ЛЕТИТ (не взрывается)
        if not self.is_exploding:
            self.x += math.cos(self.angle) * self.speed * dt
            self.y += math.sin(self.angle) * self.speed * dt
            
            # Проверяем удар об стену
            if self.game.map.is_wall(int(self.x), int(self.y)):
                self.trigger_explosion()
                return

            # Проверяем попадание в игрока
            if math.hypot(self.game.player.x - self.x, self.game.player.y - self.y) < 0.4:
                self.game.player.take_damage(self.damage)
                self.trigger_explosion()
                return

        # Кадровая анимация
        now = pygame.time.get_ticks()
        if now - self.anim_timer > 60:
            self.anim_timer = now
            self.current_frame += 1
            
            # Если мы в режиме взрыва и дошли до конца анимации взрыва — полностью удаляем снаряд
            if self.is_exploding:
                if self.current_frame >= len(self.explosion_frames):
                    self.alive = False
            else:
                # Если просто летим — циклим кадры вихря по кругу
                self.current_frame %= len(self.frames)

    def trigger_explosion(self):
        """Включает режим покадрового взрыва об стену со звуком"""
        if self.explosion_frames:
            self.is_exploding = True
            self.speed = 0  
            self.current_frame = 0  
            
            # ИСПРАВЛЕНИЕ: Включаем кастомный звук детонации при ударе об стену!
            if self.explosion_sound:
                self.explosion_sound.play()
        else:
            self.alive = False  


    def draw(self):
        if not self.alive: return
        
        # Выбираем, какую колоду спрайтов рендерить прямо сейчас
        current_deck = self.explosion_frames if self.is_exploding else self.frames
        if not current_deck or self.current_frame >= len(current_deck): return
        
        img = current_deck[self.current_frame]
        raw_w, raw_h = img.get_size()
        
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

        dx = self.x - self.game.player.x
        dy = self.y - self.game.player.y
        dist = math.hypot(dx, dy)
        if dist < 0.2: return

        theta = math.atan2(dy, dx)
        delta = theta - self.game.player.angle
        delta = (delta + math.pi) % math.tau - math.pi
        if abs(delta) > HALF_FOV: return

        dist_flat = dist * math.cos(delta)
        if dist_flat < 0.2: return

        # Если взрывается — делаем спрайт взрыва чуть побольше (0.6), летящий шар поменьше (0.4)
        size_multiplier = 0.6 if self.is_exploding else 0.4
        proj_height = int((SCREEN_DIST / dist_flat) * size_multiplier) 
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
# 2. МЕТОДЫ ОБНОВЛЕНИЯ, ОТРИСОВКИ И ВЫСТРЕЛA БОССA
# ==============================================================================

def my_standard_boss_attack(self):
    now = pygame.time.get_ticks()
    if now - self.last_shot < self.shoot_delay:
        return

    self.last_shot = now
    self.state = "SHOOT"
    self.shoot_flash = 3  
    
    # ИСПРАВЛЕНИЕ: Глушим базовую заглушку и включаем ЧЕСТНЫЙ мощный звук залпа Босса!
    if hasattr(self, 'sound_shoulder') and self.sound_shoulder:
        self.sound_shoulder.play()

    angle_to_player = math.atan2(self.game.player.y - self.y, self.game.player.x - self.x)
    fireball_frames = getattr(self, 'boss_fireball_frames', [])
    explosion_frames = getattr(self, 'boss_explosion_frames', []) 
    
    if fireball_frames:
        # Прокидываем ссылку на звук взрыва внутрь самого фаербола
        expl_sound = getattr(self, 'sound_explosion', None)
        ball = BossBallProjectile(
            self.game, self, self.x, self.y, angle_to_player, 
            speed=4.5, frames=fireball_frames, explosion_frames=explosion_frames, 
            damage=25, explosion_sound=expl_sound  # ПЕРЕДАЕМ ЗВУК
        )
        self.boss_projectiles.append(ball)




def my_boss_custom_update(self, dt):
    """Кастомный ИИ-мостик: обновляет летящие снаряды, а затем выполняет стандартный ИИ ядра"""
    # Каждую итерацию чистим мертвые и обновляем живые фаерболы
    self.boss_projectiles = [p for p in self.boss_projectiles if p.alive]
    for proj in self.boss_projectiles:
        proj.update()

    # Сразу после этого вызываем стандартный метод перемещения и логики из ядра npc.py!
    self.update_state(dt)


def my_boss_custom_draw(self):
    """Кастомный метод отрисовки: сначала рисует самого Босса через ядро, затем поверх — его снаряды"""
    # 1. Вызываем оригинальный метод draw() из ядра, который отлично работает
    self.base_draw_method()
    
    # 2. Поверх тела Босса прорисовываем все летящие огненные шары со сверкой Z-буфера
    for proj in self.boss_projectiles:
        proj.draw()


# ==============================================================================
# 3. ТОЧКА ВХОДА ИНИЦИАЛИЗАЦИИ БОССА
# ==============================================================================

def init_logic(npc):
    """Точка входа Этапа 2.1. Инициализирует контейнеры и перехватывает draw/update/attack"""
    # Создаем локальный изолированный список для фаерболов прямо внутри Босса
    npc.boss_projectiles = []
    npc.boss_fireball_frames = []
    scale = npc.scale
    try:
        npc.sound_shoulder = pygame.mixer.Sound(os.path.join(npc.folder_path, 'sound_shoulder.wav'))
        npc.sound_explosion = pygame.mixer.Sound(os.path.join(npc.folder_path, 'sound_explosion.wav'))
        
        # Выставляем громкость босса
        npc.sound_shoulder.set_volume(0.15)
        npc.sound_explosion.set_volume(0.15)
    except Exception as e:
        print(f"[БОСС] Кастомное аудио не найдено, используем дефолт: {e}")
        npc.sound_shoulder = npc.shoot_sound
        npc.sound_explosion = npc.shoot_sound

    
    # Загружаем кадры вихря
    for idx in range(1, 10):
        filename = f"proj_vortex_{idx}.png"
        path = os.path.join(npc.folder_path, filename)
        if os.path.exists(path):
            original = pygame.image.load(path)
            new_w = int(original.get_width() * scale)
            new_h = int(original.get_height() * scale)
            npc.boss_fireball_frames.append(pygame.transform.scale(original, (new_w, new_h)))

    # Привязываем метод выстрела
    npc.perform_attack = types.MethodType(my_standard_boss_attack, npc)
    
    # Подключаем кастомное обновление и отрисовку через официальные мостики движка
    npc.custom_update = types.MethodType(my_boss_custom_update, npc)
    
    # Перехватываем метод draw()
    npc.base_draw_method = types.MethodType(npc.draw.__func__, npc)
    npc.draw = types.MethodType(my_boss_custom_draw, npc)
        # Прописываем в самый низ функции init_logic загрузку fx_big_explosion (5 кадров)
    npc.boss_explosion_frames = []
    for idx in range(1, 6):
        filename = f"fx_big_explosion_{idx}.png"
        path = os.path.join(npc.folder_path, filename)
        if os.path.exists(path):
            original = pygame.image.load(path)
            new_w = int(original.get_width() * scale)
            new_h = int(original.get_height() * scale)
            npc.boss_explosion_frames.append(pygame.transform.scale(original, (new_w, new_h)))

    print(f"[БОСС Этап 2.1] Изолированный вывод снарядов успешно подключен.")
