"""Консоль разработчика

Содержит класс DevConsole для отладки и ввода команд во время игры.
"""

import pygame
from setting import *


class DevConsole:
    """Консоль разработчика для отладки

    Позволяет выполнять команды во время игры: менять уровень, HP, патроны,
    включать godmode и другие.

    Attributes:
        game: Объект игры
        active: Активна ли консоль
        input_text: Текст текущего ввода
        lines: Список строк истории
        max_lines: Максимальное количество строк в истории
        font: Шрифт консоли
        bg_color: Цвет фона (RGBA)
        text_color: Цвет текста
    """

    def __init__(self, game):
        """Инициализирует консоль разработчика

        Args:
            game: Объект игры
        """
        self.game = game
        self.active = False
        self.input_text = ""
        self.lines = []
        self.max_lines = 10
        self.font = pygame.font.Font(None, 24)

        self.bg_color = (0, 0, 0, 180)
        self.text_color = (0, 255, 0)

    def toggle(self):
        """Переключает состояние консоли (открыть/закрыть)"""
        self.active = not self.active
        if not self.active:
            self.input_text = ""

    def handle_event(self, event):
        """Обрабатывает события ввода в консоли

        Args:
            event: Событие pygame

        Returns:
            bool: True если событие обработано
        """
        if not self.active:
            return False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.execute_command(self.input_text)
                self.input_text = ""
                return True
            elif event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
                return True
            elif event.key in (pygame.K_ESCAPE, pygame.K_BACKQUOTE):
                self.toggle()
                return True
            else:
                char = event.unicode
                if char.isprintable():
                    self.input_text += char
                return True
        return False

    def execute_command(self, command):
        """Выполняет команду разработчика

        Args:
            command: Строка команды
        """
        self.lines.append(f"> {command}")

        if command == "help":
            self.lines.extend([
                "Доступные команды:",
                "  help - показать справку",
                "  level <число> - загрузить уровень",
                "  hp <число> - установить HP (1-100)",
                "  ammo <число> - установить патроны для текущего оружия",
                "  godmod <0/1> - включить/выключить бессмертие"
            ])

        elif command.startswith("level "):
            try:
                level = int(command[6:])
                self.game.current_level = level
                self.game.load_level(level)
                self.lines.append(f"Загружен уровень {level}")
            except Exception:
                self.lines.append("Ошибка: level <число>")

        elif command.startswith("hp "):
            try:
                hp = int(command[3:])
                hp = max(1, min(100, hp))
                self.game.level_manager.player.hp = hp
                self.lines.append(f"HP установлен на {hp}")
            except Exception:
                self.lines.append("Ошибка: hp <число>")

        elif command.startswith("ammo "):
            try:
                ammo = int(command[5:])
                ammo = max(0, ammo)
                self.game.level_manager.weapon.ammo = ammo
                self.lines.append(f"Патроны установлены на {ammo}")
            except Exception:
                self.lines.append("Ошибка: ammo <число>")

        elif command.startswith("godmod"):
            try:
                status = command[7:]
                if status == "1":
                    self.game.level_manager.player.hp = 10 ** 7
                    self.lines.append("Godmode активирован")
                elif status == "0":
                    self.game.level_manager.player.hp = 100
                    self.lines.append("Godmode деактивирован")
                else:
                    self.lines.append("Ошибка: godmod <0/1>")
            except Exception:
                self.lines.append("Ошибка: godmod <0/1>")

        elif command == "clear":
            self.lines.clear()

        else:
            self.lines.append(f"Неизвестная команда: {command}")

        if len(self.lines) > self.max_lines:
            self.lines = self.lines[-self.max_lines:]

    def draw(self, screen):
        """Рисует консоль на экране

        Args:
            screen: Экран pygame
        """
        if not self.active:
            return

        console_surface = pygame.Surface((WIDTH, HEIGHT // 2))
        console_surface.set_alpha(180)
        console_surface.fill((0, 0, 0))
        screen.blit(console_surface, (0, 0))

        y = 10
        for line in self.lines:
            text = self.font.render(line, True, self.text_color)
            screen.blit(text, (10, y))
            y += 25

        input_surface = self.font.render(f"> {self.input_text}", True, self.text_color)
        screen.blit(input_surface, (10, HEIGHT // 2 - 30))

        if pygame.time.get_ticks() % 1000 < 500:
            cursor = self.font.render("_", True, self.text_color)
            cursor_x = 10 + input_surface.get_width()
            screen.blit(cursor, (cursor_x, HEIGHT // 2 - 30))
