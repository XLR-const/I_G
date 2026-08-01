#!/usr/bin/env python
"""Режим разработки — гибкий запуск игры с отключением компонентов"""

import sys
import os
import pygame
import math
import numpy as np
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
from core.weapon_selector import WeaponSelector
from rendering.flashlight import FlashlightMask


class DevGame:
    """Игра в режиме разработки с гибкими настройками"""

    def __init__(self, config):
        """
        Args:
            config: dict с настройками компонентов
        """
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
        
        self.weapon_selector = WeaponSelector(self)
        # UI Manager
        self.ui_manager = None
        if config.get('ui_manager', True):
            self.ui_manager = UIManager(self)
            self.ui_manager.current_state = self.ui_manager.states['PLAYING']
        else:
            print("[DevMode] UI Manager отключён — игра без меню")
        
        # Консоль
        self.console = DevConsole(self) if config.get('console', True) else None
        if self.console:
            print("[DevMode] Консоль включена (~ для открытия)")

        # Музыка
        self.music_manager = MusicManager() if config.get('music_manager', False) else None
        
        # Level Manager
        self.level_manager = LevelManager(self) if config.get('level_manager', True) else None

        # Игровые объекты
        self.player = None
        self.map = None
        self.npcs = []
        self.items = []
        self.inventory = []
        self.weapon = None
        self.particles = []
        self.exit_pos = None
        self.total_kills = 0
        self.current_level = 1
        self.level_start_time = 0
        self.projectiles = []

        # Катсцена — всегда выключена
        self.intro_player = None

        # Загружаем уровень
        if self.level_manager:
            self.load_level(self.current_level)
        self.flashlight = FlashlightMask(self)
        self.flashlight.active = True

        self._print_status()

    def _print_status(self):
        """Печатает статус запуска"""
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
        """Загружает уровень через LevelManager"""
        if not self.level_manager:
            print("[Ошибка] LevelManager отключён!")
            return

        self.level_manager.load_level(level_num)

        self.player = self.level_manager.player
        self.map = self.level_manager.map
        self.npcs = self.level_manager.npcs
        self.items = self.level_manager.items
        self.inventory = self.level_manager.inventory
        self.weapon = self.level_manager.weapon
        self.particles = self.level_manager.particles
        self.exit_pos = self.level_manager.exit_pos
        self.total_kills = self.level_manager.total_kills
        self.current_level = self.level_manager.current_level


    def update(self):
        """Обновляет состояние игры"""
        self.weapon_selector.update()
        if self.weapon_selector.active:
            return
        
        if self.player:
            self.player.update()

        if self.level_manager:
            self.level_manager.check_exit()

        if self.map:
            for door in self.map.doors:
                door.update()

        # Частицы
        self.particles = [p for p in self.particles
                          if pygame.time.get_ticks() - p.start_time < p.life_time]
        for p in self.particles:
            p.update()

        # NPC
        for npc in self.npcs:
            npc.update()

        # Предметы
        for item in self.items[:]:
            item.update(self.player)
        self.items = [item for item in self.items if item.alive]

        # Оружие
        if self.weapon:
            self.weapon.update_animation()
            
        # Снаряды
        for proj in self.projectiles:
            proj.update()
        self.projectiles = [p for p in self.projectiles if p.alive]
        

        # Стрельба
        mouse_buttons = pygame.mouse.get_pressed()
        if mouse_buttons[0] and self.weapon:
            if self.weapon.is_continuous and not self.weapon.reloading:
                self.weapon.fire()

        # Регенерация
        if self.player:
            self.player.update_regen()

        self.delta_time = self.clock.tick(FPS)

    def draw(self):
        """Отрисовывает игру"""
        if self.renderer:
            self.renderer.draw_background_panoram()

        if self.raycasting:
            self.raycasting.ray_cast()

        if self.renderer:
            self.renderer.draw_fps()

        # Сбор всех 3D объектов для сортировки
        render_queue = []
        render_queue.extend(self.npcs)
        render_queue.extend(self.items)
        render_queue.extend(self.particles)
        render_queue.extend([p for p in self.projectiles if p.alive])

        # Сортировка по дистанции
        render_queue.sort(
            key=lambda obj: math.hypot(obj.x - self.player.x, obj.y - self.player.y),
            reverse=True
        )

        # Отрисовка объектов
        for obj in render_queue:
            obj.draw()

        # Полоски HP над NPC
        visible_npcs = [npc for npc in self.npcs if npc.alive]
        visible_npcs.sort(key=lambda npc: math.hypot(npc.x - self.player.x, npc.y - self.player.y))
        
        for npc in visible_npcs:
            if self.renderer:
                if not getattr(npc, 'is_boss', False):
                    self.renderer.draw_npc_health(npc)
                else:
                    npc.draw_boss_hud()

        # Оружие
        if self.weapon:
            self.weapon.draw()

        # Интерфейс
        if self.renderer:
            self.renderer.draw_interface()
            self.renderer.draw_crosshair()

        # Консоль
        if self.console:
            self.console.draw(self.screen)
        self.weapon_selector.draw()

        pygame.display.flip()

    def handle_events(self):
        """Обрабатывает события"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # Консоль
            if self.console and self.console.active:
                self.console.handle_event(event)
                if event.type == pygame.KEYDOWN and event.key == pygame.K_BACKQUOTE:
                    self.console.toggle()
                continue

            # Открытие консоли
            if event.type == pygame.KEYDOWN and event.key == pygame.K_BACKQUOTE:
                if self.console:
                    self.console.toggle()
                    if self.console.active:
                        continue

            # UI Manager (если включён)
            if self.ui_manager:
                handled = self.ui_manager.handle_event(event)
                if handled:
                    continue

                if self.ui_manager.current_state != self.ui_manager.states['PLAYING']:
                    continue

            # Если UI выключен — ESC выходит
            if not self.ui_manager:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        print("[DevMode] Выход по ESC")
                        pygame.quit()
                        sys.exit()
                        
            # 🔥 ОБНОВЛЕННЫЙ ТАКТИЧЕСКИЙ ПЕРЕХВАТ:
            # Селектор теперь слушает и нажатия (для открытия), и отпускания (для закрытия/выбора)
            if self.weapon_selector.check_input(event):
                continue
                
            # Логика твоей стандартной стрельбы по ЛКМ (Блок else)
            if not self.weapon_selector.active:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if not self.weapon.reloading and not self.weapon.is_continuous:
                        self.weapon.fire()

            # Игровые события
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE and self.ui_manager:
                    self.ui_manager.current_state = self.ui_manager.states['PAUSE']
                    self.ui_manager.selected_option = 0

                # Смена оружия (цифры)
                if event.key == pygame.K_1:
                    self.level_manager.current_weapon_index = 0
                if event.key == pygame.K_2 and len(self.inventory) > 1:
                    self.level_manager.current_weapon_index = 1
                if event.key == pygame.K_3 and len(self.inventory) > 2:
                    self.level_manager.current_weapon_index = 2
                if event.key == pygame.K_4 and len(self.inventory) > 3:
                    self.level_manager.current_weapon_index = 3
                if event.key == pygame.K_5 and len(self.inventory) > 4:
                    self.level_manager.current_weapon_index = 4

                if self.level_manager.current_weapon_index < len(self.inventory):
                    self.weapon = self.inventory[self.level_manager.current_weapon_index]
                # Интерактивное нажатие на секретку
                if event.key == pygame.K_e:
                    # Проверяем секретные двери
                    for door in self.map.doors:
                        if door.door_type == "secret":
                            dx = self.player.x - door.x
                            dy = self.player.y - door.y
                            if math.hypot(dx, dy) < 1.3:
                                door.try_open()
                                break

                # F5 — перезагрузить уровень
                if event.key == pygame.K_F5:
                    print("🔄 Перезагрузка уровня...")
                    self.load_level(self.current_level)

            # Стрельба и колесо мыши
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and self.weapon:
                    if not self.weapon.reloading and not self.weapon.is_continuous:
                        self.weapon.fire()

                if event.button == 4:
                    self.level_manager.current_weapon_index = (
                        self.level_manager.current_weapon_index + 1
                    ) % max(1, len(self.inventory))
                    self.weapon = self.inventory[self.level_manager.current_weapon_index]
                    
                if event.button == 5:
                    self.level_manager.current_weapon_index = (
                        self.level_manager.current_weapon_index - 1
                    ) % max(1, len(self.inventory))
                    self.weapon = self.inventory[self.level_manager.current_weapon_index]

    def run(self):
        """Главный цикл"""
        while True:
            self.handle_events()

            # Музыка
            if self.music_manager and self.ui_manager:
                self.music_manager.update(self.ui_manager.current_state, self.current_level)

            # Игровой цикл
            if self.ui_manager:
                if self.ui_manager.current_state == self.ui_manager.states['PLAYING']:
                    self.update()
                    self.draw()
                else:
                    self.ui_manager.draw(self.screen)
                    pygame.display.flip()
            else:
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
    """Запуск dev_mode"""
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
