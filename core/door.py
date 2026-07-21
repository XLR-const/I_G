import pygame
import math
from setting import *
from config.game_data import SYMBOLS_CONFIG

class Door:
    """Класс двери с автоматическим открытием и секретными стенами-мимикриками"""

    def __init__(self, game, x, y, door_type="normal", required_key=None, texture=None):
        self.game = game
        self.x = float(x)
        self.y = float(y)
        
        self.door_type = str(door_type).strip().lower()      # "normal", "locked", "secret"
        self.required_key = str(required_key).strip().lower() if required_key else None
        
        # Базовая текстура из конфига (для обычных и цветных дверей)
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
            self.trigger_distance = 1.2    
            self.speed = 0.03              
            
            # 🔥 Вместо тяжелого сканирования пустой карты при старте,
            # просто ставим флаг: текстура еще не украдена!
            self.texture_id = None
            self.texture_stolen = False



    def try_open(self):
        """Метод вызывается внешним хендлером при нажатии игроком клавиши 'E' в упор"""
        if self.state == "CLOSED" and self.door_type == "secret":
            print("🎉 [СЕКРЕТ] Потайной проход обнаружен!")
            self.state = "OPENING"
            
            # 🔥 ЖЕСТКИЙ УДАР ПО КОЛЛИЗИИ: Намертво стираем секретную стену из карты стен,
            # чтобы хитбокс игрока перестал упираться в невидимую преграду!
            # Переводим координаты (которые у двери имеют сдвиг +0.5) обратно в целочисленные индексы клетки
            tile_x = int(self.x - 0.5)
            tile_y = int(self.y - 0.5)
            
            if hasattr(self.game, 'map') and hasattr(self.game.map, 'world_map'):
                if (tile_x, tile_y) in self.game.map.world_map:
                    del self.game.map.world_map[(tile_x, tile_y)]
                    print(f"🧱 [ФИЗИКА] Клетка ({tile_x}, {tile_y}) удалена из world_map. Путь свободен!")

            # Проигрываем звук открытия
            if hasattr(self.game, 'sound') and self.game.sound and hasattr(self.game.sound, 'door_open'):
                self.game.sound.door_open.play()


    def update(self):
        """Обновляет состояние двери"""
        # 🔥 ЖЕЛЕЗНЫЙ АВТОПОДБОР НА ПЕРВОМ КАДРЕ:
        # Карта уже 100% загружена в память, соседи гарантированно на месте!
        if self.door_type == "secret" and not self.texture_stolen:
            try:
                tx, ty = int(self.x), int(self.y)
                directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
                
                for dx, dy in directions:
                    nx, ny = tx + dx, ty + dy
                    if 0 <= ny < len(self.game.map.text_map) and 0 <= nx < len(self.game.map.text_map[ny]):
                        neighbor_char = str(self.game.map.text_map[ny][nx]).strip()
                        
                        if neighbor_char not in ('floor', '.', '_', 'secret_wall', 'door_normal', ''):
                            self.texture_id = neighbor_char
                            self.texture_stolen = True
                            print(f"🧱 [ГОТОВО] Секретка на первом кадре успешно украла соседа: '{neighbor_char}'")
                            break
                            
                if not self.texture_stolen:
                    # Если кругом вообще пусто, берем первую попавшуюся стену из конфига редактора
                    from config.game_data import SYMBOLS_CONFIG
                    for symbol in SYMBOLS_CONFIG:
                        if SYMBOLS_CONFIG[symbol].get('type') == 'wall':
                            self.texture_id = symbol
                            self.texture_stolen = True
                            break
            except Exception as e:
                print(f"❌ Ошибка сканера на первом кадре: {e}")
        dx = self.game.player.x - self.x
        dy = self.game.player.y - self.y
        dist = math.hypot(dx, dy)

        if self.state == "CLOSED":
            # 🔥 КРИТИЧЕСКОЕ ИЗМЕНЕНИЕ: Секретная стена ИГНОРИРУЕТ автоматическое приближение!
            if self.door_type == "secret":
                return

            # Логика для обычных автоматических дверей
            if dist < self.trigger_distance:
                if self.door_type == "locked" and self.required_key:
                    player_keys = getattr(self.game.player, 'keys_inventory', [])
                    if self.required_key in player_keys:
                        self.state = "OPENING"
                    else:
                        if pygame.time.get_ticks() % 2000 < 20:
                            print(f"[ЗАПЕРТО] Требуется {self.required_key.upper()} ключ!")
                        return
                else:
                    self.state = "OPENING"

        elif self.state == "OPENING":
            self.open_progress += self.speed
            if self.open_progress >= 1.0:
                self.open_progress = 1.0
                self.state = "OPEN"
                self.close_timer = pygame.time.get_ticks() + self.close_delay

        elif self.state == "OPEN":
            # 🔥 ФИКС: Секретная стена-мимикрик ОСТАЕТСЯ ОТКРЫТОЙ НАВСЕГДА
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
