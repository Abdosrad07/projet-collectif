import pygame
import sys

# Importer les classes d'interface depuis le dossier ui
from ui.menu import MenuInterface
from ui.config import ConfigInterface
from ui.game import GameInterface
from ui.results import ResultsInterface
# Importer FarmLogic pour le chargement de partie
from core.farm_logic import FarmLogic

def main():
    """
    Fonction principale du jeu.
    Initialise Pygame, gère la boucle de jeu et les transitions entre les écrans.
    """
    # 1. Initialisation de Pygame et de la fenêtre
    pygame.init()
    screen_width = 1280
    screen_height = 750
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Farm Navigator")

    # 2. Instanciation des gestionnaires d'interface pour chaque écran
    menu_interface = MenuInterface(screen)
    config_interface = ConfigInterface(screen)
    game_interface = GameInterface(screen)
    results_interface = ResultsInterface(screen)

    # 3. État du jeu
    current_screen = "menu"
    running = True
    clock = pygame.time.Clock()

    # 4. Variables pour la transition en fondu
    transition_state = None  # Peut être 'out' (fondu au noir) ou 'in' (fondu depuis le noir)
    transition_target = None # L'écran de destination après le fondu
    transition_alpha = 0
    FADE_SPEED = 15 # Vitesse du fondu (plus élevé = plus rapide)
    transition_surface = pygame.Surface((screen_width, screen_height))
    transition_surface.fill((0, 0, 0))

    # 5. Boucle principale du jeu
    while running:
        # Récupérer tous les événements (clavier, souris)
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False

        # --- Gestion des états et des transitions ---
        # Si on n'est pas en transition, on gère la logique de l'écran actuel
        if not transition_state:
            if current_screen == "menu":
                for event in events:
                    action = menu_interface.handle_event(event)
                    if action:
                        if action == "quit":
                            running = False
                        else:
                            transition_target = action # "new_game" ou "continue"
                            transition_state = 'out'
            
            elif current_screen == "config":
                action_to_take = None
                # Ne gérer les événements que si l'écran de config n'est pas déjà en chargement
                if not config_interface.loading:
                    for event in events:
                        action = config_interface.handle_event(event)
                        if action:
                            action_to_take = action
                            break
                
                if action_to_take == "prepare_game":
                    # Cas spécial : on affiche le chargement, on fait le travail, PUIS on lance la transition
                    config_interface.draw()
                    pygame.display.flip()

                    config_interface.prepare_game_config()
                    game_config = config_interface.get_config()

                    if game_config and "error" not in game_config:
                        game_interface.setup_from_config(game_config)
                        transition_target = "game"
                        transition_state = 'out'
                    # En cas d'erreur, on reste sur l'écran de config, sans transition
                
                elif action_to_take == "back":
                    transition_target = "menu"
                    transition_state = 'out'

            elif current_screen == "game":
                # La fin de partie est gérée par draw(), qui renvoie "game_over"
                game_action = game_interface.draw()
                if game_action == "game_over":
                    results = game_interface.get_results()
                    results_interface.setup_from_game(results)
                    transition_target = "results"
                    transition_state = 'out'
                else:
                    for event in events:
                        action = game_interface.handle_event(event)
                        if action == "menu":
                            transition_target = "menu"
                            transition_state = 'out'

            elif current_screen == "results":
                for event in events:
                    action = results_interface.handle_event(event)
                    if action: # "replay" ou "menu"
                        transition_target = "config" if action == "replay" else "menu"
                        transition_state = 'out'

        # --- Dessin des écrans ---
        # On dessine toujours l'écran actuel, même pendant la transition
        if current_screen == "menu":
            menu_interface.draw()
        elif current_screen == "config":
            config_interface.draw()
        elif current_screen == "game":
            # draw() est déjà appelé plus haut pour la logique de fin de partie
            pass
        elif current_screen == "results":
            results_interface.draw()

        # --- Gestion de l'animation de transition ---
        if transition_state == 'out':
            transition_alpha += FADE_SPEED
            if transition_alpha >= 255:
                transition_alpha = 255
                transition_state = 'in' # On passe en mode fondu d'entrée

                # --- C'est ici, au milieu de la transition, qu'on change l'état du jeu ---
                if transition_target == "new_game":
                    current_screen = "config"
                elif transition_target == "continue":
                    if game_interface.logic.load_game():
                        game_interface.generate_crop_cards_from_logic()
                        current_screen = "game"
                    else: # Si le chargement échoue, on retourne au menu
                        current_screen = "menu"
                else:
                    current_screen = transition_target

        elif transition_state == 'in':
            transition_alpha -= FADE_SPEED
            if transition_alpha <= 0:
                transition_alpha = 0
                transition_state = None # Fin de la transition
                transition_target = None

        # Dessiner la surface de fondu si nécessaire
        if transition_alpha > 0:
            transition_surface.set_alpha(transition_alpha)
            screen.blit(transition_surface, (0, 0))

        # 6. Mise à jour de l'affichage global
        pygame.display.flip()

        # 7. Limiter la vitesse de la boucle
        clock.tick(60)

    # 8. Quitter Pygame
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()

