"""Запуск видео через внешний плеер с управлением состоянием"""

import subprocess
import os


class IntroPlayer:
    """Класс для воспроизведения видео с управлением состоянием"""

    def __init__(self, game):
        self.game = game
        self.process = None
        self.is_playing = False
        self.finished = False
        self._previous_music_state = None  # для восстановления

    def play(self):
        """Запускает видео и переключает UI в состояние CUTSCENE"""
        exe_path = "resources/intro/intro.exe"

        if not os.path.exists(exe_path):
            print("[WARNING] intro.exe не найден, пропускаем")
            self._finish()
            return False

        try:
            # === ОСТАНАВЛИВАЕМ МУЗЫКУ ===
            if hasattr(self.game, 'music_manager'):
                self.game.music_manager.stop()
                self._previous_music_state = 'stopped'
                print("[INFO] Музыка остановлена для катсцены")

            # Переключаем UI в катсцену
            self.game.ui_manager.current_state = self.game.ui_manager.states['CUTSCENE']
            self.is_playing = True
            self.finished = False

            self.process = subprocess.Popen(
                [exe_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
            return True
        except Exception as e:
            print(f"[ERROR] Не удалось запустить интро: {e}")
            self._finish()
            return False

    def update(self):
        """Проверяет статус видео (вызывается из main.py каждый кадр)"""
        if not self.is_playing or self.finished:
            return

        if self.process is not None and self.process.poll() is not None:
            self._finish()

    def skip(self):
        """Пропускает видео (вызывается из main.py при нажатии клавиши)"""
        if self.process is not None and self.is_playing:
            try:
                self.process.terminate()
                self.process = None
            except:
                pass
            self._finish()
            return True
        return False

    def _finish(self):
        """Внутренний метод завершения видео"""
        self.is_playing = False
        self.finished = True
        self.process = None

        # === ВКЛЮЧАЕМ МУЗЫКУ ОБРАТНО ===
        if hasattr(self.game, 'music_manager'):
            # Запускаем музыку меню после катсцены
            self.game.music_manager.play('menu')
            print("[INFO] Музыка возобновлена после катсцены")

        # Переход на брифинг
        self.game.ui_manager.current_state = self.game.ui_manager.states['BRIEFING']
        print("[INFO] Катсцена завершена, переход к брифингу")

    def is_finished(self):
        """Возвращает True, если видео завершено"""
        return self.finished

    def is_active(self):
        """Возвращает True, если видео ещё идёт"""
        return self.is_playing and not self.finished
