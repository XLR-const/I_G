#!/usr/bin/env python
"""Режим разработки — гибкий запуск игры с отключением компонентов"""

import sys
import os
import pygame
import math
from setting import *
from rendering.raycasting import RayCasting
from rendering.renderer import Renderer
from utils.pathfinding import PathFinder
from utils.level_manager import LevelManager
from utils.music_manager import MusicManager
from ui.ui_manager import UIManager
from utils.save_system import SaveSystem
from ui.console import DevConsole
from utils.intro_player import IntroPlayer


class DevGame:
    """Игра в режиме разработки с гибкими настройками"""

    def __init__(self, config):
        self.config = config
        
        pygame.mouse.set_visible(False)
        self.screen = pygame.display.set_mode(RES, pygame.SCALED | pygame.FULLSCREEN)
        self.clock = pygame.time.Clock()
        self.delta_time = 1
        self.font = pygame.font.SysFont('Arial', 30, bold=True)

        # Компоненты
        self.save_system = SaveSystem() if config.get('save_system', True) else None
        self.raycasting = RayCasting(self) if config.get('raycasting', True) else None
        self.renderer = Renderer(self) if config.get('renderer', True) else None
        self.pathfinder = PathFinder(self) if config.get('pathfinder', True) else None

        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        
        # UI Manager
        self.ui_manager = None
        if config.get('ui_manager', True):
            self.ui_manager = UIManager(self)
            self.ui_manager.current_state = self.ui_manager.states['PLAYING']
        else:
            print("[DevMode] UI Manager отключён — игра без меню")
        
        # КОНСОЛЬ — ВСЕГДА ВКЛЮЧЕНА (если не отключена явно)
        self.console = DevConsole(self) if config.get('console', True) else None
        if self.console:
            print("[DevMode] Консоль включена (~ для открытия)")

        self.music_manager = MusicManager() if config.get('music_manager', False) else None
        self.level_manager = LevelManager(self) if config.get('level_manager', True) else None

        # Игровые объекты
        self.player = None
        self.map = None
        self.npcs = []
        self.inventory = []
        self.weapon = None
        self.particles = []
        self.exit_pos = None
        self.total_kills = 0
        self.current_level = 1
        self.level_start_time = 0

        self.intro_player = None

        self.load_level(self.current_level)

        self._print_status()

    def _print_status(self):
        print("\n" + "=" * 60)
        print("  🛠️  РЕЖИМ РАЗРАБОТКИ")
        print("=" * 60)
        print("\n  Включенные компоненты:")
        for key, value in self.config.items():
            status = "✅" if value else "❌"
            print(f"    {status} {key}")
        
        if not self.config.get('ui_manager', True):
            print("\n  ⚠️  UI Manager отключён — ESC для выхода")
        
        if not self.config.get('music_manager', False):
            print("  🔇 Музыка отключена")
        
        if self.console:
            print("  ⌨️  Консоль: ~ (тильда) для открытия")
        
        print("=" * 60 + "\n")

    def load_level(self, level_num):
        if not self.level_manager:
            print("[Ошибка] LevelManager отключён!")
            return

        self.level_manager.load_level(level_num)

        self.player = self.level_manager.player
        self.map = self.level_manager.map
        self.npcs = self.level_manager.npcs
        self.inventory = self.level_manager.inventory
        self.weapon = self.level_manager.weapon
        self.particles = self.level_manager.particles
        self.exit_pos = self.level_manager.exit_pos
        self.total_kills = self.level_manager.total_kills
        self.current_level = self.level_manager.current_level
        self.level_start_time = self.level_manager.level_start_time

    def update(self):
        if self.player:
            self.player.update()

        if self.level_manager:
            self.level_manager.check_exit()

        if self.map:
            for door in self.map.doors:
                door.update()

        self.particles = [p for p in self.particles
                          if pygame.time.get_ticks() - p.start_time < p.life_time]
        for p in self.particles:
            p.update()

        for npc in self.npcs:
            npc.update()

        if self.weapon:
            self.weapon.update_animation()

        mouse_buttons = pygame.mouse.get_pressed()
        if mouse_buttons[0] and self.weapon:
            if self.weapon.is_continuous and not self.weapon.reloading:
                self.weapon.fire()

        if self.player:
            self.player.update_regen()

        self.delta_time = self.clock.tick(FPS)

    def draw(self):
        if self.renderer:
            self.renderer.draw_background()

        if self.raycasting:
            self.raycasting.ray_cast()

        if self.renderer:
            self.renderer.draw_fps()

        if self.npcs:
            self.npcs.sort(key=lambda npc: math.hypot(
                npc.x - self.player.x, npc.y - self.player.y), reverse=True)
            for npc in self.npcs:
                npc.draw()
                if npc.alive and self.renderer:
                    if not getattr(npc, 'is_boss', False):
                        self.renderer.draw_npc_health(npc)
                    else:
                        npc.draw_boss_hud()

        for p in self.particles:
            p.draw()

        if self.weapon:
            self.weapon.draw()

        if self.renderer:
            self.renderer.draw_interface()
            self.renderer.draw_crosshair()

        # КОНСОЛЬ — ВСЕГДА ПОВЕРХ ВСЕГО
        if self.console:
            self.console.draw(self.screen)

        pygame.display.flip()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # ============================================================
            # КОНСОЛЬ — ПЕРВЫЙ ПРИОРИТЕТ
            # ============================================================
            if self.console and self.console.active:
                self.console.handle_event(event)
                # Проверяем, не нажата ли тильда для закрытия консоли
                if event.type == pygame.KEYDOWN and event.key == pygame.K_BACKQUOTE:
                    self.console.toggle()
                continue

            # ============================================================
            # ОТКРЫТИЕ КОНСОЛИ (тильда)
            # ============================================================
            if event.type == pygame.KEYDOWN and event.key == pygame.K_BACKQUOTE:
                if self.console:
                    self.console.toggle()
                    # Если консоль открылась — пропускаем событие дальше
                    if self.console.active:
                        continue

            # ============================================================
            # ОБЫЧНЫЕ СОБЫТИЯ (только если консоль не активна)
            # ============================================================

            # UI Manager (если включён)
            if self.ui_manager:
                # Пропускаем события через UI Manager
                handled = self.ui_manager.handle_event(event)
                if handled:
                    continue

                # Если UI не в PLAYING — рисуем UI и не обрабатываем игру
                if self.ui_manager.current_state != self.ui_manager.states['PLAYING']:
                    continue

            # Если UI выключен — ESC выходит
            if not self.ui_manager:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        print("[DevMode] Выход по ESC")
                        pygame.quit()
                        sys.exit()

            # Игровые события
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE and self.ui_manager:
                    self.ui_manager.current_state = self.ui_manager.states['PAUSE']
                    self.ui_manager.selected_option = 0

                # Смена оружия
                if event.key == pygame.K_1:
                    self.level_manager.current_weapon_index = 0
                if event.key == pygame.K_2 and len(self.inventory) > 1:
                    self.level_manager.current_weapon_index = 1
                if event.key == pygame.K_3 and len(self.inventory) > 2:
                    self.level_manager.current_weapon_index = 2
                if event.key == pygame.K_4 and len(self.inventory) > 3:
                    self.level_manager.current_weapon_index = 3

                if self.level_manager.current_weapon_index < len(self.inventory):
                    self.weapon = self.inventory[self.level_manager.current_weapon_index]

                # F5 — перезагрузить уровень
                if event.key == pygame.K_F5:
                    print("🔄 Перезагрузка уровня...")
                    self.load_level(self.current_level)

            # Стрельба
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and self.weapon:
                    if not self.weapon.reloading and not self.weapon.is_continuous:
                        self.weapon.fire()

                # Колесо мыши
                if event.button == 4:
                    self.level_manager.current_weapon_index = (
                        self.level_manager.current_weapon_index + 1
                    ) % len(self.inventory)
                if event.button == 5:
                    self.level_manager.current_weapon_index = (
                        self.level_manager.current_weapon_index - 1
                    ) % len(self.inventory)
                self.weapon = self.inventory[self.level_manager.current_weapon_index]

    def run(self):
        while True:
            self.handle_events()

            if self.music_manager and self.ui_manager:
                self.music_manager.update(self.ui_manager.current_state, self.current_level)

            if self.ui_manager:
                if self.ui_manager.current_state == self.ui_manager.states['PLAYING']:
                    self.update()
                    self.draw()
                else:
                    self.ui_manager.draw(self.screen)
                    pygame.display.flip()
            else:
                # Без UI — всегда в игре
                self.update()
                self.draw()

            self.delta_time = self.clock.tick(FPS)


def get_user_config():
    """Запрашивает у пользователя настройки компонентов"""
    print("\n" + "=" * 60)
    print("  🛠️  НАСТРОЙКА РЕЖИМА РАЗРАБОТКИ")
    print("=" * 60)
    print("\n  По умолчанию: все компоненты включены, кроме музыки и UI.")
    print("-" * 60)

    config = {
        'save_system': True,
        'raycasting': True,
        'renderer': True,
        'pathfinder': True,
        'level_manager': True,
        'console': True,
        'ui_manager': False,
        'music_manager': False,
    }

    print("\n  ❓ Настройка компонентов:")
    print("  (y — включить, n — выключить, Enter — оставить по умолчанию)")

    # UI Manager
    prompt = "    UI Manager (меню, пауза) [n]: "
    choice = input(prompt).strip().lower()
    if choice == 'y':
        config['ui_manager'] = True
    elif choice == 'n':
        config['ui_manager'] = False

    # Музыка
    prompt = "    Музыка [n]: "
    choice = input(prompt).strip().lower()
    if choice == 'y':
        config['music_manager'] = True
    elif choice == 'n':
        config['music_manager'] = False

    # Консоль
    prompt = "    Консоль разработчика [y]: "
    choice = input(prompt).strip().lower()
    if choice == 'n':
        config['console'] = False
    else:
        config['console'] = True

    return config


def main():
    print("\n" + "=" * 60)
    print("  🛠️  РЕЖИМ РАЗРАБОТКИ")
    print("=" * 60)

    if len(sys.argv) > 1 and sys.argv[1] == '--default':
        config = {
            'save_system': True,
            'raycasting': True,
            'renderer': True,
            'pathfinder': True,
            'level_manager': True,
            'console': True,
            'ui_manager': False,
            'music_manager': False,
        }
        print("\n  Запуск с настройками по умолчанию (без UI и музыки)...")
    else:
        config = get_user_config()

    game = DevGame(config)
    game.run()


if __name__ == "__main__":
    main()
