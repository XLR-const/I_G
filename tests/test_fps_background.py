import pygame
import math
import time
import os

# Инициализация минимального окружения Pygame для теста
pygame.init()
WIDTH, HEIGHT = 800, 600  # Подставь свои константы разрешения, если они другие
HALF_HEIGHT = HEIGHT // 2
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Тест производительности HUD/Фона")

# Класс-заглушка для имитации объектов игры
class DummyPlayer:
    def __init__(self):
        self.x = 3.5
        self.y = 5.2
        self.angle = 1.45
        self.speed = 1.0

class DummyGame:
    def __init__(self):
        self.screen = screen
        self.player = DummyPlayer()

class BenchmarkRenderer:
    def __init__(self):
        self.game = DummyGame()
        self.ceiling_color = (50, 50, 50)
        self.floor_color = (30, 30, 30)
        
        # Пути к твоим текстурам
        floor_path = 'resources/textures/forest_floor.png'
        ceiling_path = 'resources/textures/ceiling.png'
        
        # Безопасная загрузка
        if os.path.exists(floor_path) and os.path.exists(ceiling_path):
            self.floor_texture = pygame.image.load(floor_path).convert()
            self.ceiling_texture = pygame.image.load(ceiling_path).convert()
            print("🧱 [УСПЕХ] Тестовые текстуры успешно загружены для бэнчмарка.")
        else:
            print("❌ [ОШИБКА] Указанные текстуры не найдены! Проверь пути.")
            # Создаем временные цветные заглушки, чтобы тест не падал, если файлы заняты
            self.floor_texture = pygame.Surface((128, 128))
            self.floor_texture.fill((100, 80, 60))
            self.ceiling_texture = pygame.Surface((128, 128))
            self.ceiling_texture.fill((60, 80, 100))

    def draw_background(self):
        """Старая базовая версия (Тайлинг по мировым осям без Numba-тригонометрии)"""
        player = self.game.player
        tile_scale = 14
        
        if self.ceiling_texture:
            tex_w = self.ceiling_texture.get_width()
            tex_h = self.ceiling_texture.get_height()
            move_x = int(player.x * tile_scale) % tex_w
            move_y = int(player.y * tile_scale) % tex_h
            for x in range(-move_x, WIDTH + tex_w, tex_w):
                for y in range(-move_y, HALF_HEIGHT + 5 + tex_h, tex_h):
                    if y < HALF_HEIGHT + 5:
                        self.game.screen.blit(self.ceiling_texture, (x, y))
        else:
            pygame.draw.rect(self.game.screen, self.ceiling_color, (0, 0, WIDTH, HALF_HEIGHT + 5))

        if self.floor_texture:
            tex_w = self.floor_texture.get_width()
            tex_h = self.floor_texture.get_height()
            move_x = int(player.x * tile_scale) % tex_w
            move_y = int(player.y * tile_scale) % tex_h
            floor_start_y = HALF_HEIGHT - 5
            for x in range(-move_x, WIDTH + tex_w, tex_w):
                for y in range(floor_start_y - move_y, HEIGHT + tex_h, tex_h):
                    if y >= floor_start_y:
                        self.game.screen.blit(self.floor_texture, (x, y))
        else:
            pygame.draw.rect(self.game.screen, self.floor_color, (0, HALF_HEIGHT - 5, WIDTH, HALF_HEIGHT + 5))

    def draw_background_panoram(self):
        """Новая оптимизированная версия (Раздельные оси, аппаратный set_clip, мышь)"""
        player = self.game.player
        base_speed = getattr(player, 'speed', 1.0)
        
        scale_x = 48.0 * base_speed
        scale_y = 16.0 * base_speed 

        y_movement = player.x * scale_y
        map_x_movement = -player.y * scale_x
        mouse_turn_offset = int((player.angle / math.tau) * (WIDTH * 4.0))
        x_movement = mouse_turn_offset + int(map_x_movement)

        original_clip = self.game.screen.get_clip()

        # 1. ПОТОЛОК
        self.game.screen.set_clip(pygame.Rect(0, 0, WIDTH, HALF_HEIGHT + 5))
        if self.ceiling_texture:
            tex_w = self.ceiling_texture.get_width()
            tex_h = self.ceiling_texture.get_height()
            move_x = int(x_movement) % tex_w
            move_y = int(y_movement) % tex_h
            for x in range(-move_x, WIDTH + tex_w, tex_w):
                for y in range(-move_y, HALF_HEIGHT + 5 + tex_h, tex_h):
                    self.game.screen.blit(self.ceiling_texture, (x, y))
        else:
            pygame.draw.rect(self.game.screen, self.ceiling_color, (0, 0, WIDTH, HALF_HEIGHT + 5))

        # 2. ПОЛ
        floor_start_y = HALF_HEIGHT - 5
        self.game.screen.set_clip(pygame.Rect(0, floor_start_y, WIDTH, HEIGHT - floor_start_y))
        if self.floor_texture:
            tex_w = self.floor_texture.get_width()
            tex_h = self.floor_texture.get_height()
            move_x = int(x_movement) % tex_w
            move_y = int(-y_movement) % tex_h
            for x in range(-move_x, WIDTH + tex_w, tex_w):
                for y in range(floor_start_y - move_y, HEIGHT + tex_h, tex_h):
                    self.game.screen.blit(self.floor_texture, (x, y))
        else:
            pygame.draw.rect(self.game.screen, self.floor_color, (0, floor_start_y, WIDTH, HEIGHT - floor_start_y))

        self.game.screen.set_clip(original_clip)

def run_fps_test():
    renderer = BenchmarkRenderer()
    NUM_FRAMES = 500  # Количество итераций для точного замера
    
    print("\n⏱️ Запуск стресс-теста производительности (по 500 кадров на метод)...")
    print("============================================================")
    
    # --- ТЕСТ 1: draw_background ---
    start_time = time.time()
    for _ in range(NUM_FRAMES):
        renderer.draw_background()
        # Слегка меняем координаты, имитируя движение в игре
        renderer.game.player.x += 0.001 
    end_time = time.time()
    
    total_time_old = end_time - start_time
    fps_old = NUM_FRAMES / total_time_old
    print(f"📊 МЕТОД [draw_background]: Время: {total_time_old:.4f} сек | СРЕДНИЙ FPS: {fps_old:.1f}")

    # --- ТЕСТ 2: draw_background_panoram ---
    start_time = time.time()
    for _ in range(NUM_FRAMES):
        renderer.draw_background_panoram()
        renderer.game.player.x += 0.001
    end_time = time.time()
    
    total_time_new = end_time - start_time
    fps_new = NUM_FRAMES / total_time_new
    print(f"🚀 МЕТОД [draw_background_panoram]: Время: {total_time_new:.4f} сек | СРЕДНИЙ FPS: {fps_new:.1f}")
    print("============================================================")
    
    # Сравнение результатов
    if fps_new > fps_old:
        gain = ((fps_new - fps_old) / fps_old) * 100
        print(f"🏆 Результат: Версия _panoram БЫСТРЕЕ на {gain:.1f}% за счет аппаратного клиппинга!")
    else:
        loss = ((fps_old - fps_new) / fps_old) * 100
        print(f"📉 Результат: Версия _panoram медленнее на {loss:.1f}% из-за дополнительных математических расчетов.")

if __name__ == "__main__":
    run_fps_test()
    pygame.quit()
