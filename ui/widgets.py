import pygame
import os
from .constants import GRAY_DARK

def get_font(size):
    """
    Charge la meilleure police disponible pour le rendu du texte et des symboles.
    Tente dans cet ordre :
    1. Segoe UI Emoji (pour les emojis sur Windows)
    2. DejaVuSans.ttf (fournie avec le jeu, pour la portabilité)
    3. Police par défaut de Pygame (solution de repli)
    """
    # 1. Essayer de charger la police système "Segoe UI Emoji" (idéal sur Windows)
    try:
        return pygame.font.SysFont("Segoe UI Emoji", size)
    except pygame.error:
        # Police non trouvée, on passe à la suite
        pass

    # 2. Essayer de charger la police "DejaVu Sans" fournie avec le jeu
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    font_path = os.path.join(project_root, "assets", "fonts", "DejaVuSans.ttf")
    try:
        return pygame.font.Font(font_path, size)
    except pygame.error:
        # Police non trouvée, on passe à la solution de repli
        print(f"AVERTISSEMENT: Police 'DejaVuSans.ttf' non trouvée dans 'assets/fonts/'. Utilisation de la police par défaut.")
        pass
    
    # 3. Utiliser la police par défaut de Pygame en dernier recours
    return pygame.font.Font(None, size)

_emoji_cache = {}
_emoji_folder = None

def _initialize_emoji_handler():
    """Définit le chemin global vers le dossier des images d'emojis."""
    global _emoji_folder
    if _emoji_folder is None:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        _emoji_folder = os.path.join(project_root, "assets", "emojis")
        if not os.path.isdir(_emoji_folder):
            print(f"AVERTISSEMENT: Dossier d'emojis non trouvé à '{_emoji_folder}'. Les emojis en couleur ne s'afficheront pas.")
            _emoji_folder = None

def get_emoji_image(char, size):
    """Charge, redimensionne et met en cache une image d'emoji."""
    _initialize_emoji_handler()
    if not _emoji_folder: return None
    
    if (char, size) in _emoji_cache:
        return _emoji_cache[(char, size)]

    codepoint = hex(ord(char))[2:]
    filepath = os.path.join(_emoji_folder, f"{codepoint}.png")

    try:
        image = pygame.image.load(filepath).convert_alpha()
        image = pygame.transform.smoothscale(image, (size, size))
        _emoji_cache[(char, size)] = image
        return image
    except pygame.error:
        _emoji_cache[(char, size)] = None # Mettre en cache l'échec pour ne pas réessayer
        return None

def render_text_with_emojis(text, font, color):
    """Crée une surface unique contenant du texte et des emojis (en couleur si possible)."""
    parts = []
    current_str = ""
    for char in text:
        # Heuristique pour détecter les caractères qui sont probablement des emojis/symboles à remplacer par une image.
        codepoint = ord(char)
        is_emoji_char = (
            0x1F300 <= codepoint <= 0x1F6FF or  # Emojis principaux, smileys, transport
            0x2600 <= codepoint <= 0x27BF or   # Symboles divers, dingbats (inclut ☀️, ❄️, ✅)
            codepoint == 0x23F8 or             # Pause ⏸️
            codepoint == 0x25B6               # Play ▶️
        )

        if is_emoji_char:
            if current_str: parts.append(font.render(current_str, True, color))
            current_str = ""
            emoji_size = int(font.get_height() * 1.1)
            img = get_emoji_image(char, emoji_size)
            parts.append(img if img else font.render(char, True, color)) # Fallback to monochrome
        else:
            current_str += char
    if current_str: parts.append(font.render(current_str, True, color))

    if not parts: return pygame.Surface((0, 0), pygame.SRCALPHA)

    total_width = sum(p.get_width() for p in parts)
    max_height = max(p.get_height() for p in parts)

    final_surface = pygame.Surface((total_width, max_height), pygame.SRCALPHA)
    current_x = 0
    for part in parts:
        y_pos = (max_height - part.get_height()) // 2
        final_surface.blit(part, (current_x, y_pos))
        current_x += part.get_width()
    return final_surface

class Button:
    """
    Une classe de bouton réutilisable pour l'interface Pygame.
    Centraliser ce composant évite la duplication de code.
    """
    def __init__(self, x, y, width, height, text, color, text_color=(255, 255, 255), font_size=24):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.text_color = text_color
        self.font = get_font(font_size)
        self.hovered = False

    def draw(self, screen):
        # Ombre portée pour un effet de profondeur, toujours visible
        shadow_rect = self.rect.move(3, 3)
        pygame.draw.rect(screen, GRAY_DARK, shadow_rect, border_radius=10)

        # Couleur du bouton (plus claire au survol pour un meilleur feedback)
        button_color = self.color
        if self.hovered:
            button_color = tuple(min(255, c + 30) for c in self.color)
        pygame.draw.rect(screen, button_color, self.rect, border_radius=10)

        text_surface = render_text_with_emojis(self.text, self.font, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and self.hovered:
            return True
        return False

