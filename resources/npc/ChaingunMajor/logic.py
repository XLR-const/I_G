import pygame
import types
from random import uniform
from core.particle import Particle

def my_custom_chaingun_attack(self):
    """Кастомная атака пулеметчика: затяжная очередь из 8 выстрелов"""
    now = pygame.time.get_ticks()
    
    if not hasattr(self, 'chain_counter'):
        self.chain_counter = 0
        self.next_chain_bullet_time = 0

    if self.chain_counter == 0:
        if now - self.last_shot < self.shoot_delay:
            return  
        else:
            self.chain_counter = 8
            self.next_chain_bullet_time = now

    if self.chain_counter > 0 and now >= self.next_chain_bullet_time:
        self.next_chain_bullet_time = now + 70  
        self.chain_counter -= 1
        
        if self.chain_counter == 0:
            self.last_shot = now

        self.state = "SHOOT"
        self.shoot_flash = 2  
        self.shoot_sound.play()

        actual_damage = int(self.damage * uniform(0.7, 1.3))
        self.game.player.take_damage(actual_damage)

        for _ in range(4):
            p_x = self.x + uniform(-0.08, 0.08)
            p_y = self.y + uniform(-0.08, 0.08)
            self.game.particles.append(
                Particle(self.game, (p_x, p_y), (255, 220, 100), uniform(0.003, 0.006))
            )

def init_logic(npc):
    """Главная точка входа для пулеметчика"""
    # Подменяем метод атаки пулеметчика через MethodType
    npc.perform_attack = types.MethodType(my_custom_chaingun_attack, npc)
