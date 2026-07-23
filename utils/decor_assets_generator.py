import os
import pygame
import random
import math


def generate_procedural_decorations(size=512):
    """Монументальный 2.5D .KKRIEGER-style генератор True-Doom спрайтов.
    Попиксельный рендеринг, фрактальный шум, симуляция ржавчины, слизи и электроники!"""

    print("\n💀 [HELLISH DOOM-STYLE SPRITE GENERATOR ACTIVE]")

    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    folder = os.path.join(project_root, 'resources', 'decorations')
    os.makedirs(folder, exist_ok=True)

    if not pygame.get_init():
        pygame.init()

    # 🔥 ОБНОВЛЕННЫЙ УПРАВЛЯЮЩИЙ СПИСОК ГЕНЕРАТОРА:
    # Добавили сюда все новые имена, чтобы цикл начал передавать их в твои ветки elif!
    decor_list = [
        'prop_military_crate', 'prop_sandbag_wall', 'prop_sewage_pillar',
        'prop_lab_capsule', 'prop_server_rack', 'prop_core_reactor',
        'prop_cargo_container', 'prop_hangar_frame',
        
        # Наши новые 10 детализированных сай-фай объектов:
        'prop_sewage_pipe', 'prop_industrial_generator', 'prop_vent_fan',
        'prop_bio_puddle', 'prop_microscope_bench', 'prop_chemical_barrel',
        'prop_ceiling_lamp', 'prop_control_console', 'prop_laser_grid',
        'prop_ammo_crate', 'prop_forklift'
    ]


    for name in decor_list:
        path = os.path.join(folder, f"{name}.png")
        print(f"🧬 [МАТЕМАТИЧЕСКИЙ СИНТЕЗ] Создаю биллборд: '{name}'")

        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        canvas = pygame.Surface((size, size), pygame.SRCALPHA)
        mid = size // 2

        # ==================================================================
        # 📦 1. АРМЕЙСКИЙ ЯЩИК (prop_military_crate) - Фронтальный биллборд
        # ==================================================================
        if name == 'prop_military_crate':
            rect_w, rect_h = size - 120, size - 120
            rx, ry = 60, 60
            pygame.draw.rect(canvas, (105, 70, 40), (rx, ry, rect_w, rect_h))

            board_h = rect_h // 6
            for b in range(1, 6):
                by = ry + b * board_h
                pygame.draw.line(canvas, (55, 30, 15), (rx, by), (rx + rect_w, by), 6)
                pygame.draw.line(canvas, (135, 95, 60), (rx, by + 3), (rx + rect_w, by + 3), 2)

            for _ in range(int(size * size * 0.18)):
                px = random.randint(rx, rx + rect_w - 1)
                py = random.randint(ry, ry + rect_h - 1)
                r, g, b_c, _ = canvas.get_at((px, py))
                noise = random.randint(-18, 18)
                canvas.set_at((px, py), (max(0, min(255, r + noise)), max(0, min(255, g + noise)), max(0, min(255, b_c + noise)), 255))

            for _ in range(25):
                sx = random.randint(rx + 20, rx + rect_w - 40)
                sy = random.randint(ry + 20, ry + rect_h - 20)
                slen = random.randint(15, 60)
                pygame.draw.line(canvas, (40, 20, 10), (sx, sy), (sx + slen, sy + random.randint(-3, 3)), 4)
                pygame.draw.line(canvas, (150, 110, 75), (sx, sy + 2), (sx + slen, sy + 2 + random.randint(-3, 3)), 1)

            for ux, uy in [(rx, ry), (rx + rect_w - 50, ry), (rx, ry + rect_h - 50), (rx + rect_w - 50, ry + rect_h - 50)]:
                pygame.draw.rect(canvas, (45, 48, 50), (ux, uy, 50, 50))
                pygame.draw.rect(canvas, (25, 27, 28), (ux, uy, 50, 50), 4)
                for dx, dy in [(15, 15), (35, 15), (15, 35), (35, 35)]:
                    pygame.draw.circle(canvas, (15, 17, 18), (ux + dx, uy + dy), 5)
                    pygame.draw.circle(canvas, (110, 115, 120), (ux + dx, uy + dy), 3)

        # ==================================================================
        # 🎛️ 2. ТЕХНО-СЕРВЕРНАЯ СТОЙКА (prop_server_rack) - Детализированная шина
        # ==================================================================
        elif name == 'prop_server_rack':
            sx, sy, sw, sh = 80, 40, size - 160, size - 80
            pygame.draw.rect(canvas, (40, 42, 45), (sx, sy, sw, sh))
            pygame.draw.rect(canvas, (20, 22, 23), (sx, sy, sw, sh), 8)

            for y_line in range(sy, sy + sh):
                bright = random.randint(-12, 12)
                for x_line in range(sx, sx + sw):
                    r, g, b_c, _ = canvas.get_at((x_line, y_line))
                    canvas.set_at((x_line, y_line), (max(0, min(255, r + bright)), max(0, min(255, g + bright)), max(0, min(255, b_c + bright)), 255))

            for y in range(sy + 30, sy + sh - 50, 75):
                pygame.draw.rect(canvas, (12, 14, 15), (sx + 20, y, sw - 40, 55))
                pygame.draw.rect(canvas, (60, 65, 70), (sx + 20, y, sw - 40, 55), 2)

                for rx in range(sx + 35, sx + 160, 12):
                    pygame.draw.rect(canvas, (5, 6, 7), (rx, y + 12, 6, 32))
                    pygame.draw.line(canvas, (50, 53, 55), (rx + 6, y + 12), (rx + 6, y + 44), 1)

                for px in range(sx + 190, sx + 280, 24):
                    pygame.draw.rect(canvas, (100, 105, 110), (px, y + 20, 16, 12))
                    pygame.draw.rect(canvas, (0, 0, 0), (px + 3, y + 23, 10, 6))

                for idx_led in range(5):
                    led_c = random.choice([(0, 255, 50), (255, 0, 0), (0, 180, 255), (255, 200, 0)])
                    lx = sx + sw - 70 + idx_led * 10
                    pygame.draw.circle(canvas, (int(led_c[0] * 0.3), int(led_c[1] * 0.3), int(led_c[2] * 0.3)), (lx, y + 26), 5)
                    pygame.draw.circle(canvas, led_c, (lx, y + 26), 3)
                    pygame.draw.circle(canvas, (255, 255, 255), (lx - 1, y + 24), 1)

        # ==================================================================
        # ⚛️ 3. ЯДРО РЕАКТОРА БОМБЫ (prop_core_reactor) - Максимальная детализация
        # ==================================================================
        elif name == 'prop_core_reactor':
            cx, cy, cr = mid, size - 240, size // 2 - 40

            for layer in range(60, size - 40):
                grad = int(50 * math.sin((layer - 60) / (size - 100) * math.pi))
                pygame.draw.circle(canvas, (30 + grad, 33 + grad, 38 + grad), (cx, cy), cr - (layer // 20))

            for vy in range(120, size - 120, 32):
                pygame.draw.ellipse(canvas, (10, 12, 13), (cx - cr + 40, vy, cr * 2 - 80, 16), 4)

            for side_sign in [-1, 1]:
                cable_x = cx + side_sign * (cr - 30)
                points_left = []
                for cy_pos in range(100, size - 40, 20):
                    wave_x = cable_x + int(math.sin(cy_pos * 0.08) * 12)
                    points_left.append((wave_x, cy_pos))
                if len(points_left) > 1:
                    pygame.draw.lines(canvas, (15, 17, 18), False, points_left, 14)
                    pygame.draw.lines(canvas, (80, 30, 20), False, points_left, 10)
                    pygame.draw.lines(canvas, (140, 50, 30), False, points_left, 4)

            pygame.draw.circle(canvas, (10, 10, 15), (cx, cy), cr - 80)
            pygame.draw.circle(canvas, (40, 45, 55), (cx, cy), cr - 80, 8)
            pygame.draw.circle(canvas, (255, 50, 0), (cx, cy), cr - 120)

            random.seed(1337)
            for _ in range(24):
                ang = random.uniform(0, math.pi * 2)
                r_start = random.randint(0, 30)
                r_end = random.randint(50, cr - 120)

                x1 = cx + int(math.cos(ang) * r_start)
                y1 = cy + int(math.sin(ang) * r_start)

                steps = 4
                for step in range(steps):
                    t_ratio = (step + 1) / steps
                    curr_r = r_start + t_ratio * (r_end - r_start)
                    curr_ang = ang + random.uniform(-0.4, 0.4)
                    x2 = cx + int(math.cos(curr_ang) * curr_r)
                    y2 = cy + int(math.sin(curr_ang) * curr_r)

                    pygame.draw.line(canvas, (255, 230, 160), (x1, y1), (x2, y2), random.randint(3, 7))
                    x1, y1 = x2, y2
            random.seed(None)

        # ==================================================================
        # 🛡️ 4. МЕШКИ С ПЕСКОМ (prop_sandbag_wall) - Многослойный бруствер
        # ==================================================================
        elif name == 'prop_sandbag_wall':
            c_base = (145, 135, 115)
            c_shadow = (95, 85, 75)
            c_highlight = (185, 175, 155)

            def draw_single_bag(surface, bx, by, bw, bh, color_mod):
                pygame.draw.ellipse(surface, (40, 35, 30), (bx - 2, by - 2, bw + 4, bh + 4))
                pygame.draw.ellipse(surface, tuple(max(0, min(255, c + color_mod)) for c in c_shadow), (bx, by, bw, bh))
                pygame.draw.ellipse(surface, tuple(max(0, min(255, c + color_mod)) for c in c_base), (bx + 4, by + 4, bw - 8, bh - 8))
                pygame.draw.arc(surface, (60, 55, 45), (bx + 10, by + 10, bw - 20, bh - 20), 0, math.pi, 3)
                pygame.draw.line(surface, tuple(max(0, min(255, c + color_mod)) for c in c_highlight), (bx + bw // 4, by + 8), (bx + 3 * bw // 4, by + 8), 2)

            for idx in range(4):
                draw_single_bag(canvas, 40 + idx * 115, size - 140, 130, 95, -20)
            for idx in range(3):
                draw_single_bag(canvas, 95 + idx * 115, size - 210, 132, 95, -10)
            for idx in range(2):
                draw_single_bag(canvas, 150 + idx * 115, size - 280, 135, 95, 0)
            draw_single_bag(canvas, mid - 70, size - 350, 140, 98, 15)

        # ==================================================================
        # ⛓️ 5. ГРУЗОВОЙ КОНТЕЙНЕР (prop_cargo_container) - Штампованная гофра
        # ==================================================================
        elif name == 'prop_cargo_container':
            bx, by, bw, bh = 50, 80, size - 100, size - 140
            pygame.draw.rect(canvas, (30, 85, 155), (bx, by, bw, bh))
            pygame.draw.rect(canvas, (15, 45, 90), (bx, by, bw, bh), 10)

            for x in range(bx + 25, bx + bw - 20, 36):
                pygame.draw.rect(canvas, (10, 35, 70), (x, by + 10, 16, bh - 20))
                pygame.draw.rect(canvas, (55, 125, 215), (x + 16, by + 10, 8, bh - 20))
                pygame.draw.line(canvas, (5, 15, 30), (x, by + 10), (x, by + bh - 10), 3)

            for _ in range(int(size * 2)):
                rx = random.randint(bx + 10, bx + bw - 10)
                ry = random.randint(by + bh - 45, by + bh - 10) if random.random() < 0.8 else random.randint(by + 10, by + 40)
                r, g, b_c, _ = canvas.get_at((rx, ry))
                canvas.set_at((rx, ry), (max(0, min(255, r + 90)), max(0, min(255, g + 35)), max(0, min(255, b_c - 40)), 255))

        # ==================================================================
        # 🩻 6. БИО-КАПСУЛА (prop_lab_capsule) - Колба с пузырями и ошметками
        # ==================================================================
        elif name == 'prop_lab_capsule':
            cx, cy, cw, ch = 130, 60, size - 260, size - 100
            pygame.draw.rect(canvas, (45, 48, 50), (cx - 20, cy + ch - 50, cw + 40, 50))
            pygame.draw.rect(canvas, (20, 22, 23), (cx - 20, cy + ch - 50, cw + 40, 50), 4)
            pygame.draw.rect(canvas, (12, 16, 20), (cx, cy + 40, cw, ch - 90))

            slime_h = ch - 160
            pygame.draw.rect(canvas, (0, 180, 40), (cx, cy + ch - 50 - slime_h, cw, slime_h))

            for _ in range(20):
                bx = random.randint(cx + 15, cx + cw - 15)
                by = random.randint(cy + ch - 40 - slime_h, cy + ch - 60)
                b_radius = random.randint(3, 9)
                pygame.draw.circle(canvas, (160, 255, 180), (bx, by), b_radius, 2)
                pygame.draw.circle(canvas, (255, 255, 255), (bx - b_radius // 3, by - b_radius // 3), 1)

            for _ in range(6):
                ox_pos = random.randint(cx + 30, cx + cw - 30)
                oy_pos = random.randint(cy + ch - 30 - slime_h, cy + ch - 70)
                pygame.draw.ellipse(canvas, (10, 80, 20), (ox_pos, oy_pos, random.randint(12, 35), random.randint(8, 20)))

            glass_surf = pygame.Surface((cw, ch - 90), pygame.SRCALPHA)
            pygame.draw.line(glass_surf, (255, 255, 255, 45), (0, 0), (cw, ch - 90), 20)
            pygame.draw.line(glass_surf, (255, 255, 255, 25), (40, 0), (cw, ch - 130), 10)
            canvas.blit(glass_surf, (cx, cy + 40))

            pygame.draw.rect(canvas, (55, 58, 60), (cx - 10, cy, cw + 20, 40))
            pygame.draw.rect(canvas, (25, 27, 28), (cx - 10, cy, cw + 20, 40), 4)

        # ==================================================================
        # 🏛️ 7. КОЛОННА КОЛЛЕКТОРА (prop_sewage_pillar) - Гнилой бетон и трещины
        # ==================================================================
        elif name == 'prop_sewage_pillar':
            bx, by, bw, bh = 100, 40, size - 200, size - 80
            pygame.draw.rect(canvas, (80, 82, 75), (bx, by, bw, bh))

            for _ in range(8):
                sx = random.randint(bx + 20, bx + bw - 60)
                sy = random.randint(by + 40, by + bh - 80)
                x1, y1 = sx, sy
                for _ in range(random.randint(3, 6)):
                    x2 = x1 + random.randint(-25, 25)
                    y2 = y1 + random.randint(15, 45)
                    if bx < x2 < bx + bw and by < y2 < by + bh:
                        pygame.draw.line(canvas, (35, 38, 33), (x1, y1), (x2, y2), 5)
                        pygame.draw.line(canvas, (120, 125, 110), (x1 + 2, y1), (x2 + 2, y2), 1)
                    x1, y1 = x2, y2

            for _ in range(12):
                slime_x = random.randint(bx + 15, bx + bw - 40)
                slime_y = random.randint(by, by + 100)
                slime_w = random.randint(15, 35)
                slime_h = random.randint(80, bh - 100)
                pygame.draw.ellipse(canvas, (10, 100, 25), (slime_x, slime_y, slime_w, slime_h))
                pygame.draw.ellipse(canvas, (0, 160, 40), (slime_x + 3, slime_y, slime_w - 6, slime_h - 10))
                pygame.draw.ellipse(canvas, (140, 255, 100), (slime_x + 6, slime_y + slime_h - 25, slime_w - 12, 15))

            pygame.draw.rect(canvas, (40, 42, 45), (bx + 30, by + bh - 140, 16, 90))
            for ry in range(by + bh - 130, by + bh - 60, 15):
                pygame.draw.line(canvas, (110, 50, 20), (bx + 25, ry), (bx + 50, ry + 5), 4)

        # ==================================================================
        # 🏗️ 8. БАЛКА АНГАРА (prop_hangar_frame) - Тяжелый двутавр
        # ==================================================================
        elif name == "prop_hangar_frame":
            pygame.draw.rect(canvas, (45, 48, 50), (60, size - 110, size - 120, 70))
            pygame.draw.rect(canvas, (20, 22, 23), (60, size - 110, size - 120, 70), 5)

            pygame.draw.line(canvas, (30, 32, 34), (100, size - 110), (size - 100, 80), 55)
            pygame.draw.line(canvas, (30, 32, 34), (size - 100, size - 110), (100, 80), 55)
            pygame.draw.line(canvas, (65, 68, 70), (100, size - 110), (size - 100, 80), 40)
            pygame.draw.line(canvas, (65, 68, 70), (size - 100, size - 110), (100, 80), 40)

            pygame.draw.line(canvas, (125, 128, 130), (100, size - 110), (size - 100, 80), 10)
            pygame.draw.line(canvas, (125, 128, 130), (size - 100, size - 110), (100, 80), 10)

            for joint_x, joint_y in [(120, size - 140), (size - 120, size - 140), (160, 130), (size - 160, 130)]:
                pygame.draw.circle(canvas, (20, 22, 23), (joint_x, joint_y), 10)
                pygame.draw.circle(canvas, (90, 95, 98), (joint_x, joint_y), 7)
                pygame.draw.circle(canvas, (255, 255, 255), (joint_x - 2, joint_y - 2), 2)

        # ==================================================================
        # ⛓️ 1. ТРУБА КОЛЛЕКТОРА (prop_sewage_pipe) - Вместо старой колонны
        # ==================================================================
        elif name == 'prop_sewage_pipe':
            px_w = 90
            pygame.draw.rect(canvas, (25, 27, 28), (mid - px_w // 2, 0, px_w, size))

            for x_line in range(mid - px_w // 2 + 4, mid + px_w // 2 - 4):
                grad = int(45 * math.sin((x_line - (mid - px_w // 2)) / px_w * math.pi))
                pygame.draw.line(canvas, (35 + grad, 40 + grad, 45 + grad), (x_line, 0), (x_line, size), 1)

            for fy in [40, mid, size - 80]:
                pygame.draw.rect(canvas, (20, 22, 23), (mid - px_w // 2 - 15, fy, px_w + 30, 24))
                pygame.draw.rect(canvas, (75, 80, 85), (mid - px_w // 2 - 12, fy + 3, px_w + 24, 18))
                for fx in range(mid - px_w // 2 - 5, mid + px_w // 2 + 10, 20):
                    pygame.draw.circle(canvas, (10, 12, 13), (fx, fy + 12), 4)

            for vy in [58, mid + 18]:
                for _ in range(3):
                    sx = mid + random.randint(-30, 30)
                    pygame.draw.line(canvas, (0, 180, 50), (sx, vy), (sx, vy + random.randint(40, 120)), random.randint(4, 8))

        # ==================================================================
        # ⚙️ 2. ИНДУСТРИАЛЬНЫЙ ГЕНЕРАТОР (prop_industrial_generator)
        # ==================================================================
        elif name == 'prop_industrial_generator':
            gx, gy, gw, gh = 60, size - 320, size - 120, 280
            pygame.draw.rect(canvas, (55, 65, 55), (gx, gy, gw, gh))
            pygame.draw.rect(canvas, (20, 25, 20), (gx, gy, gw, gh), 8)

            pygame.draw.rect(canvas, (10, 12, 10), (gx + gw - 120, gy + 40, 90, gh - 80))
            for rx in range(gx + gw - 110, gx + gw - 40, 14):
                pygame.draw.rect(canvas, (40, 45, 40), (rx, gy + 50, 6, gh - 100))

            for i in range(2):
                pygame.draw.circle(canvas, (15, 17, 15), (gx + 60 + i * 60, gy + 60), 22)
                pygame.draw.circle(canvas, (230, 225, 210), (gx + 60 + i * 60, gy + 60), 18)
                ang = random.uniform(0, math.pi)
                ex = gx + 60 + i * 60 + int(math.cos(ang) * 14)
                ey = gy + 60 - int(math.sin(ang) * 14)
                pygame.draw.line(canvas, (200, 0, 0), (gx + 60 + i * 60, gy + 60), (ex, ey), 3)

        # ==================================================================
        # 🌪️ 3. ВЕНТИЛЯЦИОННАЯ ТУРБИНА (prop_vent_fan)
        # ==================================================================
        elif name == 'prop_vent_fan':
            fx, fy, f_size = 50, 40, size - 100
            pygame.draw.rect(canvas, (45, 48, 50), (fx, fy, f_size, f_size))
            pygame.draw.circle(canvas, (10, 12, 13), (mid, mid), f_size // 2 - 20)
            pygame.draw.circle(canvas, (75, 80, 85), (mid, mid), f_size // 2 - 20, 8)

            for blade in range(6):
                ang = (blade * math.pi / 3) + 0.4
                x1 = mid + int(math.cos(ang) * 20)
                y1 = mid + int(math.sin(ang) * 20)
                x2 = mid + int(math.cos(ang) * (f_size // 2 - 35))
                y2 = mid + int(math.sin(ang) * (f_size // 2 - 35))
                pygame.draw.polygon(canvas, (35, 38, 40), [
                    (x1, y1), (x2, y2),
                    (x2 + int(math.cos(ang + 0.3) * 30), y2 + int(math.sin(ang + 0.3) * 30)),
                    (x1 + int(math.cos(ang + 0.3) * 10), y1 + int(math.sin(ang + 0.3) * 10))
                ])
            pygame.draw.circle(canvas, (20, 22, 23), (mid, mid), 24)
            pygame.draw.circle(canvas, (130, 135, 140), (mid, mid), 16)

        # ==================================================================
        # 🦠 4. ЛУЖА БИО-СЛИЗИ (prop_bio_puddle) - Плоский напольный декор
        # ==================================================================
        elif name == 'prop_bio_puddle':
            px, py, pw, ph = 40, size - 140, size - 80, 100
            pygame.draw.ellipse(canvas, (10, 90, 30), (px, py, pw, ph))
            pygame.draw.ellipse(canvas, (0, 190, 50), (px + 8, py + 6, pw - 16, ph - 12))

            for _ in range(8):
                bx = random.randint(px + 40, px + pw - 40)
                by = random.randint(py + 20, py + ph - 20)
                pygame.draw.circle(canvas, (140, 255, 90), (bx, by), random.randint(4, 9), 2)

        # ==================================================================
        # 🔬 5. ЛАБОРАТОРНЫЙ СТОЛ (prop_microscope_bench)
        # ==================================================================
        elif name == 'prop_microscope_bench':
            bx, by, bw, bh = 60, size - 280, size - 120, 240
            pygame.draw.rect(canvas, (140, 145, 150), (bx, by, bw, 25))
            pygame.draw.rect(canvas, (40, 42, 45), (bx + 15, by + 25, 30, bh - 25))
            pygame.draw.rect(canvas, (40, 42, 45), (bx + bw - 45, by + 25, 30, bh - 25))

            pygame.draw.rect(canvas, (55, 58, 60), (bx + 40, by - 70, 110, 70))
            pygame.draw.rect(canvas, (0, 30, 5), (bx + 50, by - 60, 60, 50))
            sin_pts = []
            for sx in range(bx + 52, bx + 108, 4):
                sy = by - 35 + int(math.sin(sx * 0.2) * 15)
                sin_pts.append((sx, sy))
            if len(sin_pts) > 1:
                pygame.draw.lines(canvas, (0, 255, 50), False, sin_pts, 2)

            pygame.draw.rect(canvas, (20, 22, 24), (bx + 180, by - 90, 40, 90))
            pygame.draw.ellipse(canvas, (100, 200, 255), (bx + 240, by - 40, 24, 40))

        # ==================================================================
        # ☣️ 6. ХИМИЧЕСКАЯ БОЧКА (prop_chemical_barrel)
        # ==================================================================
        elif name == 'prop_chemical_barrel':
            bx, by, bw, bh = 110, size - 340, size - 220, 300
            pygame.draw.rect(canvas, (200, 160, 0), (bx, by, bw, bh))
            pygame.draw.rect(canvas, (40, 35, 0), (bx, by, bw, bh), 6)

            for ry in [by + 60, by + 150, by + 240]:
                pygame.draw.rect(canvas, (35, 30, 0), (bx, ry, bw, 14))
                pygame.draw.line(canvas, (255, 220, 50), (bx, ry + 2), (bx + bw, ry + 2), 2)

            cx, cy = bx + bw // 2, by + bh // 2 - 10
            pygame.draw.circle(canvas, (20, 20, 20), (cx, cy), 28)
            pygame.draw.circle(canvas, (200, 160, 0), (cx, cy), 22)
            for sector in range(3):
                ang = sector * 2 * math.pi / 3
                p1 = (cx, cy)
                p2 = (cx + int(math.cos(ang - 0.4) * 32), cy + int(math.sin(ang - 0.4) * 32))
                p3 = (cx + int(math.cos(ang + 0.4) * 32), cy + int(math.sin(ang + 0.4) * 32))
                pygame.draw.polygon(canvas, (20, 20, 20), [p1, p2, p3])
            pygame.draw.circle(canvas, (20, 20, 20), (cx, cy), 8)

        # ==================================================================
        # 💡 7. ПОДВЕСНОЙ ПРОЖЕКТОР (prop_ceiling_lamp) - Прижат к потолку
        # ==================================================================
        elif name == 'prop_ceiling_lamp':
            pygame.draw.rect(canvas, (50, 52, 55), (mid - 50, 0, 100, 30))
            pygame.draw.line(canvas, (20, 22, 23), (mid, 30), (mid, 120), 12)

            lamp_p = [(mid - 80, 200), (mid + 80, 200), (mid + 30, 120), (mid - 30, 120)]
            pygame.draw.polygon(canvas, (75, 80, 85), lamp_p)
            pygame.draw.polygon(canvas, (35, 38, 40), lamp_p, 4)

            pygame.draw.ellipse(canvas, (180, 240, 255), (mid - 76, 185, 152, 30))
            pygame.draw.ellipse(canvas, (255, 255, 255), (mid - 50, 190, 100, 16))

        # ==================================================================
        # 🚨 8. ПУЛЬТ УПРАВЛЕНИЯ (prop_control_console)
        # ==================================================================
        elif name == 'prop_control_console':
            bx, by, bw, bh = 70, size - 290, size - 140, 250
            console_p = [(bx + 40, by), (bx + bw - 40, by), (bx + bw, by + bh), (bx, by + bh)]
            pygame.draw.polygon(canvas, (45, 48, 52), console_p)
            pygame.draw.polygon(canvas, (20, 22, 24), console_p, 6)

            for row_k in range(by + 40, by + bh - 40, 45):
                for col_k in range(bx + 50, bx + bw - 60, 36):
                    progress = (row_k - by) / bh
                    sx = col_k + int((row_k - (by + 40)) * 0.08)
                    if random.random() < 0.8:
                        btn_c = random.choice([(255, 0, 50), (0, 255, 100), (255, 220, 0), (40, 45, 50)])
                        pygame.draw.rect(canvas, btn_c, (sx, row_k, 20, 20))
                        pygame.draw.rect(canvas, (10, 12, 13), (sx, row_k, 20, 20), 2)
                        if btn_c != (40, 45, 50):
                            pygame.draw.rect(canvas, (255, 255, 255), (sx + 3, row_k + 3, 4, 4))

        # ==================================================================
        # ⚡ 9. ЛАЗЕРНАЯ ЗАЩИТНАЯ ТУРЕЛЬ (prop_laser_grid)
        # ==================================================================
        elif name == 'prop_laser_grid':
            pygame.draw.rect(canvas, (40, 45, 48), (mid - 60, 0, 120, 45))
            pygame.draw.rect(canvas, (40, 45, 48), (mid - 60, size - 45, 120, 45))

            pygame.draw.circle(canvas, (20, 22, 24), (mid, 45), 20)
            pygame.draw.circle(canvas, (20, 22, 24), (mid, size - 45), 20)

            for lx_offset in [-24, 0, 24]:
                lx = mid + lx_offset
                pygame.draw.line(canvas, (255, 0, 0), (lx, 45), (lx, size - 45), 10)
                pygame.draw.line(canvas, (255, 240, 240), (lx, 45), (lx, size - 45), 3)

        # ==================================================================
        # 💣 10. ОТКРЫТЫЙ ЯЩИК С ПАТРОНАМИ (prop_ammo_crate)
        # ==================================================================
        elif name == 'prop_ammo_crate':
            bx, by, bw, bh = 60, size - 220, size - 120, 180
            pygame.draw.rect(canvas, (70, 75, 70), (bx, by, bw, bh))
            pygame.draw.rect(canvas, (35, 38, 35), (bx, by, bw, bh), 6)

            for rx in range(bx + 30, bx + bw - 40, 36):
                pygame.draw.rect(canvas, (130, 50, 30), (rx, by + 20, 24, bh - 40))
                pygame.draw.polygon(canvas, (200, 190, 0), [(rx, by + 20), (rx + 24, by + 20), (rx + 12, by - 15)])
                pygame.draw.rect(canvas, (20, 22, 23), (rx, by + 20, 24, bh - 40), 2)

        # ==================================================================
        # 🚜 11. СКЛАДСКОЙ ПОГРУЗЧИК АНГАРА (prop_forklift)
        # ==================================================================
        elif name == 'prop_forklift':
            pygame.draw.circle(canvas, (15, 17, 18), (140, size - 70), 55)
            pygame.draw.circle(canvas, (15, 17, 18), (size - 140, size - 70), 55)
            pygame.draw.circle(canvas, (80, 85, 90), (140, size - 70), 25)
            pygame.draw.circle(canvas, (80, 85, 90), (size - 140, size - 70), 25)

            pygame.draw.rect(canvas, (220, 160, 0), (100, size - 260, size - 200, 140))
            pygame.draw.rect(canvas, (30, 32, 35), (100, size - 260, size - 200, 140), 8)

            pygame.draw.rect(canvas, (50, 53, 55), (40, size - 140, 60, 20))
            pygame.draw.rect(canvas, (30, 32, 35), (90, size - 280, 16, 160))
        
        # ==================================================================
        # 🚨 ЧИСТОКРОВНЫЙ DOOM-ХАК: ЖИРНЫЙ ПИКСЕЛЬНЫЙ КОНТУР И ОБВОДКА
        # ==================================================================
        mask = pygame.mask.from_surface(canvas)
        outline_surf = mask.to_surface(setcolor=(0, 0, 0, 255), unsetcolor=(0, 0, 0, 0))

        for dx, dy in [(-6, 0), (6, 0), (0, -6), (0, 6), (-4, -4), (4, -4), (-4, 4), (4, 4)]:
            surf.blit(outline_surf, (dx, dy))

        surf.blit(canvas, (0, 0))

        for _ in range(int(size * size * 0.05)):
            px, py = random.randint(0, size - 1), random.randint(0, size - 1)
            r, g, b, a = surf.get_at((px, py))
            if a > 0 and r + g + b > 0:
                n = random.randint(-15, 15)
                surf.set_at((px, py), (max(0, min(255, r + n)), max(0, min(255, g + n)), max(0, min(255, b + n)), a))

        try:
            pygame.image.save(surf, path)
            print(f"  • [ЗАПИСЬ УСПЕШНА] Doom-биллборд сгенерирован: {path}")
        except Exception as e:
            print(f"  • [СБОЙ ЗАПИСИ] Не удалось сохранить файл: {e}")

    print("\n🏁 [DOOM-STYLE SPRITE GENERATOR COMPLETE]\n")


if __name__ == "__main__":
    generate_procedural_decorations(size=512)