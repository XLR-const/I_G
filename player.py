import pygame as pg
import math
from setting import *

class Player:
    def __init__(self, game):
        self.game = game
        self.x, self.y = PLAYER_POS
        self.angle = PLAYER_ANGLE
        self.hp = 100
        # Сразу ставим мышь в центр при создании игрока
        pg.mouse.set_pos([WIDTH // 2, HEIGHT // 2])

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

    def draw(self):
        # Временная отрисовка луча взгляда для 2D режима
        pg.draw.line(self.game.screen, 'yellow', (self.x * TILE, self.y * TILE),
                    (self.x * TILE + WIDTH * math.cos(self.angle),
                     self.y * TILE + WIDTH * math.sin(self.angle)), 2)
        pg.draw.circle(self.game.screen, 'green', (self.x * TILE, self.y * TILE), 15)
