import pygame
import math

class FlashlightMask:
    def __init__(self, game):
        self.game = game
        self.active = True  # Проверь, чтобы было True для тестов лаборатории!
        
        # ==================================================================
        # 📐 ПАРАМЕТРЫ ДЛЯ КАЛИБРОВКИ (Укрупненные радиусы под твой экран)
        # ==================================================================
        self.inner_radius = 160   # Радиус центрального яркого пятна
        self.outer_radius = 240  # Радиус внешнего мягкого размытия
        self.darkness = 200      # Плотность тьмы по краям (от 0 до 255)
        
        self.mask_surf = None

    def _rebuild_mask(self):
        """КАНОНИЧНЫЙ МЕТОД + ТУМАН ДАЛЬНОСТИ: Ограничивает дальность луча фонаря 
        за счет базовой плотности тумана, не нагружая рэйкастинг стен!"""
        screen_w = self.game.screen.get_width()
        screen_h = self.game.screen.get_height()
        cx, cy = screen_w // 2, screen_h // 2

        # 1. Создаем финальную маску темноты
        self.mask_surf = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        self.mask_surf.fill((0, 0, 0, self.darkness))

        # 2. Создаем временную поверхность для вычитания света
        light_surf = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        light_surf.fill((0, 0, 0, 0))

        # ==================================================================
        # 🔥 АРХИТЕКТУРНЫЙ ПАРАМЕТР: ТУМАН ДАЛЬНОСТИ (FOG DENSITY)
        # Задает уровень темноты в САМОМ ЦЕНТРЕ луча фонарика (от 0 до 255).
        # Если поставить 0 — видно бесконечно далеко (как было у тебя).
        # Значение 140–160 создает идеальный эффект "короткого луча": 
        # все дальние стены и монстры гарантированно растворяются в черной мгле!
        # ==================================================================
        self.fog_density = 145  # Поиграй с этим значением (оптимально 130-160)

        # Вычисляем максимальную силу вычитания темноты для центра луча
        max_sub_alpha = self.darkness - self.fog_density

        # 3. Пошагово прорисовываем конус света от внешнего радиуса к внутреннему
        steps = 24
        for i in range(steps + 1):
            t = i / steps
            curr_radius = self.outer_radius - (self.outer_radius - self.inner_radius) * t
            
            # Сила вычитания плавно растет, но упирается в предел max_sub_alpha
            alpha_val = int(max_sub_alpha * t)
            pygame.draw.circle(light_surf, (0, 0, 0, alpha_val), (cx, cy), int(curr_radius))

        # Заливаем центр луча фиксированным значением ограничения дальности
        pygame.draw.circle(light_surf, (0, 0, 0, max_sub_alpha), (cx, cy), self.inner_radius)

        # 4. Вычитаем свет из маски темноты
        self.mask_surf.blit(light_surf, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)

    def check_debug_input(self, event):
        """ХАК ДЛЯ МГНОВЕННОЙ КАЛИБРОВКИ: Позволяет крутить радиусы кнопками в игре!"""
        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_UP:
            self.outer_radius += 15
            self._rebuild_mask()
            print(f"🔦 [Фонарь калибровка] Внешний радиус: {self.outer_radius}")
        elif event.key == pygame.K_DOWN:
            self.outer_radius = max(self.inner_radius + 15, self.outer_radius - 15)
            self._rebuild_mask()
            print(f"🔦 [Фонарь калибровка] Внешний радиус: {self.outer_radius}")
        elif event.key == pygame.K_RIGHT:
            self.inner_radius += 10
            self._rebuild_mask()
            print(f"🔦 [Фонарь калибровка] Внутренний радиус: {self.inner_radius}")
        elif event.key == pygame.K_LEFT:
            self.inner_radius = max(10, self.inner_radius - 10)
            self._rebuild_mask()
            print(f"🔦 [Фонарь калибровка] Внутренний радиус: {self.inner_radius}")

    def draw(self):
        """Накладывает готовую маску темноты поверх отрендеренного 3D мира"""
        if not self.active:
            return
            
        # Ленивая сборка при первом кадре отрисовки кадра
        if self.mask_surf is None:
            self._rebuild_mask()
            print("⚙️ [Фонарь] Полноэкранный хоррор-фильтр успешно запущен!")
            
        self.game.screen.blit(self.mask_surf, (0, 0))
