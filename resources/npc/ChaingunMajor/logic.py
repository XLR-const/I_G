import pygame
from random import uniform
from core.particle import Particle

def perform_attack(self):
    """Кастомная атака пулеметчика: затяжная очередь из 8 выстрелов"""
    now = pygame.time.get_ticks()
    
    # Инициализируем переменные очереди, если это первый залп
    if not hasattr(self, 'chain_counter'):
        self.chain_counter = 0
        self.next_chain_bullet_time = 0

    # Проверяем кулдаун между ДЛИННЫМИ очередями
    if self.chain_counter == 0:
        if now - self.last_shot < self.shoot_delay:
            return  # Перезаряжает ленту пулемета
        else:
            # Начинаем длинную очередь на 8 патронов!
            self.chain_counter = 8
            self.next_chain_bullet_time = now

    # Выстрелы внутри пулеметной очереди (очень частые — каждые 70 миллисекунд!)
    if self.chain_counter > 0 and now >= self.next_chain_bullet_time:
        self.next_chain_bullet_time = now + 70  # Бешеный темп стрельбы
        self.chain_counter -= 1
        
        # Если пулемет выпустил последний патрон, взводим глобальный кулдаун перезарядки
        if self.chain_counter == 0:
            self.last_shot = now

        # Включаем FSM-состояние вспышки
        self.state = "SHOOT"
        self.shoot_flash = 2  # Короткая вспышка, так как темп огня огромный
        self.shoot_sound.play()

        # Наносим урон игроку с учетом пулеметного разброса (случайный урон)
        actual_damage = int(self.damage * uniform(0.7, 1.3))
        self.game.player.take_damage(actual_damage)

        # Выбиваем плотное облако искр из пулеметного ствола
        for _ in range(4):
            p_x = self.x + uniform(-0.08, 0.08)
            p_y = self.y + uniform(-0.08, 0.08)
            self.game.particles.append(
                Particle(self.game, (p_x, p_y), (255, 220, 100), uniform(0.003, 0.006))
            )
