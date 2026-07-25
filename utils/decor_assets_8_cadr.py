import os
import pygame
import random
import math


def generate_flat_texture_source(name, size=512):
    """Генерирует сплошной плоский холст текстуры высокого качества"""
    surf = pygame.Surface((size, size))

    # 📦 ТЕКСТУРА ДОСОК ДЛЯ ЯЩИКОВ
    if name in ('prop_military_crate', 'prop_cargo_pallet'):
        surf.fill((115, 75, 45))
        for y in range(0, size, 64):
            pygame.draw.line(surf, (65, 40, 20), (0, y), (size, y), 8)
        for _ in range(int(size * size * 0.15)):
            px, py = random.randint(0, size - 1), random.randint(0, size - 1)
            r, g, b, _ = surf.get_at((px, py))
            n = random.randint(-14, 14)
            surf.set_at((px, py), (max(0, min(255, r + n)), max(0, min(255, g + n)), max(0, min(255, b + n))))

    # 🎛️ ТЕКСТУРА СЕРВЕРОВ И СУПЕРКОМПЬЮТЕРОВ
    elif name in ('prop_server_rack', 'prop_mainframe_wall', 'prop_control_console'):
        surf.fill((35, 38, 40))
        for y in range(size):
            bright = random.randint(-8, 8)
            for x in range(size):
                surf.set_at((x, y), (max(0, min(255, 35 + bright)), max(0, min(255, 38 + bright)), max(0, min(255, 40 + bright))))
        for y in range(40, size, 64):
            pygame.draw.rect(surf, (12, 14, 15), (20, y, size - 40, 44))
            for kx in range(30, size - 160, 14):
                pygame.draw.line(surf, (40, 45, 48), (kx, y + 8), (kx, y + 36), 3)

    # ⛓️ ТЕКСТУРА ШТАМПОВАННОЙ ГОФРЫ
    elif name == 'prop_cargo_container':
        surf.fill((30, 85, 155))
        for x in range(0, size, 32):
            pygame.draw.rect(surf, (15, 50, 100), (x, 0, 16, size))
            pygame.draw.line(surf, (65, 135, 220), (x + 16, 0), (x + 16, size), 2)

    # 🏛️ ТЕКСТУРА ГРЯЗНОГО БЕТОНА (дефолт)
    else:
        surf.fill((90, 92, 85))
        for step in range(0, size, 128):
            pygame.draw.line(surf, (50, 52, 48), (0, step), (size, step), 4)
            pygame.draw.line(surf, (50, 52, 48), (step, 0), (step, size), 4)
        for _ in range(int(size * size * 0.1)):
            px, py = random.randint(0, size - 1), random.randint(0, size - 1)
            r, g, b, _ = surf.get_at((px, py))
            n = random.randint(-15, 15)
            surf.set_at((px, py), (max(0, min(255, r + n)), max(0, min(255, g + n)), max(0, min(255, b + n))))

    return surf


def blit_texture_via_mask(target_canvas, texture_source, polygon_points, color_tint=(255, 255, 255)):
    """Вырезает кусок из сплошной текстуры по форме 3D-полигона"""
    size = target_canvas.get_width()

    mask_surf = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.polygon(mask_surf, (255, 255, 255, 255), polygon_points)

    tinted_texture = texture_source.copy()
    tint_surf = pygame.Surface((size, size))
    tint_surf.fill(color_tint)
    tinted_texture.blit(tint_surf, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

    tinted_texture.blit(mask_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    target_canvas.blit(tinted_texture, (0, 0))


def generate_procedural_decorations(size=512):
    """Полноценный 8-ракурсный генератор с текстурированием граней"""

    print("\n💀 [HELLISH TEXTURED DOOM SPRITE PIPELINE STARTING]")

    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    base_folder = os.path.join(project_root, 'resources', 'decorations')
    os.makedirs(base_folder, exist_ok=True)

    if not pygame.get_init():
        pygame.init()

    DECOR_GEOMETRY = {
        'prop_military_crate': 'BOX',
        'prop_sandbag_wall': 'CYLINDER',
        'prop_sewage_pillar': 'BOX',
        'prop_lab_capsule': 'CYLINDER',
        'prop_server_rack': 'BOX',
        'prop_core_reactor': 'CYLINDER',
        'prop_cargo_container': 'BOX',
        'prop_hangar_frame': 'BOX',
        'prop_sewage_pipe': 'CYLINDER',
        'prop_industrial_generator': 'BOX',
        'prop_vent_fan': 'BOX',
        'prop_bio_puddle': 'FLAT',
        'prop_microscope_bench': 'BOX',
        'prop_chemical_barrel': 'CYLINDER',
        'prop_ceiling_lamp': 'CYLINDER',
        'prop_control_console': 'BOX',
        'prop_laser_grid': 'BOX',
        'prop_ammo_crate': 'BOX',
        'prop_forklift': 'BOX',
        'prop_searchlight': 'CYLINDER',
        'prop_comm_antenna': 'CYLINDER',
        'prop_sewage_pump': 'BOX',
        'prop_toxic_waste': 'CYLINDER',
        'prop_hydraulic_press': 'BOX',
        'prop_autopsy_table': 'BOX',
        'prop_decon_shower': 'BOX',
        'prop_mainframe_wall': 'BOX',
        'prop_stasis_chamber': 'BOX',
        'prop_fuel_tank': 'CYLINDER',
        'prop_cargo_pallet': 'BOX'
    }

    for name, shape_type in DECOR_GEOMETRY.items():
        obj_folder = os.path.join(base_folder, name)
        os.makedirs(obj_folder, exist_ok=True)
        print(f"🧱 [МАСКИРОВАНИЕ ТЕКСТУР] Рендеринг папки: {name}")

        random.seed(42)
        texture_source = generate_flat_texture_source(name, size)

        for angle_idx in range(1, 9):
            path_angle = os.path.join(obj_folder, f"{angle_idx}.png")

            frame_surf = pygame.Surface((size, size), pygame.SRCALPHA)
            canvas = pygame.Surface((size, size), pygame.SRCALPHA)
            mid = size // 2

            tint_top = (255, 255, 255)
            tint_left = (180, 184, 190)
            tint_right = (100, 102, 105)

            # ==============================================================
            # ТРАФАРЕТ 1: НАРЕЗКА ТЕКСТУРЫ НА ГРАНИ КУБА (BOX)
            # ==============================================================
            if shape_type == 'BOX':
                bx, by, bw, bh = 80, 120, size - 160, size - 180
                h_top = 45

                if angle_idx in (1, 5):
                    blit_texture_via_mask(canvas, texture_source, [(bx, by), (bx + bw, by), (bx + bw, by + bh), (bx, by + bh)], tint_left)

                elif angle_idx in (3, 7):
                    blit_texture_via_mask(canvas, texture_source, [(mid - bw // 4, by), (mid + bw // 4, by), (mid + bw // 4, by + bh), (mid - bw // 4, by + bh)], tint_right)

                elif angle_idx in (2, 6):
                    poly_top = [(mid, by - h_top), (bx + bw, by), (mid, by + h_top), (bx, by)]
                    poly_left = [(bx, by), (mid, by + h_top), (mid, by + bh), (bx, by + bh - h_top)]
                    poly_right = [(mid, by + h_top), (bx + bw, by), (bx + bw, by + bh - h_top), (mid, by + bh)]

                    blit_texture_via_mask(canvas, texture_source, poly_top, tint_top)
                    blit_texture_via_mask(canvas, texture_source, poly_left, tint_left)
                    blit_texture_via_mask(canvas, texture_source, poly_right, tint_right)

                elif angle_idx in (4, 8):
                    poly_top = [(mid, by - h_top), (bx + bw, by), (mid, by + h_top), (bx, by)]
                    poly_right = [(bx, by), (mid, by + h_top), (mid, by + bh), (bx, by + bh - h_top)]
                    poly_left = [(mid, by + h_top), (bx + bw, by), (bx + bw, by + bh - h_top), (mid, by + bh)]

                    blit_texture_via_mask(canvas, texture_source, poly_top, tint_top)
                    blit_texture_via_mask(canvas, texture_source, poly_left, tint_left)
                    blit_texture_via_mask(canvas, texture_source, poly_right, tint_right)

            # ==============================================================
            # ТРАФАРЕТ 2: МАСКА ДЛЯ КРУГЛЫХ ЦИЛИНДРОВ (CYLINDER)
            # ==============================================================
            elif shape_type == 'CYLINDER':
                rx_w, rx_h = size - 200, 100
                by, bh = 140, size - 220

                blit_texture_via_mask(canvas, texture_source, [(mid - rx_w // 2, by), (mid + rx_w // 2, by), (mid + rx_w // 2, by + bh), (mid - rx_w // 2, by + bh)], tint_left)
                pygame.draw.ellipse(canvas, (40, 42, 45), (mid - rx_w // 2, by - rx_h // 2, rx_w, rx_h))

                shadow_overlay = pygame.Surface((size, size), pygame.SRCALPHA)
                for x_line in range(mid - rx_w // 2, mid + rx_w // 2):
                    grad = int(140 * math.sin((x_line - (mid - rx_w // 2)) / rx_w * math.pi))
                    pygame.draw.line(shadow_overlay, (0, 0, 0, 200 - grad), (x_line, by), (x_line, by + bh), 1)
                canvas.blit(shadow_overlay, (0, 0))

            # ==============================================================
            # ТРАФАРЕТ 3: МАСКА НАПОЛЬНЫХ ЛУЖ (FLAT)
            # ==============================================================
            elif shape_type == 'FLAT':
                blit_texture_via_mask(canvas, texture_source, [(60, size - 160), (size - 60, size - 160), (size - 60, size - 60), (60, size - 60)], tint_left)

            # Дополнительные детали
            if name in ('prop_server_rack', 'prop_mainframe_wall') and angle_idx in (1, 2, 8):
                for led_y in range(160, size - 120, 64):
                    pygame.draw.circle(canvas, random.choice([(0, 255, 50), (255, 0, 0)]), (mid - 30, led_y), 6)
                    pygame.draw.circle(canvas, (255, 255, 255), (mid - 32, led_y - 2), 2)

            # ==============================================================
            # DOOM-ОБВОДКА
            # ==============================================================
            mask = pygame.mask.from_surface(canvas)
            outline_surf = mask.to_surface(setcolor=(0, 0, 0, 255), unsetcolor=(0, 0, 0, 0))

            for dx, dy in [(-6, 0), (6, 0), (0, -6), (0, 6), (-4, -4), (4, -4), (-4, 4), (4, 4)]:
                frame_surf.blit(outline_surf, (dx, dy))

            frame_surf.blit(canvas, (0, 0))

            pygame.image.save(frame_surf, path_angle)

        random.seed(None)

    print("\n🏁 [HELLISH TEXTURED PIPELINE COMPLETE!]\n")


if __name__ == "__main__":
    generate_procedural_decorations(size=512)