import pygame
import math
import random
import time

# Couleurs
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN_PRIMARY = (34, 197, 94)
GREEN_LIGHT = (134, 239, 172)
GREEN_DARK = (21, 128, 61)
YELLOW = (254, 240, 138)
BLUE = (59, 130, 246)
ORANGE = (251, 146, 60)
PURPLE = (168, 85, 247)
GRAY_LIGHT = (243, 244, 246)
GRAY_DARK = (75, 85, 99)

class Button:
    def __init__(self, x, y, width, height, text, color, text_color=WHITE, font_size=24):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.text_color = text_color
        self.font = pygame.font.Font(None, font_size)
        self.hovered = False
        
    def draw(self, screen):
        # Ombre du bouton
        if not self.hovered:
            shadow_color = (self.color[0]//2, self.color[1]//2, self.color[2]//2, 100) # Couleur plus foncée et transparente
            shadow_rect = self.rect.move(3, 3)
            pygame.draw.rect(screen, shadow_color, shadow_rect, border_radius=10)

        # Couleur du bouton (plus claire au survol)
        button_color = self.color
        if self.hovered:
            button_color = tuple(min(255, c + 30) for c in self.color) # Éclaircir au survol
        
        pygame.draw.rect(screen, button_color, self.rect, border_radius=10)
        
        # Texte du bouton
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                return True
        return False

class CropCard:
    def __init__(self, x, y, width, height, name, progress, color):
        self.rect = pygame.Rect(x, y, width, height)
        self.name = name
        self.progress = progress
        self.color = color
        self.font = pygame.font.Font(None, 24)
        
    def draw(self, screen):
        # Fond de la carte avec ombre subtile
        shadow_rect = self.rect.move(5, 5)
        pygame.draw.rect(screen, GRAY_DARK, shadow_rect, border_radius=15) # Ombre
        pygame.draw.rect(screen, self.color, self.rect, border_radius=15) # Fond principal
        
        # Bordure
        pygame.draw.rect(screen, BLACK, self.rect, width=2, border_radius=15)
        
        # Icône de plante (simple représentation améliorée)
        if self.name:
            icon_size = 50
            icon_x = self.rect.centerx
            icon_y = self.rect.y + 40
            
            # Tige
            pygame.draw.line(screen, GREEN_DARK, 
                            (icon_x, icon_y + 10), 
                            (icon_x, icon_y + icon_size), 4)
            
            # Feuilles (plus stylisées)
            leaf_color = GREEN_DARK
            pygame.draw.ellipse(screen, leaf_color, (icon_x - 20, icon_y, 25, 15))
            pygame.draw.ellipse(screen, leaf_color, (icon_x - 5, icon_y - 10, 25, 15))
            pygame.draw.ellipse(screen, leaf_color, (icon_x - 20, icon_y + 15, 25, 15))
            pygame.draw.ellipse(screen, leaf_color, (icon_x - 5, icon_y + 25, 25, 15))
        
        # Nom de la culture
        if self.name:
            text_surface = self.font.render(self.name, True, BLACK)
            text_rect = text_surface.get_rect(centerx=self.rect.centerx, 
                                            y=self.rect.y + 100) # Ajuster la position
            screen.blit(text_surface, text_rect)
            
            # Barre de progression
            progress_width = self.rect.width - 30 # Plus de marge
            progress_height = 10 # Plus épaisse
            progress_x = self.rect.x + 15
            progress_y = self.rect.bottom - 35 # Ajuster la position
            
            # Fond de la barre
            pygame.draw.rect(screen, GRAY_LIGHT, 
                            (progress_x, progress_y, progress_width, progress_height),
                            border_radius=5)
            
            # Progression
            fill_width = int(progress_width * self.progress)
            if fill_width > 0:
                pygame.draw.rect(screen, BLUE, 
                               (progress_x, progress_y, fill_width, progress_height),
                               border_radius=5)
                
            # Texte de progression
            progress_percent_text = self.font.render(f"{int(self.progress * 100)}%", True, BLACK)
            progress_percent_rect = progress_percent_text.get_rect(centerx=self.rect.centerx, y=progress_y - 20)
            screen.blit(progress_percent_text, progress_percent_rect)

class GameInterface:
    def __init__(self, screen):
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        # Polices
        self.title_font = pygame.font.Font(None, 72)
        self.subtitle_font = pygame.font.Font(None, 28)
        self.text_font = pygame.font.Font(None, 24)
        
        # État du jeu
        self.current_day = 1
        self.max_days = 7
        self.last_day_change = time.time()
        self.day_duration = 300 # 300 secondes par jour virtuel
        self.water_level = 75
        self.money = 1150
        self.sustainability_score = 100
        self.daily_yields = []
        self.actions_taken = []
        self.show_ai_popup = False
        self.ai_advice = ""
        self.crop_cards = []
        
        # Boutons d'action (centrés et espacés)
        button_width = 140
        button_height = 50
        button_spacing = 20
        total_buttons_width = (button_width * 4) + (button_spacing * 3)
        start_x_buttons = (self.width - total_buttons_width) // 2
        
        self.water_btn = Button(start_x_buttons, 550, button_width, button_height, "💧 Arroser (10L)", BLUE)
        self.fertilize_btn = Button(start_x_buttons + button_width + button_spacing, 550, button_width, button_height, "🌱 Fertiliser (50€)", ORANGE)
        self.harvest_btn = Button(start_x_buttons + (button_width + button_spacing) * 2, 550, button_width, button_height, "🌾 Récolter", GREEN_PRIMARY)
        self.ai_btn = Button(start_x_buttons + (button_width + button_spacing) * 3, 550, button_width, button_height, "🤖 Conseil IA", PURPLE)
        
        # Menu contextuel IA (centré)
        self.ai_popup_rect = pygame.Rect(self.width // 2 - 200, self.height // 2 - 150, 400, 300)
        self.close_ai_btn = Button(self.ai_popup_rect.right - 60, self.ai_popup_rect.y + 10, 
                                  50, 30, "✕", (220, 38, 38))
        
    def setup_from_config(self, config):
        """Configure le jeu à partir des paramètres de configuration"""
        self.reset_simulation()
        self.generate_crop_cards(config)
        
    def reset_simulation(self):
        """Remet à zéro la simulation pour une nouvelle partie"""
        self.current_day = 1
        self.last_day_change = time.time()
        self.water_level = 75
        self.money = 1150
        self.sustainability_score = 100
        self.daily_yields = []
        self.actions_taken = []
        self.show_ai_popup = False
        self.ai_advice = ""
        
    def generate_crop_cards(self, config):
        """Génère les cartes de cultures basées sur la configuration"""
        self.crop_cards.clear()
        
        # Calculer la disposition des cartes (centrées)
        cards_per_row = 3
        card_width = 160 # Légèrement plus large
        card_height = 180 # Légèrement plus haute
        card_padding_x = 30
        card_padding_y = 30
        
        # Calculer le point de départ pour centrer les cartes
        total_cards_width = (card_width * cards_per_row) + (card_padding_x * (cards_per_row - 1))
        start_x = (self.width - total_cards_width) // 2
        start_y = 100 # Ajuster la position de départ en Y
        
        available_crops = config["region_data"]["cultures"]
        
        for i in range(config["plots"]):
            row = i // cards_per_row
            col = i % cards_per_row
            x = start_x + col * (card_width + card_padding_x)
            y = start_y + row * (card_height + card_padding_y)
            
            # Assigner une culture ou laisser vide
            if i < len(available_crops):
                crop_name = available_crops[i]
                progress = 0.0
                color = GREEN_LIGHT
            else:
                crop_name = ""
                progress = 0.0
                color = YELLOW
            
            card = CropCard(x, y, card_width, card_height, crop_name, progress, color)
            self.crop_cards.append(card)
            
    def update_simulation(self):
        """Met à jour la simulation jour par jour"""
        current_time = time.time()
        if current_time - self.last_day_change >= self.day_duration:
            if self.current_day < self.max_days:
                self.current_day += 1
                self.last_day_change = current_time
                
                # Évolution naturelle
                self.water_level = max(0, self.water_level - random.randint(5, 15))
                
                # Croissance des cultures
                daily_yield = 0
                for card in self.crop_cards:
                    if card.name:  # Si la parcelle a une culture
                        growth = random.uniform(0.05, 0.15)
                        card.progress = min(1.0, card.progress + growth)
                        if card.progress >= 0.8:  # Culture mature
                            daily_yield += random.randint(10, 30)
                
                self.daily_yields.append(daily_yield)
                
                # Événements aléatoires
                if random.random() < 0.3:  # 30% de chance d'événement
                    self.sustainability_score = max(0, self.sustainability_score - random.randint(5, 15))
                    
    def get_ai_advice(self):
        """Génère un conseil IA contextuel"""
        advices = []
        
        if self.water_level < 30:
            advices.append("💧 Attention ! Votre réserve d'eau est critique. Arrosez vos cultures rapidement.")
        
        mature_crops = sum(1 for card in self.crop_cards if card.progress >= 0.8 and card.name)
        if mature_crops > 0:
            advices.append(f"🌾 {mature_crops} culture(s) sont prêtes à être récoltées !")
            
        if self.sustainability_score < 50:
            advices.append("🌍 Votre score de durabilité baisse. Utilisez moins d'engrais chimiques.")
            
        if self.current_day >= 5:
            advices.append("⏰ Fin de cycle proche ! Récoltez vos cultures matures.")
            
        empty_plots = sum(1 for card in self.crop_cards if not card.name)
        if empty_plots > 0:
            advices.append(f"🌱 Vous avez {empty_plots} parcelle(s) vide(s). Plantez pour optimiser vos rendements.")
        
        if not advices:
            advices.append("✅ Excellent travail ! Votre potager se développe bien.")
            
        return " ".join(advices[:2])  # Maximum 2 conseils
        
    def draw_ai_popup(self):
        """Affiche le menu contextuel des conseils IA"""
        if not self.show_ai_popup:
            return
            
        # Fond semi-transparent
        overlay = pygame.Surface((self.width, self.height))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # Popup
        pygame.draw.rect(self.screen, WHITE, self.ai_popup_rect, border_radius=15)
        pygame.draw.rect(self.screen, GREEN_PRIMARY, self.ai_popup_rect, width=3, border_radius=15)
        
        # Titre
        title_text = self.subtitle_font.render("🤖 Conseil de l'IA", True, GREEN_PRIMARY)
        title_rect = title_text.get_rect(centerx=self.ai_popup_rect.centerx, 
                                       y=self.ai_popup_rect.y + 20)
        self.screen.blit(title_text, title_rect)
        
        # Contenu du conseil
        self._draw_text_multiline(self.ai_advice, self.ai_popup_rect.x + 20, 
                                self.ai_popup_rect.y + 70, self.ai_popup_rect.width - 40)
        
        # Bouton fermer
        self.close_ai_btn.draw(self.screen)
        
    def _draw_text_multiline(self, text, x, y, max_width):
        """Dessine du texte sur plusieurs lignes"""
        words = text.split()
        lines = []
        current_line = []
        line_width = 0
        
        for word in words:
            word_width = self.text_font.size(word + " ")[0]
            if line_width + word_width <= max_width:
                current_line.append(word)
                line_width += word_width
            else:
                lines.append(" ".join(current_line))
                current_line = [word]
                line_width = word_width
        if current_line:
            lines.append(" ".join(current_line))
        
        y_offset = y
        for line in lines:
            advice_text = self.text_font.render(line, True, BLACK)
            self.screen.blit(advice_text, (x, y_offset))
            y_offset += 30
            
    def draw(self):
        self.screen.fill(GRAY_LIGHT)
        
        # Mise à jour de la simulation
        self.update_simulation()
        
        # Vérifier fin de jeu
        if self.current_day >= self.max_days:
            return "game_over"
        
        # En-tête (avec dégradé et ombre)
        header_surface = pygame.Surface((self.width, 70), pygame.SRCALPHA)
        pygame.draw.rect(header_surface, GREEN_PRIMARY, header_surface.get_rect(), border_radius=0)
        pygame.draw.rect(header_surface, (0,0,0,50), header_surface.get_rect().move(0,5), border_radius=0) # Ombre
        self.screen.blit(header_surface, (0,0))
        
        # Bouton menu (plus stylisé)
        menu_btn_rect = pygame.Rect(15, 15, 100, 40)
        pygame.draw.rect(self.screen, GREEN_DARK, menu_btn_rect, border_radius=8)
        menu_text = self.text_font.render("← Menu", True, WHITE)
        menu_rect = menu_text.get_rect(center=menu_btn_rect.center)
        self.screen.blit(menu_text, menu_rect)
        
        # Titre avec jour (plus grand et centré)
        title_text = self.title_font.render(f"Farm Navigator", True, WHITE)
        day_text = self.subtitle_font.render(f"Jour {self.current_day}/{self.max_days}", True, WHITE)
        
        title_rect = title_text.get_rect(centerx=self.width//2, y=10)
        day_rect = day_text.get_rect(centerx=self.width//2, y=title_rect.bottom + 5)
        
        self.screen.blit(title_text, title_rect)
        self.screen.blit(day_text, day_rect)
        
        # Indicateur de temps restant (plus visible)
        days_left = self.max_days - self.current_day
        if days_left > 0:
            time_panel_rect = pygame.Rect(self.width - 180, 15, 160, 40)
            pygame.draw.rect(self.screen, YELLOW, time_panel_rect, border_radius=8)
            time_text = self.text_font.render(f"⏰ {days_left} jour(s) restant(s)", True, BLACK)
            time_rect = time_text.get_rect(center=time_panel_rect.center)
            self.screen.blit(time_text, time_rect)
        
        # Grille des cultures
        for card in self.crop_cards:
            card.draw(self.screen)
        
        # Panels d'information
        self._draw_info_panels()
        
        # Indicateur de sélection (plus stylisé)
        selected_panel_rect = pygame.Rect(self.width//2 - 150, 500, 300, 40)
        pygame.draw.rect(self.screen, GREEN_LIGHT, selected_panel_rect, border_radius=10)
        pygame.draw.rect(self.screen, GREEN_DARK, selected_panel_rect, width=2, border_radius=10)
        selected_text = self.text_font.render("🌱 Parcelle 1 sélectionnée", True, BLACK)
        selected_rect = selected_text.get_rect(center=selected_panel_rect.center)
        self.screen.blit(selected_text, selected_rect)
        
        # Boutons d'action
        self.water_btn.draw(self.screen)
        self.fertilize_btn.draw(self.screen)
        self.harvest_btn.draw(self.screen)
        self.ai_btn.draw(self.screen)
        
        # Menu contextuel IA
        self.draw_ai_popup()
        
        return None
        
    def _draw_info_panels(self):
        """Dessine les panels d'information"""
        # Panel météo
        weather_panel = pygame.Rect(620, 80, 350, 150) # Agrandir le panel
        pygame.draw.rect(self.screen, WHITE, weather_panel, border_radius=10)
        pygame.draw.rect(self.screen, GRAY_DARK, weather_panel, width=2, border_radius=10) # Bordure
        
        weather_title = self.subtitle_font.render("☀️ Météo du jour", True, BLACK)
        self.screen.blit(weather_title, (630, 90))
        
        sunny_text = self.text_font.render("☀️ Ensoleillé    25°C", True, BLACK)
        self.screen.blit(sunny_text, (630, 120))
        
        # Barre de progression du jour
        day_progress = ((time.time() - self.last_day_change) / self.day_duration)
        if self.current_day < self.max_days:
            progress_text = self.text_font.render(f"Jour {self.current_day}: {int(day_progress * 100)}%", True, BLACK)
            self.screen.blit(progress_text, (630, 150))
            
            # Barre de progression
            progress_rect = pygame.Rect(630, 170, 300, 15) # Plus épaisse
            pygame.draw.rect(self.screen, GRAY_LIGHT, progress_rect, border_radius=7)
            fill_width = int(300 * day_progress)
            if fill_width > 0:
                pygame.draw.rect(self.screen, GREEN_PRIMARY, 
                               (630, 170, fill_width, 15), border_radius=7)
        
        # Panel ressources
        resources_panel = pygame.Rect(620, 240, 350, 150) # Agrandir le panel
        pygame.draw.rect(self.screen, WHITE, resources_panel, border_radius=10)
        pygame.draw.rect(self.screen, GRAY_DARK, resources_panel, width=2, border_radius=10) # Bordure
        
        resources_title = self.subtitle_font.render("💧 Ressources", True, BLACK)
        self.screen.blit(resources_title, (630, 250))
        
        # Couleur d'alerte pour l'eau
        water_color = (220, 38, 38) if self.water_level < 30 else BLACK
        water_text = self.text_font.render(f"💧 Eau                    {self.water_level}L", True, water_color)
        self.screen.blit(water_text, (630, 280))
        
        money_text = self.text_font.render(f"💰 Argent             {self.money}€", True, BLACK)
        self.screen.blit(money_text, (630, 310))
        
        # Score de durabilité
        sustain_color = GREEN_PRIMARY if self.sustainability_score > 70 else (255, 165, 0) if self.sustainability_score > 40 else (220, 38, 38)
        sustain_text = self.text_font.render(f"🌍 Durabilité        {self.sustainability_score}%", True, sustain_color)
        self.screen.blit(sustain_text, (630, 340))
        
        # Panel état des cultures
        crops_panel = pygame.Rect(620, 400, 350, 100) # Agrandir le panel
        pygame.draw.rect(self.screen, WHITE, crops_panel, border_radius=10)
        pygame.draw.rect(self.screen, GRAY_DARK, crops_panel, width=2, border_radius=10) # Bordure
        
        crops_title = self.subtitle_font.render("🌱 État des cultures", True, BLACK)
        self.screen.blit(crops_title, (630, 410))
        
        mature_count = sum(1 for card in self.crop_cards if card.progress >= 0.8 and card.name)
        growing_count = sum(1 for card in self.crop_cards if 0 < card.progress < 0.8 and card.name)
        
        status_text = self.text_font.render(f"Matures: {mature_count} | En croissance: {growing_count}", True, BLACK)
        self.screen.blit(status_text, (630, 440))
        
    def handle_event(self, event):
        # Vérifier clic sur "Menu"
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos
            if (mouse_pos[1] < 60 and mouse_pos[0] < 100):
                return "menu"
        
        # Gestion des boutons d'action
        if self.water_btn.handle_event(event):
            if self.water_level >= 10:
                self.water_level -= 10
                self.money -= 5  # Coût de l'eau
                # Améliorer la croissance des cultures
                for card in self.crop_cards:
                    if card.name:
                        card.progress = min(1.0, card.progress + 0.1)
                self.actions_taken.append("water")
                print("Arrosage effectué!")
        elif self.fertilize_btn.handle_event(event):
            if self.money >= 50:
                self.money -= 50
                self.sustainability_score = max(0, self.sustainability_score - 10)
                # Boost de croissance
                for card in self.crop_cards:
                    if card.name:
                        card.progress = min(1.0, card.progress + 0.2)
                self.actions_taken.append("fertilize")
                print("Fertilisation effectuée!")
        elif self.harvest_btn.handle_event(event):
            harvested = 0
            for card in self.crop_cards:
                if card.progress >= 0.8 and card.name:
                    # Récolte
                    yield_amount = random.randint(20, 40)
                    self.money += yield_amount
                    card.progress = 0.0  # Reset pour replantation
                    harvested += 1
            if harvested > 0:
                self.actions_taken.append("harvest")
                print(f"Récolte effectuée! {harvested} culture(s) récoltée(s)")
        elif self.ai_btn.handle_event(event):
            self.ai_advice = self.get_ai_advice()
            self.show_ai_popup = True
            print("Conseil IA demandé!")
            
        # Gestion du popup IA
        if self.show_ai_popup:
            if self.close_ai_btn.handle_event(event):
                self.show_ai_popup = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if not self.ai_popup_rect.collidepoint(event.pos):
                    self.show_ai_popup = False
                    
        return None
        
    def get_results(self):
        """Retourne les résultats de la simulation"""
        return {
            "daily_yields": self.daily_yields,
            "sustainability_score": self.sustainability_score,
            "final_money": self.money,
            "final_water": self.water_level,
            "actions_taken": self.actions_taken,
            "crop_cards": self.crop_cards
        }
