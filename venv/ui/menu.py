import pygame
import math

# Couleurs
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN_PRIMARY = (34, 197, 94)
GREEN_DARK = (21, 128, 61)
GRAY_LIGHT = (243, 244, 246)
ORANGE = (251, 146, 60)

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

class MenuInterface:
    def __init__(self, screen):
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()

        # Polices
        self.title_font = pygame.font.Font(None, 72)
        self.subtitle_font = pygame.font.Font(None, 28)
        self.text_font = pygame.font.Font(None, 24)

        # Boutons du menu principal
        self.new_game_btn = Button(self.width//2 - 175, 300, 350, 50, "Nouvelle partie", GREEN_PRIMARY)
        self.continue_btn = Button(self.width//2 - 175, 370, 350, 50, "Continuer", GRAY_LIGHT, BLACK)
        self.quit_btn = Button(self.width//2 - 75, 440, 150, 40, "Quitter", WHITE, ORANGE, 20)

    def draw(self):
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
            title_text = self.title_font.render("FARM NAVIGATOR", True, GREEN_PRIMARY)
            title_rect = title_text.get_rect(centerx=self.width//2, y=170)
            self.screen.blit(title_text, title_rect)

            # Sous-titre
            subtitle_text = self.subtitle_font.render("CULTIVEZ VÔTRE RÊVE", True, GREEN_DARK)
            subtitle_rect = subtitle_text.get_rect(centerx=self.width//2, y=220)
            self.screen.blit(subtitle_text, subtitle_rect)

            # Boutons
            self.new_game_btn.draw(self.screen)
            self.continue_btn.draw(self.screen)
            self.quit_btn.draw(self.screen)

            # Version 
            version_text = self.text_font.render("Version  1.0.0", True, GREEN_PRIMARY)
            version_rect = version_text.get_rect(centerx=self.width//2, y=self.height - 40)
            self.screen.blit(version_text, version_rect)
    
    def handle_event(self, event):
        if self.new_game_btn.handle_event(event):
            return "new_game"
        elif self.continue_btn.handle_event(event):
            return "continue"
        elif self.quit_btn.handle_event(event):
            return "quit"
        return None

        