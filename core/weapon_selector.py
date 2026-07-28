import pygame
import math

class HalfLifeWeaponSelector:
    def __init__(self, game):
        self.game = game
        self.active = False          # Открыто ли колесо оружия
        
        # Мы жестко фиксируем 6 секторов-слотов на круге!
        self.NUM_SLOTS = 6
        self.hovered_slot = 1        # На какой слот (1-6) сейчас наведена мышь
        
        # Словарь, который хранит текущий выбранный под-индекс пушки внутри каждого слота.
        # По умолчанию выбран 0-й элемент (первая пушка в категории).
        self.sub_indices = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
        
        # Виртуальные координаты прицела (джойстика) внутри колеса
        self.vx = 0
        self.vy = 0

    def check_input(self, event):
        """Обрабатывает зажатие/отпускание клавиш и прокрутку колесика мыши"""
        # Слушаем цифровые клавиши 1-6 и кнопку Q
        valid_keys = (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6, pygame.K_q)
        
        # 1. ЗАЖАЛИ КНОПКУ -> ОТКРЫВАЕМ КОЛЕСО
        if event.type == pygame.KEYDOWN:
            if event.key in valid_keys:
                if not self.active:
                    self.active = True
                    self.vx = 0
                    self.vy = 0
                    pygame.mouse.get_rel() # Сброс дельты
                return True

        # 2. ОТПУСТИЛИ КНОПКУ -> МГНОВЕННАЯ СМЕНА ПУШКИ
        if event.type == pygame.KEYUP:
            if event.key in valid_keys and self.active:
                self.confirm_selection()
                return True

        # 3. 🔥 ПРОКРУТКА КОЛЕСИКА МЫШИ (ПЕРЕБОР ПУШЕК ВНУТРИ АКТИВНОГО СЕКТОРА)
        if self.active and event.type == pygame.MOUSEBUTTONDOWN:
            # Получаем список пушек, которые сейчас есть у игрока в ПОДСВЕЧЕННОМ слоте
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
        """Клики ЛКМ/ПКМ глушим, так как колесико мыши обрабатывается в check_input"""
        if self.active and event.type == pygame.MOUSEBUTTONDOWN and event.button in (1, 4, 5):
            return True
        return False

    def confirm_selection(self):
        """Берет выбранную пушку из активного слота и передает ее в инвентарь игры"""
        weapons = self._get_weapons_in_slot(self.hovered_slot)
        
        if weapons:
            # Защита: проверяем, что выбранный скроллом под-индекс не вылетел за границы массива пушек
            chosen_sub_idx = min(self.sub_indices[self.hovered_slot], len(weapons) - 1)
            chosen_sub_idx = max(0, chosen_sub_idx)
            
            # Достаем честный глобальный индекс пушки внутри твоего динамического self.inventory
            target_inventory_idx = weapons[chosen_sub_idx]['inventory_index']
            
            game_obj = self.game
            inventory = getattr(game_obj, 'inventory', [])
            level_manager = getattr(game_obj, 'level_manager', None)
            
            if level_manager is not None and target_inventory_idx < len(inventory):
                level_manager.current_weapon_index = target_inventory_idx
                game_obj.weapon = inventory[target_inventory_idx]
                print(f"🚀 [КОЛЕСО ДОСТАЛО СЛОТ {self.hovered_slot}] Пушка активирована под индексом: {target_inventory_idx}")
        
        # ==================================================================
        # 🔥 УЛЬТИМАТИВНЫЙ ДВОЙНОЙ СБРОС МЫШИ ДЛЯ 2.5D/3D РЕЖИМОВ
        # ==================================================================
        # 1. Находим точные координаты центра экрана
        cx = self.game.screen.get_width() // 2
        cy = self.game.screen.get_height() // 2
        
        # 2. Насильно телепортируем физический курсор мыши в идеальный центр!
        # Когда на следующем кадре включится код игрока, он увидит мышь строго в центре
        # и поймет, что никакого движения и разворота камеры совершать не нужно.
        pygame.mouse.set_pos(cx, cy)
        
        # 3. Дополнительно «съедаем» относительную дельту, чтобы очистить буфер SDL
        pygame.mouse.get_rel()
                
        self.active = False

    def update(self):
        """Рассчитывает виртуальный вектор смещения мыши для 6 жестко зафиксированных секторов"""
        if not self.active:
            return

        dx, dy = pygame.mouse.get_rel()
        self.vx += dx
        self.vy += dy
        
        dist = math.hypot(self.vx, self.vy)

        if dist > 150:
            self.vx = (self.vx / dist) * 150
            self.vy = (self.vy / dist) * 150

        # Мышь определяет сектор только за пределами мертвой зоны (20 пикселей)
        if dist > 20:
            mouse_angle = math.atan2(self.vy, self.vx)
            if mouse_angle < 0:
                mouse_angle += math.tau

            # Шаг одного сектора для 6 слотов равен ровно 60 градусов (math.tau / 6)
            sector_step = math.tau / self.NUM_SLOTS
            
            # Смещаем фазу, чтобы SLOT 1 находился ровно по центру на "12 часах"
            adjusted_angle = (mouse_angle + sector_step / 2) % math.tau
            
            # Магическая формула: находим номер слота от 1 до 6 на круге
            # Прибавляем 1, так как слоты у нас начинаются с единицы, а не с нуля
            self.hovered_slot = (int(adjusted_angle / sector_step) % self.NUM_SLOTS) + 1

    def draw(self):
        """Рендерит фиксированное 6-слойное круговое меню с каскадной прокруткой оружия"""
        if not self.active:
            return

        font_title = pygame.font.SysFont('Arial', 18, bold=True)
        font_weapon = pygame.font.SysFont('Arial', 13, bold=True)
        font_slot = pygame.font.SysFont('Arial', 11, bold=True)

        screen_w = self.game.screen.get_width()
        screen_h = self.game.screen.get_height()
        cx, cy = screen_w // 2, screen_h // 2

        # Кинематографичное киберпанк затемнение фона
        dim_surf = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        dim_surf.fill((0, 0, 0, 140)) 
        self.game.screen.blit(dim_surf, (0, 0))

        base_radius = 110
        sector_step = math.tau / self.NUM_SLOTS

        # РИСУЕМ 6 НАМЕРТВО ЗАФИКСИРОВАННЫХ СЕКТОРОВ НА КРУГЕ
        for i in range(self.NUM_SLOTS):
            slot_num = i + 1 # Номер текущего слота от 1 до 6
            is_hovered = (slot_num == self.hovered_slot)
            
            weapons = self._get_weapons_in_slot(slot_num)
            has_weapons = len(weapons) > 0

            # Настройка сочных циановых неоновых цветов
            if is_hovered:
                color_edge = (0, 240, 255)
                color_fill = (0, 140, 255, 65) if has_weapons else (0, 140, 255, 20)
            elif has_weapons:
                color_edge = (0, 90, 140)
                color_fill = (8, 18, 28, 140)
            else:
                color_edge = (35, 45, 55)
                color_fill = (10, 12, 14, 40) # Прозрачный пустой сектор, если оружия нет

            # Границы дуги сектора
            angle_start = i * sector_step - (sector_step / 2)
            angle_end = (i + 1) * sector_step - (sector_step / 2)

            arc_points = [(cx, cy)]
            steps = 12
            for s in range(steps + 1):
                curr_angle = angle_start + (angle_end - angle_start) * (s / steps)
                radius_dist = base_radius + 15 if is_hovered else base_radius
                px = cx + int(radius_dist * math.cos(curr_angle))
                py = cy + int(radius_dist * math.sin(curr_angle))
                arc_points.append((px, py))

            poly_surf = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
            pygame.draw.polygon(poly_surf, color_fill, arc_points)
            self.game.screen.blit(poly_surf, (0, 0))
            pygame.draw.lines(self.game.screen, color_edge, True, arc_points, 2 if is_hovered else 1)

            # Вычисляем центральный вектор направления текущего сектора для текста
            text_angle = angle_start + (sector_step / 2)
            text_dist = (base_radius + 30) if is_hovered else (base_radius + 15)
            tx = cx + int(text_dist * math.cos(text_angle))
            ty = cy + int(text_dist * math.sin(text_angle))

            # ОТРИСОВКА НАЗВАНИЙ ОРУЖИЯ ВНУТРИ СЕКТОРОВ
            if has_weapons:
                # Берем пушку, выбранную скроллом мыши в этом слоте
                current_sub_idx = self.sub_indices[slot_num] % len(weapons)
                display_name = str(weapons[current_sub_idx]['display_name']).upper()
                
                # Если в слоте несколько пушек — добавляем красивый индикатор скролла "[+]"
                if len(weapons) > 1:
                    display_name = f"↕ {display_name}"
                    
                w_txt = font_weapon.render(display_name, True, (255, 255, 255) if is_hovered else (140, 180, 200))
            else:
                w_txt = font_weapon.render("EMPTY", True, (65, 75, 85))

            txt_rect = w_txt.get_rect(center=(tx, ty))
            self.game.screen.blit(w_txt, txt_rect)
            
            # Маленькая подпись номера слота над названием пушки
            slot_txt = font_slot.render(f"SLOT {slot_num}", True, (0, 200, 255) if is_hovered else (80, 95, 110))
            slot_rect = slot_txt.get_rect(center=(tx, ty - 14))
            self.game.screen.blit(slot_txt, slot_rect)

        # РЕНДЕР ЦЕНТРАЛЬНОГО НЕОНОВОГО ЯДРА СЕЛЕКТОРA
        active_weapons = self._get_weapons_in_slot(self.hovered_slot)
        if active_weapons:
            active_sub_idx = self.sub_indices[self.hovered_slot] % len(active_weapons)
            active_name = str(active_weapons[active_sub_idx]['display_name']).upper()
            title_color = (0, 255, 255)
        else:
            active_name = f"SLOT {self.hovered_slot} EMPTY"
            title_color = (100, 110, 120)
        
        title_txt = font_title.render(active_name, True, title_color)
        title_rect = title_txt.get_rect(center=(cx, cy))
        
        pygame.draw.circle(self.game.screen, (10, 12, 16), (cx, cy), 42)
        pygame.draw.circle(self.game.screen, title_color, (cx, cy), 42, 1)
        
        # Точка виртуального прицела мыши
        dot_x = cx + int(self.vx * 0.18)
        dot_y = cy + int(self.vy * 0.18)
                # (Это самый конец метода draw...)
        pygame.draw.circle(self.game.screen, (10, 12, 16), (cx, cy), 42)
        pygame.draw.circle(self.game.screen, title_color, (cx, cy), 42, 1)
        
        # Точка виртуального прицела мыши
        dot_x = cx + int(self.vx * 0.18)
        dot_y = cy + int(self.vy * 0.18)
        pygame.draw.circle(self.game.screen, (0, 255, 255), (dot_x, dot_y), 3)
        
        # Отрисовка названия пушки в центре колеса
        self.game.screen.blit(title_txt, title_rect)

    # 🔥 ВСТАВЛЯЙ МЕТОД НИЖЕ СТРОГО С ДВУМЯ ОТСТУПАМИ (4 ПРОБЕЛА) ОТ КРАЯ КЛАССА:
    def _get_weapons_in_slot(self, slot_num):
        """ОБРАТНЫЙ СКАНЕР: Сканирует динамический инвентарь и раскидывает пушки
        строго по слотам 1-6 на основе настроек WEAPON_CONFIG."""
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
                    # Читаем слот напрямую из конфига пушки
                    slot = w_data.get('slot', 4)

                    if slot == slot_num:
                        valid_weapons.append({
                            'key': w_key,
                            'display_name': w_data.get('name', w_key),
                            'inventory_index': inv_idx
                        })
                        break 

        return valid_weapons

