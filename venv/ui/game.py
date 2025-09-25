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
        color = self.color if not self.hovered else tuple(max(0, c-30) for c in self.color)
        pygame.draw.rect(screen, color, self.rect, border_radius=10)
        
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
        # Fond de la carte
        pygame.draw.rect(screen, self.color, self.rect, border_radius=15)
        
        # Icône de plante (simple représentation)
        if self.name:
            icon_size = 40
            icon_x = self.rect.centerx
            icon_y = self.rect.y + 30
            
            # Tige
            pygame.draw.line(screen, GREEN_DARK, 
                            (icon_x, icon_y + 20), 
                            (icon_x, icon_y + icon_size), 3)
            
            # Feuilles
            for i, angle in enumerate([45, -45, 135, -135]):
                if i < 2:  # Feuilles du haut
                    end_x = icon_x + math.cos(math.radians(angle)) * 15
                    end_y = icon_y + 10 + math.sin(math.radians(angle)) * 15
                    pygame.draw.line(screen, GREEN_DARK, 
                                   (icon_x, icon_y + 10), (end_x, end_y), 2)
        
        # Nom de la culture
        if self.name:
            text_surface = self.font.render(self.name, True, BLACK)
            text_rect = text_surface.get_rect(centerx=self.rect.centerx, 
                                            y=self.rect.y + 80)
            screen.blit(text_surface, text_rect)
            
            # Barre de progression
            progress_width = self.rect.width - 20
            progress_height = 8
            progress_x = self.rect.x + 10
            progress_y = self.rect.bottom - 30
            
            # Fond de la barre
            pygame.draw.rect(screen, WHITE, 
                            (progress_x, progress_y, progress_width, progress_height),
                            border_radius=4)
            
            # Progression
            fill_width = int(progress_width * self.progress)
            if fill_width > 0:
                pygame.draw.rect(screen, BLUE, 
                               (progress_x, progress_y, fill_width, progress_height),
                               border_radius=4)

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
        
        # Boutons d'action
        self.water_btn = Button(160, 550, 120, 40, "💧 Arroser (10L)", BLUE)
        self.fertilize_btn = Button(320, 550, 150, 40, "🌱 Fertiliser (50€)", ORANGE)
        self.harvest_btn = Button(492, 550, 120, 40, "🌾 Récolter", GREEN_PRIMARY)
        self.ai_btn = Button(620, 550, 120, 40, "🤖 Conseil IA", PURPLE)
        
        # Menu contextuel IA
        self.ai_popup_rect = pygame.Rect(300, 200, 400, 300)
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
        
        # Calculer la disposition des cartes
        cards_per_row = 3
        card_width = 150
        card_height = 150
        start_x = 50
        start_y = 120
        spacing_x = 170
        spacing_y = 170
        
        available_crops = config["region_data"]["cultures"]
        
        for i in range(config["plots"]):
            row = i // cards_per_row
            col = i % cards_per_row
            x = start_x + col * spacing_x
            y = start_y + row * spacing_y
            
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
        
        # En-tête
        header_rect = pygame.Rect(0, 0, self.width, 60)
        pygame.draw.rect(self.screen, GREEN_PRIMARY, header_rect)
        
        # Bouton menu
        menu_text = self.text_font.render("← Menu", True, WHITE)
        menu_rect = menu_text.get_rect(x=20, centery=30)
        self.screen.blit(menu_text, menu_rect)
        
        # Titre avec jour
        title_text = self.text_font.render(f"Farm Navigator - Jour {self.current_day}/{self.max_days}", True, WHITE)
        title_rect = title_text.get_rect(centerx=self.width//2, centery=30)
        self.screen.blit(title_text, title_rect)
        
        # Indicateur de temps restant
        days_left = self.max_days - self.current_day
        if days_left > 0:
            time_text = self.text_font.render(f"⏰ {days_left} jour(s) restant(s)", True, WHITE)
            time_rect = time_text.get_rect(x=self.width - 200, centery=30)
            self.screen.blit(time_text, time_rect)
        
        # Grille des cultures
        for card in self.crop_cards:
            card.draw(self.screen)
        
        # Panels d'information
        self._draw_info_panels()
        
        # Indicateur de sélection
        selected_text = self.text_font.render("🌱 Parcelle 1 sélectionnée", True, GREEN_PRIMARY)
        selected_rect = selected_text.get_rect(centerx=self.width//2, y=500)
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
        weather_panel = pygame.Rect(620, 80, 350, 120)
        pygame.draw.rect(self.screen, WHITE, weather_panel, border_radius=10)
        
        weather_title = self.text_font.render("☀️ Météo du jour", True, BLACK)
        self.screen.blit(weather_title, (630, 90))
        
        sunny_text = self.text_font.render("☀️ Ensoleillé    25°C", True, BLACK)
        self.screen.blit(sunny_text, (630, 120))
        
        # Barre de progression du jour
        day_progress = ((time.time() - self.last_day_change) / self.day_duration)
        if self.current_day < self.max_days:
            progress_text = self.text_font.render(f"Jour {self.current_day}: {int(day_progress * 100)}%", True, BLACK)
            self.screen.blit(progress_text, (630, 150))
            
            # Barre de progression
            progress_rect = pygame.Rect(630, 170, 300, 10)
            pygame.draw.rect(self.screen, GRAY_LIGHT, progress_rect, border_radius=5)
            fill_width = int(300 * day_progress)
            if fill_width > 0:
                pygame.draw.rect(self.screen, GREEN_PRIMARY, 
                               (630, 170, fill_width, 10), border_radius=5)
        
        # Panel ressources
        resources_panel = pygame.Rect(620, 220, 350, 120)
        pygame.draw.rect(self.screen, WHITE, resources_panel, border_radius=10)
        
        resources_title = self.text_font.render("💧 Ressources", True, BLACK)
        self.screen.blit(resources_title, (630, 230))
        
        # Couleur d'alerte pour l'eau
        water_color = (220, 38, 38) if self.water_level < 30 else BLACK
        water_text = self.text_font.render(f"💧 Eau                    {self.water_level}L", True, water_color)
        self.screen.blit(water_text, (630, 260))
        
        money_text = self.text_font.render(f"💰 Argent             {self.money}€", True, BLACK)
        self.screen.blit(money_text, (630, 290))
        
        # Score de durabilité
        sustain_color = GREEN_PRIMARY if self.sustainability_score > 70 else (255, 165, 0) if self.sustainability_score > 40 else (220, 38, 38)
        sustain_text = self.text_font.render(f"🌍 Durabilité        {self.sustainability_score}%", True, sustain_color)
        self.screen.blit(sustain_text, (630, 315))
        
        # Panel état des cultures
        crops_panel = pygame.Rect(620, 360, 350, 80)
        pygame.draw.rect(self.screen, WHITE, crops_panel, border_radius=10)
        
        crops_title = self.text_font.render("🌱 État des cultures", True, BLACK)
        self.screen.blit(crops_title, (630, 370))
        
        mature_count = sum(1 for card in self.crop_cards if card.progress >= 0.8 and card.name)
        growing_count = sum(1 for card in self.crop_cards if 0 < card.progress < 0.8 and card.name)
        
        status_text = self.text_font.render(f"Matures: {mature_count} | En croissance: {growing_count}", True, BLACK)
        self.screen.blit(status_text, (630, 400))
        
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