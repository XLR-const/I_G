import pygame
import math

class FlashlightMask:
    def __init__(self, game):
        self.game = game
        self.active = True  # Проверь, чтобы было True для тестов лаборатории!
        
        # ==================================================================
        # 📐 ПАРАМЕТРЫ ДЛЯ КАЛИБРОВКИ (Укрупненные радиусы под твой экран)
        # ==================================================================
        self.inner_radius = 80   # Радиус центрального яркого пятна
        self.outer_radius = 240  # Радиус внешнего мягкого размытия
        self.darkness = 245      # Плотность тьмы по краям (от 0 до 255)
        
        self.mask_surf = None

    def _rebuild_mask(self):
        """ЧИСТЫЙ МЕТОД: Строит маску темноты через вычитание блендинга SDL,
        полностью исключая ошибки colormasks на любых видеокартах!"""
        screen_w = self.game.screen.get_width()
        screen_h = self.game.screen.get_height()
        cx, cy = screen_w // 2, screen_h // 2

        # 1. Создаем финальную маску. Флаг SRCONLY гарантирует работу альфа-канала
        self.mask_surf = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        # Заливаем экран плотной темнотой
        self.mask_surf.fill((0, 0, 0, self.darkness))

        # 2. Создаем временную поверхность для рисования луча света
        light_surf = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        light_surf.fill((0, 0, 0, 0)) # Изначально она полностью прозрачная

        # 3. Пошагово прорисовываем конус света от внешнего радиуса к внутреннему.
        # Мы рисуем круги, интенсивность цвета которых плавно растет до максимума (255)
        steps = 24
        for i in range(steps + 1):
            t = i / steps
            curr_radius = self.outer_radius - (self.outer_radius - self.inner_radius) * t
            
            # Плавно увеличиваем силу вычитания альфы (от 0 до self.darkness)
            alpha_val = int(self.darkness * t)
            pygame.draw.circle(light_surf, (0, 0, 0, alpha_val), (cx, cy), int(curr_radius))

        # Насильно вырезаем идеальный стопроцентный свет в самом центре луча
        pygame.draw.circle(light_surf, (0, 0, 0, self.darkness), (cx, cy), self.inner_radius)

        # 4. 🔥 МАГИЯ ВЫЧИТАНИЯ BLEND_RGBA_SUB:
        # Мы берем наш нарисованный конус света и ВЫЧИТАЕМ его из черной маски.
        # Там, где у света альфа-канал равен self.darkness (в центре), темнота вычтется в полный 0!
        # Образуется идеально прозрачное окно налобного фонарика с мягкими краями.
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
