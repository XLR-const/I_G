import pygame
import types
from random import uniform
from core.particle import Particle

def my_custom_burst_attack(self):
    """Кастомная атака автоматчика: стрельба очередями по 3 пули"""
    now = pygame.time.get_ticks()
    
    # Инициализируем переменные очереди, если их еще нет
    if not hasattr(self, 'burst_counter'):
        self.burst_counter = 0
        self.next_burst_bullet_time = 0

    if self.burst_counter == 0:
        if now - self.last_shot < self.shoot_delay:
            return  # Перезарядка между очередями
        else:
            self.burst_counter = 3
            self.next_burst_bullet_time = now

    if self.burst_counter > 0 and now >= self.next_burst_bullet_time:
        self.next_burst_bullet_time = now + 120  
        self.burst_counter -= 1
        
        if self.burst_counter == 0:
            self.last_shot = now

        self.state = "SHOOT"
        self.shoot_flash = 3  
        self.shoot_sound.play()

        actual_damage = int(self.damage * uniform(0.8, 1.2))
        self.game.player.take_damage(actual_damage)

        for _ in range(6):
            p_x = self.x + uniform(-0.05, 0.05)
            p_y = self.y + uniform(-0.05, 0.05)
            self.game.particles.append(
                Particle(self.game, (p_x, p_y), (255, 180, 50), uniform(0.002, 0.005))
            )

def init_logic(npc):
    """Главная точка входа, вызываемая ядром движка при спавне NPC"""
    # Намертво связываем функцию очереди с методом perform_attack конкретного NPC
    npc.perform_attack = types.MethodType(my_custom_burst_attack, npc)
