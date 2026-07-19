import pygame
import math
from setting import *
from config.game_data import *


class Door:
    """Класс двери с анимацией открытия, запертыми замками и секретными стенами-мимикриками"""

    def __init__(self, game, x, y, door_type="normal", required_key=None, texture=None):
        """Инициализирует дверь с текстурой из конфига"""
        self.game = game
        self.x = float(x)
        self.y = float(y)
        
        self.door_type = str(door_type).strip().lower()
        self.required_key = str(required_key).strip().lower() if required_key else None
        
        # 🔥 СОХРАНЯЕМ ТЕКСТУРУ ИЗ КОНФИГА: Рэйкастинг прочитает этот путь
        self.texture_id = texture 
        
        self.state = "CLOSED"
        self.open_progress = 0.0
        self.speed = 0.05
        self.trigger_distance = 1.5
        self.close_delay = 1000
        self.close_timer = 0
        self.color = (100, 100, 100)
        self.frame = 0

        # === АВТОПОДБОР ТЕКСТУРЫ ДЛЯ СЕКРЕТНЫХ СТЕН ===
        if self.door_type == "secret":
            self.trigger_distance = 1.1
            self.speed = 0.03
            
            try:
                nx = int(self.x) - 1
                ny = int(self.y)
                
                if 0 <= ny < len(self.game.map.text_map) and 0 <= nx < len(self.game.map.text_map[ny]):
                    neighbor_char = str(self.game.map.text_map[ny][nx]).strip()
                    
                    # 🔥 КРАДЕМ ТЕКСТУРУ ИЗ КОНФИГА СОСЕДА:
                    # Ищем соседа в SYMBOLS_CONFIG и забираем у него параметр 'texture'!
                    if neighbor_char in SYMBOLS_CONFIG:
                        neighbor_texture = SYMBOLS_CONFIG[neighbor_char].get('texture', None)
                        if neighbor_texture:
                            self.texture_id = neighbor_texture # Полная визуальная маскировка!
                            print(f"[СЕКРЕТ] Скопирована текстура соседа из конфига: '{neighbor_texture}'")
            except Exception as e:
                print(f"[ДВЕРЬ] Ошибка мимикрии: {e}")


    def update(self):
        """Обновляет состояние двери с учетом ключей и типов проходов"""
        dx = self.game.player.x - self.x
        dy = self.game.player.y - self.y
        dist = math.hypot(dx, dy)

        if self.state == "CLOSED":
            if dist < self.trigger_distance:
                
                # 1. ПРОВЕРКА ДЛЯ ЗАПЕРТЫХ ЦВЕТНЫХ ДВЕРЕЙ
                if self.door_type == "locked" and self.required_key:
                    player_keys = getattr(self.game.player, 'keys_inventory', [])
                    
                    if self.required_key in player_keys:
                        print(f"[ДВЕРЬ] Замок открыт {self.required_key.upper()} ключом!")
                        self.state = "OPENING"
                    else:
                        if pygame.time.get_ticks() % 2000 < 20:
                            print(f"[ЗАПЕРТО] Нужен {self.required_key.upper()} ключ!")
                        return
                
                # 2. ДЛЯ ОБЫЧНЫХ И СЕКРЕТНЫХ ДВЕРЕЙ
                else:
                    if self.door_type == "secret":
                        print("🎉 [СЕКРЕТ] Вы нашли потайной проход!")
                    self.state = "OPENING"

        elif self.state == "OPENING":
            self.open_progress += self.speed
            if self.open_progress >= 1.0:
                self.open_progress = 1.0
                self.state = "OPEN"
                self.close_timer = pygame.time.get_ticks() + self.close_delay

        elif self.state == "OPEN":
            # 🔥 ФИКС: Секретная стена никогда не закрывается сама!
            if self.door_type == "secret":
                return
                
            if dist > self.trigger_distance * 1.5:
                if pygame.time.get_ticks() > self.close_timer:
                    self.state = "CLOSING"

        elif self.state == "CLOSING":
            self.open_progress -= self.speed
            if self.open_progress <= 0.0:
                self.open_progress = 0.0
                self.state = "CLOSED"

    def is_wall(self):
        return self.state == "CLOSED" or self.state == "CLOSING"

    def get_texture_offset(self):
        if self.state == "OPENING" or self.state == "CLOSING":
            return self.open_progress
        elif self.state == "OPEN":
            return 1.0
        else:
            return 0.0
