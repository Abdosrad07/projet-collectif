import pygame
import json
import os
from datetime import datetime, timedelta

# Importer les constantes et les widgets partagés
from .constants import WHITE, BLACK, GREEN_PRIMARY, GRAY_LIGHT, GRAY_DARK, GREEN_LIGHT, GREEN_DARK, ORANGE
from .widgets import Button, get_font, render_text_with_emojis

# Importer la fonction de l'API NASA
from core.nasa_api import get_nasa_power_data

class ConfigInterface:
    def __init__(self, screen):
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        # Polices
        self.title_font = get_font(72)
        self.subtitle_font = get_font(28)
        self.text_font = get_font(24)
        
        # Configuration
        self.selected_plots = 6
        self.selected_years = 1
        self.selected_config = None
        self.status_message = ""
        self.loading = False

        # Données des régions chargées depuis un fichier JSON
        self.region_data = self._load_regions()
        self.locations = list(self.region_data.keys())
        self.location_index = 0
        self.selected_location = self.locations[self.location_index] if self.locations else ""
        
         # Charger la clé API depuis les variables d'environnement pour la sécurité
        self.nasa_api_key = os.getenv("NASA_API_KEY")
        
        # Positions relatives pour les boutons
        center_x = self.width // 2
        
        # Boutons
        self.plots_minus_btn = Button(center_x - 350, 220, 50, 50, "-", GRAY_DARK)
        self.plots_plus_btn = Button(center_x - 150, 220, 50, 50, "+", GRAY_DARK)
        self.years_minus_btn = Button(center_x + 150, 220, 50, 50, "-", GRAY_DARK)
        self.years_plus_btn = Button(center_x + 350, 220, 50, 50, "+", GRAY_DARK)

        self.location_prev_btn = Button(center_x - 300, 340, 50, 50, "←", GRAY_DARK)
        self.location_next_btn = Button(center_x + 250, 340, 50, 50, "→", GRAY_DARK)
        
        # Boutons du bas
        bottom_y = self.height - 90
        self.confirm_config_btn = Button(center_x - 100, bottom_y, 200, 50, "Confirmer", GREEN_PRIMARY)
        self.back_to_menu_btn = Button(40, bottom_y + 5, 120, 40, "← Retour", GRAY_DARK, WHITE, 20)
        
    def _load_regions(self):
        """Charge les données des régions depuis un fichier JSON."""
        # Construit un chemin robuste vers le fichier, indépendant du lieu d'exécution
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        regions_path = os.path.join(project_root, "data", "regions_fr.json")
        try:
            with open(regions_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Erreur: Fichier '{regions_path}' introuvable ou invalide. {e}")
            return {}    
        
    def draw(self):
        # Si en cours de chargement, afficher un écran dédié
        if self.loading:
            self.screen.fill(GRAY_LIGHT)
            status_text = render_text_with_emojis(self.status_message, self.subtitle_font, BLACK)
            status_rect = status_text.get_rect(center=(self.width / 2, self.height / 2 - 20))
            self.screen.blit(status_text, status_rect)
            # Simple animation de chargement
            pygame.draw.circle(self.screen, GREEN_PRIMARY, (self.width // 2, self.height // 2 + 30), 20, 4)
            return

        # Fond similaire au menu
        for y in range(self.height):
            alpha = y / self.height
            color = tuple(int(WHITE[i] * (1 - alpha) + GRAY_LIGHT[i] * alpha) for i in range(3))
            pygame.draw.line(self.screen, color, (0, y), (self.width, y))
        
        # Titre
        title_text = render_text_with_emojis("CONFIGURATION DU POTAGER", self.title_font, GREEN_PRIMARY)
        title_rect = title_text.get_rect(centerx=self.width//2, y=50)
        self.screen.blit(title_text, title_rect)

        # Variable pour centrer les éléments, nécessaire pour le positionnement dynamique
        center_x = self.width // 2
        
        # Section nombre de parcelles
        # Afficher un message d'avertissement si la clé API est manquante
        if not self.nasa_api_key:
            warning_text = render_text_with_emojis("Clé API NASA non configurée. Le jeu utilisera une météo aléatoire.", self.text_font, ORANGE)
            warning_rect = warning_text.get_rect(centerx=self.width/2, y=110)
            self.screen.blit(warning_text, warning_rect)


        plots_title = render_text_with_emojis("Nombre de parcelles", self.subtitle_font, GREEN_DARK)
        plots_rect = plots_title.get_rect(centerx=center_x - 250, y=160)
        self.screen.blit(plots_title, plots_rect)
        
        # Affichage du nombre de parcelles avec boutons
        self.plots_minus_btn.draw(self.screen)
        plots_text = render_text_with_emojis(str(self.selected_plots), self.title_font, GREEN_PRIMARY)
        plots_text_rect = plots_text.get_rect(centerx=center_x - 250, centery=245)
        self.screen.blit(plots_text, plots_text_rect)
        self.plots_plus_btn.draw(self.screen)

        # Section nombre d'années
        years_title = render_text_with_emojis("Durée (années)", self.subtitle_font, GREEN_DARK)
        years_rect = years_title.get_rect(centerx=center_x + 250, y=160)
        self.screen.blit(years_title, years_rect)
        
        self.years_minus_btn.draw(self.screen)
        years_text = render_text_with_emojis(str(self.selected_years), self.title_font, GREEN_PRIMARY)
        years_text_rect = years_text.get_rect(centerx=center_x + 250, centery=245)
        self.screen.blit(years_text, years_text_rect)
        self.years_plus_btn.draw(self.screen)
        
        
        # Section localisation
        location_title = render_text_with_emojis("Localisation", self.subtitle_font, GREEN_DARK)
        location_rect = location_title.get_rect(centerx=self.width//2, y=310)
        self.screen.blit(location_title, location_rect)
        
        # Affichage de la localisation avec boutons
        self.location_prev_btn.draw(self.screen)
        location_text = render_text_with_emojis(self.selected_location, self.subtitle_font, GREEN_PRIMARY)
        location_text_rect = location_text.get_rect(centerx=self.width//2, centery=365)
        self.screen.blit(location_text, location_text_rect)
        self.location_next_btn.draw(self.screen)
        
        
        # Informations sur la région sélectionnée
        if not self.selected_location or self.selected_location not in self.region_data:
            return # Ne pas dessiner les panneaux si les données sont absentes
        region_info = self.region_data[self.selected_location]
        
        # Calculs pour les panneaux d'information du bas
        panel_y = 420
        panel_height = 220
        total_panel_width = self.width * 0.9
        panel_spacing = 20
        soil_panel_width = total_panel_width * 0.55
        crops_panel_width = total_panel_width - soil_panel_width - panel_spacing
        start_x = (self.width - total_panel_width) / 2
        
        # Panel des caractéristiques du sol
        soil_panel = pygame.Rect(start_x, panel_y, soil_panel_width, panel_height)
        pygame.draw.rect(self.screen, WHITE, soil_panel, border_radius=15)
        pygame.draw.rect(self.screen, GREEN_PRIMARY, soil_panel, width=3, border_radius=15)
        
        soil_title = render_text_with_emojis("🌍 Caractéristiques du Sol", self.subtitle_font, GREEN_DARK)
        self.screen.blit(soil_title, (soil_panel.x + 15, soil_panel.y + 15))
        
        climat_text = render_text_with_emojis(f"Climat: {region_info['climat']}", self.text_font, BLACK)
        self.screen.blit(climat_text, (soil_panel.x + 15, soil_panel.y + 60))
        
        sol_text = render_text_with_emojis(f"Type de sol: {region_info['sol']}", self.text_font, BLACK)
        self.screen.blit(sol_text, (soil_panel.x + 15, soil_panel.y + 85))
        
        ph_text = render_text_with_emojis(f"pH optimal: {region_info['ph']}", self.text_font, BLACK)
        self.screen.blit(ph_text, (soil_panel.x + 15, soil_panel.y + 110))
        
        # Panel des cultures disponibles
        crops_panel = pygame.Rect(start_x + soil_panel_width + panel_spacing, panel_y, crops_panel_width, panel_height)
        pygame.draw.rect(self.screen, WHITE, crops_panel, border_radius=15)
        pygame.draw.rect(self.screen, GREEN_PRIMARY, crops_panel, width=3, border_radius=15)
        
        crops_title = render_text_with_emojis("🌱 Cultures Disponibles", self.subtitle_font, GREEN_DARK)
        self.screen.blit(crops_title, (crops_panel.x + 15, crops_panel.y + 15))
        
        # Affichage des cultures en colonnes
        for i, culture in enumerate(region_info['cultures']):
            x = crops_panel.x + 15 + (i % 2) * (crops_panel.width / 2.2)
            y = crops_panel.y + 60 + (i // 2) * 25
            culture_text = render_text_with_emojis(f"• {culture}", self.text_font, BLACK)
            self.screen.blit(culture_text, (x, y))
        
        # Boutons
        self.back_to_menu_btn.draw(self.screen)
        self.confirm_config_btn.draw(self.screen)
        
    
    def handle_event(self, event):
        if self.loading:
            return None # Bloquer les interactions pendant le chargement

        if self.plots_minus_btn.handle_event(event):
            if self.selected_plots > 3:
                self.selected_plots -= 1
        elif self.plots_plus_btn.handle_event(event):
            if self.selected_plots < 12:
                self.selected_plots += 1
        elif self.years_minus_btn.handle_event(event):
            if self.selected_years > 1:
                self.selected_years -= 1
        elif self.years_plus_btn.handle_event(event):
            if self.selected_years < 5:
                self.selected_years += 1
        elif self.location_prev_btn.handle_event(event):
            self.location_index = (self.location_index - 1) % len(self.locations)
            self.selected_location = self.locations[self.location_index]
        elif self.location_next_btn.handle_event(event):
            self.location_index = (self.location_index + 1) % len(self.locations)
            self.selected_location = self.locations[self.location_index]
        elif self.confirm_config_btn.handle_event(event):
            # Lancer la préparation de la configuration
            self.loading = True
            self.status_message = f"Chargement des données météo pour {self.selected_location}..."
            return "prepare_game" # Indiquer au main.py de lancer la préparation
        elif self.back_to_menu_btn.handle_event(event):
            return "back"
        return None

    def prepare_game_config(self):
        """
        Récupère les données météo de la NASA et finalise la configuration du jeu.
        Cette méthode est bloquante et doit être appelée après avoir affiché l'écran de chargement.
        """
        region_info = self.region_data[self.selected_location]

        # Vérifier si les coordonnées sont présentes
        if "lat" not in region_info or "lon" not in region_info:
            print(f"ERREUR: Coordonnées (lat, lon) manquantes pour {self.selected_location} dans regions_fr.json.")
            self.status_message = "Erreur: Coordonnées manquantes."
            self.selected_config = {"error": "Missing coordinates"}
            self.loading = False
            return

        # Si la clé API n'est pas définie, on continue sans données météo
        nasa_data = None

        # --- NOUVELLE LOGIQUE ---
        # On récupère les données météo sur une année complète (l'année passée).
        # La simulation de 40 jours sera une "compression" de cette année.

        end_date_api = datetime.now() - timedelta(days=1)
        start_date_api = end_date_api - timedelta(days=364) # 365 jours au total
        if self.nasa_api_key:

            try:
                nasa_data = get_nasa_power_data(
                    latitude=region_info["lat"],
                    longitude=region_info["lon"],
                    start_date=start_date_api.strftime("%Y%m%d"),
                    end_date=end_date_api.strftime("%Y%m%d"),
                    api_key=self.nasa_api_key,
                )
                self.status_message = "Données NASA chargées. Lancement..."
            except Exception as e:
                print(f"Erreur lors de la récupération des données NASA : {e}")
                self.status_message = "Erreur de connexion à l'API NASA."
                self.selected_config = {"error": str(e)}
        else:
            self.status_message = "Lancement sans données météo (clé API manquante)."
            start_date_api = datetime.now() # Pour le mode hors-ligne, on utilise la date actuelle

        # Finaliser la configuration
        self.selected_config = {
            "plots": self.selected_plots,
            "years": self.selected_years,
            "location": self.selected_location,
            "region_data": region_info,
            "nasa_weather_data": nasa_data,
            "start_date": start_date_api, # On passe la date de début de la PÉRIODE de 365 jours
        }
        self.loading = False    
        
    def get_config(self):
        """Retourne la configuration finale du jeu, une fois prête."""
        return self.selected_config