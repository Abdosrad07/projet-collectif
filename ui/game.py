import pygame
import numpy as np
import math
import time
import random
import os

from core.farm_logic import FarmLogic
from .constants import (
    WHITE, BLACK, GREEN_PRIMARY, GREEN_LIGHT, GREEN_DARK, RED,
    YELLOW, BLUE, ORANGE, PURPLE, GRAY_LIGHT, GRAY_DARK, BROWN, BACKGROUND_GAME
)
from .widgets import Button, get_font, render_text_with_emojis

# ─────────────────────────────────────────────
#  PALETTE ÉTENDUE (cohérente menu / config)
# ─────────────────────────────────────────────
BG_GAME        = (210, 235, 210)
HEADER_COL     = GREEN_PRIMARY
PANEL_BG       = (248, 253, 245)
PANEL_BORDER   = GREEN_PRIMARY
STEPPER_BG     = (60,  90,  70)
GREEN_GLOW     = (80, 200,  80)
BLUE_LIGHT     = (173, 216, 230)
CARD_EMPTY     = (245, 220, 160)
CARD_CROP      = (180, 225, 160)
CARD_DRY       = (210, 180, 140)
CRACK_COL      = (139, 69,  19)
TOOLTIP_BG     = (20,  30,  20, 215)
TOOLTIP_BORDER = GREEN_PRIMARY

ACT_COLORS = {
    "Plante":    (GREEN_DARK,        WHITE),
    "Arroser":   (BLUE,              WHITE),
    "Drainer":   ((96, 165, 250),    WHITE),
    "Fertiliser":(ORANGE,            WHITE),
    "Traiter":   ((139, 0, 139),     WHITE),
    "Récolter":  (GREEN_PRIMARY,     WHITE),
    "Conseil IA":(PURPLE,            WHITE),
}


# ─────────────────────────────────────────────
#  BOUTON ANIMÉ (copié de menu.py)
# ─────────────────────────────────────────────
class AnimBtn:
    def __init__(self, cx, y, w, h, text,
                 color=GREEN_PRIMARY, text_color=WHITE,
                 font_size=20, radius=None):
        self.cx = cx; self.y = y
        self.base_w = w; self.base_h = h
        self.text = text; self.color = color
        self.text_color = text_color
        self.font_size = font_size
        self.radius = radius
        self.scale = 1.0; self.target_scale = 1.0
        self.glow_alpha = 0; self.hover = False
        self.click_anim = 0.0

    def get_rect(self):
        w = int(self.base_w * self.scale)
        h = int(self.base_h * self.scale)
        return pygame.Rect(self.cx - w//2, self.y - (h - self.base_h)//2, w, h)

    def update(self, dt, mouse):
        rect = pygame.Rect(self.cx - self.base_w//2, self.y, self.base_w, self.base_h)
        self.hover = rect.collidepoint(mouse)
        self.target_scale = 1.06 if self.hover else 1.0
        self.scale += (self.target_scale - self.scale) * min(1.0, dt * 8)
        tg = 170 if self.hover else 0
        self.glow_alpha += (tg - self.glow_alpha) * min(1.0, dt * 6)
        if self.click_anim > 0:
            self.click_anim = max(0.0, self.click_anim - dt * 4)

    def draw(self, surface, font):
        rect = self.get_rect()
        r = self.radius if self.radius else min(rect.height//2, 18)
        # Ombre
        sh = pygame.Surface((rect.width+8, rect.height+8), pygame.SRCALPHA)
        pygame.draw.rect(sh, (0,0,0,30), pygame.Rect(4,4,rect.width,rect.height), border_radius=r)
        surface.blit(sh, (rect.x-4, rect.y-4))
        # Glow
        if self.glow_alpha > 5:
            gs = pygame.Surface((rect.width+28, rect.height+28), pygame.SRCALPHA)
            for ex in range(0,14,4):
                ec = (*GREEN_GLOW, int(self.glow_alpha*(0.28-ex*0.015)))
                pygame.draw.rect(gs, ec, pygame.Rect(14-ex//2,14-ex//2,rect.width+ex,rect.height+ex), border_radius=r+ex//2+2)
            surface.blit(gs, (rect.x-14, rect.y-14))
        # Corps
        pygame.draw.rect(surface, self.color, rect, border_radius=r)
        # Reflet
        sh2 = max(3, rect.height//3)
        shine = pygame.Surface((rect.width-4, sh2), pygame.SRCALPHA)
        for sy in range(sh2):
            pygame.draw.line(shine, (255,255,255,int(50*(1-sy/sh2))), (0,sy),(rect.width-4,sy))
        surface.blit(shine, (rect.x+2, rect.y+2))
        # Flash clic
        if self.click_anim > 0:
            cs = pygame.Surface((rect.width,rect.height), pygame.SRCALPHA)
            pygame.draw.rect(cs, (255,255,255,int(self.click_anim*100)), cs.get_rect(), border_radius=r)
            surface.blit(cs, rect)
        # Texte
        ts = font.render(self.text, True, self.text_color)
        surface.blit(ts, ts.get_rect(center=rect.center))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.get_rect().collidepoint(event.pos):
                self.click_anim = 1.0
                return True
        return False


# ─────────────────────────────────────────────
#  CARTE DE PARCELLE
# ─────────────────────────────────────────────
class CropCard:
    def __init__(self, x, y, width, height, plot_data):
        self.rect = pygame.Rect(x, y, width, height)
        self.plot_data = plot_data
        self.harvest_timer = 0
        self.water_animation_timer = 0
        self.current_image = None
        self.next_image = None
        self.fade_alpha = 0
        self.font      = get_font(max(11, int(height / 9.5)))
        self.name_font = get_font(max(12, int(height / 8)))

    def draw(self, screen, is_selected):
        wl = self.plot_data['water_level']
        # Couleur de fond
        if wl < 20:
            if self.plot_data["crop"] and self.plot_data["progress"] >= 0.9:
                pulse = math.sin(self.harvest_timer * 0.05) * 5
                color = (int(210 + pulse), int(180 + pulse), 140)
            else:
                color = CARD_DRY
        elif self.plot_data["crop"]:
            color = CARD_CROP
        else:
            color = CARD_EMPTY

        # Ombre
        shadow = self.rect.move(4, 4)
        pygame.draw.rect(screen, (100,100,100,60), shadow, border_radius=14)

        # Fond avec dégradé simulé
        pygame.draw.rect(screen, color, self.rect, border_radius=14)
        shine = pygame.Surface((self.rect.width, self.rect.height//3), pygame.SRCALPHA)
        for sy in range(self.rect.height//3):
            a = int(35 * (1 - sy/(self.rect.height//3)))
            pygame.draw.line(shine, (255,255,255,a), (0,sy),(self.rect.width,sy))
        screen.blit(shine, self.rect.topleft)

        # Bordure sélection / normale
        if is_selected:
            # Halo orange
            for bw, ba in [(6, 40), (4, 80), (2, 200)]:
                pygame.draw.rect(screen, (*ORANGE, ba), self.rect.inflate(bw*2, bw*2), width=bw, border_radius=14+bw)
            pygame.draw.rect(screen, ORANGE, self.rect, width=3, border_radius=14)
        else:
            pygame.draw.rect(screen, (160,185,160), self.rect, width=2, border_radius=14)

        # Craquelures sécheresse
        if wl < 20:
            for pts in [
                [(0.10, 0.60),(0.30, 0.80),(0.35, 0.75)],
                [(0.80, 0.55),(0.70, 0.85),(0.60, 0.80)],
            ]:
                pygame.draw.lines(screen, CRACK_COL, False,
                    [(self.rect.x + self.rect.width*p[0], self.rect.y + self.rect.height*p[1]) for p in pts], 2)

        # Icône maladie
        if self.plot_data.get("disease"):
            di = self.font.render("💀", True, RED)
            screen.blit(di, di.get_rect(topright=(self.rect.right-8, self.rect.top+5)))

        # Image de la plante
        if self.plot_data["crop"]:
            crop_name  = self.plot_data["crop"]
            progress   = self.plot_data["progress"]
            image_idx  = int(progress * 5)
            image_path = os.path.join("assets", "images", crop_name, f"{crop_name}_{image_idx}.png")
            if os.path.exists(image_path):
                try:
                    img = pygame.image.load(image_path).convert_alpha()
                    mw  = self.rect.width  * 0.70
                    mh  = self.rect.height * 0.48
                    iw, ih = img.get_size()
                    sc = min(mw/iw, mh/ih) if iw > 0 and ih > 0 else 1
                    si = pygame.transform.scale(img, (int(iw*sc), int(ih*sc)))
                    screen.blit(si, si.get_rect(centerx=self.rect.centerx, y=self.rect.y + self.rect.height*0.08))
                except pygame.error:
                    pass

        # Nom + barre progression
        if self.plot_data["crop"]:
            crop_name = self.plot_data["crop"]
            progress  = self.plot_data["progress"]

            ns = self.name_font.render(crop_name, True, (30,60,30))
            screen.blit(ns, ns.get_rect(centerx=self.rect.centerx, y=self.rect.y + self.rect.height*0.55))

            pw  = self.rect.width * 0.75
            ph  = max(6, int(self.rect.height * 0.04))
            px  = self.rect.centerx - pw/2
            py  = self.rect.bottom - self.rect.height*0.27

            pygame.draw.rect(screen, GRAY_LIGHT, (px, py, pw, ph), border_radius=4)
            fw = int(pw * progress)
            if fw > 0:
                bar_col = GREEN_PRIMARY if progress >= 0.9 else BLUE
                pygame.draw.rect(screen, bar_col, (px, py, fw, ph), border_radius=4)

            pct = self.font.render(f"{int(progress*100)}%", True, (40,70,40))
            screen.blit(pct, pct.get_rect(centerx=self.rect.centerx, bottom=int(py)-3))

            if progress >= 0.9:
                self.harvest_timer += 1

        # Barres bas (eau / nutriments / sol)
        bw  = self.rect.width * 0.25
        bh  = max(5, int(self.rect.height * 0.035))
        by  = self.rect.bottom - bh - int(self.rect.height * 0.06)
        ico = self.font

        for offset, key, maxv, col, icon_txt in [
            (self.rect.x + 20,                       'water_level',     100,  BLUE,        "💧"),
            (self.rect.centerx - bw/2,               'fertilizer_bonus', 0.5, YELLOW,      "⚡"),
            (self.rect.right - 20 - bw,              'soil_quality',     1.0,  BROWN,       "🌍"),
        ]:
            val = self.plot_data[key]
            if key == 'fertilizer_bonus':
                pct = min(1.0, val / 0.5)
            elif key == 'water_level':
                pct = val / 100.0
            else:
                pct = val

            pygame.draw.rect(screen, GRAY_LIGHT, (offset, by, bw, bh), border_radius=3)
            fw2 = int(bw * pct)
            if fw2 > 0:
                pygame.draw.rect(screen, col, (offset, by, fw2, bh), border_radius=3)

            ic = ico.render(icon_txt, True, BLACK)
            screen.blit(ic, (offset - ic.get_width() - 2, by - 2))

        if self.water_animation_timer > 0:
            self.water_animation_timer -= 1


# ─────────────────────────────────────────────
#  INTERFACE DE JEU
# ─────────────────────────────────────────────
class GameInterface:
    def __init__(self, screen):
        self.screen = screen
        self.width  = screen.get_width()
        self.height = screen.get_height()

        # ── Zones layout fixes ──
        self.HEADER_H  = max(60,  int(self.height * 0.09))
        self.OBJBAR_H  = max(24,  int(self.height * 0.032))
        self.TOPBAR_H  = self.HEADER_H + self.OBJBAR_H         # hauteur totale en-tête
        self.PANEL_W   = max(220, int(self.width * 0.27))       # largeur panneaux droite
        self.BOTBAR_H  = max(70,  int(self.height * 0.115))     # zone boutons bas
        self.CARDS_X0  = 0                                       # début zone cartes
        self.CARDS_W   = self.width - self.PANEL_W - 12
        self.CARDS_Y0  = self.TOPBAR_H + 8
        self.CARDS_H   = self.height - self.TOPBAR_H - self.BOTBAR_H - 8

        # ── Polices responsive ──
        self.title_font    = get_font(max(22, int(self.HEADER_H * 0.48)))
        self.subtitle_font = get_font(max(14, int(self.height * 0.024)))
        self.text_font     = get_font(max(12, int(self.height * 0.021)))
        self.small_font    = get_font(max(10, int(self.height * 0.017)))
        self.btn_font      = get_font(max(12, int(self.BOTBAR_H * 0.26)))

        # ── Logique ──
        self.logic = FarmLogic()

        # ── État UI ──
        self.selected_plot_index = 0
        self.show_ai_popup  = False
        self.ai_advice      = ""
        self.show_plant_menu = False
        self.crop_cards      = []
        self.tooltip_lines   = []
        self.tooltip_pos     = (0, 0)

        # ── Temps ──
        self.is_paused            = True
        self.day_duration         = 15
        self.day_timer            = 0
        self.last_frame_time      = time.time()
        self.time_speed_multiplier = 1

        # ── Météo ──
        self.rain_particles  = []
        self.snow_particles  = []
        self.wind_particles  = []

        # ── Boutons d'action (positionnés dynamiquement) ──
        self._build_action_buttons()

        # ── Popup IA ──
        pw = min(480, int(self.width * 0.48))
        ph = min(300, int(self.height * 0.40))
        self.ai_popup_rect = pygame.Rect(self.width//2 - pw//2, self.height//2 - ph//2, pw, ph)
        self.close_ai_btn  = AnimBtn(self.ai_popup_rect.right - 28, self.ai_popup_rect.y + 8,
                                     40, 28, "✕", (220, 38, 38), WHITE,
                                     max(12, int(self.height * 0.018)))

        # ── Menu plantation ──
        self.plant_menu_rect    = pygame.Rect(0, 0, max(180, int(self.width * 0.15)), 300)
        self.plant_menu_buttons = []

        # ── Pré-rendu fond ──
        self._bg = self._build_bg()

    # ── Fond dégradé ─────────────────────────────
    def _build_bg(self):
        surf = pygame.Surface((self.width, self.height))
        top  = (218, 240, 210)
        bot  = (190, 225, 185)
        for y in range(self.height):
            t = y / self.height
            r = int(top[0]*(1-t) + bot[0]*t)
            g = int(top[1]*(1-t) + bot[1]*t)
            b = int(top[2]*(1-t) + bot[2]*t)
            pygame.draw.line(surf, (r, g, b), (0, y), (self.width, y))
        return surf

    # ── Boutons d'action ─────────────────────────
    def _build_action_buttons(self):
        bh    = max(36, int(self.BOTBAR_H * 0.52))
        bh_sm = max(30, int(self.BOTBAR_H * 0.44))
        fs    = max(11, int(bh * 0.30))

        labels = ["Plante", "Arroser", "Drainer", "Fertiliser", "Traiter", "Récolter", "Conseil IA"]
        # Largeur proportionnelle à la zone cartes
        total_gap  = int(self.CARDS_W * 0.04)
        avail_w    = self.CARDS_W - total_gap * 2
        bw_unit    = int(avail_w / len(labels)) - 6
        bw_unit    = max(70, min(bw_unit, 130))

        total_btns = bw_unit * len(labels) + 6 * (len(labels)-1)
        start_x    = self.CARDS_X0 + (self.CARDS_W - total_btns) // 2

        by = self.height - self.BOTBAR_H + (self.BOTBAR_H - bh) // 2

        self.action_buttons = {}
        for i, lbl in enumerate(labels):
            col, tcol = ACT_COLORS[lbl]
            cx = start_x + i * (bw_unit + 6) + bw_unit // 2
            btn = AnimBtn(cx, by, bw_unit, bh, lbl, col, tcol, fs)
            self.action_buttons[lbl] = btn

        # Boutons play/pause et vitesse (dans la zone panneaux droite)
        pp_y   = self.height - self.BOTBAR_H + (self.BOTBAR_H - bh_sm) // 2
        pp_cx  = self.width - self.PANEL_W + self.PANEL_W // 4
        spd_cx = self.width - self.PANEL_W + self.PANEL_W * 3 // 4
        pp_w   = int(self.PANEL_W * 0.42)

        self.play_pause_btn = AnimBtn(pp_cx, pp_y, pp_w, bh_sm,
                                      "▶ Jouer", STEPPER_BG, WHITE, fs)
        self.speed_btn      = AnimBtn(spd_cx, pp_y, pp_w, bh_sm,
                                      "Vitesse x1", STEPPER_BG, WHITE, fs)

    # ── Accesseurs boutons (rétro-compat) ────────
    @property
    def plant_btn(self):    return self.action_buttons["Plante"]
    @property
    def water_btn(self):    return self.action_buttons["Arroser"]
    @property
    def drain_btn(self):    return self.action_buttons["Drainer"]
    @property
    def fertilize_btn(self):return self.action_buttons["Fertiliser"]
    @property
    def treat_btn(self):    return self.action_buttons["Traiter"]
    @property
    def harvest_btn(self):  return self.action_buttons["Récolter"]
    @property
    def ai_btn(self):       return self.action_buttons["Conseil IA"]

    # ── Setup depuis config ───────────────────────
    def setup_from_config(self, config):
        self.logic.setup_from_config(config)
        self.generate_crop_cards_from_logic()
        self.selected_plot_index       = 0
        self.show_ai_popup             = False
        self.ai_advice                 = ""
        self.show_plant_menu           = False
        self.is_paused                 = True
        self.day_timer                 = 0
        self.last_frame_time           = time.time()
        self.time_speed_multiplier     = 1
        self.play_pause_btn.text       = "▶ Jouer"
        self.speed_btn.text            = "Vitesse x1"

    # ── Génération des cartes ─────────────────────
    def generate_crop_cards_from_logic(self):
        self.crop_cards.clear()
        n = self.logic.plots_config

        if n <= 4:   cpr, base_cw = n, int(self.CARDS_W * 0.22)
        elif n <= 8: cpr, base_cw = 4, int(self.CARDS_W * 0.22)
        else:        cpr, base_cw = 6, int(self.CARDS_W * 0.15)

        # Adapter pour que la grille tienne dans CARDS_W × CARDS_H
        num_rows = (n + cpr - 1) // cpr
        pad_x    = max(8, int(self.CARDS_W * 0.018))
        pad_y    = max(8, int(self.CARDS_H * 0.035))
        max_cw   = (self.CARDS_W - pad_x * (cpr + 1)) // cpr
        max_ch   = (self.CARDS_H - pad_y * (num_rows + 1)) // num_rows
        cw       = min(base_cw, max_cw)
        ch       = min(int(cw * 1.15), max_ch)

        grid_w  = cpr * cw + pad_x * (cpr - 1)
        grid_h  = num_rows * ch + pad_y * (num_rows - 1)
        ox      = self.CARDS_X0 + (self.CARDS_W - grid_w) // 2
        oy      = self.CARDS_Y0 + (self.CARDS_H - grid_h) // 2

        for i, pd in enumerate(self.logic.plots):
            row = i // cpr
            col = i % cpr
            x   = ox + col * (cw + pad_x)
            y   = oy + row * (ch + pad_y)
            self.crop_cards.append(CropCard(x, y, cw, ch, pd))

    # ── Conseil IA ────────────────────────────────
    def get_ai_advice(self):
        advices = []
        if not (0 <= self.selected_plot_index < len(self.logic.plots)):
            return "Sélectionnez une parcelle pour obtenir un conseil."
        plot = self.logic.plots[self.selected_plot_index]
        if plot.get("disease"):
            advices.append(f"💀 La plante est atteinte de {plot['disease']}. Un traitement est urgent !")
        if plot["crop"]:
            if plot["progress"] >= 0.9:
                advices.append(f"🌾 {plot['crop']} est prêt à être récolté !")
            elif plot["progress"] < 0.3:
                advices.append(f"🌱 {plot['crop']} est encore jeune. Patience.")
            if plot["water_level"] < 30:
                advices.append(f"💧 {plot['crop']} a soif. Un arrosage serait bénéfique.")
            elif plot["water_level"] > 90:
                advices.append(f"🌊 Attention, {plot['crop']} est sur-irrigué. Pensez à drainer.")
            if plot["fertilizer_bonus"] < 20:
                advices.append(f"🌿 {plot['crop']} pourrait bénéficier d'un peu d'engrais.")
        else:
            advices.append("🌱 Cette parcelle est vide. C'est le moment idéal pour planter !")
        if plot["soil_quality"] < 0.5:
            advices.append("🌍 La qualité du sol se dégrade. Évitez les fertilisants un moment.")
        elif plot["soil_quality"] > 0.8:
            advices.append("🌟 Ce sol est en excellente condition !")
        if self.logic.water_reserve < 50:
            advices.append("🚰 Votre réserve d'eau globale est faible.")
        if not advices:
            advices.append("✅ Tout semble sous contrôle. Continuez !")
        return " ".join(advices[:2])

    # ── Popup IA ─────────────────────────────────
    def draw_ai_popup(self):
        if not self.show_ai_popup:
            return
        ov = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 110))
        self.screen.blit(ov, (0, 0))

        r = self.ai_popup_rect
        # Fond
        ps = pygame.Surface((r.width, r.height), pygame.SRCALPHA)
        pygame.draw.rect(ps, (248, 253, 245, 245), ps.get_rect(), border_radius=18)
        pygame.draw.rect(ps, (*GREEN_PRIMARY, 220), ps.get_rect(), width=3, border_radius=18)
        self.screen.blit(ps, r)

        ts = self.subtitle_font.render("🤖 Conseil de l'IA", True, GREEN_PRIMARY)
        self.screen.blit(ts, ts.get_rect(centerx=r.centerx, y=r.y + 16))

        sep_y = r.y + 16 + ts.get_height() + 8
        pygame.draw.line(self.screen, (*GREEN_DARK, 80), (r.x+16, sep_y), (r.right-16, sep_y))

        self._draw_text_multiline(self.ai_advice, r.x+18, sep_y+10, r.width-36)
        self.close_ai_btn.draw(self.screen, self.small_font)

    # ── Menu plantation ───────────────────────────
    def _build_plant_menu(self):
        if not (0 <= self.selected_plot_index < len(self.crop_cards)):
            return
        card_rect = self.crop_cards[self.selected_plot_index].rect
        mw = max(180, int(self.width * 0.14))
        mh = 20 + len(self.logic.available_crops) * 48
        # Positionnement intelligent (ne pas déborder)
        mx = card_rect.right + 8
        if mx + mw > self.CARDS_W:
            mx = card_rect.left - mw - 8
        my = card_rect.top
        if my + mh > self.height - self.BOTBAR_H:
            my = max(self.TOPBAR_H + 4, self.height - self.BOTBAR_H - mh)
        self.plant_menu_rect = pygame.Rect(mx, my, mw, mh)

        self.plant_menu_buttons.clear()
        fs    = max(12, int(self.height * 0.022))
        btn_h = max(36, int(self.height * 0.052))
        yo    = my + 10
        for crop in self.logic.available_crops:
            btn = AnimBtn(mx + mw//2, yo, mw - 16, btn_h, crop, GREEN_DARK, WHITE, fs)
            self.plant_menu_buttons.append(btn)
            yo += btn_h + 8

    def draw_plant_menu(self):
        if not self.show_plant_menu:
            return
        r = self.plant_menu_rect
        ps = pygame.Surface((r.width, r.height), pygame.SRCALPHA)
        pygame.draw.rect(ps, (248, 253, 245, 235), ps.get_rect(), border_radius=12)
        pygame.draw.rect(ps, (*GREEN_PRIMARY, 200), ps.get_rect(), width=2, border_radius=12)
        self.screen.blit(ps, r)
        font = get_font(max(12, int(self.height * 0.022)))
        for btn in self.plant_menu_buttons:
            btn.draw(self.screen, font)

    # ── Texte multiline ───────────────────────────
    def _draw_text_multiline(self, text, x, y, max_width):
        words = text.split()
        lines = []
        cur = []
        lw  = 0
        for w in words:
            ww = self.text_font.size(w + " ")[0]
            if lw + ww <= max_width:
                cur.append(w); lw += ww
            else:
                lines.append(" ".join(cur)); cur = [w]; lw = ww
        if cur:
            lines.append(" ".join(cur))
        yo = y
        for line in lines:
            s = render_text_with_emojis(line, self.text_font, BLACK)
            self.screen.blit(s, (x, yo)); yo += 28

    # ── Barre objectif ────────────────────────────
    def _draw_objective_bar(self):
        bw = int(self.width * 0.50)
        bh = self.OBJBAR_H - 4
        bx = (self.width - bw) // 2
        by = self.HEADER_H + 2

        lbl = render_text_with_emojis("Objectif:", self.small_font, WHITE)
        self.screen.blit(lbl, (bx - lbl.get_width() - 8, by + (bh - lbl.get_height())//2))

        fp = np.clip(self.logic.food_harvested / self.logic.food_target, 0, 1.0) if self.logic.food_target > 0 else 0

        pygame.draw.rect(self.screen, (255,255,255,80), (bx, by, bw, bh), border_radius=bh//2)
        pygame.draw.rect(self.screen, (200,220,200), (bx, by, bw, bh), width=1, border_radius=bh//2)
        fw = int((bw - 4) * fp)
        if fw > 0:
            pygame.draw.rect(self.screen, GREEN_LIGHT, (bx+2, by+2, fw, bh-4), border_radius=bh//2-2)

        pt = render_text_with_emojis(f"{self.logic.food_harvested:.0f} / {self.logic.food_target:.0f} kg",
                                     self.small_font, WHITE)
        self.screen.blit(pt, pt.get_rect(center=(bx + bw//2, by + bh//2)))

    # ── Panneaux d'info (droite) ──────────────────
    def _draw_info_panels(self):
        px   = self.width - self.PANEL_W + 6
        pw   = self.PANEL_W - 12
        py   = self.TOPBAR_H + 6
        gap  = max(6, int(self.height * 0.01))
        avail_h = self.height - py - self.BOTBAR_H - gap

        # Hauteurs des panneaux proportionnelles
        wh = int(avail_h * 0.30)
        rh = int(avail_h * 0.24)
        ch = int(avail_h * 0.18)
        eh = avail_h - wh - rh - ch - gap*3

        def panel(x, y, w, h, border_col=PANEL_BORDER):
            surf = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.rect(surf, (*PANEL_BG, 235), surf.get_rect(), border_radius=13)
            pygame.draw.rect(surf, (*border_col, 180), surf.get_rect(), width=2, border_radius=13)
            # Ombre
            sh = pygame.Surface((w+8, h+8), pygame.SRCALPHA)
            pygame.draw.rect(sh, (0,0,0,18), pygame.Rect(4,4,w,h), border_radius=13)
            self.screen.blit(sh, (x-4, y-4))
            self.screen.blit(surf, (x, y))

        # ── Météo ──
        panel(px, py, pw, wh)
        weather = self.logic.get_current_day_weather()
        temp    = weather.get('temp', 0)
        precip  = weather.get('precip', 0)
        cond    = weather.get('condition', '')
        icon    = "🥵" if "heatwave" in cond else "🥶" if "frost" in cond else "🌧️" if "Pluie" in cond else "☀️"

        ts = self.subtitle_font.render(f"{icon} Météo du jour", True, GREEN_DARK)
        self.screen.blit(ts, (px+12, py+10))
        sep_y = py + 10 + ts.get_height() + 4
        pygame.draw.line(self.screen, (*GREEN_DARK, 60), (px+10, sep_y), (px+pw-10, sep_y))
        self.screen.blit(self.text_font.render(f"Température : {temp:.1f}°C", True, BLACK), (px+12, sep_y+6))
        self.screen.blit(self.text_font.render(f"Précipitations : {precip:.1f} mm", True, BLACK), (px+12, sep_y+6+22))
        if cond in ("heatwave", "frost"):
            alert = self.text_font.render(f"⚠ Alerte : {cond.capitalize()} !", True, RED)
            self.screen.blit(alert, (px+12, sep_y+6+44))

        # ── Ressources ──
        ry = py + wh + gap
        panel(px, ry, pw, rh)
        ts2 = self.subtitle_font.render("Ressources Globales", True, GREEN_DARK)
        self.screen.blit(ts2, (px+12, ry+8))
        sep2 = ry + 8 + ts2.get_height() + 4
        pygame.draw.line(self.screen, (*GREEN_DARK, 60), (px+10, sep2), (px+pw-10, sep2))

        wcolor = RED if self.logic.water_reserve < 50 else BLACK
        line_h = max(20, int(rh * 0.26))
        self.screen.blit(self.text_font.render(f"💧 Eau : {self.logic.water_reserve:.0f} L", True, wcolor), (px+12, sep2+4))
        self.screen.blit(self.text_font.render(f"💰 Argent : {self.logic.money:.0f} €", True, BLACK), (px+12, sep2+4+line_h))
        sc  = self.logic.sustainability_score
        scol = GREEN_PRIMARY if sc > 70 else (ORANGE if sc > 40 else RED)
        self.screen.blit(self.text_font.render(f"🌍 Durabilité : {sc}%", True, scol), (px+12, sep2+4+line_h*2))

        # ── État cultures ──
        cy2 = ry + rh + gap
        panel(px, cy2, pw, ch)
        ts3 = self.subtitle_font.render("État du Potager", True, GREEN_DARK)
        self.screen.blit(ts3, (px+12, cy2+8))
        sep3 = cy2 + 8 + ts3.get_height() + 4
        pygame.draw.line(self.screen, (*GREEN_DARK, 60), (px+10, sep3), (px+pw-10, sep3))
        mature  = sum(1 for p in self.logic.plots if p["crop"] and p["progress"] >= 0.9)
        growing = sum(1 for p in self.logic.plots if p["crop"] and 0 < p["progress"] < 0.95)
        self.screen.blit(self.text_font.render(f"🌾 Matures : {mature}", True, BLACK),   (px+12, sep3+5))
        self.screen.blit(self.text_font.render(f"🌱 Croissance : {growing}", True, BLACK),(px+12, sep3+5+22))

        # ── Rendement estimé ──
        ey = cy2 + ch + gap
        panel(px, ey, pw, eh, BLUE)
        ts4 = self.subtitle_font.render("📦 Rendement Estimé", True, BLUE)
        self.screen.blit(ts4, (px+12, ey+8))
        sep4 = ey + 8 + ts4.get_height() + 4
        pygame.draw.line(self.screen, (*BLUE, 60), (px+10, sep4), (px+pw-10, sep4))

        sel = self.logic.plots[self.selected_plot_index] if self.logic.plots else None
        if sel and sel["crop"]:
            est = self._estimate_yield(sel)
            if est is not None:
                crop_def = self.logic.crop_definitions.get(sel["crop"], {})
                max_k    = crop_def.get("max_k", 100)
                ratio    = min(1.0, est / max_k) if max_k > 0 else 0
                bx2  = px + 12; bw2 = pw - 24; bh2 = max(8, int(eh * 0.15))
                by2  = sep4 + 5
                pygame.draw.rect(self.screen, GRAY_LIGHT, (bx2, by2, bw2, bh2), border_radius=5)
                fc   = GREEN_PRIMARY if ratio > 0.6 else (ORANGE if ratio > 0.3 else RED)
                pygame.draw.rect(self.screen, fc, (bx2, by2, int(bw2*ratio), bh2), border_radius=5)
                vt = self.text_font.render(f"~{est:.0f} kg  (max {max_k:.0f} kg)", True, BLACK)
                self.screen.blit(vt, (px+12, by2 + bh2 + 4))

                adv = ""
                if sel['water_level'] < 25:       adv = "💧 Arrosage recommandé"
                elif sel.get('disease'):           adv = "💀 Traitement urgent !"
                elif sel['soil_quality'] < 0.4:   adv = "🌍 Sol appauvri"
                elif sel['progress'] >= 0.9:       adv = "🌾 Prête à récolter !"
                if adv:
                    ac = RED if "urgent" in adv else ORANGE
                    at = self.small_font.render(adv, True, ac)
                    self.screen.blit(at, (px+12, by2 + bh2 + 4 + 22))
        else:
            rec = self._get_crop_recommendation(sel) if sel else None
            if rec:
                rt = self.text_font.render(f"💡 Essayez : {rec}", True, GREEN_DARK)
                self.screen.blit(rt, (px+12, sep4+8))
            et = self.text_font.render("Parcelle vide — plantez !", True, GRAY_DARK)
            self.screen.blit(et, (px+12, sep4+8+(26 if rec else 0)))

    # ── Barre de progression du jour ─────────────
    def _draw_day_progress_bar(self):
        bh = 6
        by = self.height - bh
        progress = self.day_timer / self.day_duration if self.day_duration > 0 else 0
        pygame.draw.rect(self.screen, (200,225,200), (0, by, self.width, bh))
        pygame.draw.rect(self.screen, GREEN_PRIMARY,  (0, by, int(self.width*progress), bh))

    # ── Tooltip enrichie ──────────────────────────
    def _draw_tooltip(self):
        if not self.tooltip_lines:
            return
        lh      = max(18, int(self.height * 0.025))
        tfont   = get_font(max(12, int(self.height * 0.020)))
        sfont   = get_font(max(10, int(self.height * 0.017)))
        pad     = 10
        max_lw  = max((tfont if i==0 else sfont).size(l)[0] for i,l in enumerate(self.tooltip_lines))
        tw      = max_lw + pad*2
        th      = len(self.tooltip_lines) * lh + pad*2

        tx = self.tooltip_pos[0] + 16
        ty = self.tooltip_pos[1] - th//2
        # Clamper pour ne jamais déborder
        tx = max(2, min(tx, self.width  - tw - 4))
        ty = max(self.TOPBAR_H + 2, min(ty, self.height - self.BOTBAR_H - th - 4))

        # Fond
        bg = pygame.Surface((tw, th), pygame.SRCALPHA)
        bg.fill(TOOLTIP_BG)
        pygame.draw.rect(bg, TOOLTIP_BORDER, bg.get_rect(), width=2, border_radius=10)
        self.screen.blit(bg, (tx, ty))

        for i, line in enumerate(self.tooltip_lines):
            f    = tfont if i == 0 else sfont
            col  = GREEN_LIGHT if i == 0 else (235, 235, 235)
            surf = render_text_with_emojis(line, f, col)
            self.screen.blit(surf, (tx + pad, ty + pad + i*lh))

    # ── Météo ─────────────────────────────────────
    def _update_and_draw_weather_effects(self):
        cond = self.logic.get_current_day_weather()['condition']
        if "Pluie" in cond: self._draw_rain("forte" in cond)
        else: self.rain_particles.clear()
        if cond == "snow": self._draw_snow()
        else: self.snow_particles.clear()
        if cond == "heatwave": self._draw_heatwave_effect()
        self._draw_wind_effect()

    def _draw_rain(self, is_heavy):
        n = 250 if is_heavy else 100
        if len(self.rain_particles) != n:
            self.rain_particles = [[random.randint(0,self.width), random.randint(0,self.height)] for _ in range(n)]
        for p in self.rain_particles:
            p[1] += 12 if is_heavy else 8
            if p[1] > self.height: p[1] = random.randint(-20,0); p[0] = random.randint(0,self.width)
            pygame.draw.line(self.screen, BLUE_LIGHT, (p[0],p[1]), (p[0],p[1]+7), 2 if is_heavy else 1)

    def _draw_snow(self):
        if not self.snow_particles:
            self.snow_particles = [[random.randint(0,self.width), random.randint(0,self.height), random.randint(2,4)] for _ in range(150)]
        for p in self.snow_particles:
            p[1] += 1.5; p[0] += random.uniform(-0.5,0.5)
            if p[1] > self.height: p[1] = -5; p[0] = random.randint(0,self.width)
            pygame.draw.circle(self.screen, WHITE, (int(p[0]),int(p[1])), p[2])

    def _draw_heatwave_effect(self):
        ov = pygame.Surface((self.width,self.height), pygame.SRCALPHA)
        ov.fill((255,140,0,28)); self.screen.blit(ov,(0,0))

    def _draw_wind_effect(self):
        if not self.wind_particles and random.random() < 0.01:
            self.wind_particles = [[random.randint(-100,self.width), random.randint(0,self.height)] for _ in range(15)]
        elif self.wind_particles and random.random() < 0.01:
            self.wind_particles.clear()
        for p in self.wind_particles:
            p[0] += 25
            if p[0] > self.width: p[0] = -50; p[1] = random.randint(0,self.height)
            pygame.draw.line(self.screen, (200,210,220), (p[0],p[1]), (p[0]+50,p[1]), 1)

    # ── Estimation rendement ──────────────────────
    def _estimate_yield(self, plot):
        if not plot["crop"]: return None
        crop_def = self.logic.crop_definitions.get(plot["crop"], {})
        max_k    = crop_def.get("max_k", 100)
        wf       = max(0.1, 1.0 - abs(plot['water_level'] - crop_def.get("water_need",60)) / 100)
        dp       = 1.0 - (plot.get('disease_severity',0)*0.8) if plot.get('disease') else 1.0
        return max_k * plot['soil_quality'] * plot['progress'] * wf * dp

    def _get_crop_recommendation(self, plot):
        season    = self.logic.get_current_season()
        available = self.logic.available_crops
        if not available: return None
        crop_defs = self.logic.crop_definitions
        best, best_score = None, -1
        for crop in available:
            d         = crop_defs.get(crop, {})
            season_ok = 0.5 if season in ("Hiver","Grande saison sèche") else 1.0
            score     = season_ok * (1.0 - abs(plot['soil_quality'] - d.get("soil_demand",0.5)))
            if score > best_score: best_score = score; best = crop
        return best

    # ── DRAW PRINCIPAL ────────────────────────────
    def draw(self):
        # Fond
        self.screen.blit(self._bg, (0, 0))

        # Temps
        now  = time.time()
        dt   = min(now - self.last_frame_time, 0.05)
        self.last_frame_time = now

        if not self.is_paused:
            self.day_timer += dt * self.time_speed_multiplier
            if self.day_timer >= self.day_duration:
                self.logic.update_simulation()
                self.day_timer -= self.day_duration

        # Fin de jeu
        if self.logic.current_day > self.logic.max_days:
            return "game_over"

        mouse = pygame.mouse.get_pos()

        # ── En-tête ──
        hsurf = pygame.Surface((self.width, self.HEADER_H), pygame.SRCALPHA)
        pygame.draw.rect(hsurf, (*GREEN_PRIMARY, 255), hsurf.get_rect())
        # Dégradé léger
        for y in range(self.HEADER_H):
            a = int(30 * (1 - y / self.HEADER_H))
            pygame.draw.line(hsurf, (255,255,255,a), (0,y),(self.width,y))
        self.screen.blit(hsurf, (0, 0))

        # Bandeau objectif
        obj_surf = pygame.Surface((self.width, self.OBJBAR_H), pygame.SRCALPHA)
        pygame.draw.rect(obj_surf, (*GREEN_DARK, 220), obj_surf.get_rect())
        self.screen.blit(obj_surf, (0, self.HEADER_H))
        self._draw_objective_bar()

        # Bouton menu
        menu_rect = pygame.Rect(10, (self.HEADER_H - 34)//2, 90, 34)
        pygame.draw.rect(self.screen, GREEN_DARK, menu_rect, border_radius=8)
        mt = render_text_with_emojis("← Menu", self.small_font, WHITE)
        self.screen.blit(mt, mt.get_rect(center=menu_rect.center))

        # Titre
        season     = self.logic.get_current_season()
        icons_map  = {"Printemps":"🌱","Été":"☀️","Automne":"🍂","Hiver":"❄️",
                      "Petite saison des pluies":"🌦️","Grande saison sèche":"☀️",
                      "Grande saison des pluies":"🌧️","Petite saison sèche":"🏜️"}
        sicon      = icons_map.get(season, "❓")
        rd         = self.logic.config.get("region_data",{})
        dur        = rd.get("season_durations",[10,10,10,10])
        diy        = sum(dur) if sum(dur)>0 else 1
        yr         = ((self.logic.current_day-1) // diy) + 1
        title_str  = f"Farm Navigator — Année {yr} — {sicon} {season}"
        ts = render_text_with_emojis(title_str, self.title_font, WHITE)
        self.screen.blit(ts, ts.get_rect(centerx=self.width//2, centery=self.HEADER_H//2))

        # Jour (dans bandeau objectif)
        ds = render_text_with_emojis(f"Jour {self.logic.current_day}/{self.logic.max_days}",
                                     self.small_font, (220,245,220))
        self.screen.blit(ds, ds.get_rect(right=self.width - self.PANEL_W - 14,
                                          centery=self.HEADER_H + self.OBJBAR_H//2))

        # ── Zone boutons bas (fond) ──
        bot_surf = pygame.Surface((self.width, self.BOTBAR_H), pygame.SRCALPHA)
        pygame.draw.rect(bot_surf, (*GREEN_DARK, 200),
                         pygame.Rect(0, 0, self.CARDS_W, self.BOTBAR_H), border_radius=0)
        pygame.draw.rect(bot_surf, (*STEPPER_BG, 200),
                         pygame.Rect(self.CARDS_W, 0, self.PANEL_W, self.BOTBAR_H))
        self.screen.blit(bot_surf, (0, self.height - self.BOTBAR_H))

        # ── Séparateur vertical cartes / panneaux ──
        sep_x = self.CARDS_W
        sep_s = pygame.Surface((2, self.height - self.TOPBAR_H - self.BOTBAR_H), pygame.SRCALPHA)
        for y in range(sep_s.get_height()):
            a = int(80 * math.sin(math.pi * y / sep_s.get_height()))
            pygame.draw.line(sep_s, (*GREEN_DARK, a), (0,y),(1,y))
        self.screen.blit(sep_s, (sep_x, self.TOPBAR_H))

        # ── Cartes ──
        for i, card in enumerate(self.crop_cards):
            card.draw(self.screen, i == self.selected_plot_index)

        # ── Indicateur parcelle sélectionnée ──
        sel_w = max(160, int(self.CARDS_W * 0.34))
        sel_h = max(26, int(self.BOTBAR_H * 0.36))
        sel_r = pygame.Rect(self.CARDS_W//2 - sel_w//2,
                            self.height - self.BOTBAR_H - sel_h - 4,
                            sel_w, sel_h)
        ss = pygame.Surface((sel_w, sel_h), pygame.SRCALPHA)
        pygame.draw.rect(ss, (*GREEN_LIGHT, 200), ss.get_rect(), border_radius=sel_h//2)
        pygame.draw.rect(ss, (*GREEN_DARK, 160), ss.get_rect(), width=2, border_radius=sel_h//2)
        self.screen.blit(ss, sel_r)
        slt = render_text_with_emojis(f"Parcelle {self.selected_plot_index+1} sélectionnée",
                                      self.small_font, (20,60,20))
        self.screen.blit(slt, slt.get_rect(center=sel_r.center))

        # ── Panneaux info ──
        self._draw_info_panels()

        # ── Boutons d'action ──
        for btn in self.action_buttons.values():
            btn.update(dt, mouse)
            btn.draw(self.screen, self.btn_font)
        self.play_pause_btn.update(dt, mouse)
        self.speed_btn.update(dt, mouse)
        self.play_pause_btn.draw(self.screen, self.btn_font)
        self.speed_btn.draw(self.screen, self.btn_font)

        # ── Menus contextuels ──
        self.draw_plant_menu()
        self.draw_ai_popup()

        # ── Barre progression jour ──
        self._draw_day_progress_bar()

        # ── Météo ──
        self._update_and_draw_weather_effects()

        # ── Tooltip (toujours au-dessus) ──
        self._draw_tooltip()

        return None

    # ── Événements ────────────────────────────────
    def handle_event(self, event):
        # Survol pour tooltip
        if event.type == pygame.MOUSEMOTION:
            self.tooltip_lines = []
            self.tooltip_pos   = event.pos
            for idx, card in enumerate(self.crop_cards):
                if card.rect.collidepoint(event.pos):
                    plot  = card.plot_data
                    lines = [f"━━ Parcelle {idx+1} ━━"]
                    if plot["crop"]:
                        pct    = int(plot["progress"]*100)
                        status = "🌾 Prête à récolter!" if plot["progress"]>=0.9 else f"🌱 Croissance: {pct}%"
                        lines += [status, f"Culture: {plot['crop']}"]
                    else:
                        lines.append("Parcelle vide")
                        rec = self._get_crop_recommendation(plot)
                        if rec: lines.append(f"💡 Recommandé: {rec}")
                    water = plot['water_level']
                    wi    = "💧" if water>=40 else ("🏜️" if water<20 else "💧")
                    ws    = "Bon" if 40<=water<=80 else ("Sec" if water<40 else "Excès")
                    lines.append(f"{wi} Eau: {water:.0f}% ({ws})")
                    soil  = plot['soil_quality']*100
                    si    = "🌟" if soil>70 else ("⚠️" if soil<40 else "🌍")
                    lines.append(f"{si} Sol: {soil:.0f}%")
                    fert  = min(1.0, plot['fertilizer_bonus']/0.5)*100
                    lines.append(f"⚡ Nutriments: {fert:.0f}%")
                    if plot.get("disease"):
                        sev = int(plot['disease_severity']*100)
                        lines.append(f"💀 {plot['disease']} ({sev}% sévérité)")
                    est = self._estimate_yield(plot)
                    if est is not None:
                        lines.append(f"📦 Rendement estimé: ~{est:.0f} kg")
                    self.tooltip_lines = lines
                    break

        # Popup IA
        if self.show_ai_popup:
            if self.close_ai_btn.handle_event(event):
                self.show_ai_popup = False
                return None

        # Menu plantation
        if self.show_plant_menu:
            font = get_font(max(12, int(self.height*0.022)))
            for i, btn in enumerate(self.plant_menu_buttons):
                if btn.handle_event(event):
                    self.logic.plant_action(self.selected_plot_index, self.logic.available_crops[i])
                    self.show_plant_menu = False
                    return None

        # Boutons d'action
        if self.plant_btn.handle_event(event):
            if self.logic.plots[self.selected_plot_index]["crop"] is None:
                self.show_plant_menu = not self.show_plant_menu
                if self.show_plant_menu: self._build_plant_menu()
            return None
        elif self.water_btn.handle_event(event):
            if self.logic.water_action(self.selected_plot_index):
                self.crop_cards[self.selected_plot_index].water_animation_timer = 30
            return None
        elif self.drain_btn.handle_event(event):
            self.logic.drain_action(self.selected_plot_index); return None
        elif self.fertilize_btn.handle_event(event):
            self.logic.fertilize_action(self.selected_plot_index); return None
        elif self.treat_btn.handle_event(event):
            self.logic.treat_action(self.selected_plot_index); return None
        elif self.harvest_btn.handle_event(event):
            self.logic.harvest_action(self.selected_plot_index); return None
        elif self.ai_btn.handle_event(event):
            self.show_ai_popup = True
            self.ai_advice     = self.get_ai_advice()
            return None
        elif self.play_pause_btn.handle_event(event):
            self.is_paused = not self.is_paused
            self.play_pause_btn.text = "▶ Jouer" if self.is_paused else "⏸ Pause"
            if not self.is_paused: self.last_frame_time = time.time()
            return None
        elif self.speed_btn.handle_event(event):
            if self.time_speed_multiplier == 1:
                self.time_speed_multiplier = 2; self.speed_btn.text = "Vitesse x2"
            elif self.time_speed_multiplier == 2:
                self.time_speed_multiplier = 4; self.speed_btn.text = "Vitesse x4"
            else:
                self.time_speed_multiplier = 1; self.speed_btn.text = "Vitesse x1"
            return None

        if event.type == pygame.MOUSEBUTTONDOWN:
            # Bouton Menu
            menu_rect = pygame.Rect(10, (self.HEADER_H-34)//2, 90, 34)
            if menu_rect.collidepoint(event.pos):
                self.logic.save_game(); return "menu"

            # Fermer menus si clic hors
            if self.show_plant_menu and not self.plant_menu_rect.collidepoint(event.pos):
                self.show_plant_menu = False
            if self.show_ai_popup and not self.ai_popup_rect.collidepoint(event.pos):
                self.show_ai_popup = False

            # Sélection parcelle
            if not self.show_plant_menu and not self.show_ai_popup:
                for i, card in enumerate(self.crop_cards):
                    if card.rect.collidepoint(event.pos):
                        self.selected_plot_index = i; break

        return None

    def get_results(self):
        return {
            "daily_yields":        self.logic.daily_yields,
            "daily_soil_quality":  self.logic.daily_soil_quality,
            "sustainability_score":self.logic.sustainability_score,
            "food_harvested":      self.logic.food_harvested,
            "food_target":         self.logic.food_target,
            "final_money":         self.logic.money,
            "final_water":         self.logic.water_reserve,
            "actions_taken":       self.logic.actions_taken,
            "plots_data":          self.logic.plots,
        }
