import os
import pygame
from config.game_data import MUSIC_CONFIG


class MusicManager:
    def __init__(self):
        self.current_track = None
        self.volume = 0.2
        self.fade_time = 500
        
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

    def play(self, track_key, loop=-1):
        """Воспроизводит музыку"""
        if track_key not in MUSIC_CONFIG:
            return
        
        # Если тот же трек — ничего не делаем
        if self.current_track == track_key:
            return
        
        path = MUSIC_CONFIG[track_key]
        
        # Если файл не существует — останавливаем текущую музыку
        if not os.path.exists(path):
            print(f"Файл музыки не найден: {path}")
            self.stop()
            return
        
        try:
            # Останавливаем старую музыку
            pygame.mixer.music.stop()
            # Загружаем новую
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(self.volume)
            pygame.mixer.music.play(loop)
            self.current_track = track_key
        except Exception as e:
            print(f"Ошибка загрузки музыки {track_key}: {e}")
            self.stop()

    def stop(self, fade=False):
        """Останавливает музыку"""
        if fade:
            pygame.mixer.music.fadeout(self.fade_time)
        else:
            pygame.mixer.music.stop()
        self.current_track = None

    def update(self, state, level_num=1):
        """Обновляет музыку по состоянию UI"""
        state_music = {
            1: 'menu',       # MENU
            2: 'briefing',   # BRIEFING
            5: 'level_end',  # LEVEL_END
            6: 'death',      # DEAD
        }
        
        if state in state_music:
            self.play(state_music[state])
        elif state == 3:
            if level_num == 1:
                self.play('level_1')
            elif level_num == 2:
                self.play('level_2')
            elif level_num == 3:
                self.play('level_3')
            else:
                self.play('level_1')
        # PAUSE (4) — ничего не делаем

    def set_volume(self, volume):
        self.volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.volume)
