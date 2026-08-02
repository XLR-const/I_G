import pygame
import math
import os
from setting import *

class Projectile:
    def __init__(self, game, x, y, angle, config):
        """Инициализирует физический снаряд, состыкованный с WEAPON_CONFIG"""
        self.game = game
        self.x = x
        self.y = y
        self.angle = angle
        
        # Читаем параметры строго по паспорту твоего WEAPON_CONFIG
        self.damage = config.get('damage', 75)
        self.speed = config.get('projectile_speed', 0.3)
        self.folder = config.get('folder_name', 'PLASMA')
        self.prefix_fly = config.get('prefix_fly', 'RGTR')
        self.prefix_exp = config.get('prefix_exp', 'RGTX')
        
        self.alive = True
        self.is_exploding = False 
        
        self.frame_index = 0
        self.last_anim_time = pygame.time.get_ticks()
        
        self.explosion_sound = None
        if config.get("explosive"):
            sound_path = f"resources/weapons/{self.folder}/explosive.wav"
            
            if os.path.exists(sound_path):
                try:
                    self.explosion_sound = pygame.mixer.Sound(sound_path)
                    self.explosion_sound.set_volume(0.1)
                    # Можно сразу выставить кастомную громкость, если бабах слишком громкий:
                    # self.explosion_sound.set_volume(0.8)
                except Exception as e:
                    print(f"⚠️ [Аудио] Не удалось загрузить звук взрыва {sound_path}: {e}")
        
        # Загружаем спрайты по буквам DOOM (A0, B0, C0...)
        self.fly_images = self._load_sprites(self.prefix_fly)
        self.exp_images = self._load_sprites(self.prefix_exp)
        # 🔥 ЖЕЛЕЗНЫЙ ФИКС АТРИБУТОВ (ЗАЩИТА ОТ AttributeError)
        # Вытягиваем радиус и урон взрывной волны из переданного конфига пушки
        self.splash_radius = config.get('splash_radius', 0)
        self.splash_damage = config.get('splash_damage', 0)

        
        self.current_images = self.fly_images
        self.texture = self.current_images[0] if self.current_images else None

    def _load_sprites(self, prefix):
        """Универсальный и чистый загрузчик: ищет префикс любой длины + буква + 0.png"""
        images = []
        path = f"resources/weapons/{self.folder}/"
        
        # Строго перебираем буквы латинского алфавита для фаз анимации (A, B, C, D...)
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        
        for letter in alphabet:
            # Математически точная склейка по твоему правилу:
            # префикс (любой длины) + буква (кадр) + 0 (угол) + расширение
            file_name = f"{path}{prefix}{letter}0.png"
            
            if os.path.exists(file_name):
                try:
                    img = pygame.image.load(file_name).convert_alpha()
                    images.append(img)
                except Exception as e:
                    print(f"❌ [Снаряд] Ошибка чтения {file_name}: {e}")
            else:
                # Если цепочка букв на диске прервалась — анимация полностью собрана
                break

        # Железная страховка от пустых папок
        if not images:
            print(f"🚨 [КРИТ] Файлы по правилу '{prefix}[A-Z]0.png' не найдены в '{path}'!")
            dummy = pygame.Surface((16, 16), pygame.SRCALPHA)
            pygame.draw.circle(dummy, (0, 255, 0), (8, 8), 6) # Зеленый шар БФГ
            images.append(dummy)
            
        return images


    def update(self):
        """Обновление логики, микрофизики sub-stepping и коллизий снаряда"""
        if not self.alive: 
            return
            
        current_time = pygame.time.get_ticks()
        
        # 1. АНИМАЦИЯ КАДРОВ
        anim_delay = 40 if self.is_exploding else 70
        if current_time - self.last_anim_time > anim_delay:
            if self.current_images:
                if self.is_exploding:
                    if self.frame_index < len(self.current_images) - 1:
                        self.frame_index += 1
                    else:
                        self.alive = False # Конец взрыва — удаляем объект из ОЗУ
                else:
                    self.frame_index = (self.frame_index + 1) % len(self.current_images)
                self.last_anim_time = current_time

        if self.current_images and self.frame_index < len(self.current_images):
            self.texture = self.current_images[self.frame_index]

        # Если снаряд уже детерминирован и взрывается — физику и коллизии отключаем
        if self.is_exploding: 
            return

        # 2. МИКРОШАГИ ДЛЯ ИСКЛЮЧЕНИЯ ПРОЛЕТОВ СКВОЗЬ СТЕНЫ И NPC
        sub_steps = 4
        step_speed = self.speed / sub_steps
        
        for _ in range(sub_steps):
            self.prev_x = self.x
            self.prev_y = self.y
            
            next_x = self.x + step_speed * math.cos(self.angle)
            next_y = self.y + step_speed * math.sin(self.angle)

            # --- ПРОВЕРКА КОЛЛИЗИИ С ПЛОТЬЮ NPC (ИСПРАВЛЕНО ПОД ТВОЙ self.game.npcs) ---
            if hasattr(self.game, 'npcs') and self.game.npcs:
                for npc in self.game.npcs:
                    # Проверяем, жив ли монстр по твоему свойству npc.alive из PDF
                    is_dead = (hasattr(npc, 'alive') and not npc.alive) or \
                              (hasattr(npc, 'state') and npc.state == "DEAD") or \
                              (hasattr(npc, 'hp') and npc.hp <= 0)
                              
                    if is_dead: 
                        continue

                    # Вычисляем расстояние от микрошага до центра NPC
                    dist_to_npc = math.hypot(npc.x - next_x, npc.y - next_y)
                    if dist_to_npc < 0.55:
                        print(f"💥 [Попадание] Плазма пробила плоть {npc.name}! Наношу: {self.damage} урона.")
                        
                        # Вызываем твой честный метод get_damage(damage) из страницы 8 PDF
                        if hasattr(npc, 'get_damage'):
                            npc.get_damage(self.damage)
                            
                        self.trigger_explosion()
                        return

            # --- ПРОВЕРКА КОЛЛИЗИИ СО СТЕНАМИ В NUMERIC_GRID ---
            tile_x = int(next_x)
            tile_y = int(next_y)
            
            grid_h = len(self.game.map.numeric_grid)
            grid_w = len(self.game.map.numeric_grid) if grid_h > 0 else 0

            if 0 <= tile_x < grid_w and 0 <= tile_y < grid_h:
                cell_value = self.game.map.numeric_grid[tile_y][tile_x]
                door_id = getattr(self.game.raycasting, 'door_id', -1)
                
                if cell_value > 0:
                    if cell_value == door_id:
                        door_offset = self.game.map.door_states[tile_y][tile_x]
                        if door_offset < 0.5: # Врезаемся, если дверь закрыта
                            self.trigger_explosion()
                            return
                    else:
                        self.trigger_explosion()
                        return

            # Сдвигаем снаряд на безопасный шаг
            self.x = next_x
            self.y = next_y

    def trigger_explosion(self):
        """Переключает снаряд в режим взрыва и мгновенно бьет радиальным Splash-уроном по площади"""
        if self.is_exploding: 
            return
            
        self.is_exploding = True
        self.frame_index = 0
        self.current_images = self.exp_images
        self.texture = self.current_images if self.current_images else None
        
        self.texture = self.current_images[0] if self.current_images else None
        
        if self.explosion_sound is not None:
            try:
                self.explosion_sound.play()
            except Exception as e:
                print(f"❌ [Аудио] Ошибка при воспроизведении звука взрыва: {e}")
        
        
        # Выталкиваем координаты взрыва на чистый пол, чтобы вспышка не утопала в стенах
        if hasattr(self, 'prev_x'):
            self.x = self.prev_x
            self.y = self.prev_y

        # ==================================================================
        # 🔥 РАДИАЛЬНЫЙ МАССОВЫЙ УРОН (SPLASH DAMAGE) В ТОЧКЕ ДЕТОНАЦИИ
        # ==================================================================
        # Если у пушки, которая выпустила этот снаряд, прописан радиус взрыва
        if self.splash_radius > 0 and self.splash_damage > 0:
            print(f"💥 [ДЕТОНАЦИЯ] Снаряд разорвался! Запуск волны в радиусе {self.splash_radius} кл.")
            
            # Берем твой системный список живых монстров из dev_mode.py
            if hasattr(self.game, 'npcs') and self.game.npcs:
                for npc in self.game.npcs:
                    # Пропускаем мертвых
                    is_dead = (hasattr(npc, 'alive') and not npc.alive) or \
                              (hasattr(npc, 'state') and npc.state == "DEAD") or \
                              (hasattr(npc, 'hp') and npc.hp <= 0)
                    if is_dead: 
                        continue

                    # Считаем расстояние от точки взрыва (куда прилетел шар) до текущего NPC
                    dist = math.hypot(npc.x - self.x, npc.y - self.y)

                    # Если штурмовик оказался внутри зоны взрывной волны БФГ
                    if dist <= self.splash_radius:
                        # Урон падает с расстоянием: 100% в эпицентре, 0% на самом краю радиуса
                        # Мягкое затухание: даже на самом краю взрывной волны враг получит ощутимый урон
                        damage_dropoff = 1.0 - (dist / self.splash_radius) * 0.5  # Зажимаем падение в 2 раза
                        #final_splash_damage = int(self.splash_damage * damage_dropoff)
                        final_splash_damage = self.splash_damage

                        if final_splash_damage > 0:
                            print(f"  -> Взрыв задел {npc.name}! Дистанция: {dist:.2f} кл. Нанесено: {final_splash_damage} HP")
                            
                            # Наносим урон через твой родной метод боли из PDF!
                            if hasattr(npc, 'get_damage'):
                                npc.get_damage(final_splash_damage)

                            # ЭФФЕКТ УДАРНОЙ ВОЛНЫ: Физически раскидываем выживших в стороны от взрыва
                            dx_push = npc.x - self.x
                            dy_push = npc.y - self.y
                            dist_push = math.hypot(dx_push, dy_push)
                            if dist_push > 0:
                                # Сила толчка зависит от близости к эпицентру
                                npc.x += (dx_push / dist_push) * (0.4 * damage_dropoff)
                                npc.y += (dy_push / dist_push) * (0.4 * damage_dropoff)


    def draw(self):
        """Рендерит снаряд целиком с ручной компенсацией аппаратного растяжения экрана"""
        if not self.alive or not self.texture:
            return

        dx = self.x - self.game.player.x
        dy = self.y - self.game.player.y
        dist = math.hypot(dx, dy)

        if dist < 0.1: 
            return

        theta = math.atan2(dy, dx)
        delta = theta - self.game.player.angle
        
        while delta > math.pi: delta -= math.tau
        while delta < -math.pi: delta += math.tau
        
        if abs(delta) > HALF_FOV + 0.4: 
            return

        dist_flat = dist * math.cos(delta)
        if dist_flat < 0.1: 
            return

        # 🔥 КОРРЕКЦИЯ SCREEN_DIST: Пересчитываем константу строго под твою ширину WIDTH = 1536
        # Это страхует от рассинхрона углов в setting.py
        local_screen_dist = (WIDTH // 2) / math.tan(HALF_FOV)

        # Находим экранный центр снаряда
        screen_x = int(WIDTH // 2 + math.tan(delta) * local_screen_dist)

        # Вертикальный расчет высоты
        wall_height = int(local_screen_dist / dist_flat)
        size_factor = 0.35 if self.is_exploding else 0.25
        proj_height = int(wall_height * size_factor)
        if proj_height < 2: 
            return

        raw_w, raw_h = self.texture.get_size()
        current_ratio = raw_w / raw_h
        
        # Базовая теоретическая ширина
        base_width = int(proj_height * current_ratio)
        
        # ==================================================================
        # 🔥 ГЛАВНЫЙ ФИКС: АНТИ-РАСТЯЖЕНИЕ (КОМПЕНСАТОР ПРОПОРЦИЙ МОНИТОРА)
        # ==================================================================
        # Так как твой движок или флаг SCALED принудительно растягивает картинку вширь,
        # мы умышленно СЖИМАЕМ ширину снаряда на множитель 0.75 (минус 25% ширины).
        # На чистом полотне он будет казаться узким, но на твоем экране он станет ИДЕАЛЬНО КРУГЛЫМ!
        # Если покажется слишком узким — поставь 0.8, если все еще широковат — поставь 0.7.
        proj_width = int(base_width * 0.72)
        if proj_width < 2: 
            proj_width = 2

        start_x = int(screen_x - proj_width // 2)
        screen_y = HALF_HEIGHT - proj_height // 2

        # Сверка с Z-буфером для скрытия за углами
        center_ray = int(screen_x // SCALE)
        if 0 <= center_ray < NUM_RAYS:
            if dist_flat > self.game.raycasting.z_buffer[center_ray] + 0.3:
                return

        try:
            # Масштабируем сжатый по горизонтали спрайт
            scaled_projectile = pygame.transform.scale(self.texture, (proj_width, proj_height))
            # Выводим на экран
            self.game.screen.blit(scaled_projectile, (start_x, screen_y))
        except Exception as e:
            print(f"❌ [Рендер] Ошибка blit снаряда: {e}")
