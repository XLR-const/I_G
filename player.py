import pygame as pg
import math
from setting import *

class Player:
    def __init__(self, game):
        self.game = game
        self.x, self.y = PLAYER_POS
        self.angle = PLAYER_ANGLE
        self.hp = 100
        self.last_damage_time = 0
        self.regen_delay = 10000  # 10 секунды
        self.regen_speed = 10    # 10 HP в секунду
        self.death_sound = pg.mixer.Sound('resources/player/death.wav')
        self.death_sound.set_volume(0.5)
        # Сразу ставим мышь в центр при создании игрока
        pg.mouse.set_pos([WIDTH // 2, HEIGHT // 2])

    def update_regen(self):
        """Регенерация HP"""
        current_time = pygame.time.get_ticks()
        
        if current_time - self.last_damage_time > self.regen_delay:
            if self.hp < 100:
                self.hp += self.regen_speed * self.game.delta_time / 1000
                if self.hp > 100:
                    self.hp = 100

    def take_damage(self, damage):
        """Получение урона игроком"""
        self.hp -= damage
        self.last_damage_time = pygame.time.get_ticks()  # ← сброс таймера регена
        
        if self.hp <= 0:
            self.hp = 0
            self.game.ui_manager.current_state = self.game.ui_manager.states['DEAD']
    
    def movement(self):
        # Расчет векторов движения
        sin_a = math.sin(self.angle)
        cos_a = math.cos(self.angle)
        dx, dy = 0, 0
        speed = PLAYER_SPEED * self.game.delta_time
        
        keys = pg.key.get_pressed()
        if keys[pg.K_w]:
            dx += speed * cos_a
            dy += speed * sin_a
        if keys[pg.K_s]:
            dx += -speed * cos_a
            dy += -speed * sin_a
        if keys[pg.K_a]:
            dx += speed * sin_a
            dy += -speed * cos_a
        if keys[pg.K_d]:
            dx += -speed * sin_a
            dy += speed * cos_a

        self.check_wall_collision(dx, dy)

    def check_wall_collision(self, dx, dy):
        # Коллизия: проверяем новую позицию по каждой оси отдельно для "скольжения"
        # 0.2 — это небольшой радиус игрока, чтобы не прилипать вплотную к стене
        # Радиус игрока + радиус NPC
        collision_dist = 0.6 
        
        scale = 0.2
        can_move_x = (int(self.x + dx + (scale if dx > 0 else -scale)), int(self.y)) not in self.game.map.world_map
        can_move_y = (int(self.x), int(self.y + dy + (scale if dy > 0 else -scale))) not in self.game.map.world_map

        # проверка дверей
        for door in self.game.map.doors:
            door_x, door_y = int(door.x), int(door.y)
            
            # Проверка X движения
            check_x = int(self.x + dx + (scale if dx > 0 else -scale))
            if check_x == door_x and int(self.y) == door_y:
                if door.is_wall():  # если дверь закрыта или закрывается
                    can_move_x = False
            
            # Проверка Y движения
            check_y = int(self.y + dy + (scale if dy > 0 else -scale))
            if int(self.x) == door_x and check_y == door_y:
                if door.is_wall():
                    can_move_y = False
        
        # Проверка коллизии с NPC
        for npc in self.game.npcs:
            if npc.alive:
                if math.hypot(self.x + dx - npc.x, self.y - npc.y) < collision_dist:
                    can_move_x = False
                if math.hypot(self.x - npc.x, self.y + dy - npc.y) < collision_dist:
                    can_move_y = False

        if can_move_x: 
            self.x += dx
        if can_move_y: 
            self.y += dy

    def mouse_control(self):
        mx, my = pg.mouse.get_pos()
        
        # Если мышь сдвинулась с центра
        if mx != WIDTH // 2:
            # Считаем разницу (смещение)
            dx = mx - WIDTH // 2
            # Применяем поворот (без delta_time для резкости, либо с ним для плавности)
            self.angle += dx * MOUSE_SENSITIVITY
            # Мгновенно возвращаем курсор в центр экрана
            pg.mouse.set_pos([WIDTH // 2, HEIGHT // 2])

    def update(self):
        self.mouse_control()
        self.movement()
        # Ограничиваем угол поворота от 0 до 2*PI
        self.angle %= math.tau
        
        if self.hp <= 0:
            self.death_sound.play()
            self.game.ui_manager.current_state = self.game.ui_manager.states['DEAD']

    def draw(self):
        # Временная отрисовка луча взгляда для 2D режима
        pg.draw.line(self.game.screen, 'yellow', (self.x * TILE, self.y * TILE),
                    (self.x * TILE + WIDTH * math.cos(self.angle),
                     self.y * TILE + WIDTH * math.sin(self.angle)), 2)
        pg.draw.circle(self.game.screen, 'green', (self.x * TILE, self.y * TILE), 15)
