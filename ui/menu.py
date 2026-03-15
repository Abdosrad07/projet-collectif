import pygame
import os
import math
import random
import time

# Importer les constantes et widgets partagés
from .constants import WHITE, BLACK, GREEN_PRIMARY, GREEN_DARK, GRAY_LIGHT, ORANGE
from .widgets import Button, get_font, render_text_with_emojis


# ─────────────────────────────────────────────
#  COULEURS ÉTENDUES
# ─────────────────────────────────────────────
GREEN_LIGHT   = (144, 213, 110)
GREEN_GLOW    = (80,  200,  80)
BG_TOP        = (232, 245, 228)
BG_BOTTOM     = (195, 230, 185)
SHADOW_COLOR  = (0, 0, 0, 60)
PARTICLE_COLS = [
    (100, 200,  80),
    (140, 220, 100),
    ( 60, 160,  60),
    (180, 230, 130),
    ( 80, 180,  90),
]


# ─────────────────────────────────────────────
#  PARTICULE
# ─────────────────────────────────────────────
class Particle:
    """Petite feuille / bulle flottante animée."""

    def __init__(self, width, height):
        self.W = width
        self.H = height
        self.reset(initial=True)

    def reset(self, initial=False):
        self.x     = random.uniform(0, self.W)
        self.y     = random.uniform(0, self.H) if initial else self.H + 10
        self.size  = random.uniform(4, 14)
        self.speed = random.uniform(0.3, 1.2)
        self.drift = random.uniform(-0.4, 0.4)
        self.alpha = random.randint(80, 200)
        self.color = random.choice(PARTICLE_COLS)
        self.angle = random.uniform(0, 360)
        self.spin  = random.uniform(-1.5, 1.5)
        self.shape = random.choice(["leaf", "circle", "diamond"])
        self.wobble_offset = random.uniform(0, math.pi * 2)
        self.wobble_speed  = random.uniform(0.5, 1.5)

    def update(self, dt):
        t = time.time()
        wobble = math.sin(t * self.wobble_speed + self.wobble_offset) * 0.5
        self.x    += (self.drift + wobble) * dt * 60
        self.y    -= self.speed * dt * 60
        self.angle = (self.angle + self.spin * dt * 60) % 360
        if self.y < -20:
            self.reset()

    def draw(self, surface):
        s = self.size
        col = (*self.color, self.alpha)

        # Surface temporaire avec alpha
        tmp = pygame.Surface((int(s * 3), int(s * 3)), pygame.SRCALPHA)
        cx, cy = int(s * 1.5), int(s * 1.5)

        if self.shape == "circle":
            pygame.draw.circle(tmp, col, (cx, cy), int(s))
        elif self.shape == "diamond":
            pts = [(cx, cy - s), (cx + s, cy), (cx, cy + s), (cx - s, cy)]
            pygame.draw.polygon(tmp, col, pts)
        else:  # leaf
            pts = [(cx, cy - s), (cx + s * 0.6, cy), (cx, cy + s * 0.4), (cx - s * 0.6, cy)]
            pygame.draw.polygon(tmp, col, pts)

        # Rotation
        rotated = pygame.transform.rotate(tmp, self.angle)
        rect = rotated.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(rotated, rect)


# ─────────────────────────────────────────────
#  BOUTON AMÉLIORÉ avec glow + scale hover
# ─────────────────────────────────────────────
class AnimatedButton:
    def __init__(self, cx, y, w, h, text,
                 color=GREEN_PRIMARY, text_color=WHITE,
                 font_size=24, disabled=False):
        self.cx       = cx          # centre x
        self.y        = y
        self.base_w   = w
        self.base_h   = h
        self.text     = text
        self.color    = color
        self.text_color = text_color
        self.font_size  = font_size
        self.disabled   = disabled

        self.scale      = 1.0       # échelle actuelle
        self.target_scale = 1.0
        self.glow_alpha   = 0
        self.hover        = False
        self.click_anim   = 0.0     # 0..1, flash au clic

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

        # Lissage de la scale
        speed = 8.0
        self.scale += (self.target_scale - self.scale) * min(1.0, dt * speed)

        # Glow alpha
        target_glow = 180 if self.hover else 0
        self.glow_alpha += (target_glow - self.glow_alpha) * min(1.0, dt * 6)

        # Decay animation clic
        if self.click_anim > 0:
            self.click_anim = max(0.0, self.click_anim - dt * 4)

    def draw(self, surface, font):
        rect = self.get_rect()
        r = min(rect.height // 2, 22)

        if self.disabled:
            col = GRAY_LIGHT
            tcol = (160, 160, 160)
        else:
            col = self.color
            tcol = self.text_color

        # ── Ombre portée ──
        shadow_surf = pygame.Surface((rect.width + 8, rect.height + 8), pygame.SRCALPHA)
        shadow_rect = pygame.Rect(4, 4, rect.width, rect.height)
        pygame.draw.rect(shadow_surf, (0, 0, 0, 40), shadow_rect, border_radius=r)
        surface.blit(shadow_surf, (rect.x - 4, rect.y - 4))

        # ── Glow halo ──
        if self.glow_alpha > 5 and not self.disabled:
            glow_s = pygame.Surface((rect.width + 30, rect.height + 30), pygame.SRCALPHA)
            glow_r = pygame.Rect(15, 15, rect.width, rect.height)
            glow_col = (*GREEN_GLOW, int(self.glow_alpha * 0.35))
            pygame.draw.rect(glow_s, glow_col, glow_r, border_radius=r + 4)
            # Blur simulé : 3 calques légèrement agrandis
            for extra in range(3, 14, 4):
                ec = (*GREEN_GLOW, int(self.glow_alpha * 0.08))
                er = pygame.Rect(15 - extra // 2, 15 - extra // 2,
                                 rect.width + extra, rect.height + extra)
                pygame.draw.rect(glow_s, ec, er, border_radius=r + extra // 2 + 2)
            surface.blit(glow_s, (rect.x - 15, rect.y - 15))

        # ── Corps bouton ──
        pygame.draw.rect(surface, col, rect, border_radius=r)

        # ── Reflet supérieur ──
        if not self.disabled:
            shine_h = max(4, rect.height // 3)
            shine_s = pygame.Surface((rect.width - 4, shine_h), pygame.SRCALPHA)
            for sy in range(shine_h):
                a = int(60 * (1 - sy / shine_h))
                pygame.draw.line(shine_s, (255, 255, 255, a), (0, sy), (rect.width - 4, sy))
            shine_r = pygame.Rect(rect.x + 2, rect.y + 2, rect.width - 4, shine_h)
            surface.blit(shine_s, shine_r)

        # ── Flash clic ──
        if self.click_anim > 0:
            fa = int(self.click_anim * 120)
            click_s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            pygame.draw.rect(click_s, (255, 255, 255, fa), click_s.get_rect(), border_radius=r)
            surface.blit(click_s, rect)

        # ── Texte ──
        txt_surf = font.render(self.text, True, tcol)
        txt_rect = txt_surf.get_rect(center=rect.center)
        surface.blit(txt_surf, txt_rect)

    def handle_event(self, event):
        if self.disabled:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.get_rect().collidepoint(event.pos):
                self.click_anim = 1.0
                return True
        return False


# ─────────────────────────────────────────────
#  INTERFACE MENU PRINCIPALE
# ─────────────────────────────────────────────
class MenuInterface:
    def __init__(self, screen):
        self.screen = screen
        self.width  = screen.get_width()
        self.height = screen.get_height()
        self._last_time = time.time()

        # ── Polices (taille relative à l'écran) ──
        title_size    = max(48, int(self.height * 0.10))
        subtitle_size = max(18, int(self.height * 0.030))
        btn_font_size = max(16, int(self.height * 0.028))
        version_size  = max(14, int(self.height * 0.020))

        self.title_font    = get_font(title_size)
        self.subtitle_font = get_font(subtitle_size)
        self.btn_font      = get_font(btn_font_size)
        self.version_font  = get_font(version_size)

        # ── Layout responsive ──
        cx  = self.width  // 2
        btn_w = min(360, int(self.width * 0.38))
        btn_h = max(44, int(self.height * 0.065))
        btn_gap = int(btn_h * 1.35)

        btn_top = int(self.height * 0.52)

        self.new_game_btn = AnimatedButton(cx, btn_top,            btn_w, btn_h, "Nouvelle partie", GREEN_PRIMARY, WHITE, btn_font_size)
        self.continue_btn = AnimatedButton(cx, btn_top + btn_gap,  btn_w, btn_h, "Continuer",        GRAY_LIGHT,    BLACK, btn_font_size, disabled=True)
        self.quit_btn     = AnimatedButton(cx, btn_top + btn_gap * 2, int(btn_w * 0.55), btn_h, "Quitter", WHITE, ORANGE, btn_font_size)

        self.save_exists = False

        # ── Particules ──
        n_particles = max(18, int(self.width * self.height / 25000))
        self.particles = [Particle(self.width, self.height) for _ in range(n_particles)]

        # ── Animation titre ──
        self.title_pulse   = 0.0   # phase oscillation
        self.title_scale   = 1.0

        # ── Pré-rendu fond dégradé ──
        self._bg_surface = self._build_bg()

        # ── Surface particules (re-créée chaque frame) ──
        self._particle_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        # ── Maison : positions relatives ──
        self._house_size = max(55, int(self.height * 0.10))
        self._house_cx   = cx
        self._house_cy   = int(self.height * 0.18)

    # ── Fond dégradé pré-calculé ────────────────
    def _build_bg(self):
        surf = pygame.Surface((self.width, self.height))
        for y in range(self.height):
            t = y / self.height
            r = int(BG_TOP[0] * (1 - t) + BG_BOTTOM[0] * t)
            g = int(BG_TOP[1] * (1 - t) + BG_BOTTOM[1] * t)
            b = int(BG_TOP[2] * (1 - t) + BG_BOTTOM[2] * t)
            pygame.draw.line(surf, (r, g, b), (0, y), (self.width, y))
        return surf

    # ── Mise à jour bouton Continuer ────────────
    def update_continue_button(self):
        self.save_exists = os.path.exists("data/savegame.json")
        self.continue_btn.disabled = not self.save_exists
        if self.save_exists:
            self.continue_btn.color      = GREEN_PRIMARY
            self.continue_btn.text_color = WHITE
        else:
            self.continue_btn.color      = GRAY_LIGHT
            self.continue_btn.text_color = (150, 150, 150)

    # ── Dessin maison animée ─────────────────────
    def _draw_house(self, t):
        s   = self._house_size
        cx  = self._house_cx
        cy  = self._house_cy
        bob = math.sin(t * 1.2) * 4   # léger flottement vertical

        cy_f = cy + bob

        # Ombre maison
        shadow_s = pygame.Surface((s * 2, s * 2), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_s, (0, 0, 0, 30),
                            (s // 4, int(s * 1.5), s, s // 4))
        self.screen.blit(shadow_s, (cx - s, int(cy_f) - s // 2))

        # Toit avec glow
        roof_pts = [
            (cx,         cy_f - s * 0.55),
            (cx - s * 0.55, cy_f),
            (cx + s * 0.55, cy_f),
        ]
        # Halo toit
        glow_a = int(60 + 30 * math.sin(t * 2))
        glow_s = pygame.Surface((s * 2, s * 2), pygame.SRCALPHA)
        offset_pts = [(p[0] - (cx - s), p[1] - (cy_f - s)) for p in roof_pts]
        pygame.draw.polygon(glow_s, (*GREEN_GLOW, glow_a), offset_pts)
        self.screen.blit(glow_s, (cx - s, cy_f - s))

        pygame.draw.polygon(self.screen, GREEN_PRIMARY, roof_pts)
        # Reflet toit
        mid_x = (roof_pts[1][0] + roof_pts[2][0]) / 2
        shine_pts = [
            (cx, roof_pts[0][1] + 4),
            (mid_x * 0.3 + cx * 0.7, cy_f - 6),
            (mid_x * 0.1 + cx * 0.9, cy_f - 6),
        ]
        pygame.draw.polygon(self.screen, (255, 255, 255, 40), shine_pts)

        # Corps maison
        body_w = int(s * 0.62)
        body_h = int(s * 0.52)
        body_r = pygame.Rect(cx - body_w // 2, int(cy_f), body_w, body_h)
        pygame.draw.rect(self.screen, GREEN_PRIMARY, body_r, border_radius=3)

        # Fenêtre gauche
        win_size = max(8, int(s * 0.16))
        win_l = pygame.Rect(cx - body_w // 2 + 6, int(cy_f) + 8, win_size, win_size)
        pygame.draw.rect(self.screen, WHITE, win_l, border_radius=2)
        pygame.draw.rect(self.screen, (200, 230, 200), win_l.inflate(-3, -3), border_radius=1)

        # Fenêtre droite
        win_r = pygame.Rect(cx + body_w // 2 - 6 - win_size, int(cy_f) + 8, win_size, win_size)
        pygame.draw.rect(self.screen, WHITE, win_r, border_radius=2)
        pygame.draw.rect(self.screen, (200, 230, 200), win_r.inflate(-3, -3), border_radius=1)

        # Porte
        door_w = max(10, int(s * 0.18))
        door_h = max(16, int(s * 0.28))
        door_r = pygame.Rect(cx - door_w // 2, int(cy_f) + body_h - door_h, door_w, door_h)
        pygame.draw.rect(self.screen, WHITE, door_r, border_radius=2)

        # Poignée
        pygame.draw.circle(self.screen, GREEN_DARK,
                           (door_r.right - 3, door_r.centery + 2), 2)

    # ── Dessin titre avec pulse ──────────────────
    def _draw_title(self, t):
        # Oscillation lumineuse
        pulse = 0.5 + 0.5 * math.sin(t * 2.0)
        r = int(GREEN_PRIMARY[0] + (GREEN_LIGHT[0] - GREEN_PRIMARY[0]) * pulse)
        g = int(GREEN_PRIMARY[1] + (GREEN_LIGHT[1] - GREEN_PRIMARY[1]) * pulse)
        b = int(GREEN_PRIMARY[2] + (GREEN_LIGHT[2] - GREEN_PRIMARY[2]) * pulse)
        title_color = (r, g, b)

        title_surf = self.title_font.render("FARM NAVIGATOR", True, title_color)

        # Ombre titre
        shadow_surf = self.title_font.render("FARM NAVIGATOR", True, (80, 120, 60))
        shadow_rect = shadow_surf.get_rect(centerx=self.width // 2 + 3,
                                           y=int(self.height * 0.35) + 3)
        self.screen.blit(shadow_surf, shadow_rect)

        title_rect = title_surf.get_rect(centerx=self.width // 2,
                                          y=int(self.height * 0.35))
        self.screen.blit(title_surf, title_rect)

        # Sous-titre
        subtitle_surf = self.subtitle_font.render("CULTIVEZ VÔTRE RÊVE", True, GREEN_DARK)
        subtitle_rect = subtitle_surf.get_rect(centerx=self.width // 2,
                                                y=int(self.height * 0.35) + title_surf.get_height() + 6)
        # Ligne décorative sous le sous-titre
        line_y = subtitle_rect.bottom + 8
        line_w = subtitle_surf.get_width() + 40
        line_col = (*GREEN_DARK, 120)
        line_surf = pygame.Surface((line_w, 2), pygame.SRCALPHA)
        pygame.draw.line(line_surf, line_col, (0, 0), (line_w, 0), 2)
        self.screen.blit(line_surf, (self.width // 2 - line_w // 2, line_y))
        self.screen.blit(subtitle_surf, subtitle_rect)

    # ── Update général ───────────────────────────
    def _update(self):
        now = time.time()
        dt = min(now - self._last_time, 0.05)
        self._last_time = now

        mouse = pygame.mouse.get_pos()
        self.new_game_btn.update(dt, mouse)
        self.continue_btn.update(dt, mouse)
        self.quit_btn.update(dt, mouse)

        for p in self.particles:
            p.update(dt)

        return dt

    # ── Draw ─────────────────────────────────────
    def draw(self):
        self.update_continue_button()
        dt = self._update()
        t  = time.time()

        # Fond
        self.screen.blit(self._bg_surface, (0, 0))

        # Particules (surface SRCALPHA)
        self._particle_surf.fill((0, 0, 0, 0))
        for p in self.particles:
            p.draw(self._particle_surf)
        self.screen.blit(self._particle_surf, (0, 0))

        # Maison
        self._draw_house(t)

        # Titre + sous-titre
        self._draw_title(t)

        # Boutons
        self.new_game_btn.draw(self.screen, self.btn_font)
        self.continue_btn.draw(self.screen, self.btn_font)
        self.quit_btn.draw(self.screen, self.btn_font)

        # Séparateur décoratif entre les boutons et le bord
        sep_y = int(self.height * 0.90)
        sep_w = int(self.width * 0.25)
        sep_col = (*GREEN_DARK, 80)
        for dx, sign in [(-10, -1), (10, 1)]:
            s = pygame.Surface((sep_w, 1), pygame.SRCALPHA)
            pygame.draw.line(s, sep_col, (0, 0), (sep_w, 0))
            self.screen.blit(s, (self.width // 2 + dx + (sep_w * sign - sep_w) // 2 * (-sign), sep_y))

        # Version
        version_surf = self.version_font.render("Version 1.0.0", True, GREEN_DARK)
        version_rect = version_surf.get_rect(centerx=self.width // 2,
                                              y=self.height - int(self.height * 0.05))
        self.screen.blit(version_surf, version_rect)

    # ── Événements ───────────────────────────────
    def handle_event(self, event):
        if self.new_game_btn.handle_event(event):
            return "new_game"
        if self.continue_btn and self.save_exists and self.continue_btn.handle_event(event):
            return "continue"
        if self.quit_btn.handle_event(event):
            return "quit"
        return None
