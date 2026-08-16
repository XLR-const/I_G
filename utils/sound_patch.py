# utils/sound_patch.py
import os
import pygame
import setting

# Инициализируем микшер Pygame, чтобы класс Sound гарантированно существовал в памяти
pygame.mixer.init()

# Импортируем файл настроек пользователя
import config.user_settings as us

# 1. Сохраняем оригинальный C-класс звука Pygame в надежное место
_OriginalSound = pygame.mixer.Sound

# 2. Наш кастомный класс-прокси
class SmartSound:
    """Умная Sci-Fi обертка над звуком Pygame. 
    Автоматически сохраняет баланс громкости на основе мастер-ползунка."""
    def __init__(self, *args, **kwargs):
        self._sound = _OriginalSound(*args, **kwargs)
        self.base_volume = 1.0  # Дефолтная громкость, если .set_volume не вызовут

    def set_volume(self, volume):
        """Перехватываем установку громкости: запоминаем базовый баланс звука"""
        self.base_volume = volume
        master_vol = us.USER_SETTINGS.get("MASTER_VOLUME", 1.0)
        self._sound.set_volume(self.base_volume * master_vol)

    def get_volume(self):
        return self._sound.get_volume()

    def play(self, *args, **kwargs):
        """Перехватываем воспроизведение: обновляем громкость по ползунку перед выстрелом"""
        master_vol = us.USER_SETTINGS.get("MASTER_VOLUME", 1.0)
        self._sound.set_volume(self.base_volume * master_vol)
        return self._sound.play(*args, **kwargs)

    def stop(self):
        self._sound.stop()

    def fadeout(self, time):
        self._sound.fadeout(time)

    def get_length(self):
        return self._sound.get_length()

    def get_num_channels(self):
        return self._sound.get_num_channels()

# 3. 🔥 АВТОМАТИЧЕСКИЙ ПЕРЕХВАТ ПРИ ИМПОРТЕ
# Как только main.py импортирует этот файл, оригинальный метод Pygame мгновенно подменится в ОЗУ!
pygame.mixer.Sound = SmartSound
print("⚙️ [ПАТЧ СИСТЕМЫ] Глобальный перехват микшера Pygame.mixer.Sound успешно активирован.")
