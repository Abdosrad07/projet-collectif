import pygame
import numpy as np
import time
import random
import os

from core.farm_logic import FarmLogic
# Importer les constantes et widgets partagés
from .constants import (
    WHITE, BLACK, GREEN_PRIMARY, GREEN_LIGHT, GREEN_DARK, RED,
    YELLOW, BLUE, ORANGE, PURPLE, GRAY_LIGHT, GRAY_DARK, BROWN, BACKGROUND_GAME
)
from .widgets import Button, get_font, render_text_with_emojis

class CropCard:
    def __init__(self, x, y, width, height, plot_data):
        self.rect = pygame.Rect(x, y, width, height)
        self.plot_data = plot_data  # Garde une référence au dictionnaire de la parcelle
        self.harvest_timer = 0  # Minuteur pour l'animation de récolte
        self.water_animation_timer = 0 # Timer pour l'animation d'arrosage
        # Polices adaptatives (légèrement réduites)
        self.current_image = None
        self.next_image = None
        self.fade_alpha = 0
        self.font = get_font(int(height / 9.5))
        self.name_font = get_font(int(height / 8))

    def draw(self, screen, is_selected):
        # 1. Fond de la carte
        if self.plot_data['water_level'] < 20:
            # Animation de récolte : détermine la couleur de fond
            if self.plot_data["crop"] and self.plot_data["progress"] >= 0.9:
                animation_speed = 0.05 # Ajustez pour modifier la vitesse
                pulse_factor = np.sin(self.harvest_timer * animation_speed) * 5  # Amplitude du pulse
                color = (210 + pulse_factor, 180 + pulse_factor, 140) # Couleur terre sèche
            color = (210, 180, 140) # Couleur terre sèche
        elif self.plot_data["crop"]:
            color = GREEN_LIGHT
        else:
            color = YELLOW # Parcelle vide
        # Fond de la carte avec ombre subtile
        shadow_rect = self.rect.move(5, 5)
        pygame.draw.rect(screen, GRAY_DARK, shadow_rect, border_radius=15) # Ombre
        pygame.draw.rect(screen, color, self.rect, border_radius=15) # Fond principal
        
        # 2. Bordure de sélection
        if is_selected:
            pygame.draw.rect(screen, ORANGE, self.rect, width=4, border_radius=15)
        else:
            pygame.draw.rect(screen, BLACK, self.rect, width=2, border_radius=15)

        # Animation de sécheresse sur la parcelle
        if self.plot_data['water_level'] < 20:
            # Coordonnées relatives pour s'adapter à la taille de la carte
            crack_color = (139, 69, 19)
            pygame.draw.line(screen, crack_color, (self.rect.x + self.rect.width * 0.1, self.rect.y + self.rect.height * 0.6), (self.rect.x + self.rect.width * 0.3, self.rect.y + self.rect.height * 0.8), 2)
            pygame.draw.line(screen, crack_color, (self.rect.x + self.rect.width * 0.3, self.rect.y + self.rect.height * 0.8), (self.rect.x + self.rect.width * 0.35, self.rect.y + self.rect.height * 0.75), 2)
            pygame.draw.line(screen, crack_color, (self.rect.right - self.rect.width * 0.2, self.rect.y + self.rect.height * 0.55), (self.rect.right - self.rect.width * 0.3, self.rect.y + self.rect.height * 0.85), 2)
            pygame.draw.line(screen, crack_color, (self.rect.right - self.rect.width * 0.3, self.rect.y + self.rect.height * 0.85), (self.rect.right - self.rect.width * 0.4, self.rect.y + self.rect.height * 0.8), 2)

        # 3. Indicateurs visuels (maladie, plante)
        if self.plot_data.get("disease"):
            disease_icon = render_text_with_emojis("💀", self.font, RED)
            icon_rect = disease_icon.get_rect(topright=(self.rect.right - 10, self.rect.top + 5))
            screen.blit(disease_icon, icon_rect)    
        
        # Chargement et affichage de l'image de la plante en fonction de son évolution
        if self.plot_data["crop"]:
            crop_name = self.plot_data["crop"]
            progress = self.plot_data["progress"]

            # Détermine l'index de l'image (ex: 0 à 5 si vous avez 6 images)
            # progress (0.0 à 1.0) * 5 donne un nombre entre 0.0 et 5.0.
            # int() le tronque pour obtenir un index de 0, 1, 2, 3, 4 ou 5.
            image_index = int(progress * 5)

            # Construction du chemin de l'image
            image_path = os.path.join("assets", "images", crop_name, f"{crop_name}_{image_index}.png")

            scaled_image = None
            if os.path.exists(image_path):
                try:
                    # Charger l'image originale
                    image = pygame.image.load(image_path).convert_alpha()
                    # Redimensionner l'image pour qu'elle s'adapte à la carte
                    max_width = self.rect.width * 0.7
                    max_height = self.rect.height * 0.5
                    img_width, img_height = image.get_size()
                    scale = min(max_width / img_width, max_height / img_height) if img_width > 0 and img_height > 0 else 1
                    new_size = (int(img_width * scale), int(img_height * scale))
                    scaled_image = pygame.transform.scale(image, new_size)

                except pygame.error as e:
                    # Gestion de l'erreur si l'image ne peut pas être chargée
                    error_message = f"Image manquante: {image_path}"
                    error_surface = self.font.render(error_message, True, RED)
                    error_rect = error_surface.get_rect(center=self.rect.center)
                    screen.blit(error_surface, error_rect)
                    print(f"Erreur de chargement de l'image {image_path}: {e}")
            
            # Centrer et afficher l'image si elle a été chargée et redimensionnée
            if scaled_image:
                image_rect = scaled_image.get_rect(centerx=self.rect.centerx, y=self.rect.y + self.rect.height * 0.1)
                screen.blit(scaled_image, image_rect)
            
        
        # 4. Informations textuelles et barres de progression
        crop_name = self.plot_data["crop"]
        if crop_name:
            text_surface = render_text_with_emojis(crop_name, self.name_font, BLACK)
            text_rect = text_surface.get_rect(centerx=self.rect.centerx,
                                            y=self.rect.y + self.rect.height * 0.55)
            screen.blit(text_surface, text_rect)
            
            # Barre de progression
            progress = self.plot_data["progress"]
            progress_width = self.rect.width * 0.75
            progress_height = 10
            progress_x = self.rect.centerx - progress_width / 2
            progress_y = self.rect.bottom - self.rect.height * 0.25
            
            pygame.draw.rect(screen, GRAY_LIGHT,
                            (progress_x, progress_y, progress_width, progress_height),
                            border_radius=5)
            
            fill_width = int(progress_width * progress)
            if fill_width > 0:
                pygame.draw.rect(screen, BLUE,
                               (progress_x, progress_y, fill_width, progress_height),
                               border_radius=5)
                
            progress_percent_text = render_text_with_emojis(f"{int(progress * 100)}%", self.font, BLACK)
            progress_percent_rect = progress_percent_text.get_rect(centerx=self.rect.centerx, bottom=progress_y - 5)
            screen.blit(progress_percent_text, progress_percent_rect)

             # Incrémenter le minuteur de récolte si la plante est prête
            if self.plot_data["crop"] and self.plot_data["progress"] >= 0.9:
                self.harvest_timer += 1

         # 6. Animation de l'eau
        if self.water_animation_timer > 0:
            water_drop_size = int(self.rect.height * 0.1)
            water_drop_x = self.rect.centerx + random.randint(-10, 10)
            water_drop_y = self.rect.y + self.rect.height * 0.6 + random.randint(-5, 5)
            # pygame.draw.circle(screen, BLUE, (water_drop_x, water_drop_y), water_drop_size)
            self.water_animation_timer -= 1

        # Gestion de la transition
        if self.fade_alpha < 255 and self.current_image and self.next_image:
            self.fade_alpha += 15  # Ajustez la valeur pour une transition plus rapide ou plus lente

        

        # 5. Indicateurs d'état (eau et sol) en bas de la carte
        bar_width = self.rect.width * 0.25 # Barres plus petites pour en loger trois
        bar_height = 8
        bar_y = self.rect.bottom - bar_height - 10
        icon_y_offset = bar_y - 5
        
        # Barre d'eau (gauche)
        water_bar_rect = pygame.Rect(self.rect.x + 20, bar_y, bar_width, bar_height)
        pygame.draw.rect(screen, GRAY_LIGHT, water_bar_rect, border_radius=4)
        water_fill_width = int(water_bar_rect.width * (self.plot_data['water_level'] / 100))
        pygame.draw.rect(screen, BLUE, (water_bar_rect.x, water_bar_rect.y, water_fill_width, water_bar_rect.height), border_radius=4)
        screen.blit(render_text_with_emojis("💧", self.font, BLACK), (water_bar_rect.x - 18, icon_y_offset))

        # Barre de nutriments (centre)
        fert_bar_rect = pygame.Rect(self.rect.centerx - bar_width / 2, bar_y, bar_width, bar_height)
        pygame.draw.rect(screen, GRAY_LIGHT, fert_bar_rect, border_radius=4)
        # Le bonus peut dépasser 0.5, mais on le cape visuellement à 100% de la barre pour la clarté
        fert_fill_percent = min(1.0, self.plot_data['fertilizer_bonus'] / 0.5)
        fert_fill_width = int(fert_bar_rect.width * fert_fill_percent)
        pygame.draw.rect(screen, YELLOW, (fert_bar_rect.x, fert_bar_rect.y, fert_fill_width, fert_bar_rect.height), border_radius=4)
        screen.blit(render_text_with_emojis("⚡", self.font, BLACK), (fert_bar_rect.x - 18, icon_y_offset))

        # Barre de qualité du sol (droite)
        soil_bar_rect = pygame.Rect(self.rect.right - 20 - bar_width, bar_y, bar_width, bar_height)
        pygame.draw.rect(screen, GRAY_LIGHT, soil_bar_rect, border_radius=4)
        soil_fill_width = int(soil_bar_rect.width * self.plot_data['soil_quality'])
        pygame.draw.rect(screen, BROWN, (soil_bar_rect.x, soil_bar_rect.y, soil_fill_width, soil_bar_rect.height), border_radius=4)
        screen.blit(render_text_with_emojis("🌍", self.font, BLACK), (soil_bar_rect.x - 18, icon_y_offset))

class GameInterface:
    def __init__(self, screen):
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        # Polices
        self.title_font = get_font(48) # Un peu plus petit pour faire de la place
        self.subtitle_font = get_font(28)
        self.text_font = get_font(24)
        
        # Logique du jeu
        self.logic = FarmLogic()
        
        # État de l'UI
        self.selected_plot_index = 0
        self.show_ai_popup = False
        self.ai_advice = ""
        self.show_plant_menu = False
        self.crop_cards = []

        # NOUVEAU: État pour les infobulles
        self.tooltip_text = ""
        self.tooltip_pos = (0, 0)

        # NOUVEAU: Gestion du temps réel
        self.is_paused = True
        self.day_duration = 15  # Durée d'un jour en secondes
        self.day_timer = 0
        self.last_frame_time = time.time()
        self.time_speed_multiplier = 1

        # Particules pour les animations météo
        self.rain_particles = []
        self.snow_particles = []
        self.wind_particles = []

        # Boutons d'action
        button_width = 110
        button_height = 45
        button_spacing = 10
        num_buttons = 7 # Augmenté pour inclure "Traiter"
        total_buttons_width = (button_width * num_buttons) + (button_spacing * (num_buttons - 1))
        start_x_buttons = (self.width - total_buttons_width) // 2 # Centrage des boutons
        buttons_y = self.height - 150 # Position verticale des boutons d'action
        
        self.plant_btn = Button(start_x_buttons, buttons_y, button_width, button_height, "Plante", GREEN_DARK)
        self.water_btn = Button(start_x_buttons + (button_width + button_spacing), buttons_y, button_width, button_height, "Arroser", BLUE)
        self.drain_btn = Button(start_x_buttons + (button_width + button_spacing) * 2, buttons_y, button_width, button_height, "Drainer", (96, 165, 250))
        self.fertilize_btn = Button(start_x_buttons + (button_width + button_spacing) * 3, buttons_y, button_width, button_height, "Fertiliser", ORANGE)
        self.treat_btn = Button(start_x_buttons + (button_width + button_spacing) * 4, buttons_y, button_width, button_height, "Traiter", (139, 0, 139)) # Violet foncé
        self.harvest_btn = Button(start_x_buttons + (button_width + button_spacing) * 5, buttons_y, button_width, button_height, "Récolter", GREEN_PRIMARY)
        self.ai_btn = Button(start_x_buttons + (button_width + button_spacing) * 6, buttons_y, button_width, button_height, "Conseil IA", PURPLE)
        self.play_pause_btn = Button(self.width - 340, self.height - 80, 150, 50, "▶️ Jouer", GREEN_DARK)
        self.speed_btn = Button(self.width - 170, self.height - 80, 150, 50, "Vitesse x1", GREEN_DARK)

        # Menu contextuel IA (centré)
        self.ai_popup_rect = pygame.Rect(self.width // 2 - 200, self.height // 2 - 150, 400, 300)
        self.close_ai_btn = Button(self.ai_popup_rect.right - 60, self.ai_popup_rect.y + 10, 
                                  50, 30, "✕", (220, 38, 38))
        
        # Menu de plantation
        self.plant_menu_rect = pygame.Rect(0, 0, 250, 300) # Position sera dynamique
        self.plant_menu_buttons = []
        
    def setup_from_config(self, config):
        """Configure le jeu à partir des paramètres de configuration"""
        self.logic.setup_from_config(config)
        self.generate_crop_cards_from_logic()
        self.selected_plot_index = 0
        self.show_ai_popup = False
        self.ai_advice = ""
        self.show_plant_menu = False
        self.is_paused = True
        self.day_timer = 0
        self.last_frame_time = time.time()
        self.time_speed_multiplier = 1
        self.play_pause_btn.text = "▶️ Jouer"
        self.speed_btn.text = "Vitesse x1"
        
    def generate_crop_cards_from_logic(self):
        """Génère les cartes de cultures en s'assurant qu'elles ne chevauchent pas les panneaux."""
        self.crop_cards.clear()
        num_plots = self.logic.plots_config
        
        # --- NOUVELLE LOGIQUE DE DISPOSITION ADAPTATIVE ---
        # La disposition s'adapte pour ne jamais dépasser 2 rangées, évitant les conflits verticaux.
        if num_plots <= 4:
            cards_per_row = num_plots
            card_width = 200
        elif num_plots <= 8:
            cards_per_row = 4
            card_width = 200
        else:  # 9 à 12 parcelles
            cards_per_row = 6
            card_width = 150  # Cartes plus petites pour faire 2 rangées de 6

        card_height = card_width * 1.1 # Maintenir un ratio
        card_padding_x = 20
        card_padding_y = 30
        
        # 1. Définir l'espace disponible pour les cartes (à gauche des panneaux d'information)
        info_panel_area_width = self.width * 0.35  # 30% pour les panneaux + 5% de marge
        cards_area_width = self.width - info_panel_area_width

        # 2. Calculer la largeur réelle de la grille pour un centrage parfait
        num_rows = (num_plots + cards_per_row - 1) // cards_per_row
        # La largeur de la grille dépend du nombre de cartes dans la rangée la plus large
        actual_cards_in_widest_row = min(num_plots, cards_per_row) if num_rows == 1 else cards_per_row
        grid_width = actual_cards_in_widest_row * (card_width + card_padding_x) - card_padding_x
        
        # 3. Centrer la grille dans l'espace disponible
        start_x = (cards_area_width - grid_width) / 2
        start_y = 140 # Un peu plus bas pour laisser de l'espace à l'en-tête
        
        for i, plot_data in enumerate(self.logic.plots):
            row = i // cards_per_row
            col = i % cards_per_row
            x = start_x + col * (card_width + card_padding_x)
            y = start_y + row * (card_height + card_padding_y)
            
            card = CropCard(x, y, card_width, card_height, plot_data)
            self.crop_cards.append(card)

    

    def get_ai_advice(self):
        """Génère un conseil IA contextuel pour la parcelle sélectionnée."""
        advices = []
        
        if not (0 <= self.selected_plot_index < len(self.logic.plots)):
            return "Sélectionnez une parcelle pour obtenir un conseil."

        plot = self.logic.plots[self.selected_plot_index]

        # Conseils liés aux maladies
        if plot.get("disease"):
            advices.append(f"💀 La plante est atteinte de {plot['disease']}. Un traitement est urgent !")
        
        # Conseils liés à la culture
        if plot["crop"]:
            if plot["progress"] >= 0.9:
                advices.append(f"🌾 {plot['crop']} est prêt à être récolté !")
            elif plot["progress"] < 0.3:
                advices.append(f"🌱 {plot['crop']} est encore jeune. Patience avant la récolte.")
            
            if plot["water_level"] < 30:
                advices.append(f"💧 {plot['crop']} a soif. Un arrosage serait bénéfique.")
            elif plot["water_level"] > 90:
                advices.append(f"🌊 Attention, {plot['crop']} est sur-irrigué. Pensez à drainer.")
            
            if plot["fertilizer_bonus"] < 20:
                advices.append(f"🌿 {plot['crop']} pourrait bénéficier d'un peu d'engrais.")
            elif plot["fertilizer_bonus"] > 80:
                advices.append(f"⚠️ {plot['crop']} a reçu trop d'engrais. Réduisez les apports.")
        else:
            advices.append("🌱 Cette parcelle est vide. C'est le moment idéal pour planter !")

        # Conseils liés à la qualité du sol
        if plot["soil_quality"] < 0.5:
            advices.append("🌍 La qualité de ce sol se dégrade. Évitez les fertilisants pendant un moment.")
        elif plot["soil_quality"] > 0.8:
            advices.append("🌟 Ce sol est en excellente condition. Profitez-en pour cultiver des plantes exigeantes.")

        # Conseils liés à la réserve d'eau globale
        if self.logic.water_reserve < 50:
            advices.append("🚰 Votre réserve d'eau globale est faible.")
        elif self.logic.water_reserve > 200:
            advices.append("💧 Votre réserve d'eau est abondante. Utilisez-la judicieusement.")
        
        if plot.get("disease"):
            advices.append(f"💀 {plot['crop']} est affecté par une maladie. Traitez-la rapidement.")

        # Conseils généraux
        if not advices:
            advices.append("✅ Tout semble sous contrôle pour cette parcelle. Continuez comme ça !")
            
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
    
    def _build_plant_menu(self):
        """Construit le menu de plantation à côté de la parcelle sélectionnée."""
        if not (0 <= self.selected_plot_index < len(self.crop_cards)):
            return

        selected_card_rect = self.crop_cards[self.selected_plot_index].rect
        self.plant_menu_rect.topleft = (selected_card_rect.right + 10, selected_card_rect.top)

        self.plant_menu_buttons.clear()
        y_offset = self.plant_menu_rect.y + 10
        for crop_name in self.logic.available_crops:
            btn = Button(self.plant_menu_rect.x + 10, y_offset, self.plant_menu_rect.width - 20, 40, crop_name, GREEN_DARK)
            self.plant_menu_buttons.append(btn)
            y_offset += 50

    def draw_plant_menu(self):
        """Affiche le menu de sélection des cultures."""
        if not self.show_plant_menu:
            return

        pygame.draw.rect(self.screen, WHITE, self.plant_menu_rect, border_radius=10)
        pygame.draw.rect(self.screen, GREEN_PRIMARY, self.plant_menu_rect, width=3, border_radius=10)

        for btn in self.plant_menu_buttons:
            btn.draw(self.screen)
        
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
            advice_text = render_text_with_emojis(line, self.text_font, BLACK)
            self.screen.blit(advice_text, (x, y_offset))
            y_offset += 30

    def _draw_objective_bar(self):
        bar_y = 85 # Juste en dessous de l'en-tête
        bar_height = 25
        bar_width = self.width * 0.6
        bar_x = (self.width - bar_width) / 2

        # Étiquette de texte
        obj_text = render_text_with_emojis("Objectif:", self.subtitle_font, BLACK)
        self.screen.blit(obj_text, (bar_x - obj_text.get_width() - 10, bar_y - 2))

        # Barre de progression
        food_progress = 0
        if self.logic.food_target > 0:
            food_progress = self.logic.food_harvested / self.logic.food_target
        food_progress = np.clip(food_progress, 0, 1.0)

        # Fond
        pygame.draw.rect(self.screen, WHITE, (bar_x, bar_y, bar_width, bar_height), border_radius=12)
        pygame.draw.rect(self.screen, GRAY_DARK, (bar_x, bar_y, bar_width, bar_height), width=2, border_radius=12)

        # Remplissage
        fill_width = int((bar_width - 4) * food_progress)
        if fill_width > 0:
            pygame.draw.rect(self.screen, GREEN_PRIMARY, (bar_x + 2, bar_y + 2, fill_width, bar_height - 4), border_radius=10)

        # Texte sur la barre
        progress_text_str = f"{self.logic.food_harvested:.0f} / {self.logic.food_target:.0f} kg"
        progress_text = render_text_with_emojis(progress_text_str, self.text_font, BLACK)
        progress_text_rect = progress_text.get_rect(center=(bar_x + bar_width / 2, bar_y + bar_height / 2))
        self.screen.blit(progress_text, progress_text_rect)

    def _draw_tooltip(self):
        """Affiche une infobulle si du texte est défini."""
        if not self.tooltip_text:
            return

        # Rendre le texte pour obtenir ses dimensions
        text_surface = render_text_with_emojis(self.tooltip_text, self.text_font, BLACK)
        text_rect = text_surface.get_rect()

        # Créer le fond de l'infobulle
        tooltip_rect = pygame.Rect(0, 0, text_rect.width + 10, text_rect.height + 10)
        
        # Positionner l'infobulle près du curseur, en s'assurant qu'elle reste à l'écran
        tooltip_rect.topleft = (self.tooltip_pos[0] + 15, self.tooltip_pos[1])
        if tooltip_rect.right > self.width:
            tooltip_rect.right = self.tooltip_pos[0] - 15
        if tooltip_rect.bottom > self.height:
            tooltip_rect.bottom = self.tooltip_pos[1]

        # Dessiner le fond et la bordure
        pygame.draw.rect(self.screen, WHITE, tooltip_rect, border_radius=5)
        pygame.draw.rect(self.screen, GRAY_DARK, tooltip_rect, width=1, border_radius=5)

        # Centrer le texte dans l'infobulle
        text_rect.center = tooltip_rect.center
        self.screen.blit(text_surface, text_rect)
    
    def _draw_day_progress_bar(self):
        """Dessine une barre de progression pour la journée en cours."""
        bar_height = 10
        bar_y = self.height - bar_height
        
        progress = 0
        if self.day_duration > 0:
            progress = self.day_timer / self.day_duration
        
        bar_width = self.width * progress
        
        pygame.draw.rect(self.screen, GREEN_LIGHT, (0, bar_y, bar_width, bar_height))
        pygame.draw.rect(self.screen, GREEN_DARK, (0, bar_y, self.width, bar_height), 1)

    def _update_and_draw_weather_effects(self):
        """Gère l'affichage des animations météo en fonction de la condition actuelle."""
        condition = self.logic.get_current_day_weather()['condition']

        if "Pluie" in condition:
            self._draw_rain(is_heavy="forte" in condition)
        else:
            self.rain_particles.clear()

        if condition == "snow":
            self._draw_snow()
        else:
            self.snow_particles.clear()
        
        if condition == "heatwave":
            self._draw_heatwave_effect()
        
        # Le vent est une animation d'ambiance, pas une condition fixe
        self._draw_wind_effect()

    def _draw_rain(self, is_heavy):
        """Dessine des particules de pluie."""
        num_particles = 250 if is_heavy else 100
        if len(self.rain_particles) != num_particles:
            self.rain_particles = [[random.randint(0, self.width), random.randint(0, self.height)] for _ in range(num_particles)]

        for p in self.rain_particles:
            p[1] += 12 if is_heavy else 8 # Vitesse de la pluie
            if p[1] > self.height:
                p[1] = random.randint(-20, 0)
                p[0] = random.randint(0, self.width)
            pygame.draw.line(self.screen, (173, 216, 230), (p[0], p[1]), (p[0], p[1] + 7), 2 if is_heavy else 1)

    def _draw_snow(self):
        """Dessine des particules de neige."""
        if not self.snow_particles:
            self.snow_particles = [[random.randint(0, self.width), random.randint(0, self.height), random.randint(2, 4)] for _ in range(150)]

        for p in self.snow_particles:
            p[1] += 1.5 # Vitesse de la neige
            p[0] += random.uniform(-0.5, 0.5) # Mouvement de dérive
            if p[1] > self.height:
                p[1] = random.randint(-20, 0)
                p[0] = random.randint(0, self.width)
            pygame.draw.circle(self.screen, WHITE, (p[0], p[1]), p[2])

    def _draw_heatwave_effect(self):
        """Applique un filtre de couleur chaude pour simuler une canicule."""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((255, 150, 0, 30)) # Orange très transparent
        self.screen.blit(overlay, (0, 0))

    def _draw_wind_effect(self):
        """Dessine des lignes rapides pour simuler le vent."""
        if not self.wind_particles and random.random() < 0.01:
            self.wind_particles = [[random.randint(-100, self.width), random.randint(0, self.height)] for _ in range(15)]
        elif self.wind_particles and random.random() < 0.01:
            self.wind_particles.clear()

        if self.wind_particles:
            for p in self.wind_particles:
                p[0] += 25 # Vitesse du vent
                if p[0] > self.width:
                    p[0] = -50
                    p[1] = random.randint(0, self.height)
                pygame.draw.line(self.screen, (200, 200, 220), (p[0], p[1]), (p[0] + 50, p[1]), 1)
                
               
    def draw(self):
        self.screen.fill(BACKGROUND_GAME)

        # --- NOUVEAU: Mise à jour du temps ---
        current_time = time.time()
        delta_time = current_time - self.last_frame_time
        self.last_frame_time = current_time

        if not self.is_paused:
            self.day_timer += delta_time * self.time_speed_multiplier
            if self.day_timer >= self.day_duration:
                self.logic.update_simulation()
                self.day_timer -= self.day_duration # Conserver le surplus de temps pour le jour suivant

        # Vérifier fin de jeu
        if self.logic.current_day > self.logic.max_days:
            if self.logic.check_win_condition():
                return "game_over"
            else:
                return "game_over"
        
        # En-tête
        header_surface = pygame.Surface((self.width, 80), pygame.SRCALPHA)
        pygame.draw.rect(header_surface, GREEN_PRIMARY, header_surface.get_rect())
        self.screen.blit(header_surface, (0,0))

        # Barre d'objectif
        self._draw_objective_bar()
        
        # Bouton menu
        menu_btn_rect = pygame.Rect(15, 20, 100, 40)
        pygame.draw.rect(self.screen, GREEN_DARK, menu_btn_rect, border_radius=8)
        menu_text = render_text_with_emojis("← Menu", self.text_font, WHITE)
        menu_rect = menu_text.get_rect(center=menu_btn_rect.center)
        self.screen.blit(menu_text, menu_rect)
        
        # Titre avec jour et saison
        season = self.logic.get_current_season()
        season_icon_map = {"Printemps": "🌱", "Été": "☀️", "Automne": "🍂", "Hiver": "❄️",
                           "Petite saison des pluies": "🌦️", "Grande saison sèche": "☀️", "Grande saison des pluies": "🌧️", "Petite saison sèche": "🏜️"}
        season_icon = season_icon_map.get(season, "❓")

        # Calcul de l'année actuelle
        region_data = self.logic.config.get("region_data", {})
        base_season_durations = region_data.get("season_durations", [10, 10, 10, 10])
        days_in_one_game_year = sum(base_season_durations) if sum(base_season_durations) > 0 else 1
        current_year = ((self.logic.current_day - 1) // days_in_one_game_year) + 1

        title_text = render_text_with_emojis(f"Farm Navigator - Année {current_year} - {season_icon} {season}", self.title_font, WHITE)
        day_text = render_text_with_emojis(f"Jour {self.logic.current_day}/{self.logic.max_days}", self.subtitle_font, WHITE)
        
        title_rect = title_text.get_rect(centerx=self.width//2, y=10)
        day_rect = day_text.get_rect(centerx=self.width//2, y=title_rect.bottom + 10)
        
        self.screen.blit(title_text, title_rect)
        self.screen.blit(day_text, day_rect)
        
        # Grille des cultures
        for i, card in enumerate(self.crop_cards):
            card.draw(self.screen, i == self.selected_plot_index)
        
        # Panels d'information
        self._draw_info_panels() # Les panneaux sont maintenant plus grands et mieux espacés
        
        # Indicateur de sélection 
        selected_panel_rect = pygame.Rect(self.width//2 - 150, self.height - 210, 300, 40)
        pygame.draw.rect(self.screen, GREEN_LIGHT, selected_panel_rect, border_radius=10)
        pygame.draw.rect(self.screen, GREEN_DARK, selected_panel_rect, width=2, border_radius=10)
        selected_text = render_text_with_emojis(f"Parcelle {self.selected_plot_index + 1} sélectionnée", self.text_font, BLACK)
        selected_rect = selected_text.get_rect(center=selected_panel_rect.center)
        self.screen.blit(selected_text, selected_rect)
        
        # Boutons d'action
        self.plant_btn.draw(self.screen)
        self.water_btn.draw(self.screen)
        self.drain_btn.draw(self.screen)
        self.fertilize_btn.draw(self.screen)
        self.treat_btn.draw(self.screen)
        self.harvest_btn.draw(self.screen)
        self.ai_btn.draw(self.screen)
        self.play_pause_btn.draw(self.screen)
        self.speed_btn.draw(self.screen)
        
        # Menus contextuels
        self.draw_plant_menu()
        self.draw_ai_popup()

        # Barre de progression du jour
        self._draw_day_progress_bar()
        
        # Effets météo par-dessus tout le reste
        self._update_and_draw_weather_effects()

        # NOUVEAU: L'infobulle est dessinée en dernier pour être au-dessus de tout
        self._draw_tooltip()

        return None

        
    def _draw_info_panels(self):
        """Dessine les panels d'information"""
        # Panneaux d'information sur le côté droit
        panel_width = self.width * 0.32 # Occupe 30% de la largeur de l'écran
        panel_x = self.width - panel_width - 30 # Avec une marge de 30px
        
        # Panel météo
        weather_panel = pygame.Rect(panel_x, 140, panel_width, 180)
        pygame.draw.rect(self.screen, WHITE, weather_panel, border_radius=10)
        pygame.draw.rect(self.screen, GRAY_DARK, weather_panel, width=2, border_radius=10) # Bordure
        
        # Récupérer la météo actuelle depuis la logique
        weather_today = self.logic.get_current_day_weather()
        temp = weather_today.get('temp', 0)
        precip = weather_today.get('precip', 0)
        condition = weather_today.get('condition', 'Inconnue')

        # Choisir une icône en fonction de la condition
        if "heatwave" in condition:
            icon = "🥵"
        elif "frost" in condition:
            icon = "🥶"
        elif "Pluie" in condition:
            icon = "🌧️"
        else:
            icon = "☀️"

        weather_title = render_text_with_emojis(f"{icon} Météo du jour", self.subtitle_font, GREEN_DARK)
        self.screen.blit(weather_title, (panel_x + 15, weather_panel.y + 15))
        
        temp_text = render_text_with_emojis(f"Température: {temp:.1f}°C", self.text_font, BLACK)
        self.screen.blit(temp_text, (panel_x + 15, weather_panel.y + 55))

        precip_text = render_text_with_emojis(f"Précipitations: {precip:.1f} mm", self.text_font, BLACK)
        self.screen.blit(precip_text, (panel_x + 15, weather_panel.y + 80))


        if condition == "heatwave" or condition == "frost":
            event_text = render_text_with_emojis(f"Alerte: {condition.capitalize()} !", self.text_font, (220, 38, 38))
            self.screen.blit(event_text, (panel_x + 15, weather_panel.y + 120))
        
        # Panel ressources
        resources_panel = pygame.Rect(panel_x, weather_panel.bottom + 20, panel_width, 140)
        pygame.draw.rect(self.screen, WHITE, resources_panel, border_radius=10)
        pygame.draw.rect(self.screen, GRAY_DARK, resources_panel, width=2, border_radius=10) # Bordure
        
        resources_title = render_text_with_emojis("Ressources Globales", self.subtitle_font, BLACK)
        self.screen.blit(resources_title, (panel_x + 10, 295))
        
        # Couleur d'alerte pour l'eau
        water_color = (220, 38, 38) if self.logic.water_reserve < 50 else BLACK
        water_text = render_text_with_emojis(f"💧 Eau: {self.logic.water_reserve:.0f}L", self.text_font, water_color)
        self.screen.blit(water_text, (panel_x + 15, resources_panel.y + 50))
        
        money_text = render_text_with_emojis(f"💰 Argent: {self.logic.money:.0f}€", self.text_font, BLACK)
        self.screen.blit(money_text, (panel_x + 15, resources_panel.y + 75))

        # Score de durabilité
        sustain_color = GREEN_PRIMARY if self.logic.sustainability_score > 70 else ORANGE if self.logic.sustainability_score > 40 else (220, 38, 38)
        sustain_text = render_text_with_emojis(f"🌍 Durabilité: {self.logic.sustainability_score}%", self.text_font, sustain_color)
        self.screen.blit(sustain_text, (panel_x + 15, resources_panel.y + 100))
        
        # Panel état des cultures
        crops_panel = pygame.Rect(panel_x, resources_panel.bottom + 20, panel_width, 100)
        pygame.draw.rect(self.screen, WHITE, crops_panel, border_radius=10)
        pygame.draw.rect(self.screen, GRAY_DARK, crops_panel, width=2, border_radius=10) # Bordure
        
        crops_title = render_text_with_emojis("État du Potager", self.subtitle_font, BLACK)
        self.screen.blit(crops_title, (panel_x + 15, crops_panel.y + 10))
        
        mature_count = sum(1 for plot in self.logic.plots if plot["crop"] and plot["progress"] >= 0.9)
        growing_count = sum(1 for plot in self.logic.plots if plot["crop"] and 0 < plot["progress"] < 0.95)
        
        status_text = render_text_with_emojis(f"Matures: {mature_count} | En croissance: {growing_count}", self.text_font, BLACK)
        self.screen.blit(status_text, (panel_x + 15, crops_panel.y + 55))
        
    def handle_event(self, event):
        # NOUVEAU: Gérer le survol pour les infobulles
        if event.type == pygame.MOUSEMOTION:
            self.tooltip_text = "" # Réinitialiser à chaque mouvement
            for card in self.crop_cards:
                # Recalculer les positions des barres pour le test de collision
                bar_width = card.rect.width * 0.25
                bar_height = 8
                bar_y = card.rect.bottom - bar_height - 10

                water_bar_rect = pygame.Rect(card.rect.x + 20, bar_y, bar_width, bar_height)
                fert_bar_rect = pygame.Rect(card.rect.centerx - bar_width / 2, bar_y, bar_width, bar_height)
                soil_bar_rect = pygame.Rect(card.rect.right - 20 - bar_width, bar_y, bar_width, bar_height)

                if water_bar_rect.collidepoint(event.pos):
                    self.tooltip_text = f"Eau: {card.plot_data['water_level']:.0f}%"
                    self.tooltip_pos = event.pos
                    break # Une seule infobulle à la fois
                elif fert_bar_rect.collidepoint(event.pos):
                    fert_percent = min(1.0, card.plot_data['fertilizer_bonus'] / 0.5) * 100
                    self.tooltip_text = f"Nutriments: {fert_percent:.0f}%"
                    self.tooltip_pos = event.pos
                    break
                elif soil_bar_rect.collidepoint(event.pos):
                    self.tooltip_text = f"Qualité du sol: {card.plot_data['soil_quality']*100:.0f}%"
                    self.tooltip_pos = event.pos
                    break

        # Gestion du popup IA (bouton fermer) - TRAITÉ EN PREMIER
        if self.show_ai_popup:
            if self.close_ai_btn.handle_event(event):
                self.show_ai_popup = False
                return None

        # Gestion du menu de plantation - TRAITÉ EN SECOND
        if self.show_plant_menu:
            for i, btn in enumerate(self.plant_menu_buttons):
                if btn.handle_event(event):
                    crop_to_plant = self.logic.available_crops[i]
                    self.logic.plant_action(self.selected_plot_index, crop_to_plant)
                    self.show_plant_menu = False
                    return None

        # Gestion des boutons d'action principaux - TRAITÉ EN TROISIÈME
        if self.plant_btn.handle_event(event):
            if self.logic.plots[self.selected_plot_index]["crop"] is None:
                self.show_plant_menu = not self.show_plant_menu
                if self.show_plant_menu:
                    self._build_plant_menu()
            return None
        elif self.water_btn.handle_event(event):
            if self.logic.water_action(self.selected_plot_index):
                self.crop_cards[self.selected_plot_index].water_animation_timer = 30
            return None
        elif self.drain_btn.handle_event(event):
            self.logic.drain_action(self.selected_plot_index)
            return None
        elif self.fertilize_btn.handle_event(event):
            self.logic.fertilize_action(self.selected_plot_index)
            return None
        elif self.treat_btn.handle_event(event):
            self.logic.treat_action(self.selected_plot_index)
            return None
        elif self.harvest_btn.handle_event(event):
            self.logic.harvest_action(self.selected_plot_index)
            return None
        elif self.ai_btn.handle_event(event):
            self.show_ai_popup = True
            self.ai_advice = self.get_ai_advice()
            return None
        elif self.play_pause_btn.handle_event(event):
            self.is_paused = not self.is_paused
            if self.is_paused:
                self.play_pause_btn.text = "▶ Jouer"
            else:
                self.play_pause_btn.text = "⏸ Pause"
                self.last_frame_time = time.time()
            return None
        elif self.speed_btn.handle_event(event):
            if self.time_speed_multiplier == 1:
                self.time_speed_multiplier = 2
                self.speed_btn.text = "Vitesse x2"
            elif self.time_speed_multiplier == 2:
                self.time_speed_multiplier = 4
                self.speed_btn.text = "Vitesse x4"
            else:
                self.time_speed_multiplier = 1
                self.speed_btn.text = "Vitesse x1"
            return None

        # Clic général - TRAITÉ EN DERNIER
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Vérifier clic sur "Menu"
            menu_btn_rect = pygame.Rect(15, 20, 100, 40)
            if menu_btn_rect.collidepoint(event.pos):
                self.logic.save_game()
                return "menu"
            
            # Fermer le menu de plantation si on clique en dehors
            if self.show_plant_menu and not self.plant_menu_rect.collidepoint(event.pos):
                self.show_plant_menu = False
            
            # Fermer le popup IA si on clique en dehors
            if self.show_ai_popup and not self.ai_popup_rect.collidepoint(event.pos):
                self.show_ai_popup = False

            # Gérer la sélection de parcelle
            if not self.show_plant_menu and not self.show_ai_popup:
                for i, card in enumerate(self.crop_cards):
                    if card.rect.collidepoint(event.pos):
                        self.selected_plot_index = i
                        break

        return None
            
    def get_results(self):
        """Retourne les résultats de la simulation"""
        return {
            "daily_yields": self.logic.daily_yields,
            "daily_soil_quality": self.logic.daily_soil_quality,
            "sustainability_score": self.logic.sustainability_score,
            "food_harvested": self.logic.food_harvested,
            "food_target": self.logic.food_target,
            "final_money": self.logic.money,
            "final_water": self.logic.water_reserve,
            "actions_taken": self.logic.actions_taken,
            "plots_data": self.logic.plots
        }
