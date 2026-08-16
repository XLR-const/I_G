"""Менеджер музыки

Содержит класс MusicManager для управления фоновой музыкой в игре.
"""

import os
import pygame
from setting import *
from config.game_data import MUSIC_CONFIG


class MusicManager:
    """Менеджер для управления фоновой музыкой

    Attributes:
        current_track: Текущий играющий трек
        volume: Громкость музыки (0.0 - 1.0)
        fade_time: Время затухания в мс
    """

    def __init__(self):
        """Инициализирует MusicManager"""
        self.current_track = None
        self.volume = MASTER_VOLUME * 0.5
        self.fade_time = 500

        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

    def play(self, track_key, loop=-1):
        """Воспроизводит музыкальный трек

        Args:
            track_key: Ключ трека из MUSIC_CONFIG
            loop: Количество повторов (-1 = бесконечно)
        """
        if track_key not in MUSIC_CONFIG:
            return

        if self.current_track == track_key:
            return

        path = MUSIC_CONFIG[track_key]

        if not os.path.exists(path):
            print(f"Файл музыки не найден: {path}")
            self.stop()
            return

        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(self.volume)
            pygame.mixer.music.play(loop)
            self.current_track = track_key
        except Exception:
            self.stop()

    def stop(self, fade=False):
        """Останавливает музыку

        Args:
            fade: Плавное затухание
        """
        if fade:
            pygame.mixer.music.fadeout(self.fade_time)
        else:
            pygame.mixer.music.stop()
        self.current_track = None

    def update(self, state, level_num=1):
        """Обновляет музыку по состоянию UI

        Args:
            state: Состояние UI (число из UIManager.states)
            level_num: Номер уровня (для PLAYING)
        """
        state_music = {
            0: 'menu',       # BOOT
            1: 'menu',       # MENU
            2: 'briefing',   # BRIEFING
            5: 'level_end',  # LEVEL_END
            6: 'death',      # DEAD
        }

        if state in state_music:
            track = state_music[state]
            # Если уже играет этот трек — ничего не делаем
            if self.current_track == track:
                return
            self.play(track)

        elif state == 3:  # PLAYING
            if level_num == 1:
                self.play('level_1')
            elif level_num == 2:
                self.play('level_2')
            elif level_num == 3:
                self.play('level_3')
            elif level_num == 4:
                self.play('level_4')
            else:
                self.play('level_5')

    def set_volume(self, volume):
        """Устанавливает громкость музыки

        Args:
            volume: Громкость от 0.0 до 1.0
        """
        self.volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.volume)
