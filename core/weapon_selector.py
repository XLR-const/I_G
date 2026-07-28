import pygame

class HalfLifeWeaponSelector:
    def __init__(self, game):
        self.game = game
        self.active = False          # Открыто ли сейчас меню выбора
        self.last_action_time = 0    # Время последнего нажатия (для автозакрытия)
        self.fade_timeout = 3000     # Меню исчезает через 3 секунды бездействия
        
        self.selected_slot = 1       # Текущая цифровая категория (1-4)
        self.selected_index = 0      # Какое конкретно оружие внутри этого слота выбрано

    def check_input(self, event):
        """Перехватывает нажатия цифр 1-4 и обрабатывает выбор слотов"""
        if event.type != pygame.KEYDOWN:
            return False

        slot_keys = {pygame.K_1: 1, pygame.K_2: 2, pygame.K_3: 3, pygame.K_4: 4}
        
        if event.key in slot_keys:
            target_slot = slot_keys[event.key]
            current_time = pygame.time.get_ticks()
            
            # Получаем список пушек, которые сейчас РЕАЛЬНО лежат в инвентаре для этого слота
            available_weapons = self._get_weapons_in_slot(target_slot)
            if not available_weapons:
                return True # Слот пустой (нет такого оружия в инвентаре), скипаем

            if not self.active or self.selected_slot != target_slot:
                self.active = True
                self.selected_slot = target_slot
                self.selected_index = 0
            else:
                # Нажатие одной и той же цифры циклически крутит список пушек внутри этой категории
                self.selected_index = (self.selected_index + 1) % len(available_weapons)
                
            self.last_action_time = current_time
            return True

        if self.active:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e):
                self.confirm_selection()
                return True
            if event.key == pygame.K_ESCAPE:
                self.active = False
                return True

        return False

    def check_mouse_click(self, event):
        """Подтверждает выбор пушки на левый клик мыши, если меню открыто"""
        if self.active and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.confirm_selection()
            return True
        return False

    def confirm_selection(self):
        """ФИНАЛЬНЫЙ СИНХРОН: Активирует пушку по её реальному текущему индексу в инвентаре!"""
        weapons = self._get_weapons_in_slot(self.selected_slot)
        if weapons and 0 <= self.selected_index < len(weapons):
            # Извлекаем честный индекс пушки внутри твоего динамического массива self.inventory
            target_inventory_idx = weapons[self.selected_index]['inventory_index']
            
            game_obj = self.game
            inventory = getattr(game_obj, 'inventory', [])
            level_manager = getattr(game_obj, 'level_manager', None)
            
            if level_manager is not None and target_inventory_idx < len(inventory):
                # 🔥 РОДНАЯ СМЕНА ПУШЕК ИЗ ТВОЕГО ХЭНДЛЕРА:
                # 1. Меняем индекс в LevelManager
                level_manager.current_weapon_index = target_inventory_idx
                
                # 2. Даем физический объект оружия в руки игре, чтобы обновились спрайты рук на экране!
                game_obj.weapon = inventory[target_inventory_idx]
                
                print(f"🚀 [СЕЛЕКТОР ДОСТАЛ] Успешная активация пушки из инвентаря по индексу: {target_inventory_idx}")
                
        self.active = False

    def update(self):
        """Автоматически закрывает селектор по таймеру бездействия"""
        if self.active:
            if pygame.time.get_ticks() - self.last_action_time > self.fade_timeout:
                self.active = False

    def draw(self):
        """Рендерит сочное Half-Life каскадное меню вверху экрана"""
        if not self.active:
            return

        font = pygame.font.SysFont('Arial', 18, bold=True)
        start_x = 40
        slot_width = 160
        box_h = 32

        for slot in range(1, 5):
            x = start_x + (slot - 1) * (slot_width + 15)
            y = 20
            
            weapons = self._get_weapons_in_slot(slot)
            has_weapons = len(weapons) > 0
            
            if slot == self.selected_slot:
                # 🔥 ЭЛЕКТРИЧЕСКИЙ ЦИАН ДЛЯ АКТИВНОГО СЛОТА
                color_bg = (0, 150, 255, 190)     
                color_text = (255, 255, 255)
            elif has_weapons:
                color_bg = (15, 35, 50, 140)      # Темно-бирюзовая полупрозрачная подложка
                color_text = (160, 200, 230)
            else:
                color_bg = (10, 15, 22, 40)       
                color_text = (50, 65, 80)

            box_surf = pygame.Surface((slot_width, box_h), pygame.SRCALPHA)
            box_surf.fill(color_bg)
            self.game.screen.blit(box_surf, (x, y))
            
            # Фикс TypeError деления кортежа на число через генератор списков
            dark_border_color = tuple(c_val // 2 for c_val in color_text)
            pygame.draw.rect(self.game.screen, dark_border_color, (x, y, slot_width, box_h), 2)

            txt = font.render(f"SLOT {slot}", True, color_text)
            self.game.screen.blit(txt, (x + 15, y + 6))

            if slot == self.selected_slot and has_weapons:
                for idx, w_data in enumerate(weapons):
                    sub_y = y + box_h + 6 + idx * (box_h + 4)
                    
                    if idx == self.selected_index:
                        # 🔥 ЯРКО-БИРЮЗОВЫЙ ФОКУС НА КОНКРЕТНУЮ ПУШКУ
                        sub_bg = (0, 190, 255, 230)
                        sub_text_c = (255, 255, 255)
                    else:
                        sub_bg = (12, 22, 32, 180)
                        sub_text_c = (140, 175, 200)

                    sub_surf = pygame.Surface((slot_width, box_h), pygame.SRCALPHA)
                    sub_surf.fill(sub_bg)
                    self.game.screen.blit(sub_surf, (x, sub_y))
                    pygame.draw.rect(self.game.screen, sub_text_c, (x, sub_y, slot_width, box_h), 1)

                    w_name = str(w_data['display_name']).upper()
                    w_txt = font.render(w_name, True, sub_text_c)
                    self.game.screen.blit(w_txt, (x + 12, sub_y + 6))

    def _get_weapons_in_slot(self, slot_num):
        """ОБРАТНЫЙ СКАНЕР: Читает красивую строку weapon_obj.name ('Super Shotgun') из инвентаря.
        Математически ищет её совпадение с параметром 'name' внутри WEAPON_CONFIG!"""
        valid_weapons = []
        
        try:
            from config.game_data import WEAPON_CONFIG
        except:
            return []

        # Забираем твой реальный динамический инвентарь из игры
        inventory = getattr(self.game, 'inventory', [])
        if not inventory:
            return []

        # Перебираем все созданные объекты оружия в инвентаре игрока
        for inv_idx, weapon_obj in enumerate(inventory):
            # Читаем красивое имя пушки из объекта (например, 'Super Shotgun' или 'Plasma Gun')
            obj_display_name = getattr(weapon_obj, 'name', None)
            if not obj_display_name:
                continue
                
            # Переводим в строку и нижний регистр для безопасного поиска
            obj_name_lower = str(obj_display_name).strip().lower()

            # 🔥 ОБРАТНЫЙ ПОИСК В WEAPON_CONFIG ПО ПОЛЮ 'name':
            # Перебираем конфиг, чтобы найти, какому техническому капс-ключу (w_key)
            # соответствует это красивое имя из инвентаря игрока!
            for w_key, w_data in WEAPON_CONFIG.items():
                config_name_lower = str(w_data.get('name', '')).strip().lower()
                
                # Если нашли точное совпадение человеческих названий пушек!
                if config_name_lower == obj_name_lower:
                    # Читаем слот СТРОГО из найденной ячейки конфига (2, 4 и т.д.)
                    slot = w_data.get('slot', 4)

                    if slot == slot_num:
                        valid_weapons.append({
                            'key': w_key,                               # Капсовый технический ключ ('COCH')
                            'display_name': w_data.get('name', w_key),  # Красивое имя ('Super Shotgun')
                            'inventory_index': inv_idx                  # Честный индекс пушки внутри твоего self.inventory!
                        })
                        break # Нашли пушку в конфиге, выходим из внутреннего цикла

        return valid_weapons
