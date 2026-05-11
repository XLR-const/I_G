import pygame
from setting import *

class DevConsole:
    def __init__(self, game):
        self.game = game
        self.active = False
        self.input_text = ""
        self.lines = []
        self.max_lines = 10
        self.font = pygame.font.Font(None, 24)
        
        self.bg_color = (0, 0, 0, 180)
        self.text_color = (0, 255, 0)
        
    def toggle(self):
        self.active = not self.active
        if not self.active:
            self.input_text = ""
    
    def handle_event(self, event):
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
        self.lines.append(f"> {command}")
        
        if command == "help":
            self.lines.extend([
                "Доступные команды:",
                "  help - показать справку",
                "  level <число> - загрузить уровень",
                "  hp <число> - установить HP (1-100)",
                "  ammo <число> - установить патроны для текущего оружия"
            ])
        
        elif command.startswith("level "):
            try:
                level = int(command[6:])
                self.game.current_level = level
                self.game.load_level(level)
                self.lines.append(f"Загружен уровень {level}")
            except:
                self.lines.append("Ошибка: level <число>")
        
        elif command.startswith("hp "):
            try:
                hp = int(command[3:])
                hp = max(1, min(100, hp))
                self.game.player.hp = hp
                self.lines.append(f"HP установлен на {hp}")
            except:
                self.lines.append("Ошибка: hp <число>")
        
        elif command.startswith("ammo "):
            try:
                ammo = int(command[5:])
                ammo = max(0, ammo)
                self.game.weapon.ammo = ammo
                self.lines.append(f"Патроны установлены на {ammo}")
            except:
                self.lines.append("Ошибка: ammo <число>")
        
        elif command == "clear":
            self.lines.clear()
        
        else:
            self.lines.append(f"Неизвестная команда: {command}")
        
        # Ограничиваем историю
        if len(self.lines) > self.max_lines:
            self.lines = self.lines[-self.max_lines:]
    
    def draw(self, screen):
        if not self.active:
            return
        
        # Полупрозрачный фон
        console_surface = pygame.Surface((WIDTH, HEIGHT // 2))
        console_surface.set_alpha(180)
        console_surface.fill((0, 0, 0))
        screen.blit(console_surface, (0, 0))
        
        # История команд
        y = 10
        for line in self.lines:
            text = self.font.render(line, True, self.text_color)
            screen.blit(text, (10, y))
            y += 25
        
        # Строка ввода
        input_surface = self.font.render(f"> {self.input_text}", True, self.text_color)
        screen.blit(input_surface, (10, HEIGHT // 2 - 30))
        
        # Мигающий курсор
        if pygame.time.get_ticks() % 1000 < 500:
            cursor = self.font.render("_", True, self.text_color)
            cursor_x = 10 + input_surface.get_width()
            screen.blit(cursor, (cursor_x, HEIGHT // 2 - 30))