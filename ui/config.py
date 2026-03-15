import pygame
import json
import os
import math
import random
import time
from datetime import datetime, timedelta

# Importer les constantes et les widgets partagés
from .constants import WHITE, BLACK, GREEN_PRIMARY, GRAY_LIGHT, GRAY_DARK, GREEN_LIGHT, GREEN_DARK, ORANGE
from .widgets import get_font, render_text_with_emojis

# Importer la fonction de l'API NASA
from core.nasa_api import get_nasa_power_data


# ─────────────────────────────────────────────
#  PALETTE ÉTENDUE (cohérente avec menu.py)
# ─────────────────────────────────────────────
GREEN_GLOW    = (80,  200,  80)
BG_TOP        = (232, 245, 228)
BG_BOTTOM     = (195, 230, 185)
PANEL_BG      = (248, 253, 245)
PANEL_BORDER  = GREEN_PRIMARY
STEPPER_BG    = (60,  90,  70)
STEPPER_HOVER = (80, 120,  90)
CARD_SHADOW   = (0, 0, 0, 25)
PARTICLE_COLS = [
    (100, 200,  80), (140, 220, 100),
    ( 60, 160,  60), (180, 230, 130),
    ( 80, 180,  90),
]
WARN_COLOR    = (220, 100, 30)
TEXT_DARK     = (40,  70,  40)


# ─────────────────────────────────────────────
#  PARTICULE (même logique que menu.py)
# ─────────────────────────────────────────────
class Particle:
    def __init__(self, width, height):
        self.W = width
        self.H = height
        self.reset(initial=True)

    def reset(self, initial=False):
        self.x     = random.uniform(0, self.W)
        self.y     = random.uniform(0, self.H) if initial else self.H + 10
        self.size  = random.uniform(3, 10)
        self.speed = random.uniform(0.25, 1.0)
        self.drift = random.uniform(-0.35, 0.35)
        self.alpha = random.randint(55, 150)
        self.color = random.choice(PARTICLE_COLS)
        self.angle = random.uniform(0, 360)
        self.spin  = random.uniform(-1.4, 1.4)
        self.shape = random.choice(["leaf", "circle", "diamond"])
        self.wobble_offset = random.uniform(0, math.pi * 2)
        self.wobble_speed  = random.uniform(0.5, 1.4)

    def update(self, dt):
        t = time.time()
        wobble = math.sin(t * self.wobble_speed + self.wobble_offset) * 0.45
        self.x    += (self.drift + wobble) * dt * 60
        self.y    -= self.speed * dt * 60
        self.angle = (self.angle + self.spin * dt * 60) % 360
        if self.y < -20:
            self.reset()

    def draw(self, surface):
        s = self.size
        col = (*self.color, self.alpha)
        tmp = pygame.Surface((int(s * 3), int(s * 3)), pygame.SRCALPHA)
        cx, cy = int(s * 1.5), int(s * 1.5)
        if self.shape == "circle":
            pygame.draw.circle(tmp, col, (cx, cy), int(s))
        elif self.shape == "diamond":
            pts = [(cx, cy - s), (cx + s, cy), (cx, cy + s), (cx - s, cy)]
            pygame.draw.polygon(tmp, col, pts)
        else:
            pts = [(cx, cy - s), (cx + s * 0.6, cy), (cx, cy + s * 0.4), (cx - s * 0.6, cy)]
            pygame.draw.polygon(tmp, col, pts)
        rotated = pygame.transform.rotate(tmp, self.angle)
        rect = rotated.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(rotated, rect)


# ─────────────────────────────────────────────
#  BOUTON ANIMÉ (identique à menu.py)
# ─────────────────────────────────────────────
class AnimatedButton:
    def __init__(self, cx, y, w, h, text,
                 color=GREEN_PRIMARY, text_color=WHITE,
                 font_size=22, disabled=False, radius=None):
        self.cx         = cx
        self.y          = y
        self.base_w     = w
        self.base_h     = h
        self.text       = text
        self.color      = color
        self.text_color = text_color
        self.font_size  = font_size
        self.disabled   = disabled
        self.radius     = radius  # None = auto

        self.scale        = 1.0
        self.target_scale = 1.0
        self.glow_alpha   = 0
        self.hover        = False
        self.click_anim   = 0.0

    def get_rect(self):
        w = int(self.base_w * self.scale)
        h = int(self.base_h * self.scale)
        return pygame.Rect(self.cx - w // 2, self.y - (h - self.base_h) // 2, w, h)

    def update(self, dt, mouse_pos):
        if self.disabled:
            return
        rect = pygame.Rect(self.cx - self.base_w // 2, self.y, self.base_w, self.base_h)
        self.hover = rect.collidepoint(mouse_pos)
        self.target_scale = 1.06 if self.hover else 1.0
        speed = 8.0
        self.scale      += (self.target_scale - self.scale) * min(1.0, dt * speed)
        target_glow = 180 if self.hover else 0
        self.glow_alpha += (target_glow - self.glow_alpha) * min(1.0, dt * 6)
        if self.click_anim > 0:
            self.click_anim = max(0.0, self.click_anim - dt * 4)

    def draw(self, surface, font):
        rect = self.get_rect()
        r = self.radius if self.radius is not None else min(rect.height // 2, 22)

        col  = GRAY_LIGHT if self.disabled else self.color
        tcol = (150, 150, 150) if self.disabled else self.text_color

        # Ombre
        sh = pygame.Surface((rect.width + 8, rect.height + 8), pygame.SRCALPHA)
        pygame.draw.rect(sh, (0, 0, 0, 35), pygame.Rect(4, 4, rect.width, rect.height), border_radius=r)
        surface.blit(sh, (rect.x - 4, rect.y - 4))

        # Glow
        if self.glow_alpha > 5 and not self.disabled:
            gs = pygame.Surface((rect.width + 30, rect.height + 30), pygame.SRCALPHA)
            for extra in range(0, 16, 4):
                ec = (*GREEN_GLOW, int(self.glow_alpha * (0.30 - extra * 0.015)))
                er = pygame.Rect(15 - extra // 2, 15 - extra // 2,
                                 rect.width + extra, rect.height + extra)
                pygame.draw.rect(gs, ec, er, border_radius=r + extra // 2 + 2)
            surface.blit(gs, (rect.x - 15, rect.y - 15))

        # Corps
        pygame.draw.rect(surface, col, rect, border_radius=r)

        # Reflet
        if not self.disabled:
            sh2 = max(4, rect.height // 3)
            shine = pygame.Surface((rect.width - 4, sh2), pygame.SRCALPHA)
            for sy in range(sh2):
                a = int(55 * (1 - sy / sh2))
                pygame.draw.line(shine, (255, 255, 255, a), (0, sy), (rect.width - 4, sy))
            surface.blit(shine, (rect.x + 2, rect.y + 2))

        # Flash clic
        if self.click_anim > 0:
            cs = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            pygame.draw.rect(cs, (255, 255, 255, int(self.click_anim * 110)), cs.get_rect(), border_radius=r)
            surface.blit(cs, rect)

        # Texte
        ts = font.render(self.text, True, tcol)
        surface.blit(ts, ts.get_rect(center=rect.center))

    def handle_event(self, event):
        if self.disabled:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.get_rect().collidepoint(event.pos):
                self.click_anim = 1.0
                return True
        return False


# ─────────────────────────────────────────────
#  STEPPER (−  valeur  +) animé
# ─────────────────────────────────────────────
class Stepper:
    """Composant −/valeur/+ avec animation de rebond sur la valeur."""

    def __init__(self, cx, cy, label, value, min_val, max_val,
                 w=300, h=54, font_sizes=(22, 52)):
        self.cx      = cx
        self.cy      = cy
        self.label   = label
        self.value   = value
        self.min_val = min_val
        self.max_val = max_val
        self.w       = w
        self.h       = h
        self.lbl_fs  = font_sizes[0]
        self.val_fs  = font_sizes[1]

        btn_size     = h
        self.minus_btn = AnimatedButton(cx - w // 2 + btn_size // 2, cy,
                                        btn_size, btn_size, "−",
                                        STEPPER_BG, WHITE, font_sizes[0], radius=12)
        self.plus_btn  = AnimatedButton(cx + w // 2 - btn_size // 2, cy,
                                        btn_size, btn_size, "+",
                                        STEPPER_BG, WHITE, font_sizes[0], radius=12)
        self.val_scale  = 1.0
        self.val_target = 1.0
        self.val_alpha  = 255
        self.changed    = False

    def update(self, dt, mouse):
        self.minus_btn.update(dt, mouse)
        self.plus_btn.update(dt, mouse)
        # Animation valeur
        if self.val_scale > 1.0:
            self.val_scale = max(1.0, self.val_scale - dt * 6)
        speed = 10
        self.val_scale += (self.val_target - self.val_scale) * min(1.0, dt * speed)
        if abs(self.val_scale - self.val_target) < 0.01:
            self.val_scale = self.val_target
            if self.val_target != 1.0:
                self.val_target = 1.0

    def bump(self):
        self.val_target = 1.18

    def handle_event(self, event):
        if self.minus_btn.handle_event(event):
            if self.value > self.min_val:
                self.value -= 1
                self.bump()
                return "minus"
        if self.plus_btn.handle_event(event):
            if self.value < self.max_val:
                self.value += 1
                self.bump()
                return "plus"
        return None

    def draw(self, surface, lbl_font, val_font):
        cx, cy = self.cx, self.cy

        # Label au-dessus
        ls = lbl_font.render(self.label, True, GREEN_DARK)
        surface.blit(ls, ls.get_rect(centerx=cx, bottom=cy - 6))

        # Fond du stepper
        bg_rect = pygame.Rect(cx - self.w // 2, cy, self.w, self.h)
        bg_s = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        pygame.draw.rect(bg_s, (255, 255, 255, 120), bg_s.get_rect(), border_radius=14)
        pygame.draw.rect(bg_s, (*GREEN_PRIMARY, 80), bg_s.get_rect(), width=2, border_radius=14)
        surface.blit(bg_s, bg_rect)

        # Boutons
        self.minus_btn.draw(surface, lbl_font)
        self.plus_btn.draw(surface, lbl_font)

        # Valeur animée
        vs = val_font.render(str(self.value), True, GREEN_PRIMARY)
        if self.val_scale != 1.0:
            nw = int(vs.get_width() * self.val_scale)
            nh = int(vs.get_height() * self.val_scale)
            vs = pygame.transform.smoothscale(vs, (max(1, nw), max(1, nh)))
        surface.blit(vs, vs.get_rect(center=(cx, cy + self.h // 2)))


# ─────────────────────────────────────────────
#  PANNEAU INFO avec fade-in
# ─────────────────────────────────────────────
class InfoPanel:
    def __init__(self, rect, title, lines, icon=""):
        self.rect    = rect
        self.title   = title
        self.lines   = lines
        self.icon    = icon
        self.alpha   = 0
        self.surface = None

    def update(self, dt, target_alpha=255):
        self.alpha = min(target_alpha, self.alpha + dt * 400)

    def draw(self, screen, title_font, body_font):
        r = self.rect
        a = int(self.alpha)

        surf = pygame.Surface((r.width, r.height), pygame.SRCALPHA)

        # Ombre
        sh = pygame.Surface((r.width + 10, r.height + 10), pygame.SRCALPHA)
        pygame.draw.rect(sh, (0, 0, 0, int(a * 0.12)),
                         pygame.Rect(5, 5, r.width, r.height), border_radius=16)
        screen.blit(sh, (r.x - 5, r.y - 5))

        # Corps
        pygame.draw.rect(surf, (*PANEL_BG, a), surf.get_rect(), border_radius=16)
        pygame.draw.rect(surf, (*GREEN_PRIMARY, min(a, 200)), surf.get_rect(),
                         width=2, border_radius=16)

        # Titre
        t_str = f"{self.icon}  {self.title}" if self.icon else self.title
        ts = title_font.render(t_str, True, (*GREEN_DARK, a))
        surf.blit(ts, (14, 12))

        # Séparateur
        sep_y = 12 + ts.get_height() + 6
        pygame.draw.line(surf, (*GREEN_PRIMARY, int(a * 0.4)),
                         (14, sep_y), (r.width - 14, sep_y), 1)

        # Lignes de texte
        line_y = sep_y + 10
        for line in self.lines:
            ls = body_font.render(line, True, (*TEXT_DARK, a))
            surf.blit(ls, (18, line_y))
            line_y += ls.get_height() + 5

        screen.blit(surf, r)


# ─────────────────────────────────────────────
#  INTERFACE CONFIGURATION PRINCIPALE
# ─────────────────────────────────────────────
class ConfigInterface:
    def __init__(self, screen):
        self.screen = screen
        self.width  = screen.get_width()
        self.height = screen.get_height()
        self._last_time = time.time()

        # ── Polices responsive ──
        title_fs    = max(36, int(self.height * 0.075))
        subtitle_fs = max(16, int(self.height * 0.026))
        body_fs     = max(13, int(self.height * 0.022))
        btn_fs      = max(15, int(self.height * 0.025))
        val_fs      = max(30, int(self.height * 0.062))

        self.title_font    = get_font(title_fs)
        self.subtitle_font = get_font(subtitle_fs)
        self.body_font     = get_font(body_fs)
        self.btn_font      = get_font(btn_fs)
        self.val_font      = get_font(val_fs)

        # ── Données ──
        self.selected_plots  = 6
        self.selected_years  = 1
        self.selected_config = None
        self.status_message  = ""
        self.loading         = False

        self.region_data       = self._load_regions()
        self.locations         = list(self.region_data.keys())
        self.location_index    = 0
        self.selected_location = self.locations[self.location_index] if self.locations else ""
        self.nasa_api_key      = os.getenv("NASA_API_KEY")

        # ── Layout ──
        cx  = self.width  // 2
        W   = self.width
        H   = self.height

        # Zone contrôles (haut)
        ctrl_y  = int(H * 0.18)
        step_h  = max(44, int(H * 0.065))
        step_w  = min(280, int(W * 0.30))
        val_fs2 = max(28, int(H * 0.058))
        lbl_fs2 = max(14, int(H * 0.024))

        # Steppers
        self.plots_stepper = Stepper(
            cx=int(W * 0.28), cy=ctrl_y,
            label="Nombre de parcelles",
            value=self.selected_plots, min_val=3, max_val=12,
            w=step_w, h=step_h,
            font_sizes=(lbl_fs2, val_fs2)
        )
        self.years_stepper = Stepper(
            cx=int(W * 0.72), cy=ctrl_y,
            label="Durée (années)",
            value=self.selected_years, min_val=1, max_val=5,
            w=step_w, h=step_h,
            font_sizes=(lbl_fs2, val_fs2)
        )

        # Localisation
        loc_y    = int(H * 0.36)
        nav_size = max(38, int(H * 0.055))
        self.loc_y       = loc_y
        self.nav_size    = nav_size
        self.loc_prev    = AnimatedButton(cx - int(W * 0.22), loc_y + nav_size // 2,
                                          nav_size, nav_size, "←",
                                          STEPPER_BG, WHITE, lbl_fs2, radius=12)
        self.loc_next    = AnimatedButton(cx + int(W * 0.22), loc_y + nav_size // 2,
                                          nav_size, nav_size, "→",
                                          STEPPER_BG, WHITE, lbl_fs2, radius=12)
        # Animation carrousel
        self.loc_slide_x  = 0.0
        self.loc_target_x = 0.0
        self.loc_anim_dir = 0

        # Panneaux info
        panel_top = int(H * 0.50)
        panel_h   = int(H * 0.30)
        margin    = int(W * 0.04)
        total_w   = W - 2 * margin
        gap       = int(W * 0.02)
        soil_w    = int(total_w * 0.52)
        crop_w    = total_w - soil_w - gap
        self.soil_rect = pygame.Rect(margin, panel_top, soil_w, panel_h)
        self.crop_rect = pygame.Rect(margin + soil_w + gap, panel_top, crop_w, panel_h)
        self.soil_panel = None
        self.crop_panel = None
        self._build_panels()

        # Boutons du bas
        bot_y    = int(H * 0.86)
        conf_w   = min(220, int(W * 0.22))
        conf_h   = max(44, int(H * 0.062))
        back_w   = min(140, int(W * 0.14))

        self.confirm_btn = AnimatedButton(cx, bot_y, conf_w, conf_h,
                                          "Confirmer", GREEN_PRIMARY, WHITE, btn_fs)
        self.back_btn    = AnimatedButton(int(W * 0.10), bot_y, back_w, conf_h,
                                          "← Retour", STEPPER_BG, WHITE, btn_fs)

        # Particules
        n = max(14, int(W * H / 28000))
        self.particles     = [Particle(W, H) for _ in range(n)]
        self._particle_surf = pygame.Surface((W, H), pygame.SRCALPHA)
        self._bg_surface    = self._build_bg()

        # Animation chargement
        self._load_angle = 0.0

    # ── Fond dégradé ─────────────────────────────
    def _build_bg(self):
        surf = pygame.Surface((self.width, self.height))
        for y in range(self.height):
            t = y / self.height
            r = int(BG_TOP[0] * (1 - t) + BG_BOTTOM[0] * t)
            g = int(BG_TOP[1] * (1 - t) + BG_BOTTOM[1] * t)
            b = int(BG_TOP[2] * (1 - t) + BG_BOTTOM[2] * t)
            pygame.draw.line(surf, (r, g, b), (0, y), (self.width, y))
        return surf

    # ── Panneaux info ─────────────────────────────
    def _build_panels(self):
        if not self.selected_location or self.selected_location not in self.region_data:
            self.soil_panel = None
            self.crop_panel = None
            return
        info = self.region_data[self.selected_location]

        soil_lines = [
            f"Climat : {info.get('climat', '—')}",
            f"Type de sol : {info.get('sol', '—')}",
            f"pH optimal : {info.get('ph', '—')}",
        ]
        if "pluviometrie" in info:
            soil_lines.append(f"Pluviométrie : {info['pluviometrie']}")

        cultures = info.get("cultures", [])
        crop_lines = []
        for i in range(0, len(cultures), 2):
            left  = f"• {cultures[i]}"
            right = f"• {cultures[i+1]}" if i + 1 < len(cultures) else ""
            crop_lines.append(f"{left:<22}{right}")

        self.soil_panel = InfoPanel(self.soil_rect, "Caractéristiques du Sol",
                                    soil_lines, icon="🌍")
        self.soil_panel.alpha = 0
        self.crop_panel = InfoPanel(self.crop_rect, "Cultures Disponibles",
                                    crop_lines, icon="🌱")
        self.crop_panel.alpha = 0

    # ── Chargement régions ────────────────────────
    def _load_regions(self):
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        regions_path = os.path.join(project_root, "data", "regions_fr.json")
        try:
            with open(regions_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Erreur: Fichier '{regions_path}' introuvable ou invalide. {e}")
            return {}

    # ── Écran de chargement ───────────────────────
    def _draw_loading(self, dt):
        self.screen.blit(self._bg_surface, (0, 0))
        cx, cy = self.width // 2, self.height // 2

        # Spinner arc
        self._load_angle = (self._load_angle + dt * 270) % 360
        for i in range(8):
            angle = math.radians(self._load_angle + i * 45)
            a     = int(255 * (i + 1) / 8)
            r     = 32
            x = cx + int(r * math.cos(angle))
            y = cy - 40 + int(r * math.sin(angle))
            pygame.draw.circle(self.screen, (*GREEN_PRIMARY, a),
                               (x, y), max(3, 8 - i))

        # Texte
        ts = self.subtitle_font.render(self.status_message, True, GREEN_DARK)
        self.screen.blit(ts, ts.get_rect(centerx=cx, y=cy + 10))

        # Titre en haut
        title_s = self.title_font.render("CONFIGURATION DU POTAGER", True, GREEN_PRIMARY)
        self.screen.blit(title_s, title_s.get_rect(centerx=cx, y=int(self.height * 0.06)))

    # ── Update ────────────────────────────────────
    def _update(self):
        now = time.time()
        dt  = min(now - self._last_time, 0.05)
        self._last_time = now

        mouse = pygame.mouse.get_pos()
        self.plots_stepper.update(dt, mouse)
        self.years_stepper.update(dt, mouse)
        self.loc_prev.update(dt, mouse)
        self.loc_next.update(dt, mouse)
        self.confirm_btn.update(dt, mouse)
        self.back_btn.update(dt, mouse)

        for p in self.particles:
            p.update(dt)

        # Slide carrousel localisation
        self.loc_slide_x += (self.loc_target_x - self.loc_slide_x) * min(1.0, dt * 12)
        if abs(self.loc_slide_x - self.loc_target_x) < 0.5:
            self.loc_slide_x = self.loc_target_x
            self.loc_target_x = 0.0
            self.loc_slide_x  = 0.0

        # Panneaux fade-in
        if self.soil_panel:
            self.soil_panel.update(dt)
        if self.crop_panel:
            self.crop_panel.update(dt)

        return dt

    # ── Titre section avec icône ligne ───────────
    def _draw_section_label(self, text, x, y, width):
        ts = self.subtitle_font.render(text, True, GREEN_DARK)
        self.screen.blit(ts, ts.get_rect(centerx=x, y=y))

    # ── Carrousel localisation ─────────────────────
    def _draw_location(self):
        cx    = self.width // 2
        loc_y = self.loc_y
        ns    = self.nav_size
        slide = self.loc_slide_x

        # Label
        lbl = self.subtitle_font.render("Localisation", True, GREEN_DARK)
        self.screen.blit(lbl, lbl.get_rect(centerx=cx, bottom=loc_y - 4))

        # Fond arrondi pour la valeur
        val_w = int(self.width * 0.38)
        val_h = ns + 4
        val_surf = pygame.Surface((val_w, val_h), pygame.SRCALPHA)
        pygame.draw.rect(val_surf, (255, 255, 255, 130), val_surf.get_rect(), border_radius=13)
        pygame.draw.rect(val_surf, (*GREEN_PRIMARY, 90), val_surf.get_rect(), width=2, border_radius=13)
        self.screen.blit(val_surf, (cx - val_w // 2, loc_y))

        # Clipper pour le slide
        clip = pygame.Rect(cx - val_w // 2, loc_y, val_w, val_h)
        old_clip = self.screen.get_clip()
        self.screen.set_clip(clip)

        # Texte localisation avec offset slide
        loc_text = self.subtitle_font.render(self.selected_location, True, GREEN_PRIMARY)
        tx = cx + int(slide) - loc_text.get_width() // 2
        ty = loc_y + (val_h - loc_text.get_height()) // 2
        self.screen.blit(loc_text, (tx, ty))

        self.screen.set_clip(old_clip)

        # Boutons nav
        self.loc_prev.draw(self.screen, self.btn_font)
        self.loc_next.draw(self.screen, self.btn_font)

    # ── Titre principal ────────────────────────────
    def _draw_title(self, t):
        pulse = 0.5 + 0.5 * math.sin(t * 1.8)
        r = int(GREEN_PRIMARY[0] + (80 - GREEN_PRIMARY[0]) * pulse * 0.25)
        g = int(GREEN_PRIMARY[1] + (200 - GREEN_PRIMARY[1]) * pulse * 0.18)
        b = GREEN_PRIMARY[2]
        col = (r, g, b)

        cx = self.width // 2
        # Ombre
        sh = self.title_font.render("CONFIGURATION DU POTAGER", True, (80, 120, 60))
        self.screen.blit(sh, sh.get_rect(centerx=cx + 2, y=int(self.height * 0.04) + 2))
        # Titre
        ts = self.title_font.render("CONFIGURATION DU POTAGER", True, col)
        self.screen.blit(ts, ts.get_rect(centerx=cx, y=int(self.height * 0.04)))

        # Ligne déco sous le titre
        ly = int(self.height * 0.04) + ts.get_height() + 4
        lw = int(self.width * 0.55)
        ls = pygame.Surface((lw, 2), pygame.SRCALPHA)
        pygame.draw.line(ls, (*GREEN_DARK, 80), (0, 0), (lw, 0), 2)
        self.screen.blit(ls, (cx - lw // 2, ly))

    # ── Draw principal ────────────────────────────
    def draw(self):
        dt = self._update()
        t  = time.time()

        if self.loading:
            self._draw_loading(dt)
            return

        # Fond
        self.screen.blit(self._bg_surface, (0, 0))

        # Particules
        self._particle_surf.fill((0, 0, 0, 0))
        for p in self.particles:
            p.draw(self._particle_surf)
        self.screen.blit(self._particle_surf, (0, 0))

        # Titre
        self._draw_title(t)

        # Avertissement API
        if not self.nasa_api_key:
            warn_s = self.body_font.render(
                "⚠  Clé API NASA non configurée — météo aléatoire utilisée",
                True, WARN_COLOR)
            self.screen.blit(warn_s, warn_s.get_rect(
                centerx=self.width // 2, y=int(self.height * 0.14)))

        # Steppers
        self.plots_stepper.draw(self.screen, self.subtitle_font, self.val_font)
        self.years_stepper.draw(self.screen, self.subtitle_font, self.val_font)

        # Séparateur entre steppers et localisation
        sep_y = int(self.height * 0.33)
        sep_w = int(self.width * 0.65)
        ss    = pygame.Surface((sep_w, 1), pygame.SRCALPHA)
        pygame.draw.line(ss, (*GREEN_DARK, 50), (0, 0), (sep_w, 0))
        self.screen.blit(ss, (self.width // 2 - sep_w // 2, sep_y))

        # Localisation
        self._draw_location()

        # Panneaux info
        if self.soil_panel:
            self.soil_panel.draw(self.screen, self.subtitle_font, self.body_font)
        if self.crop_panel:
            self.crop_panel.draw(self.screen, self.subtitle_font, self.body_font)

        # Séparateur bas
        sep2_y = int(self.height * 0.82)
        sep2_w = int(self.width * 0.80)
        ss2    = pygame.Surface((sep2_w, 1), pygame.SRCALPHA)
        pygame.draw.line(ss2, (*GREEN_DARK, 50), (0, 0), (sep2_w, 0))
        self.screen.blit(ss2, (self.width // 2 - sep2_w // 2, sep2_y))

        # Boutons
        self.confirm_btn.draw(self.screen, self.btn_font)
        self.back_btn.draw(self.screen, self.btn_font)

    # ── Événements ────────────────────────────────
    def handle_event(self, event):
        if self.loading:
            return None

        if self.plots_stepper.handle_event(event):
            self.selected_plots = self.plots_stepper.value
        elif self.years_stepper.handle_event(event):
            self.selected_years = self.years_stepper.value

        elif self.loc_prev.handle_event(event):
            self.location_index    = (self.location_index - 1) % len(self.locations)
            self.selected_location = self.locations[self.location_index]
            self.loc_target_x      = self.width * 0.25   # slide depuis la droite
            self._build_panels()

        elif self.loc_next.handle_event(event):
            self.location_index    = (self.location_index + 1) % len(self.locations)
            self.selected_location = self.locations[self.location_index]
            self.loc_target_x      = -self.width * 0.25  # slide depuis la gauche
            self._build_panels()

        elif self.confirm_btn.handle_event(event):
            self.loading        = True
            self.status_message = f"Chargement des données météo pour {self.selected_location}…"
            return "prepare_game"

        elif self.back_btn.handle_event(event):
            return "back"

        return None

    # ── Préparation config (inchangée) ────────────
    def prepare_game_config(self):
        region_info = self.region_data[self.selected_location]
        if "lat" not in region_info or "lon" not in region_info:
            print(f"ERREUR: Coordonnées (lat, lon) manquantes pour {self.selected_location}.")
            self.status_message  = "Erreur: Coordonnées manquantes."
            self.selected_config = {"error": "Missing coordinates"}
            self.loading         = False
            return

        nasa_data = None
        end_date_api   = datetime.now() - timedelta(days=1)
        start_date_api = end_date_api - timedelta(days=364)

        if self.nasa_api_key:
            try:
                nasa_data = get_nasa_power_data(
                    latitude=region_info["lat"],
                    longitude=region_info["lon"],
                    start_date=start_date_api.strftime("%Y%m%d"),
                    end_date=end_date_api.strftime("%Y%m%d"),
                    api_key=self.nasa_api_key,
                )
                self.status_message = "Données NASA chargées. Lancement…"
            except Exception as e:
                print(f"Erreur NASA : {e}")
                self.status_message  = "Erreur de connexion à l'API NASA."
                self.selected_config = {"error": str(e)}
        else:
            self.status_message = "Lancement sans données météo (clé API manquante)."
            start_date_api = datetime.now()

        self.selected_config = {
            "plots":             self.selected_plots,
            "years":             self.selected_years,
            "location":          self.selected_location,
            "region_data":       region_info,
            "nasa_weather_data": nasa_data,
            "start_date":        start_date_api,
        }
        self.loading = False

    def get_config(self):
        return self.selected_config
