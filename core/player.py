import pygame
import math
from setting import *


class Player:
    """Класс игрока

    Attributes:
        game: Объект игры
        x: Координата X
        y: Координата Y
        angle: Угол поворота в радианах
        hp: Здоровье
        last_damage_time: Время последнего получения урона
        regen_delay: Задержка перед регенерацией в мс
        regen_speed: Скорость регенерации HP в секунду
    """

    def __init__(self, game):
        """Инициализирует игрока"""
        self.game = game
        self.x, self.y = PLAYER_POS
        self.angle = PLAYER_ANGLE
        self.hp = 100
        self.armor = 0
        self.max_hp = 100
        self.max_armor = 100
        self.last_damage_time = 0
        self.regen_delay = 10000
        self.regen_speed = 10

        self.death_sound = pygame.mixer.Sound('resources/player/death.wav')
        self.death_sound.set_volume(0.5)
        self.damage_sound = pygame.mixer.Sound('resources/player/player_damage.wav')
        self.damage_sound.set_volume(0.5)

        pygame.mouse.set_pos([WIDTH // 2, HEIGHT // 2])

    def update_regen(self):
        """Обновляет регенерацию здоровья"""
        current_time = pygame.time.get_ticks()

        if current_time - self.last_damage_time > self.regen_delay:
            if self.hp < self.max_hp:
                self.hp += self.regen_speed * self.game.delta_time / 1000
                if self.hp > self.max_hp:
                    self.hp = self.max_hp
                    
    def heal(self, amount):
        """Лечит игрока из аптечек"""
        old_hp = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        return self.hp - old_hp

    def take_damage(self, damage):
        """Наносит урон игроку

        Args:
            damage: Количество урона
        """
        self.hp -= damage
        self.last_damage_time = pygame.time.get_ticks()

        if self.hp <= 0:
            self.hp = 0
            self.death_sound.play()
            self.game.ui_manager.current_state = self.game.ui_manager.states['DEAD']

    def movement(self):
        """Обрабатывает движение WASD"""
        sin_a = math.sin(self.angle)
        cos_a = math.cos(self.angle)
        dx, dy = 0, 0
        speed = PLAYER_SPEED * self.game.delta_time

        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:
            dx += speed * cos_a
            dy += speed * sin_a
        if keys[pygame.K_s]:
            dx += -speed * cos_a
            dy += -speed * sin_a
        if keys[pygame.K_a]:
            dx += speed * sin_a
            dy += -speed * cos_a
        if keys[pygame.K_d]:
            dx += -speed * sin_a
            dy += speed * cos_a

        self._check_collision(dx, dy)

    def _check_collision(self, dx, dy):
        """Проверяет коллизии со стенами, дверями и NPC

        Args:
            dx: Смещение по X
            dy: Смещение по Y
        """
        collision_dist = 0.6
        scale = 0.2

        can_move_x = True
        can_move_y = True

        # Проверка стен
        check_x = int(self.x + dx + (scale if dx > 0 else -scale))
        check_y = int(self.y + dy + (scale if dy > 0 else -scale))

        if (check_x, int(self.y)) in self.game.map.world_map:
            can_move_x = False
        if (int(self.x), check_y) in self.game.map.world_map:
            can_move_y = False

        # Проверка дверей
        for door in self.game.map.doors:
            door_x, door_y = int(door.x), int(door.y)

            if check_x == door_x and int(self.y) == door_y:
                if door.is_wall():
                    can_move_x = False

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
        """Обрабатывает поворот камеры от мыши"""
        mx, my = pygame.mouse.get_pos()

        if mx != WIDTH // 2:
            dx = mx - WIDTH // 2
            self.angle += dx * MOUSE_SENSITIVITY
            pygame.mouse.set_pos([WIDTH // 2, HEIGHT // 2])

    def update(self):
        """Обновляет состояние игрока"""
        self.mouse_control()
        self.movement()
        self.angle %= math.tau

        if self.hp <= 0:
            self.death_sound.play()
            self.game.ui_manager.current_state = self.game.ui_manager.states['DEAD']

    def draw(self):
        """Рисует игрока на 2D карте (для отладки)"""
        x = self.x * TILE
        y = self.y * TILE

        pygame.draw.line(self.game.screen, 'yellow',
                         (x, y),
                         (x + WIDTH * math.cos(self.angle),
                          y + WIDTH * math.sin(self.angle)), 2)
        pygame.draw.circle(self.game.screen, 'green',
                           (int(x), int(y)), 15)
