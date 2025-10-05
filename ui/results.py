import pygame
import re
import os
import csv

# Importer les constantes et widgets partagés
from .constants import WHITE, BLACK, GREEN_PRIMARY, GREEN_DARK, GRAY_LIGHT, GRAY_DARK, GREEN_LIGHT, ORANGE, BROWN, BLUE, RED
from .widgets import Button, get_font, render_text_with_emojis

class ResultsInterface:
    def __init__(self, screen):
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        # Polices
        self.title_font = get_font(64)  # Légèrement plus petite
        self.subtitle_font = get_font(26)  # Légèrement plus petite
        self.text_font = get_font(22)   # Légèrement plus petite
        
        # Données des résultats
        self.daily_yields = []
        self.daily_soil_quality = []
        self.sustainability_score = 0
        self.final_money = 0
        self.final_water = 0
        self.actions_taken = []
        self.plots_data = []
        self.food_target = 0
        
        # Boutons
        self.replay_btn = Button(self.width//2 - 320, self.height - 90, 180, 50, "🔄 Rejouer", GREEN_PRIMARY)
        self.export_btn = Button(self.width//2 - 90, self.height - 90, 180, 50, "Exporter", BLUE)
        self.quit_final_btn = Button(self.width//2 + 140, self.height - 90, 180, 50, "🚪 Quitter", GRAY_DARK)

        # État pour le popup de saisie du nom
        self.show_name_input = False
        self.player_name = ""
        self.input_box_active = False
        self.input_popup_rect = pygame.Rect(self.width // 2 - 200, self.height // 2 - 100, 400, 200)
        self.input_box_rect = pygame.Rect(self.input_popup_rect.x + 50, self.input_popup_rect.y + 80, 300, 40)
        self.confirm_export_btn = Button(self.input_popup_rect.centerx - 75, self.input_popup_rect.bottom - 60, 150, 40, "Confirmer", GREEN_PRIMARY)
        self.close_export_btn = Button(self.input_popup_rect.right - 45, self.input_popup_rect.top + 10, 35, 30, "✕", RED)
        self.export_status_message = ""
        
    def setup_from_game(self, results):
        """Configure l'interface avec les résultats du jeu"""
        self.daily_yields = results["daily_yields"]
        self.daily_soil_quality = results.get("daily_soil_quality", [])
        self.sustainability_score = results["sustainability_score"]
        self.food_harvested = results["food_harvested"]
        self.food_target = results.get("food_target", 0)
        self.final_money = results["final_money"]
        self.final_water = results["final_water"]
        self.actions_taken = results["actions_taken"]
        self.plots_data = results.get("plots_data", [])
        
    def draw(self):
        # Fond dégradé
        for y in range(self.height):
            alpha = y / self.height
            color = tuple(int(WHITE[i] * (1 - alpha) + GRAY_LIGHT[i] * alpha) for i in range(3))
            pygame.draw.line(self.screen, color, (0, y), (self.width, y))
        
        # Titre
        title_text = render_text_with_emojis("RÉSULTATS DE LA SIMULATION", self.title_font, GREEN_PRIMARY)
        title_rect = title_text.get_rect(centerx=self.width//2, y=30)
        self.screen.blit(title_text, title_rect)
        
        # Graphique de rendement
        self._draw_yield_graph()
        
        # Graphique de la qualité du sol
        self._draw_soil_graph()
        
        # Statistiques finales
        self._draw_statistics()
        
        # Bilan détaillé des parcelles
        self._draw_plots_summary()
        
        # Boutons
        self.replay_btn.draw(self.screen)
        self.export_btn.draw(self.screen)
        self.quit_final_btn.draw(self.screen)

        # Dessiner le popup de saisie du nom si actif
        if self.show_name_input:
            self._draw_name_input_popup()
        
    def _draw_yield_graph(self):
        """Dessine le graphique de rendement avec plus de détails."""
        # Le graphique occupe 40% de la largeur
        panel_width = self.width * 0.45
        graph_panel = pygame.Rect(self.width * 0.05, 120, panel_width, 250)
        pygame.draw.rect(self.screen, WHITE, graph_panel, border_radius=10)
        pygame.draw.rect(self.screen, GREEN_PRIMARY, graph_panel, width=3, border_radius=10)
        
        graph_title = render_text_with_emojis("📈 Rendement par Jour", self.subtitle_font, GREEN_DARK)
        title_rect = graph_title.get_rect(midtop=(graph_panel.centerx, graph_panel.top + 10))
        self.screen.blit(graph_title, title_rect)

        subtitle_text = render_text_with_emojis("Unités de récolte produites quotidiennement.", self.text_font, GRAY_DARK)
        subtitle_rect = subtitle_text.get_rect(midtop=(graph_panel.centerx, title_rect.bottom))
        self.screen.blit(subtitle_text, subtitle_rect)
        
        # Zone de dessin du graphique
        chart_rect = pygame.Rect(graph_panel.x + 40, graph_panel.y + 70, 
                                 graph_panel.width - 60, graph_panel.height - 90)
        
        # Fond de la zone de graphique
        pygame.draw.rect(self.screen, GRAY_LIGHT, chart_rect)
        
        if self.daily_yields:
            max_yield = max(self.daily_yields) if any(self.daily_yields) else 1
            
            # Dessiner les axes
            pygame.draw.line(self.screen, GRAY_DARK, (chart_rect.left, chart_rect.top), (chart_rect.left, chart_rect.bottom), 2)
            pygame.draw.line(self.screen, GRAY_DARK, (chart_rect.left, chart_rect.bottom), (chart_rect.right, chart_rect.bottom), 2)

            # Étiquettes axe Y
            max_yield_text = render_text_with_emojis(f"{max_yield:.0f}", self.text_font, BLACK)
            self.screen.blit(max_yield_text, (chart_rect.left - 35, chart_rect.top - 10))
            zero_text = render_text_with_emojis("0", self.text_font, BLACK)
            self.screen.blit(zero_text, (chart_rect.left - 15, chart_rect.bottom - 10))

            # Dessiner les barres
            num_days = len(self.daily_yields)
            bar_width = (chart_rect.width / num_days) * 0.8
            bar_spacing = (chart_rect.width / num_days) * 0.2
            
            for i, yield_val in enumerate(self.daily_yields):
                bar_height = int((yield_val / max_yield) * chart_rect.height) if max_yield > 0 else 0
                bar_x = chart_rect.x + i * (bar_width + bar_spacing)
                bar_y = chart_rect.bottom - bar_height
                
                bar_color = GREEN_PRIMARY if yield_val > 0 else GRAY_DARK
                pygame.draw.rect(self.screen, bar_color, (bar_x, bar_y, bar_width, bar_height))

                # Étiquette jour (seulement pour quelques jours pour éviter le surpeuplement)
                if num_days <= 15 or i % 5 == 0 or i == num_days - 1:
                    day_text = render_text_with_emojis(f"J{i+1}", self.text_font, BLACK)
                    day_rect = day_text.get_rect(centerx=bar_x + bar_width//2, y=chart_rect.bottom + 5)
                    self.screen.blit(day_text, day_rect)
                
    def _draw_soil_graph(self):
        """Dessine le graphique de l'évolution de la qualité du sol avec plus de détails."""
        panel_width = self.width * 0.22
        graph_panel = pygame.Rect(self.width * 0.52, 120, panel_width, 250)
        pygame.draw.rect(self.screen, WHITE, graph_panel, border_radius=10)
        pygame.draw.rect(self.screen, GREEN_PRIMARY, graph_panel, width=3, border_radius=10)

        graph_title = render_text_with_emojis("📉 Qualité du Sol", self.subtitle_font, GREEN_DARK)
        title_rect = graph_title.get_rect(midtop=(graph_panel.centerx, graph_panel.top + 10))
        self.screen.blit(graph_title, title_rect)

        subtitle_text = render_text_with_emojis("Impact de la fertilisation.", self.text_font, GRAY_DARK)
        subtitle_rect = subtitle_text.get_rect(midtop=(graph_panel.centerx, title_rect.bottom))
        self.screen.blit(subtitle_text, subtitle_rect)

        chart_rect = pygame.Rect(graph_panel.x + 40, graph_panel.y + 70, 
                                 graph_panel.width - 60, graph_panel.height - 100)

        # Fond de la zone de graphique
        pygame.draw.rect(self.screen, GRAY_LIGHT, chart_rect)

        if self.daily_soil_quality:
            points = []
            num_days = len(self.daily_soil_quality)
            for i, quality in enumerate(self.daily_soil_quality):
                x = chart_rect.x + (i / (num_days - 1 if num_days > 1 else 1)) * chart_rect.width
                y = chart_rect.bottom - (quality * chart_rect.height) # quality est 0-1
                points.append((x, y))
            
            # Dessiner les axes
            pygame.draw.line(self.screen, GRAY_DARK, (chart_rect.left, chart_rect.top), (chart_rect.left, chart_rect.bottom), 2)
            pygame.draw.line(self.screen, GRAY_DARK, (chart_rect.left, chart_rect.bottom), (chart_rect.right, chart_rect.bottom), 2)

            # Étiquettes des axes
            label_100 = render_text_with_emojis("100%", self.text_font, BLACK)
            self.screen.blit(label_100, (chart_rect.left - 38, chart_rect.top - 10))
            label_0 = render_text_with_emojis("0%", self.text_font, BLACK)
            self.screen.blit(label_0, (chart_rect.left - 25, chart_rect.bottom - 10))

            # Étiquettes axe X
            if num_days > 1:
                day1_text = render_text_with_emojis("J1", self.text_font, BLACK)
                self.screen.blit(day1_text, (chart_rect.left, chart_rect.bottom + 5))
                day_last_text = render_text_with_emojis(f"J{num_days}", self.text_font, BLACK)
                day_last_rect = day_last_text.get_rect(right=chart_rect.right, top=chart_rect.bottom + 5)
                self.screen.blit(day_last_text, day_last_rect)

            # Dessiner la ligne du graphique
            if len(points) > 1:
                pygame.draw.lines(self.screen, BROWN, False, points, 3) # Ligne marron pour le sol
            
            # Dessiner les points sur la ligne
            for point in points:
                pygame.draw.circle(self.screen, BROWN, point, 4)
        
    def _draw_statistics(self):
        """Dessine les statistiques finales"""
        # Les stats occupent 28% de la largeur
        panel_width = self.width * 0.23
        stats_panel = pygame.Rect(self.width * 0.76, 120, panel_width, 250)

        pygame.draw.rect(self.screen, WHITE, stats_panel, border_radius=10)
        pygame.draw.rect(self.screen, GREEN_PRIMARY, stats_panel, width=3, border_radius=10)
        
        stats_title = render_text_with_emojis("📊 Statistiques", self.subtitle_font, GREEN_DARK)
        title_rect = stats_title.get_rect(midtop=(stats_panel.centerx, stats_panel.top + 10))
        self.screen.blit(stats_title, title_rect)
        harvested_count = self.actions_taken.count("harvest")
        
        stats_text = [
            f"Nourriture: {self.food_harvested:.0f} / {self.food_target:.0f} kg",
            f"Cultures récoltées: {harvested_count}",
            f"Argent final: {self.final_money:.0f}€",
            f"Eau restante: {self.final_water:.0f}L"
        ]
       

        for i, stat in enumerate(stats_text):
            color = BLACK
            if i == 0: # Stat de nourriture
                color = GREEN_PRIMARY if self.food_harvested >= self.food_target else ORANGE
            stat_surface = render_text_with_emojis(stat, self.text_font, color)
            self.screen.blit(stat_surface, (stats_panel.x + 15, stats_panel.y + 50 + i * 30))
        
        # Ajouter le score de durabilité ici
        sustain_title = render_text_with_emojis("Durabilité:", self.text_font, BLACK)
        self.screen.blit(sustain_title, (stats_panel.x + 15, stats_panel.y + 50 + 4 * 28))

        if self.sustainability_score > 70: arc_color = GREEN_PRIMARY
        elif self.sustainability_score > 40: arc_color = (255, 165, 0)
        else: arc_color = (220, 38, 38)
        
        score_text = render_text_with_emojis(f"{self.sustainability_score}%", self.subtitle_font, arc_color)
        score_rect = score_text.get_rect(left=stats_panel.x + 105, centery=stats_panel.y + 50 + 4 * 28 + 10)
        self.screen.blit(score_text, score_rect)
            
    def _draw_plots_summary(self):
        """Dessine le résumé final de chaque parcelle."""
        panel_width = self.width * 0.9
        panel_height = 280 # Panneau plus grand pour les détails
        panel_x = (self.width - panel_width) / 2
        summary_panel = pygame.Rect(panel_x, 390, panel_width, panel_height)
        pygame.draw.rect(self.screen, WHITE, summary_panel, border_radius=10)
        pygame.draw.rect(self.screen, GREEN_PRIMARY, summary_panel, width=3, border_radius=10)
        
        title = render_text_with_emojis("Bilan des Parcelles", self.subtitle_font, GREEN_DARK)
        self.screen.blit(title, (summary_panel.x + 15, summary_panel.y + 15))

        if not self.plots_data:
            return

        # Layout pour les mini-cartes de résumé
        cards_per_row = 6
        card_width = (summary_panel.width - (cards_per_row + 1) * 15) / cards_per_row
        card_height = summary_panel.height - 70
        start_x = summary_panel.x + 15
        start_y = summary_panel.y + 50

        for i, plot in enumerate(self.plots_data):
            if i >= cards_per_row * 2: break # Limiter à 12 parcelles pour l'affichage

            row = i // cards_per_row
            col = i % cards_per_row
            x = start_x + col * (card_width + 10)
            y = start_y + row * (card_height + 10)

            card_rect = pygame.Rect(x, y, card_width, card_height)
            
            # Couleur de fond basée sur la qualité du sol
            soil_quality = plot['soil_quality']
            if soil_quality > 0.7: card_color = GREEN_LIGHT
            elif soil_quality > 0.4: card_color = (253, 230, 138) # Jaune
            else: card_color = (252, 165, 165) # Rouge
            
            pygame.draw.rect(self.screen, card_color, card_rect, border_radius=8)
            pygame.draw.rect(self.screen, GRAY_DARK, card_rect, width=1, border_radius=8)

            # Contenu de la mini-carte
            plot_title = render_text_with_emojis(f"Parcelle {i+1}", self.text_font, BLACK)
            self.screen.blit(plot_title, (card_rect.x + 10, card_rect.y + 10))

            soil_text = render_text_with_emojis(f"Sol: {int(soil_quality * 100)}%", self.text_font, BLACK)
            self.screen.blit(soil_text, (card_rect.x + 10, card_rect.y + 35))

            crop_text_str = plot['crop'] if plot['crop'] else "Vide"
            crop_text = render_text_with_emojis(f"Culture: {crop_text_str}", self.text_font, BLACK)
            self.screen.blit(crop_text, (card_rect.x + 10, card_rect.y + 60))

    def _draw_name_input_popup(self):
        """Dessine le popup pour demander le nom du joueur."""
        # Fond semi-transparent
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        # Boîte du popup
        pygame.draw.rect(self.screen, WHITE, self.input_popup_rect, border_radius=15)
        pygame.draw.rect(self.screen, GREEN_PRIMARY, self.input_popup_rect, width=3, border_radius=15)

        # Titre
        title_text = render_text_with_emojis("Entrez votre nom", self.subtitle_font, GREEN_DARK)
        title_rect = title_text.get_rect(centerx=self.input_popup_rect.centerx, y=self.input_popup_rect.y + 20)
        self.screen.blit(title_text, title_rect)

        # Zone de saisie
        input_box_color = GREEN_LIGHT if self.input_box_active else GRAY_LIGHT
        pygame.draw.rect(self.screen, input_box_color, self.input_box_rect, border_radius=5)
        pygame.draw.rect(self.screen, GRAY_DARK, self.input_box_rect, width=2, border_radius=5)

        # Texte du nom du joueur
        name_surface = render_text_with_emojis(self.player_name, self.text_font, BLACK)
        name_rect = name_surface.get_rect(midleft=(self.input_box_rect.x + 10, self.input_box_rect.centery))
        self.screen.blit(name_surface, name_rect)

        # Message de statut (ex: "Exporté !")
        if self.export_status_message:
            status_surface = render_text_with_emojis(self.export_status_message, self.text_font, GREEN_PRIMARY)
            status_rect = status_surface.get_rect(centerx=self.input_popup_rect.centerx, bottom=self.input_popup_rect.bottom - 70)
            self.screen.blit(status_surface, status_rect)

        # Boutons
        self.confirm_export_btn.draw(self.screen)
        self.close_export_btn.draw(self.screen)

    def _export_results_to_csv(self):
        """Exporte les résultats de la simulation dans un fichier CSV."""
        if not self.player_name.strip():
            self.export_status_message = "Le nom ne peut pas être vide."
            return

        # Nettoyer le nom pour l'utiliser comme nom de fichier
        sanitized_name = re.sub(r'[\\/*?:"<>|]', "", self.player_name)
        filename = f"{sanitized_name}_results.csv"
        
        # Créer le dossier 'rapports' s'il n'existe pas
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        exports_dir = os.path.join(project_root, "rapports")
        os.makedirs(exports_dir, exist_ok=True)
        
        filepath = os.path.join(exports_dir, filename)

        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                # Section 1: Informations générales
                writer.writerow(['Argent Final (€)', f"{self.final_money:.2f}"])
                writer.writerow(['Réserve d\'Eau Finale (L)', f"{self.final_water:.2f}"])
                writer.writerow(['Score de Durabilité Final (%)', f"{self.sustainability_score:.2f}"])
                writer.writerow(['Nombre de Récoltes', self.actions_taken.count("harvest")])
                
                # Section 2: Journal Quotidien
                writer.writerow([])  # Ligne vide
                if self.daily_yields:  # Check if daily_yields is not empty
                    writer.writerow(['Journal Quotidien'])
                    writer.writerow(['Jour', 'Rendement du jour (kg)', 'Qualité moyenne du sol (%)'])
                    
                    num_days = len(self.daily_yields)
                    for i in range(num_days):
                        day = i + 1
                        yield_val = self.daily_yields[i]
                        
                        # Vérification de la qualité du sol
                        if i < len(self.daily_soil_quality):
                            soil_val = self.daily_soil_quality[i] * 100
                        else:
                            soil_val = 'N/A'  # Si la qualité du sol est manquante
                        
                        # Validation des données
                        try:
                            yield_val_formatted = f"{yield_val:.2f}" if isinstance(yield_val, (int, float)) else "N/A"
                        except Exception as e:
                            print(f"Erreur de formatage pour le rendement du jour {day}: {e}")
                            yield_val_formatted = "N/A"
                        
                        try:
                            soil_val_formatted = f"{soil_val:.2f}" if isinstance(soil_val, (int, float)) else "N/A"
                        except Exception as e:
                            print(f"Erreur de formatage pour la qualité du sol du jour {day}: {e}")
                            soil_val_formatted = "N/A"
                        
                        # Écriture dans le fichier CSV
                        writer.writerow([day, yield_val_formatted, soil_val_formatted])
                        print(f"Exporté - Jour {day}: Rendement = {yield_val_formatted}, Qualité du sol = {soil_val_formatted}")
                    
                    # Message de succès
                    self.export_status_message = f"Exporté vers {filename} !"
                    print(self.export_status_message)
                else:
                    self.export_status_message = "Erreur : Aucune donnée de rendement à exporter."
                    print(self.export_status_message)

        except FileNotFoundError:
            self.export_status_message = "Erreur : Le fichier ou le répertoire spécifié est introuvable."
            print(self.export_status_message)

        except PermissionError:
            self.export_status_message = "Erreur : Permission refusée pour écrire dans le fichier."
            print(self.export_status_message)

        except Exception as e:
            self.export_status_message = "Erreur lors de l'export."
            print(f"Erreur d'exportation CSV : {e}")

    def handle_event(self, event):
        if self.show_name_input:
            if self.confirm_export_btn.handle_event(event):
                self._export_results_to_csv()
            elif self.close_export_btn.handle_event(event):
                self.show_name_input = False
                self.player_name = ""
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
                self.export_status_message = "" # Effacer le message de statut lors de la saisie
            return None # Consommer l'événement pour éviter d'autres actions

        if self.replay_btn.handle_event(event):
            return "replay"
        elif self.export_btn.handle_event(event):
            self.show_name_input = True
            return None
        elif self.quit_final_btn.handle_event(event):
            return "menu"
        return None