import pygame
import os



# Importer les constantes et widgets partagés
from .constants import WHITE, BLACK, GREEN_PRIMARY, GREEN_DARK, GRAY_LIGHT, ORANGE
from .widgets import Button, get_font, render_text_with_emojis  
       
class MenuInterface:
    def __init__(self, screen):
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()

        # Polices
        self.title_font = get_font(72)
        self.subtitle_font = get_font(28)
        self.text_font = get_font(24)

        # Boutons du menu principal
        self.new_game_btn = Button(self.width//2 - 175, 350, 350, 50, "Nouvelle partie", GREEN_PRIMARY)
        
        self.continue_btn = None # Sera créé/mis à jour avant l'affichage
        self.quit_btn = Button(self.width//2 - 75, 510, 150, 40, "Quitter", WHITE, ORANGE, 20)
    def update_continue_button(self):
        """Vérifie l'existence de la sauvegarde et met à jour le bouton 'Continuer'."""
        self.save_exists = os.path.exists("data/savegame.json")
        continue_color = GREEN_PRIMARY if self.save_exists else GRAY_LIGHT
        continue_text_color = WHITE if self.save_exists else BLACK
        self.continue_btn = Button(self.width//2 - 175, 430, 350, 50, "Continuer", continue_color, continue_text_color)
        

    def draw(self):
        self.update_continue_button()
        # Fond dégradé simple
        for y in range(self.height):
            alpha = y / self.height
            color = tuple(int(WHITE[i] * (1 - alpha) + GRAY_LIGHT[i] * alpha) for i in range(3))
            pygame.draw.line(self.screen, color, (0, y), (self.width, y))

        # Logo/Icône maison
        house_size = 80
        house_x = self.width//2
        house_y = 80 

        # Toit
        roof_points = [
            (house_x, house_y - house_size//2),
            (house_x - house_size//2, house_y),
            (house_x + house_size//2, house_y)
        ]
        pygame.draw.polygon(self.screen, GREEN_PRIMARY, roof_points)

            

        # Maison
        house_rect = pygame.Rect(house_x - house_size//3, house_y, house_size//1.5, house_size//2)
        pygame.draw.rect(self.screen, GREEN_PRIMARY, house_rect)

        # Porte
        door_rect = pygame.Rect(house_x - 8, house_y + 10, 16, 20)
        pygame.draw.rect(self.screen, WHITE, door_rect)

        # Titre
        title_text = render_text_with_emojis("FARM NAVIGATOR", self.title_font, GREEN_PRIMARY)
        title_rect = title_text.get_rect(centerx=self.width//2, y=170)
        self.screen.blit(title_text, title_rect)

        # Sous-titre
        subtitle_text = render_text_with_emojis("CULTIVEZ VÔTRE RÊVE", self.subtitle_font, GREEN_DARK)
        subtitle_rect = subtitle_text.get_rect(centerx=self.width//2, y=220)
        self.screen.blit(subtitle_text, subtitle_rect)

        # Boutons
        self.new_game_btn.draw(self.screen)
        self.continue_btn.draw(self.screen)
        self.quit_btn.draw(self.screen)

        # Version 
        version_text = render_text_with_emojis("Version  1.0.0", self.text_font, GREEN_PRIMARY)
        version_rect = version_text.get_rect(centerx=self.width//2, y=self.height - 40)
        self.screen.blit(version_text, version_rect)
    
    def handle_event(self, event):
        if self.new_game_btn.handle_event(event):
            return "new_game"
        if self.continue_btn and self.save_exists and self.continue_btn.handle_event(event):
            return "continue"
        elif self.quit_btn.handle_event(event):
            return "quit"
        return None

        