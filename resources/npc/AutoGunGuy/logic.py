import pygame
import math
from random import uniform
from core.particle import Particle

def perform_attack(self):
    """Кастомная атака автоматчика: стрельба очередями по 3 пули"""
    now = pygame.time.get_ticks()
    
    # self — это наш объект NPC. Так как мы привязали метод через MethodType,
    # мы имеем полный доступ ко всем переменным и таймерам врага.
    
    # Переменная для отслеживания очереди (создаем динамически, если её нет)
    if not hasattr(self, 'burst_counter'):
        self.burst_counter = 0
        self.next_burst_bullet_time = 0

    # Если сейчас идет задержка между ОЧЕРЕДЯМИ, проверяем глобальный таймер
    if self.burst_counter == 0:
        if now - self.last_shot < self.shoot_delay:
            return  # Еще не перезарядился между очередями
        else:
            # Начинаем новую очередь!
            self.burst_counter = 3
            self.next_burst_bullet_time = now

    # Стреляем внутри очереди по микро-таймеру (каждые 120 миллисекунд)
    if self.burst_counter > 0 and now >= self.next_burst_bullet_time:
        self.next_burst_bullet_time = now + 120  # Темп внутри очереди
        self.burst_counter -= 1
        
        # Если это была последняя пуля в очереди, запускаем большой кулдаун
        if self.burst_counter == 0:
            self.last_shot = now

        # Включаем новое FSM-состояние вспышки выстрела
        self.state = "SHOOT"
        self.shoot_flash = 3  # Время отображения кадра со вспышкой огня
        self.shoot_sound.play()

        # Честно наносим урон игроку (с небольшой случайной погрешностью урона)
        actual_damage = int(self.damage * uniform(0.8, 1.2))
        self.game.player.take_damage(actual_damage)

        # Выбиваем искры из автомата в сторону игрока
        for _ in range(6):
            p_x = self.x + uniform(-0.05, 0.05)
            p_y = self.y + uniform(-0.05, 0.05)
            self.game.particles.append(
                Particle(self.game, (p_x, p_y), (255, 180, 50), uniform(0.002, 0.005))
            )
