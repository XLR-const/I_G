import pygame
import sys
from setting import *
from map import Map
from player import Player
from raycasting import RayCasting
from renderer import Renderer
from weapon import Weapon, Pistol, Shotgun, MachineGun, PlasmaGun
from weapon import Particle
from npc import NPC, Solder, Jaggernaut, Kamikaze, Boss, Lightning, Tree, Fog
from pathfinding import PathFinder
from level_manager import LevelManager
from ui_manager import UIManager
from save_system import SaveSystem
from console import DevConsole

class Game:
    def __init__(self):
        pygame.mouse.set_visible(False)
        #pygame.event.set_grab(True)
        #self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.screen = pygame.display.set_mode(RES, pygame.SCALED | pygame.FULLSCREEN)
        self.clock = pygame.time.Clock() 
        self.delta_time = 1
        self.font = pygame.font.SysFont('Arial', 30, bold=True)
        self.save_system = SaveSystem()
        self.total_kills = 0
        
        self.console = DevConsole(self)
        
        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        self.ui_manager = UIManager(self)
        self.level_manager = LevelManager(self)
        self.current_level = 1
        self.load_level(self.current_level)

        
    """
    def new_game(self):
        self.map = Map(self)
        self.player = Player(self)
        self.raycasting = RayCasting(self)
        self.renderer = Renderer(self)
        self.load_level(self.current_level)
        # Guns
        self.inventory = [Pistol(self), Shotgun(self), MachineGun(self), PlasmaGun(self)]
        gun_ammo = {
                "Pistol": 20,
                "Shotgun": 10,
                "Machine Gun": 100,
                "Plasma Gun": 5
        }
        for gun in self.inventory:
            gun.ammo = gun_ammo[gun.name]
            
        self.current_weapon_index = 0
        self.weapon = self.inventory[self.current_weapon_index]
        
        
        # NPC
        #self.npcs = [NPC(self, pos=(p[0] + 0.5, p[1] + 0.5)) for p in self.map.npc_positions]
        self.npcs = []
        for npc in self.map.npc_positions:
            if npc[-1] == '2':
                self.npcs.append(Solder(self, pos=(npc[0] + 0.5, npc[1] + 0.5)))
            if npc[-1] == '3':
                self.npcs.append(Kamikaze(self, pos=(npc[0] + 0.5, npc[1] + 0.5)))
            if npc[-1] == '4':
                self.npcs.append(Jaggernaut(self, pos=(npc[0] + 0.5, npc[1] + 0.5)))
            if npc[-1] == '5':
                self.npcs.append(Boss(self, pos=(npc[0] + 0.5, npc[1] + 0.5)))
        for npc in self.npcs:
            npc.generate_waypoints_auto(4)
            npc.state = "PATROL"
        self.pathfinder = PathFinder(self)
    """ 
          
    def load_level(self, level_num):
        '''Вся инициализация здесь'''
        import time
        start_total = time.time()
        
        print(f"\n{'='*60}")
        print(f"ЗАГРУЗКА УРОВНЯ {level_num}")
        print(f"{'='*60}")
        
        # ========== 1. ПРОВЕРКА СКИПА 2 УРОВНЯ ==========
        if level_num == 2:
            print("[1] Пропускаем 2 уровень (лесной)")
            self.current_level += 1
            return self.load_level(self.current_level)
        
        # ========== 2. СОЗДАНИЕ РЕЙКАСТИНГА (1 РАЗ) ==========
        if not hasattr(self, 'raycasting'):
            print("[2] Создание рейкастинга...")
            self.raycasting = RayCasting(self)
            self.renderer = Renderer(self)
            self.pathfinder = PathFinder(self)
            print("    Готово")
        
        # ========== 3. ЗАГРУЗКА JSON ==========
        t1 = time.time()
        print("[3] Загрузка JSON...")
        level_data = self.level_manager.load_level(level_num)
        if not level_data:
            print("    ОШИБКА: JSON не загружен")
            self.game_over()
            return
        print(f"    Загружено за {time.time()-t1:.2f}с")
        
        # ========== 4. ОЧИСТКА КЭША ==========
        if hasattr(self, 'raycasting'):
            self.raycasting.texture_cache.clear()
            print("[4] Кэш текстур очищен")
        
        # ========== 5. ПАРТИКЛЫ И СТАТЫ ==========
        self.particles = []
        self.total_kills = 0
        print("[5] Партиклы и статы сброшены")
        
        # ========== 6. КАРТА ==========
        t6 = time.time()
        print("[6] Создание карты...")
        self.map = Map(self, level_data['map_data'], level_data.get('doors', []))
        print(f"    Карта: {self.map.width}x{self.map.height}, стен: {len(self.map.world_map)}")
        print(f"    Загружено за {time.time()-t6:.2f}с")
        
        # ========== 7. ФОН ==========
        background = level_data.get('background', {})
        self.renderer.set_background(background)
        print("[7] Фон установлен")
        
        # ========== 8. ВЫХОД ==========
        self.exit_pos = self.map.get_exit_pos()
        print(f"[8] Выход: {self.exit_pos}")
        
        # ========== 9. ИГРОК ==========
        t9 = time.time()
        print("[9] Создание игрока...")
        if hasattr(self, 'player'):
            self.player.x, self.player.y = level_data['player_start']
            self.player.hp = 100
        else:
            self.player = Player(self)
            self.player.x, self.player.y = level_data['player_start']
        print(f"    Игрок на ({self.player.x}, {self.player.y}) за {time.time()-t9:.2f}с")
        
        # ========== 10. ОРУЖИЕ ==========
        t10 = time.time()
        print("[10] Создание оружия...")
        self.inventory = []
        for weapon_name in level_data.get('inventory', ['Pistol']):
            if weapon_name == 'Pistol':
                self.inventory.append(Pistol(self))
            elif weapon_name == 'Shotgun':
                self.inventory.append(Shotgun(self))
            elif weapon_name == 'Machine Gun':
                self.inventory.append(MachineGun(self))
            elif weapon_name == 'Plasma Gun':
                self.inventory.append(PlasmaGun(self))
        self.current_weapon_index = 0
        self.weapon = self.inventory[0]
        
        starting_ammo = level_data.get('starting_ammo', {})
        for gun in self.inventory:
            gun.ammo = starting_ammo.get(gun.name, 0)
        print(f"    Оружие: {[w.name for w in self.inventory]} за {time.time()-t10:.2f}с")
        
        # ========== 11. NPC (С ЗАЩИТОЙ ОТ ВИСНУТА) ==========
        t11 = time.time()
        npc_positions = list(self.map.npc_positions)
        print(f"[11] Создание NPC: {len(npc_positions)} шт.")
        
        self.npcs = []
        for i, (npc_x, npc_y, npc_type) in enumerate(npc_positions):
            x, y = npc_x + 0.5, npc_y + 0.5
            print(f"    {i+1}/{len(npc_positions)}: {npc_type} на ({x:.1f}, {y:.1f})...", end=" ", flush=True)
            
            try:
                if npc_type == 'Solder':
                    self.npcs.append(Solder(self, pos=(x, y)))
                elif npc_type == 'Kamikaze':
                    self.npcs.append(Kamikaze(self, pos=(x, y)))
                elif npc_type == 'Jaggernaut':
                    self.npcs.append(Jaggernaut(self, pos=(x, y)))
                elif npc_type == 'Boss':
                    self.npcs.append(Boss(self, pos=(x, y)))
                elif npc_type == 'Lightning':
                    self.npcs.append(Lightning(self, pos=(x, y)))
                elif npc_type == 'Tree':
                    self.npcs.append(Tree(self, pos=(x, y)))
                elif npc_type == 'Fog':
                    self.npcs.append(Fog(self, pos=(x, y)))
                else:
                    print(f"НЕИЗВЕСТНЫЙ ТИП!")
                    continue
                print("OK")
            except Exception as e:
                print(f"ОШИБКА: {e}")
                import traceback
                traceback.print_exc()
                # Не прерываем загрузку, просто пропускаем этого NPC
                continue
        
        print(f"    Создано NPC: {len(self.npcs)} за {time.time()-t11:.2f}с")
        
        # ========== 12. ПАТРУЛЬНЫЕ ТОЧКИ (С ЗАЩИТОЙ) ==========
        t12 = time.time()
        print("[12] Генерация патрульных точек...")
        for i, npc in enumerate(self.npcs):
            print(f"    {i+1}/{len(self.npcs)}: {npc.name}...", end=" ", flush=True)
            try:
                npc.generate_waypoints_auto(4)
                npc.state = "PATROL"
                print("OK")
            except Exception as e:
                print(f"ОШИБКА: {e}")
                npc.waypoints = []
                npc.state = "IDLE"
        print(f"    Готово за {time.time()-t12:.2f}с")
        
        # ========== 13. ЛЕСНОЙ УРОВЕНЬ (ОСОБЫЙ СЛУЧАЙ) ==========
        if level_num == 2:
            print("[13] Настройка лесного уровня...")
            self.start_time = pygame.time.get_ticks()
            self.level_duration = 20000
            Tree.init_spawn_points(self)
            for _ in range(10):
                tree = Tree(self)
                self.npcs.append(tree)
            print("    Готово")
        
        # ========== 14. ПОВОРОТ ИГРОКА ==========
        if level_num == 2:
            self.player.angle = math.pi * 1.5
        
        print(f"\n{'='*60}")
        print(f"УРОВЕНЬ {level_num} ЗАГРУЖЕН за {time.time()-start_total:.2f}с")
        print(f"{'='*60}\n")
            
        # Close
        #self.exit_pos = level_data.get('exit', (-1, -1))
    
        
    def next_level(self):
        """Срабатывает когда игрок в координатах выхода"""
        self.level_time = (pygame.time.get_ticks() - self.level_start_time) // 1000
        self.save_system.save(self.current_level, self.total_kills, self.level_time)
        self.ui_manager.current_state = self.ui_manager.states['LEVEL_END']
        # migrate in handle self.load_level(self.current_level)
        
    def check_exit(self):
        if not hasattr(self, 'exit_pos') or self.exit_pos is None:
            return
        
        # Проверяем расстояние до выхода (можно по клеткам)
        player_cell = (int(self.player.x), int(self.player.y))
        exit_cell = (int(self.exit_pos[0]), int(self.exit_pos[1]))
        if self.current_level == 2:
            Tree.update_spawn(self)
            
            # Проверка завершения уровня
            if not Tree.is_spawning_active() and not any(isinstance(npc, Tree) for npc in self.npcs):
                self.next_level()
        if player_cell == exit_cell:
            self.ui_manager.current_state = self.ui_manager.states['LEVEL_END']
            self.next_level()
            
    def game_over(self):
        pygame.quit()

    def reset_game(self):
        """Полный сброс игры (NEW GAME)"""
        self.save_system.delete()
        self.total_kills = 0
        self.level_time = 0
        self.current_level = 1
        self.player.hp = 100
        self.level_start_time = pygame.time.get_ticks()
        self.load_level(self.current_level)            
    
    def play_music(self):
        """Управление музыкой в зависимости от текущего состояния"""
        current_state = self.ui_manager.current_state
        # Музыка для главного меню
        if current_state == self.ui_manager.states['MENU']:
            if not hasattr(self, 'current_music') or self.current_music != 'menu':
                try:
                    pygame.mixer.music.load('resources/ui_sounds/main_menu_song.wav')
                    pygame.mixer.music.set_volume(0.4)
                    pygame.mixer.music.play(-1)
                    self.current_music = 'menu'
                    print("Музыка меню запущена")  # отладка
                except Exception as e:
                    print(f"error download: main_menu_song - {e}")
        
        # Музыка для уровня 1
        elif current_state == self.ui_manager.states['PLAYING'] and self.current_level == 1:
            if not hasattr(self, 'current_music') or self.current_music != 'level1':
                try:
                    pygame.mixer.music.load('resources/level_music/level_1.wav')
                    pygame.mixer.music.set_volume(0.5)
                    pygame.mixer.music.play(-1)
                    self.current_music = 'level1'
                    print("Музыка уровня 1 запущена")  # отладка
                except Exception as e:
                    print(f"error download: level music - {e}")
                    
        elif current_state == self.ui_manager.states['BRIEFING']:
            if not hasattr(self, 'current_music') or current_state != 'briefing':
                try:
                    pygame.mixer.music.load('resources/ui_sounds/briefing.wav')
                    pygame.mixer.music.set_volume(0.5)
                    pygame.mixer.music.play(-1)
                    self.current_music = 'briefing'
                except Exception as e:
                    print(f"error download: level music - {e}")
        
        # Останавливаем музыку при смерти или конце уровня
        elif current_state in (self.ui_manager.states['DEAD'], self.ui_manager.states['LEVEL_END']):
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
                if hasattr(self, 'current_music'):
                    delattr(self, 'current_music')
                print("Музыка остановлена")
               
    def update(self):
        self.player.update()
        self.check_exit()
        
        if self.current_level == 2:
            current_time = pygame.time.get_ticks()
            if current_time - self.level_start_time >= self.level_duration:
                self.next_level()
                return
            Tree._spawn_timer += self.delta_time
            if Tree._spawn_timer >= Tree._spawn_delay:
                Tree._spawn_timer = 0
                tree = Tree(self)
                if tree.alive:
                    self.npcs.append(tree)
        
        # Проверка зажатой ЛКМ для автоматического оружия
        mouse_buttons = pygame.mouse.get_pressed()
        if mouse_buttons[0]: # 0 - это левая кнопка
            if self.weapon.is_continuous and not self.weapon.reloading:
                self.weapon.fire()
                # self.shot_sound.play() # Если есть звук

        for door in self.map.doors:
            door.update()
        self.particles = [p for p in self.particles if pygame.time.get_ticks() - p.start_time < p.life_time]
        for p in self.particles:
            p.update()
        for npc in self.npcs:
            npc.update()
        self.delta_time = self.clock.tick(FPS)
        self.player.update_regen()
        pygame.display.set_caption(f'FPS: {self.clock.get_fps() :.1f}')
        

    def draw(self):
        #self.screen.fill('black') # Очистка экрана перед каждым кадром
        self.renderer.draw_background()
        self.raycasting.ray_cast()
        self.renderer.draw_fps()
        #self.player.draw()
        self.npcs.sort(key=lambda npc: math.hypot(npc.x - self.player.x, npc.y - self.player.y), reverse=True)
        for npc in self.npcs:
            npc.draw()
        
        for p in self.particles:
            p.draw()
        self.weapon.draw()
        self.renderer.draw_fog_filter()
        self.renderer.draw_interface()
        self.renderer.draw_crosshair()
        #self.renderer.draw_line_of_cells()
        self.console.draw(self.screen)
        
        pygame.display.flip()

    def check_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            handled = self.ui_manager.handle_event(event)
            # Если UI не обработал событие и мы в игре
            if not handled and self.ui_manager.current_state == self.ui_manager.states['PLAYING']:
                # Обработка игровых событий
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.ui_manager.current_state = self.ui_manager.states['PAUSE']
                    self.ui_manager.selected_option = 0
            
                if event.type == pygame.MOUSEBUTTONDOWN:
                    # Теперь проверяем КНОПКУ (1 - левая) и статус перезарядки
                    if event.button == 1:
                        if not self.weapon.reloading and not self.weapon.is_continuous:
                            self.weapon.fire()
                # Альтернативгая стрельба
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.weapon.fire()
                            
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1: 
                        self.current_weapon_index = 0
                    if event.key == pygame.K_2: 
                        self.current_weapon_index = 1
                    if event.key == pygame.K_3: 
                        self.current_weapon_index = 2
                    if event.key == pygame.K_4: 
                        self.current_weapon_index = 3
                    # Обновляем ссылку на активное оружие
                    if self.current_weapon_index < len(self.inventory):
                        self.weapon = self.inventory[self.current_weapon_index]
                    else:
                        self.current_weapon_index = 0

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 4: # Колесо вверх
                        self.current_weapon_index = (self.current_weapon_index + 1) % len(self.inventory)
                    if event.button == 5: # Колесо вниз
                        self.current_weapon_index = (self.current_weapon_index - 1) % len(self.inventory)
                    self.weapon = self.inventory[self.current_weapon_index]
                    
                if self.console.active:
                    self.console.handle_event(event)
                    return
                if event.type == pygame.KEYDOWN and event.key == pygame.K_BACKQUOTE:
                    self.console.toggle()


    def run(self):
        while True:
            self.check_events()
            # Обновление UI
            self.ui_manager.update()
            self.play_music()
            
            # Если в игре - обновляем игровую логику
            if self.ui_manager.current_state == self.ui_manager.states['PLAYING']:
                self.update()
                self.draw()
            else:
                # только UI
                self.ui_manager.draw(self.screen)
                pygame.display.flip()
            
            self.delta_time = self.clock.tick(FPS)


game = Game()
game.run()
