import pygame
import math

class HalfLifeWeaponSelector:
    def __init__(self, game):
        self.game = game
        self.active = False          # Открыто ли колесо оружия
        self.hovered_index = 0       # Подсвеченный сектор пушки
        
        # Виртуальные координаты прицела внутри колеса (чтобы мышь не улетала за экран)
        self.vx = 0
        self.vy = 0

    def check_input(self, event):
        """Перехватывает ЗАЖАТИЕ и ОТПУСКАНИЕ клавиш для олдскульного кругового меню"""
        # Считываем клавиши 1-4 и Q
        valid_keys = (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_q)
        
        # 1. ЗАЖАЛИ КНОПКУ -> ОТКРЫВАЕМ КОЛЕСО
        if event.type == pygame.KEYDOWN:
            if event.key in valid_keys:
                if not self.active:
                    self.active = True
                    self.vx = 0
                    self.vy = 0
                    # Сбрасываем дельту мыши перед стартом, чтобы убрать резкий рывок
                    pygame.mouse.get_rel() 
                return True

        # 2. 🔥 ОТПУСТИЛИ КНОПКУ -> МГНОВЕННАЯ СМЕНА ПУШКИ (KeyUP хак)
        if event.type == pygame.KEYUP:
            if event.key in valid_keys and self.active:
                self.confirm_selection()
                return True

        return False

    def check_mouse_click(self, event):
        """Нам больше не нужны клики мыши, так как выбор происходит на отпускание кнопки!"""
        return False

    def confirm_selection(self):
        """Берет подсвеченную пушку и жестко прописывает ее в твой инвентарь"""
        inventory = getattr(self.game, 'inventory', [])
        level_manager = getattr(self.game, 'level_manager', None)
        
        if inventory and level_manager is not None:
            if 0 <= self.hovered_index < len(inventory):
                # Твоя родная схема смены оружия из хэндлера
                level_manager.current_weapon_index = self.hovered_index
                self.game.weapon = inventory[self.hovered_index]
                print(f"🎯 [ВЫБОР КОЛЕСА] Оружие успешно сменено на индекс: {self.hovered_index}")
                
        self.active = False

    def update(self):
        """Каждый кадр считает виртуальный вектор смещения мыши (механика джойстика)"""
        if not self.active:
            return

        inventory = getattr(self.game, 'inventory', [])
        num_weapons = len(inventory)
        if num_weapons == 0:
            return

        # 🔥 ГЛАВНЫЙ ФИКС БЛОКИРОВКИ МЫШИ (Считываем относительную дельту get_rel):
        # В 2.5D шутерах курсор скрыт и залочен. Мы берем чистую скорость движения руки!
        dx, dy = pygame.mouse.get_rel()
        
        # Накапливаем сдвиг в наши виртуальные координаты
        self.vx += dx
        self.vy += dy
        
        # Находим расстояние от центра виртуального джойстика
        dist = math.hypot(self.vx, self.vy)

        # Ограничиваем виртуальный курсор рамками невидимого круга (макс. радиус 150),
        # чтобы пользователю не приходилось долго вести мышь обратно
        if dist > 150:
            self.vx = (self.vx / dist) * 150
            self.vy = (self.vy / dist) * 150

        # Мертвая зона: если мышь едва сдвинулась, оставляем прошлый сектор
        if dist > 20:
            # Считаем угол виртуального вектора в радианах
            mouse_angle = math.atan2(self.vy, self.vx)
            if mouse_angle < 0:
                mouse_angle += math.tau

            # Вычисляем, на какой сектор указывает рука игрока
            sector_step = math.tau / num_weapons
            adjusted_angle = (mouse_angle + sector_step / 2) % math.tau
            self.hovered_index = int(adjusted_angle / sector_step) % num_weapons

    def draw(self):
        """Рендерит футуристичное неоновое круговое колесо оружия DOOM-стиля"""
        if not self.active:
            return

        inventory = getattr(self.game, 'inventory', [])
        num_weapons = len(inventory)
        if num_weapons == 0:
            return

        font_title = pygame.font.SysFont('Arial', 18, bold=True)
        font_weapon = pygame.font.SysFont('Arial', 14, bold=True)

        screen_w = self.game.screen.get_width()
        screen_h = self.game.screen.get_height()
        cx, cy = screen_w // 2, screen_h // 2

        # Кинематографичное затемнение заднего фона лабиринта
        dim_surf = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        dim_surf.fill((0, 0, 0, 140)) 
        self.game.screen.blit(dim_surf, (0, 0))

        base_radius = 110
        sector_step = math.tau / num_weapons

        # Отрисовка секторов векторов
        for idx in range(num_weapons):
            is_hovered = (idx == self.hovered_index)
            
            radius = base_radius + 15 if is_hovered else base_radius
            color_edge = (0, 240, 255) if is_hovered else (0, 90, 140)
            color_fill = (0, 140, 255, 60) if is_hovered else (8, 15, 25, 130)

            angle_start = idx * sector_step - (sector_step / 2)
            angle_end = (idx + 1) * sector_step - (sector_step / 2)

            arc_points = [(cx, cy)]
            steps = 12
            for s in range(steps + 1):
                curr_angle = angle_start + (angle_end - angle_start) * (s / steps)
                px = cx + int(radius * math.cos(curr_angle))
                py = cy + int(radius * math.sin(curr_angle))
                arc_points.append((px, py))

            poly_surf = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
            pygame.draw.polygon(poly_surf, color_fill, arc_points)
            self.game.screen.blit(poly_surf, (0, 0))

            pygame.draw.lines(self.game.screen, color_edge, True, arc_points, 2 if is_hovered else 1)

            # Вывод текста названий пушек по краям
            text_angle = angle_start + (sector_step / 2)
            text_dist = radius + 25 if is_hovered else radius + 15
            tx = cx + int(text_dist * math.cos(text_angle))
            ty = cy + int(text_dist * math.sin(text_angle))

            weapon_obj = inventory[idx]
            display_name = str(getattr(weapon_obj, 'name', f"WEAPON {idx}")).upper()

            w_txt = font_weapon.render(display_name, True, (255, 255, 255) if is_hovered else (150, 180, 200))
            txt_rect = w_txt.get_rect(center=(tx, ty))
            self.game.screen.blit(w_txt, txt_rect)

        # Маленькое технологичное ядро по центру кольца
        active_weapon_obj = inventory[self.hovered_index]
        active_name = str(getattr(active_weapon_obj, 'name', "SELECT WEAPON")).upper()
        
        title_txt = font_title.render(active_name, True, (0, 255, 255))
        title_rect = title_txt.get_rect(center=(cx, cy))
        
        pygame.draw.circle(self.game.screen, (10, 12, 16), (cx, cy), 40)
        pygame.draw.circle(self.game.screen, (0, 180, 255), (cx, cy), 40, 1)
        
        # Маленькая неоновая точка-прицел виртуального курсора, показывающая куда смещена мышь!
        dot_x = cx + int(self.vx * 0.2)
        dot_y = cy + int(self.vy * 0.2)
        pygame.draw.circle(self.game.screen, (0, 255, 255), (dot_x, dot_y), 3)
        
        self.game.screen.blit(title_txt, title_rect)
