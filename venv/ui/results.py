import pygame

# Couleurs
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN_PRIMARY = (34, 197, 94)
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

class ResultsInterface:
    def __init__(self, screen):
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        # Polices
        self.title_font = pygame.font.Font(None, 72)
        self.subtitle_font = pygame.font.Font(None, 28)
        self.text_font = pygame.font.Font(None, 24)
        
        # Données des résultats
        self.daily_yields = []
        self.sustainability_score = 0
        self.final_money = 0
        self.final_water = 0
        self.actions_taken = []
        self.crop_cards = []
        
        # Boutons
        self.replay_btn = Button(self.width//2 - 220, 580, 180, 50, "🔄 Rejouer", GREEN_PRIMARY)
        self.quit_final_btn = Button(self.width//2 + 40, 580, 180, 50, "🚪 Quitter", GRAY_DARK)
        
    def setup_from_game(self, results):
        """Configure l'interface avec les résultats du jeu"""
        self.daily_yields = results["daily_yields"]
        self.sustainability_score = results["sustainability_score"]
        self.final_money = results["final_money"]
        self.final_water = results["final_water"]
        self.actions_taken = results["actions_taken"]
        self.crop_cards = results["crop_cards"]
        
    def draw(self):
        # Fond dégradé
        for y in range(self.height):
            alpha = y / self.height
            color = tuple(int(WHITE[i] * (1 - alpha) + GRAY_LIGHT[i] * alpha) for i in range(3))
            pygame.draw.line(self.screen, color, (0, y), (self.width, y))
        
        # Titre
        title_text = self.title_font.render("RÉSULTATS DE LA SIMULATION", True, GREEN_PRIMARY)
        title_rect = title_text.get_rect(centerx=self.width//2, y=30)
        self.screen.blit(title_text, title_rect)
        
        # Graphique de rendement
        self._draw_yield_graph()
        
        # Score de durabilité
        self._draw_sustainability_score()
        
        # Statistiques finales
        self._draw_statistics()
        
        # Message de l'IA (feedback personnalisé)
        self._draw_ai_feedback()
        
        # Boutons
        self.replay_btn.draw(self.screen)
        self.quit_final_btn.draw(self.screen)
        
    def _draw_yield_graph(self):
        """Dessine le graphique de rendement"""
        graph_panel = pygame.Rect(50, 100, 400, 200)
        pygame.draw.rect(self.screen, WHITE, graph_panel, border_radius=10)
        pygame.draw.rect(self.screen, GREEN_PRIMARY, graph_panel, width=3, border_radius=10)
        
        graph_title = self.subtitle_font.render("📈 Rendement par Jour", True, GREEN_DARK)
        self.screen.blit(graph_title, (60, 110))
        
        if self.daily_yields:
            # Dessiner le graphique
            max_yield = max(self.daily_yields) if self.daily_yields else 1
            graph_width = graph_panel.width - 40
            graph_height = graph_panel.height - 80
            
            for i, yield_val in enumerate(self.daily_yields):
                bar_width = graph_width // len(self.daily_yields) - 5
                bar_height = int((yield_val / max_yield) * graph_height) if max_yield > 0 else 0
                bar_x = graph_panel.x + 20 + i * (bar_width + 5)
                bar_y = graph_panel.bottom - 20 - bar_height
                
                # Barre
                bar_color = GREEN_PRIMARY if yield_val > 0 else GRAY_DARK
                pygame.draw.rect(self.screen, bar_color, 
                               (bar_x, bar_y, bar_width, bar_height))
                
                # Étiquette jour
                day_text = self.text_font.render(f"J{i+1}", True, BLACK)
                day_rect = day_text.get_rect(centerx=bar_x + bar_width//2, 
                                           y=graph_panel.bottom - 15)
                self.screen.blit(day_text, day_rect)
                
    def _draw_sustainability_score(self):
        """Dessine le score de durabilité"""
        score_panel = pygame.Rect(470, 100, 200, 200)
        pygame.draw.rect(self.screen, WHITE, score_panel, border_radius=10)
        pygame.draw.rect(self.screen, GREEN_PRIMARY, score_panel, width=3, border_radius=10)
        
        score_title = self.subtitle_font.render("🌍 Durabilité", True, GREEN_DARK)
        score_rect = score_title.get_rect(centerx=score_panel.centerx, y=score_panel.y + 10)
        self.screen.blit(score_title, score_rect)
        
        # Cercle de score
        circle_center = (score_panel.centerx, score_panel.centery)
        circle_radius = 60
        
        # Fond du cercle
        pygame.draw.circle(self.screen, GRAY_LIGHT, circle_center, circle_radius)
        
        # Couleur basée sur le score
        if self.sustainability_score > 70:
            arc_color = GREEN_PRIMARY
        elif self.sustainability_score > 40:
            arc_color = (255, 165, 0)
        else:
            arc_color = (220, 38, 38)
        
        # Score au centre
        score_text = self.title_font.render(f"{self.sustainability_score}%", True, arc_color)
        score_text_rect = score_text.get_rect(center=circle_center)
        self.screen.blit(score_text, score_text_rect)
        
    def _draw_statistics(self):
        """Dessine les statistiques finales"""
        stats_panel = pygame.Rect(690, 100, 280, 200)
        pygame.draw.rect(self.screen, WHITE, stats_panel, border_radius=10)
        pygame.draw.rect(self.screen, GREEN_PRIMARY, stats_panel, width=3, border_radius=10)
        
        stats_title = self.subtitle_font.render("📊 Statistiques", True, GREEN_DARK)
        self.screen.blit(stats_title, (700, 110))
        
        total_yield = sum(self.daily_yields)
        final_crops = sum(1 for card in self.crop_cards if card.progress >= 0.8 and card.name)
        
        stats_text = [
            f"Rendement total: {total_yield} kg",
            f"Cultures récoltées: {final_crops}",
            f"Argent restant: {self.final_money}€",
            f"Eau restante: {self.final_water}L"
        ]
        
        for i, stat in enumerate(stats_text):
            stat_surface = self.text_font.render(stat, True, BLACK)
            self.screen.blit(stat_surface, (700, 150 + i * 25))
            
    def _draw_ai_feedback(self):
        """Dessine le feedback de l'IA"""
        feedback_panel = pygame.Rect(50, 320, 920, 150)
        pygame.draw.rect(self.screen, WHITE, feedback_panel, border_radius=10)
        pygame.draw.rect(self.screen, GREEN_PRIMARY, feedback_panel, width=3, border_radius=10)
        
        feedback_title = self.subtitle_font.render("🤖 Feedback de l'IA", True, GREEN_DARK)
        self.screen.blit(feedback_title, (60, 330))
        
        # Générer feedback personnalisé
        feedback = self._generate_final_feedback()
        
        # Afficher le feedback sur plusieurs lignes
        self._draw_text_multiline(feedback, 60, 360, feedback_panel.width - 40)
        
    def _generate_final_feedback(self):
        """Génère un feedback personnalisé basé sur la performance"""
        total_yield = sum(self.daily_yields)
        
        feedback_parts = []
        
        # Performance générale
        if total_yield > 150:
            feedback_parts.append("🌟 Excellente récolte ! Vos techniques de jardinage sont impressionnantes.")
        elif total_yield > 100:
            feedback_parts.append("👍 Bonne performance ! Vous maîtrisez bien les bases du jardinage.")
        elif total_yield > 50:
            feedback_parts.append("📈 Performance correcte. Il y a de la place pour améliorer vos rendements.")
        else:
            feedback_parts.append("💡 Départ modeste. Concentrez-vous sur l'arrosage régulier et la planification.")
        
        # Durabilité
        if self.sustainability_score > 80:
            feedback_parts.append("🌍 Votre approche écologique est exemplaire !")
        elif self.sustainability_score > 60:
            feedback_parts.append("♻️ Bon équilibre entre productivité et durabilité.")
        else:
            feedback_parts.append("⚠️ Attention à réduire l'usage d'engrais chimiques pour plus de durabilité.")
        
        # Conseils pour la prochaine fois
        if self.final_water < 20:
            feedback_parts.append("💧 Pensez à mieux gérer vos réserves d'eau la prochaine fois.")
        
        return " ".join(feedback_parts)
        
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
            feedback_text = self.text_font.render(line, True, BLACK)
            self.screen.blit(feedback_text, (x, y_offset))
            y_offset += 25
            
    def handle_event(self, event):
        if self.replay_btn.handle_event(event):
            return "replay"
        elif self.quit_final_btn.handle_event(event):
            return "menu"
        return None