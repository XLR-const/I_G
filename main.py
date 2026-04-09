import pygame
import math
from settings import *
from player import Player
from world import World
from raycast import cast_ray, draw_sprites
from weapons import Weapon, WeaponManager, WeaponPickup
from weapon_loader import load_weapons_from_file, create_starting_weapons

# Инициализация Pygame
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()
pygame.display.set_caption("Raycasting Demo")
pygame.mouse.set_visible(False)
pygame.event.set_grab(True)

# ========== ЗАГРУЗКА ОРУЖИЯ ==========
weapons_data = load_weapons_from_file('weapons.txt')
weapon_manager = WeaponManager()
shot_animation = 0
muzzle_flash = 0
starting_weapons = create_starting_weapons(weapons_data)
for weapon in starting_weapons:
    weapon_manager.add_weapon(weapon)

# ========== ОРУЖИЕ НА КАРТЕ ==========
weapon_pickups = [
    WeaponPickup("Shotgun", 3.5, 2.5, weapons_data),
    WeaponPickup("Rifle", 5.5, 4.5, weapons_data),
    WeaponPickup("Chaingun", 2.5, 5.5, weapons_data),
    WeaponPickup("PlasmaRifle", 6.5, 3.5, weapons_data),
    WeaponPickup("BFG9000", 4.5, 6.5, weapons_data),
]

#========ФУНКЦИИ=============
def check_weapon_pickups(player_x, player_y):
    """Проверяет подбор оружия"""
    global weapon_manager, weapon_pickups
    
    for pickup in weapon_pickups[:]:
        # Вычисляем расстояние
        dx = player_x - pickup.x
        dy = player_y - pickup.y
        distance = (dx*dx + dy*dy) ** 0.5
        
        #print(f"Distance to {pickup.weapon_name}: {distance:.2f} (radius: {pickup.radius})")
        
        if distance < pickup.radius:
            #print(f"!!! PICKING UP: {pickup.weapon_name} !!!")
            
            new_weapon = Weapon(
                pickup.weapon_name,
                pickup.damage,
                pickup.fire_rate,
                pickup.shoot_distance,
                pickup.max_ammo,
                pickup.color
            )
            weapon_manager.add_weapon(new_weapon)
            weapon_pickups.remove(pickup)
            #print(f"Weapon added! Inventory size: {len(weapon_manager.inventory)}")
def draw_texture_as_parallelogram(screen, texture, points):
    """Рисует текстуру, трансформируя её в параллелограмм"""
    if texture is None:
        return
    
    tex_width = texture.get_width()
    tex_height = texture.get_height()
    
    # Точки параллелограмма (куда нужно вписать текстуру)
    # points[0] - верх-лево, points[1] - верх-право, 
    # points[2] - низ-право, points[3] - низ-лево
    
    # Вычисляем ограничивающий прямоугольник
    min_x = min(p[0] for p in points)
    max_x = max(p[0] for p in points)
    min_y = min(p[1] for p in points)
    max_y = max(p[1] for p in points)
    
    # Создаём временную поверхность
    temp_surf = pygame.Surface((int(max_x - min_x), int(max_y - min_y)), pygame.SRCALPHA)
    
    # Масштабируем текстуру под размер
    scaled_texture = pygame.transform.scale(texture, (int(max_x - min_x), int(max_y - min_y)))
    
    # Накладываем с прозрачностью
    temp_surf.blit(scaled_texture, (0, 0))
    
    # Рисуем на экране
    screen.blit(temp_surf, (min_x, min_y))


def draw_weapon_hands(screen, weapon_name, shot_anim, weapon_textures):
    """Рисует оружие с перспективой (параллелограммом)"""
    screen_width = screen.get_width()
    screen_height = screen.get_height()
    
    # Отдача
    recoil_x = -shot_anim * 4
    recoil_y = -shot_anim * 5
    
    # Точка прицела (центр экрана)
    target_x = screen_width // 2
    target_y = screen_height // 2
    
    # Позиция приклада (правый нижний угол)
    stock_x = screen_width - 150 + recoil_x
    stock_y = screen_height - 120 + recoil_y
    
    # Вектор к прицелу
    dx = target_x - stock_x
    dy = target_y - stock_y
    length = (dx*dx + dy*dy) ** 0.5
    if length == 0:
        length = 1
    
    dir_x = dx / length
    dir_y = dy / length
    
    # Длина оружия
    weapon_length = 160
    
    # Дуло (конец оружия)
    barrel_x = stock_x + dir_x * weapon_length
    barrel_y = stock_y + dir_y * weapon_length
    
    # Толщина оружия
    thickness = 55
    
    # Перпендикуляр для толщины
    nx = -dir_y * thickness
    ny = dir_x * thickness
    
    # Четыре точки параллелограмма
    points = [
        (stock_x, stock_y),           # приклад-низ
        (stock_x + nx, stock_y + ny), # приклад-верх
        (barrel_x + nx, barrel_y + ny), # ствол-верх
        (barrel_x, barrel_y)          # ствол-низ
    ]
    
    # Пробуем загрузить текстуру
    texture = weapon_textures.get(weapon_name)
    
    if texture is not None:
        # Рисуем текстуру с трансформацией в параллелограмм
        draw_texture_as_parallelogram(screen, texture, points)
    else:
        # Fallback: цветной параллелограмм
        colors = {
            "Pistol": (100, 100, 100),
            "Shotgun": (139, 69, 19),
            "Rifle": (85, 107, 47),
            "Chaingun": (105, 105, 105),
            "PlasmaRifle": (0, 150, 0),
            "BFG9000": (128, 0, 128)
        }
        color = colors.get(weapon_name, (100, 100, 100))
        
        pygame.draw.polygon(screen, color, points)
        pygame.draw.polygon(screen, (200, 200, 200), points, 2)
        
        # Название оружия
        font = pygame.font.Font(None, 20)
        text = font.render(weapon_name, True, (255, 255, 255))
        text_rect = text.get_rect(center=(stock_x + weapon_length // 2, stock_y - 10))
        screen.blit(text, text_rect)
    
    # Эффект отдачи (белая вспышка на оружии)
    if shot_anim > 0:
        flash_surf = pygame.Surface((int(weapon_length), int(thickness)))
        flash_surf.set_alpha(80)
        flash_surf.fill((255, 255, 255))
        # Упрощённо: рисуем поверх
        screen.blit(flash_surf, (int(stock_x), int(stock_y)))
    
    # Дуло (для вспышки)
    muzzle_x = barrel_x
    muzzle_y = barrel_y
    pygame.draw.circle(screen, (80, 80, 80), (int(muzzle_x), int(muzzle_y)), 5)
    
    return (muzzle_x, muzzle_y)

def load_weapon_textures():
    """Загружает текстуры оружия из папки textures/"""
    textures = {}
    
    # Соответствие имени оружия и файла
    weapon_files = {
        "Pistol": "pistol.png",
        "Shotgun": "shotgun.png",
        "Rifle": "rifle.png",
        "Chaingun": "chaingun.png",
        "PlasmaRifle": "plasma.png",
        "BFG9000": "bfg.png"
    }
    
    for weapon_name, filename in weapon_files.items():
        try:
            path = f"textures/{filename}"
            texture = pygame.image.load(path).convert_alpha()
            # Масштабируем текстуру под размер оружия
            texture = pygame.transform.scale(texture, (180, 100))
            textures[weapon_name] = texture
            print(f"Загружена текстура: {weapon_name}")
        except:
            print(f"Не удалось загрузить текстуру для {weapon_name}, будет использован прямоугольник")
            textures[weapon_name] = None
    
    return textures
def draw_muzzle_flash(screen, flash_timer, weapon_name, shot_anim, barrel_pos):
    """Рисует вспышку из дула с трассером к прицелу"""
    if flash_timer <= 0:
        return
    
    barrel_x, barrel_y = barrel_pos
    
    # Отдача
    recoil_x = -shot_anim * 4
    recoil_y = -shot_anim * 5
    
    # Вектор к прицелу
    target_x = screen.get_width() // 2
    target_y = screen.get_height() // 2
    dx = target_x - barrel_x
    dy = target_y - barrel_y
    length = (dx*dx + dy*dy) ** 0.5
    if length == 0:
        length = 1
    
    dir_x = dx / length
    dir_y = dy / length
    
    # Вспышка вылетает по направлению к прицелу
    flash_x = barrel_x + dir_x * 15 + recoil_x
    flash_y = barrel_y + dir_y * 15 + recoil_y
    
    # Конфигурация оружия
    weapon_config = {
        "Pistol": {"size": 22, "color": (255, 200, 100)},
        "Shotgun": {"size": 35, "color": (255, 150, 50)},
        "Rifle": {"size": 20, "color": (255, 255, 150)},
        "Chaingun": {"size": 28, "color": (255, 100, 50)},
        "PlasmaRifle": {"size": 30, "color": (100, 255, 100)},
        "BFG9000": {"size": 45, "color": (255, 100, 255)}
    }
    config = weapon_config.get(weapon_name, {"size": 22, "color": (255, 200, 100)})
    
    size = config["size"]
    color = config["color"]
    
    # Вспышка
    pygame.draw.circle(screen, color, (int(flash_x), int(flash_y)), size)
    pygame.draw.circle(screen, (255, 255, 255), (int(flash_x), int(flash_y)), size // 2)
    
    # Трассер (линия от дула к прицелу)
    pygame.draw.line(screen, color, (barrel_x, barrel_y), (target_x, target_y), 4)
def draw_crosshair(screen, color):
    """Рисует прицел в центре экрана"""
    cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
    size = CROSSHAIR_SIZE
    
    # Основные линии
    pygame.draw.line(screen, color, (cx - size, cy), (cx - size//2, cy), 2)
    pygame.draw.line(screen, color, (cx + size//2, cy), (cx + size, cy), 2)
    pygame.draw.line(screen, color, (cx, cy - size), (cx, cy - size//2), 2)
    pygame.draw.line(screen, color, (cx, cy + size//2), (cx, cy + size), 2)
    
    # Точка в центре
    pygame.draw.circle(screen, color, (cx, cy), 2)
    
def draw_ui(screen, weapon_manager, player_health=100):
    """Рисует интерфейс игрока"""
    font = pygame.font.Font(None, 24)
    
    # Здоровье
    health_text = font.render(f"Health: {player_health}", True, (255, 100, 100))
    screen.blit(health_text, (10, 10))
    
    # Текущее оружие
    if weapon_manager.current_weapon:
        weapon = weapon_manager.current_weapon
        weapon_text = font.render(f"Weapon: {weapon.name}", True, (255, 255, 255))
        screen.blit(weapon_text, (10, SCREEN_HEIGHT - 60))
        
        # Патроны
        if weapon.max_ammo != -1:
            ammo_text = font.render(f"Ammo: {weapon.current_ammo}/{weapon.max_ammo}", True, (255, 255, 255))
            screen.blit(ammo_text, (10, SCREEN_HEIGHT - 35))
        else:
            ammo_text = font.render(f"Ammo: infinite", True, (200, 200, 100))
            screen.blit(ammo_text, (10, SCREEN_HEIGHT - 35))
    
    # Количество оружия в инвентаре
    inv_text = font.render(f"Weapons: {len(weapon_manager.inventory)}", True, (150, 150, 150))
    screen.blit(inv_text, (SCREEN_WIDTH - 120, 10))
def draw_pickups_on_minimap(screen, player_x, player_y):
    """Рисует мини-карту с позицией игрока и оружием"""
    minimap_size = 200
    minimap_x = SCREEN_WIDTH - minimap_size - 10
    minimap_y = 10
    cell_size = minimap_size / max(MAP_WIDTH, MAP_HEIGHT)
    
    # Рисуем фон мини-карты
    pygame.draw.rect(screen, (0, 0, 0), (minimap_x, minimap_y, minimap_size, minimap_size))
    
    # Рисуем стены
    for row in range(MAP_HEIGHT):
        for col in range(MAP_WIDTH):
            if MAP[row][col] == 1:
                rect_x = minimap_x + col * cell_size
                rect_y = minimap_y + row * cell_size
                pygame.draw.rect(screen, (100, 100, 100), (rect_x, rect_y, cell_size, cell_size))
    
    # Рисуем оружие на карте
    for pickup in weapon_pickups:
        if hasattr(pickup, 'x') and hasattr(pickup, 'y'):
            item_x = minimap_x + pickup.x * cell_size
            item_y = minimap_y + pickup.y * cell_size
            pygame.draw.rect(screen, pickup.color, (item_x, item_y, cell_size, cell_size))
            # Буква оружия
            font = pygame.font.Font(None, int(cell_size))
            text = font.render(pickup.weapon_name[0], True, (255, 255, 255))
            screen.blit(text, (item_x + 2, item_y + 2))
    
    # Рисуем игрока
    player_minimap_x = minimap_x + player_x * cell_size
    player_minimap_y = minimap_y + player_y * cell_size
    pygame.draw.circle(screen, (0, 255, 0), (int(player_minimap_x), int(player_minimap_y)), int(cell_size / 2))

# Создание объектов
player = Player(1.5, 1.5, 0)
world = World(MAP)
weapon_textures = load_weapon_textures()
# Главный цикл
running = True
while running:
    # Обработка событий
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

            # Переключение оружия цифрами 1-9
            if event.key == pygame.K_1:
                weapon_manager.switch_to(0)
            if event.key == pygame.K_2:
                weapon_manager.switch_to(1)
            if event.key == pygame.K_3:
                weapon_manager.switch_to(2)
            if event.key == pygame.K_4:
                weapon_manager.switch_to(3)
            if event.key == pygame.K_5:
                weapon_manager.switch_to(4)
            if event.key == pygame.K_6:
                weapon_manager.switch_to(5)
            if event.key == pygame.K_7:
                weapon_manager.switch_to(6)
            if event.key == pygame.K_8:
                weapon_manager.switch_to(7)
            if event.key == pygame.K_9:
                weapon_manager.switch_to(8)
            if event.key == pygame.K_0:
                weapon_manager.switch_to(9)
        
        # Колесо мыши для переключения оружия
        if event.type == pygame.MOUSEWHEEL:
            if event.y > 0:  # колесо вверх
                weapon_manager.switch_prev()
            elif event.y < 0:  # колесо вниз
                weapon_manager.switch_next()
        
        # Выстрел по ЛКМ
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # левая кнопка
                hit, hit_info = weapon_manager.shoot(player, world)
                if hit:
                    shot_animation = 5
                    muzzle_flash = 3
                    print(f"Выстрел из {weapon_manager.current_weapon.name}! "
                          f"Попадание на расстоянии {hit_info['distance']:.2f}")
                else:
                    shot_animation = 5
                    muzzle_flash = 3
                    print(f"Выстрел из {weapon_manager.current_weapon.name} — мимо!")
        # принудительный подбор по клавише f
        keys = pygame.key.get_pressed()
        if keys[pygame.K_f]:
            #print("Force pickup test")
            if weapon_pickups:
                pickup = weapon_pickups[0]
                new_weapon = Weapon(
                    pickup.weapon_name,
                    pickup.damage,
                    pickup.fire_rate,
                    pickup.shoot_distance,
                    pickup.max_ammo,
                    pickup.color
                )
                weapon_manager.add_weapon(new_weapon)
                weapon_pickups.remove(pickup)
                #print(f"Added {pickup.weapon_name}")
        
        
        
    # Управление с клавиатуры
    keys = pygame.key.get_pressed()
    new_x, new_y = player.move(keys, PLAYER_SPEED)
    player.apply_collision(new_x, new_y, world)
    
    # Автоподбор
    check_weapon_pickups(player.x, player.y)
    
    # Поворот мышью
    mouse_dx = pygame.mouse.get_rel()[0]
    player.rotate(mouse_dx, MOUSE_SENSE)
    
#===ОТРИСОВКА ПОВЕРХНОСТЕЙ==========    
    # Отрисовка неба и пола
    screen.fill((50, 50, 100))  # небо голубое
    pygame.draw.rect(screen, (50, 50, 50), (0, SCREEN_HEIGHT//2, SCREEN_WIDTH, SCREEN_HEIGHT//2))  # пол тёмный
    
    # ========== РЕЙКАСТИНГ ==========
    for ray_num in range(SCREEN_WIDTH):
        # Угол текущего луча
        ray_angle = player.angle - FOV/2 + (ray_num / SCREEN_WIDTH) * FOV
        
        # Пускаем луч
        dist, hit, side, _ = cast_ray(player.x, player.y, ray_angle, world.map)
        
        if hit:
            # Коррекция "рыбий глаз"
            fish_fix = math.cos(ray_angle - player.angle)
            dist = dist * fish_fix
            
            # Защита от деления на ноль
            ray_size = dist + 0.0001
            
            # Высота стены
            wall_height = int(HEIGHT_COEF / ray_size)
            if wall_height > SCREEN_HEIGHT:
                wall_height = SCREEN_HEIGHT
            
            y_start = SCREEN_HEIGHT//2 - wall_height//2
            if y_start < 0:
                y_start = 0
            y_end = SCREEN_HEIGHT//2 + wall_height//2
            if y_end > SCREEN_HEIGHT:
                y_end = SCREEN_HEIGHT
            
            # Затемнение по расстоянию
            brightness = 255 / (1 + dist * dist * 0.3)
            if brightness < 40:
                brightness = 40
            color_val = int(brightness)
            
            # Разные оттенки для вертикальных и горизонтальных стен
            if side == 0:
                color = (color_val // 2, color_val // 3, color_val // 2)
            else:
                color = (color_val, color_val // 2, color_val // 2)
            
            # Рисуем вертикальную полоску
            pygame.draw.line(screen, color, (ray_num, y_start), (ray_num, y_end))
    #===========
    draw_sprites(screen, player.x, player.y, player.angle, 
                 weapon_pickups, FOV, SCREEN_WIDTH, SCREEN_HEIGHT, world.map)
    
    #оТРИСОВКА ПРИЦЕЛА
    draw_crosshair(screen, weapon_manager.current_weapon.color)
    
    #  Отрисовка оружия
    if weapon_manager.current_weapon:
        weapon_name = weapon_manager.current_weapon.name
        barrel_pos = draw_weapon_hands(screen, weapon_name, shot_animation, weapon_textures)
        
        if muzzle_flash > 0:
            draw_muzzle_flash(screen, muzzle_flash, weapon_name, shot_animation, barrel_pos)
    
    #UI
    draw_ui(screen, weapon_manager)
    
    #Minimap
    #draw_pickups_on_minimap(screen, player.x, player.y)
    
    # Уменьшаем таймеры анимации
    if shot_animation > 0:
        shot_animation -= 1
    if muzzle_flash > 0:
        muzzle_flash -= 1
    
    # Отладочная информация
    font = pygame.font.Font(None, 24)
    text = font.render(f"X: {player.x:.2f} Y: {player.y:.2f} Angle: {int(math.degrees(player.angle))} deg", True, (255, 255, 255))
    screen.blit(text, (10, 10))
    
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()