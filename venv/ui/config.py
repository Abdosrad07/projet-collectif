import pygame

# Couleurs
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN_PRIMARY = (34, 197, 94)
GREEN_LIGHT = (134, 239, 172)
GREEN_DARK = (21, 128, 61)
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

class ConfigInterface:
    def __init__(self, screen):
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        # Polices
        self.title_font = pygame.font.Font(None, 72)
        self.subtitle_font = pygame.font.Font(None, 28)
        self.text_font = pygame.font.Font(None, 24)
        
        # Configuration
        self.selected_plots = 6
        self.selected_location = "Provence"
        self.locations = ["Provence", "Normandie", "Bretagne", "Alsace", "Languedoc"]
        self.location_index = 0
        
        # Boutons
        self.plots_minus_btn = Button(350, 200, 40, 40, "-", GRAY_DARK)
        self.plots_plus_btn = Button(550, 200, 40, 40, "+", GRAY_DARK)
        self.location_prev_btn = Button(350, 280, 40, 40, "←", GRAY_DARK)
        self.location_next_btn = Button(550, 280, 40, 40, "→", GRAY_DARK)
        self.confirm_config_btn = Button(self.width//2 - 100, 580, 200, 50, "Confirmer", GREEN_PRIMARY)
        self.back_to_menu_btn = Button(50, 580, 100, 40, "← Retour", GRAY_DARK, WHITE, 20)
        
        # Données des régions
        self.region_data = {
            "Provence": {
                "climat": "Méditerranéen",
                "sol": "Calcaire, bien drainé",
                "ph": "7.5-8.0",
                "cultures": ["Tomates", "Aubergines", "Courgettes", "Basilic", "Romarin"]
            },
            "Normandie": {
                "climat": "Océanique",
                "sol": "Argileux, humide",
                "ph": "6.0-6.5",
                "cultures": ["Choux", "Poireaux", "Navets", "Pommes de terre", "Carottes"]
            },
            "Bretagne": {
                "climat": "Océanique humide",
                "sol": "Acide, riche en matière organique",
                "ph": "5.5-6.0",
                "cultures": ["Artichauts", "Choux-fleurs", "Radis", "Épinards", "Oignons"]
            },
            "Alsace": {
                "climat": "Continental",
                "sol": "Limoneux, fertile",
                "ph": "6.5-7.0",
                "cultures": ["Choucroute", "Betteraves", "Houblon", "Vignes", "Blé"]
            },
            "Languedoc": {
                "climat": "Méditerranéen sec",
                "sol": "Schisteux, pauvre",
                "ph": "7.0-7.5",
                "cultures": ["Vignes", "Oliviers", "Lavande", "Thym", "Melons"]
            }
        }
        
    def draw(self):
        # Fond similaire au menu
        for y in range(self.height):
            alpha = y / self.height
            color = tuple(int(WHITE[i] * (1 - alpha) + GRAY_LIGHT[i] * alpha) for i in range(3))
            pygame.draw.line(self.screen, color, (0, y), (self.width, y))
        
        # Titre
        title_text = self.title_font.render("CONFIGURATION DU POTAGER", True, GREEN_PRIMARY)
        title_rect = title_text.get_rect(centerx=self.width//2, y=50)
        self.screen.blit(title_text, title_rect)
        
        # Section nombre de parcelles
        plots_title = self.subtitle_font.render("Nombre de parcelles", True, GREEN_DARK)
        plots_rect = plots_title.get_rect(centerx=self.width//2, y=140)
        self.screen.blit(plots_title, plots_rect)
        
        # Affichage du nombre de parcelles avec boutons
        self.plots_minus_btn.draw(self.screen)
        plots_text = self.title_font.render(str(self.selected_plots), True, GREEN_PRIMARY)
        plots_text_rect = plots_text.get_rect(centerx=self.width//2, centery=220)
        self.screen.blit(plots_text, plots_text_rect)
        self.plots_plus_btn.draw(self.screen)
        
        # Section localisation
        location_title = self.subtitle_font.render("Localisation", True, GREEN_DARK)
        location_rect = location_title.get_rect(centerx=self.width//2, y=250)
        self.screen.blit(location_title, location_rect)
        
        # Affichage de la localisation avec boutons
        self.location_prev_btn.draw(self.screen)
        location_text = self.subtitle_font.render(self.selected_location, True, GREEN_PRIMARY)
        location_text_rect = location_text.get_rect(centerx=self.width//2, centery=300)
        self.screen.blit(location_text, location_text_rect)
        self.location_next_btn.draw(self.screen)
        
        # Informations sur la région sélectionnée
        region_info = self.region_data[self.selected_location]
        
        # Panel des caractéristiques du sol
        soil_panel = pygame.Rect(50, 350, 450, 180)
        pygame.draw.rect(self.screen, WHITE, soil_panel, border_radius=15)
        pygame.draw.rect(self.screen, GREEN_PRIMARY, soil_panel, width=3, border_radius=15)
        
        soil_title = self.subtitle_font.render("🌍 Caractéristiques du Sol", True, GREEN_DARK)
        self.screen.blit(soil_title, (70, 365))
        
        climat_text = self.text_font.render(f"Climat: {region_info['climat']}", True, BLACK)
        self.screen.blit(climat_text, (70, 400))
        
        sol_text = self.text_font.render(f"Type de sol: {region_info['sol']}", True, BLACK)
        self.screen.blit(sol_text, (70, 425))
        
        ph_text = self.text_font.render(f"pH optimal: {region_info['ph']}", True, BLACK)
        self.screen.blit(ph_text, (70, 450))
        
        # Panel des cultures disponibles
        crops_panel = pygame.Rect(520, 350, 430, 180)
        pygame.draw.rect(self.screen, WHITE, crops_panel, border_radius=15)
        pygame.draw.rect(self.screen, GREEN_PRIMARY, crops_panel, width=3, border_radius=15)
        
        crops_title = self.subtitle_font.render("🌱 Cultures Disponibles", True, GREEN_DARK)
        self.screen.blit(crops_title, (540, 365))
        
        # Affichage des cultures en colonnes
        for i, culture in enumerate(region_info['cultures']):
            x = 540 + (i % 2) * 180
            y = 400 + (i // 2) * 25
            culture_text = self.text_font.render(f"• {culture}", True, BLACK)
            self.screen.blit(culture_text, (x, y))
        
        # Boutons
        self.back_to_menu_btn.draw(self.screen)
        self.confirm_config_btn.draw(self.screen)
        
        # Aperçu des parcelles (grille visuelle)
        self._draw_plot_preview()
        
    def _draw_plot_preview(self):
        grid_start_x = 125
        grid_start_y = 120
        plot_size = 25
        plot_spacing = 5
        
        plots_per_row = 3
        
        preview_title = self.text_font.render("Aperçu:", True, GREEN_DARK)
        self.screen.blit(preview_title, (grid_start_x + 150, grid_start_y - 25))
        
        for i in range(self.selected_plots):
            row = i // plots_per_row
            col = i % plots_per_row
            x = grid_start_x + 200 + col * (plot_size + plot_spacing)
            y = grid_start_y + row * (plot_size + plot_spacing)
            
            plot_rect = pygame.Rect(x, y, plot_size, plot_size)
            pygame.draw.rect(self.screen, GREEN_LIGHT, plot_rect, border_radius=3)
            pygame.draw.rect(self.screen, GREEN_DARK, plot_rect, width=2, border_radius=3)
        
    def handle_event(self, event):
        if self.plots_minus_btn.handle_event(event):
            if self.selected_plots > 3:
                self.selected_plots -= 1
        elif self.plots_plus_btn.handle_event(event):
            if self.selected_plots < 12:
                self.selected_plots += 1
        elif self.location_prev_btn.handle_event(event):
            self.location_index = (self.location_index - 1) % len(self.locations)
            self.selected_location = self.locations[self.location_index]
        elif self.location_next_btn.handle_event(event):
            self.location_index = (self.location_index + 1) % len(self.locations)
            self.selected_location = self.locations[self.location_index]
        elif self.confirm_config_btn.handle_event(event):
            return "confirm"
        elif self.back_to_menu_btn.handle_event(event):
            return "back"
        return None
        
    def get_config(self):
        """Retourne la configuration actuelle"""
        return {
            "plots": self.selected_plots,
            "location": self.selected_location,
            "region_data": self.region_data[self.selected_location]
        }