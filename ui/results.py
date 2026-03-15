"""
Page de résultats entièrement redessinée — style tableau de bord moderne.
"""
import pygame
import re
import os
import csv
import math

from .constants import (WHITE, BLACK, GREEN_PRIMARY, GREEN_DARK, GRAY_LIGHT,
                        GRAY_DARK, GREEN_LIGHT, ORANGE, BROWN, BLUE, RED, YELLOW, PURPLE)
from .widgets import Button, get_font, render_text_with_emojis

# ── Palette étendue ──────────────────────────────────────────────────────────
BG_DARK      = (15,  23,  42)
BG_CARD      = (30,  41,  59)
BG_CARD2     = (51,  65,  85)
BORDER_COLOR = (71,  85, 105)
TEXT_MUTED   = (148, 163, 184)
TEXT_BRIGHT  = (241, 245, 249)
ACCENT_GREEN = ( 34, 197,  94)
ACCENT_TEAL  = ( 20, 184, 166)
ACCENT_AMBER = (251, 191,  36)
ACCENT_RED   = (239,  68,  68)


def _lerp_color(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _score_color(score_0_1):
    if score_0_1 > 0.7:
        return ACCENT_GREEN
    elif score_0_1 > 0.4:
        return ACCENT_AMBER
    return ACCENT_RED


class ResultsInterface:
    def __init__(self, screen):
        self.screen = screen
        self.width  = screen.get_width()
        self.height = screen.get_height()

        self.font_xl = get_font(52)
        self.font_lg = get_font(32)
        self.font_md = get_font(22)
        self.font_sm = get_font(17)
        self.font_xs = get_font(14)

        self.daily_yields       = []
        self.daily_soil_quality = []
        self.sustainability_score = 0
        self.food_harvested     = 0
        self.food_target        = 0
        self.final_money        = 0
        self.final_water        = 0
        self.actions_taken      = []
        self.plots_data         = []

        self.scroll_y  = 0
        self._anim_tick = 0

        bw, bh = 190, 52
        cx = self.width // 2
        self.replay_btn = Button(cx - bw - 220, self.height - 75, bw, bh, "Rejouer",    GREEN_DARK)
        self.export_btn = Button(cx - bw//2,    self.height - 75, bw, bh, "Exporter",   BLUE)
        self.menu_btn   = Button(cx + 220,       self.height - 75, bw, bh, "Menu",       (100, 116, 139))

        self.show_name_input     = False
        self.player_name         = ""
        self.input_box_active    = False
        pw, ph = 480, 220
        self.input_popup_rect   = pygame.Rect(self.width//2 - pw//2, self.height//2 - ph//2, pw, ph)
        self.input_box_rect     = pygame.Rect(self.input_popup_rect.x + 40,
                                              self.input_popup_rect.y + 90, pw - 80, 44)
        self.confirm_export_btn = Button(self.input_popup_rect.centerx - 90,
                                         self.input_popup_rect.bottom - 62, 180, 44, "Confirmer", (34, 197, 94), BLACK)
        self.close_export_btn   = Button(self.input_popup_rect.right - 48,
                                          self.input_popup_rect.top + 10, 38, 30, "X", (239, 68, 68))
        self.export_status_message = ""

    def setup_from_game(self, results):
        self.daily_yields       = results.get("daily_yields", [])
        self.daily_soil_quality = results.get("daily_soil_quality", [])
        self.sustainability_score = results.get("sustainability_score", 0)
        self.food_harvested     = results.get("food_harvested", 0)
        self.food_target        = results.get("food_target", 0)
        self.final_money        = results.get("final_money", 0)
        self.final_water        = results.get("final_water", 0)
        self.actions_taken      = results.get("actions_taken", [])
        self.plots_data         = results.get("plots_data", [])
        self._anim_tick         = 0
        self.scroll_y           = 0

    def draw(self):
        self._anim_tick = min(self._anim_tick + 1, 60)

        self.screen.fill(BG_DARK)
        self._draw_bg_grid()
        self._draw_header()

        body_top = 130
        body_h   = self.height - body_top - 90
        left_x   = 30
        right_x  = self.width // 2 + 10
        col_w    = self.width // 2 - 40

        self._draw_yield_chart(left_x, body_top, col_w, body_h // 2 - 10)
        self._draw_soil_chart(left_x, body_top + body_h // 2 + 5, col_w, body_h // 2 - 5)

        card_h = 105
        self._draw_kpi_row(right_x, body_top, col_w, card_h)
        self._draw_actions_breakdown(right_x, body_top + card_h + 12, col_w, 105)
        self._draw_plots_summary(right_x, body_top + card_h + 129, col_w,
                                 body_h - card_h - 141)

        self._draw_bottom_bar()

        if self.show_name_input:
            self._draw_name_input_popup()

        return None

    def _draw_bg_grid(self):
        for gx in range(0, self.width, 60):
            pygame.draw.line(self.screen, (22, 33, 52), (gx, 0), (gx, self.height), 1)
        for gy in range(0, self.height, 60):
            pygame.draw.line(self.screen, (22, 33, 52), (0, gy), (self.width, gy), 1)

    def _draw_header(self):
        hh = 118
        header_surf = pygame.Surface((self.width, hh), pygame.SRCALPHA)
        for hx in range(self.width):
            t = hx / self.width
            c = _lerp_color((20, 83, 45), (30, 64, 175), t)
            pygame.draw.line(header_surf, c + (225,), (hx, 0), (hx, hh))
        self.screen.blit(header_surf, (0, 0))
        pygame.draw.line(self.screen, ACCENT_GREEN, (0, hh), (self.width, hh), 2)

        food_ok    = self.food_harvested >= self.food_target
        badge_txt  = "OBJECTIF ATTEINT" if food_ok else "FIN DE SIMULATION"
        badge_col  = ACCENT_GREEN if food_ok else ACCENT_AMBER
        badge_surf = render_text_with_emojis(badge_txt, self.font_xs, badge_col)
        self.screen.blit(badge_surf, (self.width - badge_surf.get_width() - 25, 14))

        title_surf = render_text_with_emojis("TABLEAU DE BORD  RESULTATS", self.font_lg, TEXT_BRIGHT)
        self.screen.blit(title_surf, (28, 18))

        sust       = self.sustainability_score
        sub_surf   = render_text_with_emojis(
            f"Durabilite : {sust}%    Nourriture : {self.food_harvested:.0f} / {self.food_target:.0f} kg",
            self.font_sm, TEXT_MUTED)
        self.screen.blit(sub_surf, (28, 58))

        bar_x, bar_y = 28, 90
        bar_w = min(self.width - 56, 700)
        bar_h = 14
        prog  = min(1.0, self.food_harvested / self.food_target) if self.food_target else 0
        anim_prog = prog * min(1.0, self._anim_tick / 50)
        pygame.draw.rect(self.screen, BG_CARD2, (bar_x, bar_y, bar_w, bar_h), border_radius=7)
        if anim_prog > 0:
            fc = ACCENT_GREEN if food_ok else ACCENT_AMBER
            pygame.draw.rect(self.screen, fc, (bar_x, bar_y, int(bar_w * anim_prog), bar_h), border_radius=7)
        pct_surf = render_text_with_emojis(f"{prog*100:.0f}%", self.font_xs, TEXT_BRIGHT)
        self.screen.blit(pct_surf, (bar_x + bar_w + 8, bar_y - 2))

    def _draw_kpi_row(self, x, y, w, h):
        kpis = [
            ("$",  f"{self.final_money:.0f}E",    "Argent final",      ACCENT_AMBER),
            ("~",  f"{self.final_water:.0f}L",     "Eau restante",      BLUE),
            ("*",  f"{self.actions_taken.count('harvest')}","Recoltes", ACCENT_GREEN),
            ("+",  f"{self.actions_taken.count('fertilize')}","Fert.",  ORANGE),
        ]
        icons = ["💰", "💧", "🌾", "⚡"]
        cw = (w - 9 * 3) // 4
        for i, ((_, val, label, col), icon) in enumerate(zip(kpis, icons)):
            cx2 = x + i * (cw + 9)
            self._draw_card(cx2, y, cw, h, col)
            icon_surf = render_text_with_emojis(icon, self.font_lg, col)
            self.screen.blit(icon_surf, (cx2 + 12, y + 8))
            val_surf  = render_text_with_emojis(val, self.font_md, TEXT_BRIGHT)
            self.screen.blit(val_surf, (cx2 + 12, y + h - 60))
            lbl_surf  = render_text_with_emojis(label, self.font_xs, TEXT_MUTED)
            self.screen.blit(lbl_surf, (cx2 + 12, y + h - 32))

    def _draw_actions_breakdown(self, x, y, w, h):
        self._draw_card(x, y, w, h, BORDER_COLOR)
        title = render_text_with_emojis("Actions effectuees", self.font_sm, TEXT_MUTED)
        self.screen.blit(title, (x + 14, y + 8))

        actions = ["water", "fertilize", "treat", "harvest", "drain"]
        labels  = ["Arrosages", "Fert.", "Traitements", "Recoltes", "Drainages"]
        icons   = ["💧", "⚡", "💊", "🌾", "🌀"]
        cols    = [BLUE, ORANGE, PURPLE, ACCENT_GREEN, ACCENT_TEAL]
        total   = sum(self.actions_taken.count(a) for a in actions) or 1

        bx   = x + 14
        bar_y = y + 32
        bmax = w - 28
        bh   = 10

        for act, lbl, icon, col in zip(actions, labels, icons, cols):
            count = self.actions_taken.count(act)
            ratio = count / total
            lbl_surf = render_text_with_emojis(f"{icon} {lbl}", self.font_xs, TEXT_MUTED)
            self.screen.blit(lbl_surf, (bx, bar_y))
            fill_w = int(bmax * ratio * min(1.0, self._anim_tick / 45))
            pygame.draw.rect(self.screen, BG_CARD2, (bx, bar_y + 14, bmax, bh), border_radius=4)
            if fill_w > 0:
                pygame.draw.rect(self.screen, col, (bx, bar_y + 14, fill_w, bh), border_radius=4)
            cnt_s = render_text_with_emojis(str(count), self.font_xs, TEXT_BRIGHT)
            self.screen.blit(cnt_s, (bx + bmax + 6, bar_y + 12))
            bar_y += bh + 14

    def _draw_yield_chart(self, x, y, w, h):
        self._draw_card(x, y, w, h, ACCENT_GREEN)
        title_surf = render_text_with_emojis("Rendement journalier (kg)", self.font_sm, ACCENT_GREEN)
        self.screen.blit(title_surf, (x + 14, y + 10))

        if not self.daily_yields:
            msg = render_text_with_emojis("Aucune donnee", self.font_sm, TEXT_MUTED)
            self.screen.blit(msg, (x + w//2 - 40, y + h//2))
            return

        pad_l, pad_r, pad_t, pad_b = 44, 14, 36, 28
        cx = x + pad_l; cy = y + pad_t
        cw = w - pad_l - pad_r; ch = h - pad_t - pad_b
        max_val = max(self.daily_yields) if any(v > 0 for v in self.daily_yields) else 1
        n = len(self.daily_yields)
        bar_w = max(2, cw / n - 1)

        pygame.draw.rect(self.screen, BG_CARD2, pygame.Rect(cx, cy, cw, ch), border_radius=4)

        for frac in [0.25, 0.5, 0.75, 1.0]:
            gy = cy + ch - int(ch * frac)
            pygame.draw.line(self.screen, BORDER_COLOR, (cx, gy), (cx + cw, gy), 1)
            lbl = render_text_with_emojis(f"{int(max_val * frac)}", self.font_xs, TEXT_MUTED)
            self.screen.blit(lbl, (cx - lbl.get_width() - 4, gy - 8))

        anim = min(1.0, self._anim_tick / 55)
        max_yield_day = self.daily_yields.index(max(self.daily_yields)) if max_val > 0 else -1

        for i, val in enumerate(self.daily_yields):
            bh_px = int((val / max_val) * ch * anim) if max_val > 0 else 0
            bx2   = cx + int(i * (cw / n))
            by2   = cy + ch - bh_px
            col   = ACCENT_AMBER if i == max_yield_day else ACCENT_GREEN
            if bh_px > 0:
                pygame.draw.rect(self.screen, col, (bx2 + 1, by2, int(bar_w), bh_px), border_radius=2)

        step = max(1, n // 8)
        for i in range(0, n, step):
            lx  = cx + int(i * (cw / n)) + int(bar_w // 2)
            lbl = render_text_with_emojis(f"J{i+1}", self.font_xs, TEXT_MUTED)
            self.screen.blit(lbl, (lx - lbl.get_width()//2, cy + ch + 4))

        pygame.draw.line(self.screen, BORDER_COLOR, (cx, cy), (cx, cy + ch), 1)
        pygame.draw.line(self.screen, BORDER_COLOR, (cx, cy + ch), (cx + cw, cy + ch), 1)

    def _draw_soil_chart(self, x, y, w, h):
        self._draw_card(x, y, w, h, BROWN)
        title_surf = render_text_with_emojis("Evolution de la qualite du sol (%)", self.font_sm, (200, 130, 60))
        self.screen.blit(title_surf, (x + 14, y + 10))

        if not self.daily_soil_quality:
            msg = render_text_with_emojis("Aucune donnee", self.font_sm, TEXT_MUTED)
            self.screen.blit(msg, (x + w//2 - 40, y + h//2))
            return

        pad_l, pad_r, pad_t, pad_b = 44, 14, 36, 28
        cx = x + pad_l; cy = y + pad_t
        cw = w - pad_l - pad_r; ch = h - pad_t - pad_b
        n  = len(self.daily_soil_quality)

        pygame.draw.rect(self.screen, BG_CARD2, pygame.Rect(cx, cy, cw, ch), border_radius=4)

        for frac in [0.25, 0.5, 0.75, 1.0]:
            gy = cy + ch - int(ch * frac)
            pygame.draw.line(self.screen, BORDER_COLOR, (cx, gy), (cx + cw, gy), 1)
            lbl = render_text_with_emojis(f"{int(frac*100)}%", self.font_xs, TEXT_MUTED)
            self.screen.blit(lbl, (cx - lbl.get_width() - 4, gy - 8))

        anim_n = max(2, int(n * min(1.0, self._anim_tick / 55)))
        points = []
        for i in range(anim_n):
            px = cx + int(i * cw / (n - 1)) if n > 1 else cx
            py = cy + ch - int(self.daily_soil_quality[i] * ch)
            points.append((px, py))

        if len(points) >= 2:
            fill_pts  = [(cx, cy + ch)] + points + [(points[-1][0], cy + ch)]
            fill_surf = pygame.Surface((cw, ch), pygame.SRCALPHA)
            local_pts = [(p[0] - cx, p[1] - cy) for p in fill_pts]
            pygame.draw.polygon(fill_surf, (160, 82, 45, 60), local_pts)
            self.screen.blit(fill_surf, (cx, cy))
            pygame.draw.lines(self.screen, (210, 130, 60), False, points, 2)

            vals = self.daily_soil_quality[:anim_n]
            if vals:
                mi = vals.index(min(vals)); ma = vals.index(max(vals))
                for idx, col in [(mi, ACCENT_RED), (ma, ACCENT_GREEN)]:
                    px2 = cx + int(idx * cw / (n - 1)) if n > 1 else cx
                    py2 = cy + ch - int(vals[idx] * ch)
                    pygame.draw.circle(self.screen, col, (px2, py2), 5)
                    tag = render_text_with_emojis(f"{vals[idx]*100:.0f}%", self.font_xs, col)
                    self.screen.blit(tag, (px2 - tag.get_width()//2, py2 - 16))

        pygame.draw.line(self.screen, BORDER_COLOR, (cx, cy), (cx, cy + ch), 1)
        pygame.draw.line(self.screen, BORDER_COLOR, (cx, cy + ch), (cx + cw, cy + ch), 1)

    def _draw_plots_summary(self, x, y, w, h):
        self._draw_card(x, y, w, h, BORDER_COLOR)
        title = render_text_with_emojis("Bilan des parcelles", self.font_sm, TEXT_MUTED)
        self.screen.blit(title, (x + 14, y + 10))

        if not self.plots_data:
            return

        plots       = self.plots_data
        n           = len(plots)
        cols_count  = 4 if n > 4 else n
        margin      = 10
        cw2 = max(10, (w - margin * (cols_count + 1)) // cols_count)
        rows_count  = math.ceil(n / cols_count)
        ch2 = max(55, (h - 40 - margin * (rows_count + 1)) // rows_count)

        clip_rect = pygame.Rect(x, y + 30, w, h - 30)
        self.screen.set_clip(clip_rect)

        for i, plot in enumerate(plots):
            col_i = i % cols_count
            row_i = i // cols_count
            px = x + margin + col_i * (cw2 + margin)
            py = y + 35 + row_i * (ch2 + margin) - self.scroll_y

            if py + ch2 < clip_rect.top or py > clip_rect.bottom:
                continue

            soil     = plot.get('soil_quality', 0)
            base_col = _lerp_color(ACCENT_RED, ACCENT_GREEN, soil)
            card_rect = pygame.Rect(px, py, cw2, ch2)
            pygame.draw.rect(self.screen, BG_CARD2, card_rect, border_radius=6)
            pygame.draw.rect(self.screen, base_col, card_rect, width=2, border_radius=6)

            num_surf  = render_text_with_emojis(f"P{i+1}", self.font_xs, TEXT_BRIGHT)
            self.screen.blit(num_surf, (px + 6, py + 4))

            soil_surf = render_text_with_emojis(f"Sol {int(soil*100)}%", self.font_xs, base_col)
            self.screen.blit(soil_surf, (px + 6, py + 20))

            crop_str  = (plot.get('crop') or "Vide")[:10]
            c_surf    = render_text_with_emojis(crop_str, self.font_xs, TEXT_MUTED)
            self.screen.blit(c_surf, (px + 6, py + 36))

            if ch2 > 56:
                bx3 = px + 6; by3 = py + ch2 - 11; bw3 = cw2 - 12
                pygame.draw.rect(self.screen, BG_DARK,    (bx3, by3, bw3, 6), border_radius=3)
                pygame.draw.rect(self.screen, base_col,   (bx3, by3, int(bw3 * soil), 6), border_radius=3)

        self.screen.set_clip(None)

    def _draw_bottom_bar(self):
        bar_h   = 80
        bar_surf = pygame.Surface((self.width, bar_h), pygame.SRCALPHA)
        bar_surf.fill((10, 18, 32, 220))
        self.screen.blit(bar_surf, (0, self.height - bar_h))
        pygame.draw.line(self.screen, BORDER_COLOR, (0, self.height - bar_h), (self.width, self.height - bar_h), 1)
        self.replay_btn.draw(self.screen)
        self.export_btn.draw(self.screen)
        self.menu_btn.draw(self.screen)

    def _draw_card(self, x, y, w, h, border_color=BORDER_COLOR):
        rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(self.screen, BG_CARD, rect, border_radius=10)
        pygame.draw.rect(self.screen, border_color, rect, width=2, border_radius=10)

    def _draw_name_input_popup(self):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.screen.blit(overlay, (0, 0))

        r = self.input_popup_rect
        pygame.draw.rect(self.screen, BG_CARD, r, border_radius=14)
        pygame.draw.rect(self.screen, ACCENT_GREEN, r, width=2, border_radius=14)

        title_surf = render_text_with_emojis("Entrez votre nom pour l'export", self.font_md, TEXT_BRIGHT)
        title_rect = title_surf.get_rect(centerx=r.centerx, top=r.top + 18)
        self.screen.blit(title_surf, title_rect)

        box_col = (50, 100, 70) if self.input_box_active else BG_CARD2
        pygame.draw.rect(self.screen, box_col, self.input_box_rect, border_radius=7)
        pygame.draw.rect(self.screen, ACCENT_GREEN if self.input_box_active else BORDER_COLOR,
                         self.input_box_rect, width=2, border_radius=7)
        cursor = "_" if self.input_box_active else ""
        name_surf = render_text_with_emojis(self.player_name + cursor, self.font_md, TEXT_BRIGHT)
        self.screen.blit(name_surf, (self.input_box_rect.x + 12,
                                     self.input_box_rect.centery - name_surf.get_height()//2))

        if self.export_status_message:
            col = ACCENT_GREEN if "Exporte" in self.export_status_message else ACCENT_RED
            st_surf = render_text_with_emojis(self.export_status_message, self.font_sm, col)
            st_rect = st_surf.get_rect(centerx=r.centerx, bottom=r.bottom - 60)
            self.screen.blit(st_surf, st_rect)

        self.confirm_export_btn.draw(self.screen)
        self.close_export_btn.draw(self.screen)

    def _export_results_to_csv(self):
        if not self.player_name.strip():
            self.export_status_message = "Le nom ne peut pas etre vide."
            return

        sanitized = re.sub(r'[\\/*?:"<>|]', "", self.player_name)
        filename  = f"{sanitized}_results.csv"
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        exports_dir  = os.path.join(project_root, "rapports")
        os.makedirs(exports_dir, exist_ok=True)
        filepath = os.path.join(exports_dir, filename)

        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                w = csv.writer(f)
                w.writerow(['Resume'])
                w.writerow(['Argent Final (E)',        f"{self.final_money:.2f}"])
                w.writerow(['Reserve d Eau Finale (L)', f"{self.final_water:.2f}"])
                w.writerow(['Score de Durabilite (%)',  f"{self.sustainability_score}"])
                w.writerow(['Nourriture Recoltee (kg)', f"{self.food_harvested:.2f}"])
                w.writerow(['Objectif Nourriture (kg)', f"{self.food_target:.2f}"])
                w.writerow(['Nombre de Recoltes',       self.actions_taken.count("harvest")])
                w.writerow([])
                w.writerow(['Journal Quotidien'])
                w.writerow(['Jour', 'Rendement (kg)', 'Qualite Sol (%)'])
                for i, yld in enumerate(self.daily_yields):
                    sq = self.daily_soil_quality[i] * 100 if i < len(self.daily_soil_quality) else 'N/A'
                    w.writerow([i + 1,
                                f"{yld:.2f}" if isinstance(yld, (int, float)) else 'N/A',
                                f"{sq:.2f}"  if isinstance(sq,  (int, float)) else sq])
            self.export_status_message = f"Exporte : {filename}"
        except Exception as e:
            self.export_status_message = f"Erreur : {e}"

    def handle_event(self, event):
        if event.type == pygame.MOUSEWHEEL:
            self.scroll_y = max(0, self.scroll_y - event.y * 30)
            return None

        if self.show_name_input:
            if self.confirm_export_btn.handle_event(event):
                self._export_results_to_csv()
            elif self.close_export_btn.handle_event(event):
                self.show_name_input = False
                self.player_name     = ""
                self.export_status_message = ""
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.input_box_active = self.input_box_rect.collidepoint(event.pos)
            elif event.type == pygame.KEYDOWN and self.input_box_active:
                if event.key == pygame.K_RETURN:
                    self._export_results_to_csv()
                elif event.key == pygame.K_BACKSPACE:
                    self.player_name = self.player_name[:-1]
                else:
                    self.player_name += event.unicode
                self.export_status_message = ""
            return None

        if self.replay_btn.handle_event(event):
            return "replay"
        elif self.export_btn.handle_event(event):
            self.show_name_input = True
            return None
        elif self.menu_btn.handle_event(event):
            return "menu"
        return None
