import pygame
import math
from setting import *

class WeaponSelector:
    def __init__(self, game):
        self.game = game
        self.active = False          # Открыто ли колесо оружия
        
        self.NUM_SLOTS = 6
        self.hovered_slot = 1        # На какой слот (1-6) сейчас наведена мышь
        
        # Хранит текущий выбранный под-индекс пушки внутри каждого слота
        self.sub_indices = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
        
        # Виртуальные координаты джойстика мыши
        self.vx = 0
        self.vy = 0
        self.icon_cache = {}

    def check_input(self, event):
        """Обрабатывает зажатие/отпускание клавиш и прокрутку колесика мыши"""
        valid_keys = (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6, pygame.K_q)
        
        if event.type == pygame.KEYDOWN:
            if event.key in valid_keys:
                if not self.active:
                    self.active = True
                    self.vx = 0
                    self.vy = 0
                    pygame.mouse.get_rel() 
                return True

        if event.type == pygame.KEYUP:
            if event.key in valid_keys and self.active:
                self.confirm_selection()
                return True

        if self.active and event.type == pygame.MOUSEBUTTONDOWN:
            weapons_in_hovered = self._get_weapons_in_slot(self.hovered_slot)
            if len(weapons_in_hovered) > 1:
                if event.button == 4: # Скролл ВВЕРХ
                    self.sub_indices[self.hovered_slot] = (self.sub_indices[self.hovered_slot] - 1) % len(weapons_in_hovered)
                    return True
                elif event.button == 5: # Скролл ВНИЗ
                    self.sub_indices[self.hovered_slot] = (self.sub_indices[self.hovered_slot] + 1) % len(weapons_in_hovered)
                    return True

        return False

    def check_mouse_click(self, event):
        if self.active and event.type == pygame.MOUSEBUTTONDOWN and event.button in (1, 4, 5):
            return True
        return False

    def confirm_selection(self):
        """Берет выбранную пушку и передает ее в инвентарь игры"""
        weapons = self._get_weapons_in_slot(self.hovered_slot)
        if weapons:
            chosen_sub_idx = min(self.sub_indices[self.hovered_slot], len(weapons) - 1)
            chosen_sub_idx = max(0, chosen_sub_idx)
            
            target_inventory_idx = weapons[chosen_sub_idx]['inventory_index']
            
            game_obj = self.game
            inventory = getattr(game_obj, 'inventory', [])
            level_manager = getattr(game_obj, 'level_manager', None)
            
            if level_manager is not None and target_inventory_idx < len(inventory):
                level_manager.current_weapon_index = target_inventory_idx
                game_obj.weapon = inventory[target_inventory_idx]
                print(f"🎯 [КОЛЕСО ОРУЖИЯ] Активирован слот {self.hovered_slot}, индекс: {target_inventory_idx}")
                
        pygame.mouse.get_rel() 
        self.active = False

    def update(self):
        """Рассчитывает положение виртуального джойстика мыши.
        СТРУКТУРА: Ноль радиан находится строго на 12 часах, инкремент идет по часовой стрелке!"""
        if not self.active:
            return

        inventory = getattr(self.game, 'inventory', [])
        if len(inventory) == 0:
            return

        dx, dy = pygame.mouse.get_rel()
        self.vx += dx
        self.vy += dy
        
        dist = math.hypot(self.vx, self.vy)
        if dist > 150:
            self.vx = (self.vx / dist) * 150
            self.vy = (self.vy / dist) * 150

        if dist > 20:
            # 🔥 ЧИСТАЯ СТРУКТУРА №1: Меняем оси местами в atan2(x, y). 
            # Это мгновенно разворачивает нулевой угол на 12 часов вечера 
            # и пускает тригонометрический круг строго ПО ЧАСОВОЙ СТРЕЛКЕ!
            mouse_angle = math.atan2(self.vx, -self.vy)
            if mouse_angle < 0:
                mouse_angle += math.tau

            # Шаг одного сектора для 6 слотов
            sector_step = math.tau / self.NUM_SLOTS
            
            # Вычисляем номер слота (от 1 до 6) без искусственных костылей и сдвигов
            adjusted_angle = (mouse_angle + sector_step / 2) % math.tau
            self.hovered_slot = (int(adjusted_angle / sector_step) % self.NUM_SLOTS) + 1
        cx = self.game.screen.get_width() // 2
        cy = self.game.screen.get_height() // 2
        pygame.mouse.set_pos(cx, cy)

    def draw_weapon_vector_icon(self, surface, w_key, cx, cy, color):
        """🔥 СПРАЙТОВЫЙ МОДЕРНИЗИРОВАННЫЙ МЕТОД: Автоматически подгружает и кэширует
        реальные файлы icon.png из папок пушек и блитит их строго по центру ячеек!"""
        import os
        key = str(w_key).upper()

        # 1. Проверяем, загружен ли уже этот спрайт в кэш селектора
        if key not in self.icon_cache:
            try:
                from config.game_data import WEAPON_CONFIG
                w_data = WEAPON_CONFIG.get(key, {})
                
                # Достаем имя папки оружия из твоего конфига (например, 'KNIFE', 'COCH', 'PLASMA')
                folder_name = w_data.get('folder_name', key)
                base_dir = os.path.join('resources', 'weapons', folder_name)
                icon_path = None
                
                # Сканируем дисковые расширения с защитой от любого регистра букв (.png / .PNG)
                for possible_name in ('icon.png', 'icon.PNG', 'Icon.png', 'ICON.PNG'):
                    test_path = os.path.join(base_dir, possible_name)
                    if os.path.exists(test_path):
                        icon_path = test_path
                        break
                
                # 2. Если файл icon.png найден — бережно загружаем его
                if icon_path:
                    loaded_icon = pygame.image.load(icon_path).convert_alpha()
                    
                    # 🔥 ДИНАМИЧЕСКИЙ МАСШТАБ ИКОНКИ: Считаем размеры от текущих клеток экрана!
                    grid_h = getattr(self.game, 'GRID_H', 18)
                    cell_h = HEIGHT // grid_h
                    
                    # Задаем идеальные габариты иконки внутри сектора (примерно 1.2 x 0.8 клетки)
                    max_w = int(cell_h * 1.2)
                    max_h = int(cell_h * 0.8)
                    
                    # Пропорционально ужимаем картинку, чтобы силуэт пушки не растягивало
                    if loaded_icon.get_width() > max_w or loaded_icon.get_height() > max_h:
                        aspect = loaded_icon.get_width() / loaded_icon.get_height()
                        if aspect > (max_w / max_h):
                            new_w = max_w
                            new_h = int(max_w / aspect)
                        else:
                            new_h = max_h
                            new_w = int(max_h * aspect)
                        loaded_icon = pygame.transform.smoothscale(loaded_icon, (new_w, new_h))
                    
                    self.icon_cache[key] = loaded_icon
                    print(f"🖼️ [Колесо] Иконка {key} успешно закэширована из: {icon_path}")
                else:
                    # Файла нет на диске — уходим в красивый фолбек, чтобы игра не крашилась
                    icon_path = None
            except Exception as e:
                print(f"❌ [Колесо] Ошибка загрузки ассета для {key}: {e}")
                icon_path = None

            # 3. 🔥 ВСТРОЕННЫЙ НЕОНОВЫЙ ПРЕДОХРАНИТЕЛЬ:
            # Если ты добавляешь новую пушку и забыл положить ей icon.png — селектор НЕ упадет!
            # Он на лету сгенерирует маленькую цифровую бирюзовую плашку с текстом "NO IMG".
            if not icon_path:
                grid_h = getattr(self.game, 'GRID_H', 18)
                cell_h = HEIGHT // grid_h
                fw, fh = int(cell_h * 1.1), int(cell_h * 0.5)
                
                fallback_surf = pygame.Surface((fw, fh), pygame.SRCALPHA)
                pygame.draw.rect(fallback_surf, (0, 140, 255, 40), (0, 0, fw, fh), 0, 3)
                pygame.draw.rect(fallback_surf, (0, 240, 255, 160), (0, 0, fw, fh), 1, 3)
                
                f_font = pygame.font.SysFont('Arial', int(fh * 0.5), bold=True)
                f_txt = f_font.render("NO IMG", True, (0, 255, 255))
                fallback_surf.blit(f_txt, f_txt.get_rect(center=(fw // 2, fh // 2)))
                self.icon_cache[key] = fallback_surf

        # 4. ВЫВОД ГОТОВОГО СПРАЙТА НА ЭКРАН:
        # Извлекаем картинку (или заглушку) из ОЗУ и центрируем ровно по координатам сектора
        icon_surface = self.icon_cache.get(key)
        if icon_surface:
            icon_rect = icon_surface.get_rect(center=(cx, cy))
            surface.blit(icon_surface, icon_rect)

    def draw(self):
        """Рендерит динамическое круговое меню, где ВСЕ размеры и радиусы
        вычисляются от размеров клеток сетки (CELL_W / CELL_H)"""
        if not self.active:
            return

        inventory = getattr(self.game, 'inventory', [])
        if len(inventory) == 0:
            return

        # 🔥 ДИНАМИЧЕСКИЙ РАСЧЕТ РАЗМЕРОВ КЛЕТОК (Из твоих настроек экрана)
        # Если GRID_W и GRID_H лежат в config, подставь свои значения (например, 30 и 18)
        grid_w = getattr(self.game, 'GRID_W', 30)
        grid_h = getattr(self.game, 'GRID_H', 18)
        cell_w = WIDTH // grid_w
        cell_h = HEIGHT // grid_h

        # 🔥 ДИНАМИЧЕСКИЙ МАСШТАБ ШРИФТОВ: Размеры букв плавно растут от высоты клетки!
        font_slot = pygame.font.SysFont('Arial', int(cell_h * 0.35))
        font_weapon = pygame.font.Font('resources/fonts/Fy.ttf', int(cell_h * 0.45))
        font_ammo = pygame.font.Font('resources/fonts/Fy.ttf', int(cell_h * 0.38))
        font_center = pygame.font.SysFont('Arial', int(cell_h * 0.60))

        screen_w = self.game.screen.get_width()
        screen_h = self.game.screen.get_height()
        cx, cy = screen_w // 2, screen_h // 2

        # Затемнение экрана для фокуса на приборах
        dim_surf = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        dim_surf.fill((0, 0, 0, 160)) 
        self.game.screen.blit(dim_surf, (0, 0))

        # 🔥 ТВОЕ ТРЕБОВАНИЕ: Задаем радиус огромного колеса строго в КЛЕТКАХ!
        # Колесо имеет радиус в 4.5 вертикальные клетки лабиринта
        base_radius = int(cell_h * 4.5)
        sector_step = math.tau / self.NUM_SLOTS

        # Толщина линий обводки тоже динамическая (зависит от масштаба экрана)
        line_thickness = max(2, int(cell_h * 0.06))

        # 1. СИНХРОННЫЙ РЕНДЕР СЕКТОРОВ И ИНФО-ПАКЕТОВ
        for i in range(self.NUM_SLOTS):
            slot_num = i + 1
            is_hovered = (slot_num == self.hovered_slot)
            
            weapons = self._get_weapons_in_slot(slot_num)
            has_weapons = len(weapons) > 0

            # Настройка бирюзового неона
            if is_hovered:
                color_edge = (0, 240, 255)
                color_fill = (0, 140, 255, 75) if has_weapons else (0, 140, 255, 20)
            elif has_weapons:
                color_edge = (0, 90, 140)
                color_fill = (8, 18, 28, 140)
            else:
                color_edge = (35, 45, 55)
                color_fill = (10, 12, 14, 40)

            # Каноничный старт секторов сверху на 12 часах
            angle_start = i * sector_step - (sector_step / 2)
            angle_end = (i + 1) * sector_step - (sector_step / 2)

            arc_points = [(cx, cy)]
            steps = 24 # Плавная дуга в высоком разрешении
            for s in range(steps + 1):
                curr_angle = angle_start + (angle_end - angle_start) * (s / steps)
                # Кольцо расширяется при наведении (на 0.35 части клетки)
                radius_dist = base_radius + int(cell_h * 0.35) if is_hovered else base_radius
                
                px = cx + int(radius_dist * math.sin(curr_angle))
                py = cy - int(radius_dist * math.cos(curr_angle))
                arc_points.append((px, py))

            poly_surf = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
            pygame.draw.polygon(poly_surf, color_fill, arc_points)
            self.game.screen.blit(poly_surf, (0, 0))
            pygame.draw.lines(self.game.screen, color_edge, True, arc_points, line_thickness + 2 if is_hovered else line_thickness)

            # ==================================================================
            # 📐 ИДЕАЛЬНОЕ ВЫРАВНИВАНИЕ ВНУТРИ СЕКТОРА ПО КЛЕТОЧНЫМ ДОЛЯМ
            # Мы вычисляем центральный луч сектора. Инфо-пакет будет сидеть 
            # строго в геометрическом центре самого «куска пирога», двигаясь вместе с ним!
            # ==================================================================
            text_angle = angle_start + (sector_step / 2)
            
            # Находим точку центра сектора (примерно на 65% длины радиуса от центра экрана)
            dist_pack = int(base_radius * 0.65)
            if is_hovered:
                dist_pack += int(cell_h * 0.15)

            card_cx = cx + int(dist_pack * math.sin(text_angle))
            card_cy = cy - int(dist_pack * math.cos(text_angle))

            text_color = (255, 255, 255) if is_hovered else (140, 180, 200)
            ammo_color = (0, 240, 255) if is_hovered else (90, 120, 140)
            icon_color = (0, 255, 255) if is_hovered else (0, 160, 230)

            # Вывод SLOT X (Смещение вверх динамически зависит от cell_h)
            slot_txt = font_slot.render(f"SLOT {slot_num}", True, (0, 200, 255) if is_hovered else (80, 95, 110))
            self.game.screen.blit(slot_txt, slot_txt.get_rect(center=(card_cx, card_cy - int(cell_h * 0.65))))

            if has_weapons:
                current_sub_idx = self.sub_indices[slot_num] % len(weapons)
                w_data = weapons[current_sub_idx]
                w_key = w_data['key']
                
                real_weapon_obj = inventory[w_data['inventory_index']]
                ammo_display = "INF" if getattr(real_weapon_obj, 'is_infinite', False) else str(getattr(real_weapon_obj, 'ammo', 0))

                display_name = str(w_data['display_name']).upper()
                if len(weapons) > 1:
                    display_name = f"{display_name}"

                # --- 1. ВЕКТОРНАЯ ИКОНКА (Точно в центре карточки) ---
                self.draw_weapon_vector_icon(self.game.screen, w_key, card_cx, card_cy - int(cell_h * 0.1), icon_color)

                # --- 2. НАЗВАНИЕ ПУШКИ (Сдвиг вниз пропорционально cell_h) ---
                w_txt = font_weapon.render(display_name, True, text_color)
                self.game.screen.blit(w_txt, w_txt.get_rect(center=(card_cx, card_cy + int(cell_h * 0.45))))

                # --- 3. ЖИВЫЕ ПАТРОНЫ (Сдвиг вниз пропорционально cell_h) ---
                ammo_txt = font_ammo.render(f"AMMO: {ammo_display}", True, ammo_color)
                self.game.screen.blit(ammo_txt, ammo_txt.get_rect(center=(card_cx, card_cy + int(cell_h * 0.95))))
            else:
                empty_txt = font_weapon.render("EMPTY", True, (65, 75, 85))
                self.game.screen.blit(empty_txt, empty_txt.get_rect(center=(card_cx, card_cy + int(cell_h * 0.15))))

        # ==================================================================
        # 2. РЕНДЕР ЦЕНТРАЛЬНОГО ИНФО-ЯДРА СЕЛЕКТOРА (ТОЖЕ В КЛЕТКАХ)
        # ==================================================================
        active_weapons = self._get_weapons_in_slot(self.hovered_slot)
        if active_weapons:
            active_sub_idx = self.sub_indices[self.hovered_slot] % len(active_weapons)
            active_name = str(active_weapons[active_sub_idx]['display_name']).upper()
            title_color = (0, 255, 255)
        else:
            active_name = "EMPTY SLOT"
            title_color = (100, 110, 120)
        
        title_txt = font_center.render(active_name, True, title_color)
        
        # 🔥 Радиус центрального ядра равен ровно 1.8 вертикальным клеткам экрана!
        core_radius = int(cell_h * 1.8)
        pygame.draw.circle(self.game.screen, (10, 12, 16), (cx, cy), core_radius)
        pygame.draw.circle(self.game.screen, title_color, (cx, cy), core_radius, line_thickness)
        
        # Точка виртуального прицела мыши (размер зависит от cell_h)
        dot_radius = max(3, int(cell_h * 0.1))
        dot_x = cx + int(self.vx * 0.16)
        dot_y = cy + int(self.vy * 0.16)
        pygame.draw.circle(self.game.screen, (0, 255, 255), (dot_x, dot_y), dot_radius)
        
        self.game.screen.blit(title_txt, title_txt.get_rect(center=(cx, cy)))

    # 🔥 СЛЕДУЮЩИЙ МЕТОД ИДЕТ СДВИГОМ НА ОДИН ТАБ (4 ПРОБЕЛА) ОТ КРАЯ КЛАССА:
    def _get_weapons_in_slot(self, slot_num):
        """Сканирует динамический инвентарь и раскидывает пушки строго по слотам 1-6"""
        valid_weapons = []
        
        try:
            from config.game_data import WEAPON_CONFIG
        except:
            return []

        inventory = getattr(self.game, 'inventory', [])
        if not inventory:
            return []

        for inv_idx, weapon_obj in enumerate(inventory):
            obj_display_name = getattr(weapon_obj, 'name', None)
            if not obj_display_name:
                continue
                
            obj_name_lower = str(obj_display_name).strip().lower()

            for w_key, w_data in WEAPON_CONFIG.items():
                config_name_lower = str(w_data.get('name', '')).strip().lower()
                
                if config_name_lower == obj_name_lower:
                    slot = w_data.get('slot', 4)

                    if slot == slot_num:
                        valid_weapons.append({
                            'key': w_key,
                            'display_name': w_data.get('name', w_key),
                            'inventory_index': inv_idx
                        })
                        break 

        return valid_weapons

