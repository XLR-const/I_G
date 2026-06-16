import json
import os
import pygame
import math
from setting import *
from core.map import Map
from core.player import Player
from core.npc import Solder, Kamikaze, Jaggernaut, Lightning, Boss
from core.weapon import Pistol, Shotgun, MachineGun, PlasmaGun


class LevelManager:
    def __init__(self, game):
        self.game = game
        
        # Переменные уровня (были в main.py)
        self.current_level = 1
        self.total_kills = 0
        self.level_start_time = 0
        self.level_time = 0
        self.exit_pos = None
        
        # Объекты уровня (были в main.py)
        self.player = None
        self.map = None
        self.npcs = []
        self.inventory = []
        self.weapon = None
        self.current_weapon_index = 0
        self.particles = []
        
        self.levels_folder = "resources/levels"

    def load_level(self, level_num):
        print(f"\n{'=' * 60}")
        print(f"ЗАГРУЗКА УРОВНЯ {level_num}")
        print(f"{'=' * 60}")

        # Загрузка JSON
        file_path = f"{self.levels_folder}/level_{level_num}.json"
        if not os.path.exists(file_path):
            print(f"Ошибка: уровень {file_path} не найден!")
            return False

        with open(file_path, 'r') as f:
            level_data = json.load(f)

        # Очистка кэша текстур
        if hasattr(self.game, 'raycasting'):
            self.game.raycasting.texture_cache.clear()

        # Сброс данных уровня
        self.particles = []
        self.total_kills = 0
        self.npcs = []

        # Создание карты
        self.map = Map(self.game, level_data['map'])

        # Установка фона
        background = level_data.get('background', {})
        self.game.renderer.set_background(background)

        # Выход
        self.exit_pos = self.map.get_exit_pos()
        print(f"Выход: {self.exit_pos}")

        # Игрок
        player_start = level_data.get('player_start', (1.5, 5))
        if self.player is None:
            self.player = Player(self.game)
        self.player.x, self.player.y = player_start
        self.player.hp = 100
        self.player.angle = 0
        print(f"Игрок на ({self.player.x}, {self.player.y})")

        # Оружие
        self.inventory = []
        for weapon_name in level_data.get('inventory', ['Pistol']):
            if weapon_name == 'Pistol':
                self.inventory.append(Pistol(self.game))
            elif weapon_name == 'Shotgun':
                self.inventory.append(Shotgun(self.game))
            elif weapon_name == 'Machine Gun':
                self.inventory.append(MachineGun(self.game))
            elif weapon_name == 'Plasma Gun':
                self.inventory.append(PlasmaGun(self.game))

        self.current_weapon_index = 0
        self.weapon = self.inventory[0]

        starting_ammo = level_data.get('starting_ammo', {})
        for gun in self.inventory:
            gun.ammo = starting_ammo.get(gun.name, 0)
        print(f"Оружие: {[w.name for w in self.inventory]}")

        # Создание NPC
        for npc_x, npc_y, npc_type in self.map.npc_positions:
            x, y = npc_x + 0.5, npc_y + 0.5

            if npc_type == '2':
                npc = Solder(self.game, pos=(x, y))
            elif npc_type == '3':
                npc = Kamikaze(self.game, pos=(x, y))
            elif npc_type == '4':
                npc = Jaggernaut(self.game, pos=(x, y))
            elif npc_type == '5':
                npc = Lightning(self.game, pos=(x, y))
            elif npc_type == '6':
                npc = Boss(self.game, pos=(x, y))
            else:
                continue

            self.npcs.append(npc)

        # Генерация патрульных точек
        for npc in self.npcs:
            try:
                npc.generate_waypoints_auto(4)
                npc.state = "PATROL"
            except Exception as e:
                print(f"Ошибка waypoints для {npc.name}: {e}")
                npc.waypoints = []
                npc.state = "IDLE"

        print(f"Уровень {level_num} загружен: {len(self.npcs)} NPC, {len(self.inventory)} оружия")
        return True

    def next_level(self):
        """Переход на следующий уровень"""
        self.level_time = (pygame.time.get_ticks() - self.level_start_time) // 1000
        # Сохранение через game.save_system
        self.game.save_system.save(self.current_level, self.total_kills, self.level_time)
        self.game.ui_manager.current_state = self.game.ui_manager.states['LEVEL_END']

    def check_exit(self):
        """Проверяет, достиг ли игрок выхода"""
        if self.exit_pos is None or self.player is None:
            return

        player_cell = (int(self.player.x), int(self.player.y))
        exit_cell = (int(self.exit_pos[0]), int(self.exit_pos[1]))

        if player_cell == exit_cell:
            self.next_level()

    def reset_game(self):
        """Полный сброс игры"""
        self.game.save_system.delete()
        self.total_kills = 0
        self.level_time = 0
        self.current_level = 1
        self.load_level(self.current_level)

    def game_over(self):
        """Завершение игры"""
        pygame.quit()