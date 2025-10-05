import random
import time
import json
import os
from datetime import date, datetime, timedelta
import numpy as np
from scipy.integrate import solve_ivp # Pour résoudre les équations différentielles

# Constantes pour un meilleur équilibrage
WATER_COST_PER_ACTION = 5
WATER_CONSUMPTION_PER_ACTION = 10
FERTILIZER_COST = 50
FERTILIZER_SUSTAINABILITY_PENALTY = 10
TREATMENT_COST = 30
BASE_YIELD_PER_HARVEST = 15
MAX_WATER_RESERVE = 500 # Plafond pour la réserve d'eau
SOIL_REGENERATION_RATE = 0.01 # Taux de régénération du sol par jour de jachère
# Constantes globales (utilisées si non définies par région)
DAILY_COST_OF_LIVING = 10
HEATWAVE_TEMP_THRESHOLD = 32
FROST_TEMP_THRESHOLD = 10

class FarmLogic:
    def __init__(self):
        self.crop_definitions = self._load_crop_definitions()
        self.reset_simulation()

    def _load_crop_definitions(self):
        """Charge les définitions des cultures depuis un fichier JSON."""
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        crops_path = os.path.join(project_root, "data", "samples", "crops.json")
        try:
            with open(crops_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"ERREUR: Fichier 'crops.json' introuvable ou invalide : {e}")
            return {}

    def setup_from_config(self, config):
        """Configure la logique du jeu à partir des paramètres de configuration."""
        self.reset_simulation()
        self.config = config # Garder une copie de la configuration initiale
        self.plots_config = config.get("plots", 6)
        num_years = config.get("years", 1)

        region_data = config.get("region_data", {})
        self.available_crops = region_data.get("cultures", [])
        # Charger le cycle de saisons et les durées pour UNE année
        base_seasons = region_data.get("season_cycle", ["Printemps", "Été", "Automne", "Hiver"])
        base_season_durations = region_data.get("season_durations", [10] * len(base_seasons))
        
        # Étendre pour le nombre d'années sélectionné
        self.seasons = base_seasons * num_years
        self.season_durations = base_season_durations * num_years
        self.max_days = sum(self.season_durations)
        self.season_end_days = np.cumsum(self.season_durations).tolist()

        # Charger les seuils météo spécifiques à la région
        weather_thresholds = region_data.get("weather_thresholds", {})
        self.heatwave_threshold = weather_thresholds.get("heatwave", HEATWAVE_TEMP_THRESHOLD)
        self.frost_threshold = weather_thresholds.get("frost", FROST_TEMP_THRESHOLD)

        # L'objectif de nourriture est aussi proportionnel au nombre d'années
        self.food_target = self.plots_config * 80 * num_years

        # Intégration des données météo NASA et de la date de début
        self.weather_data = config.get("nasa_weather_data")
        self.start_date = config.get("start_date")

        

        self.initialize_plots()
    def reset_simulation(self):
        """Remet à zéro la simulation pour une nouvelle partie."""
        self.current_day = 1
        self.seasons = []  # Sera défini par la configuration
        self.season_durations = []
        self.current_season_index = 0
        self.max_days = 0
        self.season_end_days = []
        
        # Ressources globales
        self.water_reserve = 400 # Réserve d'eau pour l'irrigation
        self.initial_money = 5000
        self.money = 5000
        self.sustainability_score = 100

        # Suivi
        self.daily_yields = []
        self.daily_soil_quality = []
        self.actions_taken = []
        self.harvested_today = 0
        self.plots = []
        self._weather_cache = {}

        # Nouvelles propriétés pour la météo
        self.weather_data = None
        self.start_date = None
        self.config = {}
        self.food_harvested = 0
        self.food_target = 0
        if not hasattr(self, 'crop_definitions'):
            self.crop_definitions = {}

    def initialize_plots(self):
        """Initialise les parcelles du potager."""
        self.plots = []
        for i in range(self.plots_config):
            plot_data = {
                "crop": None,           # Nom de la culture (ex: "Tomates")
                "age": 0,               # Âge de la plante en jours
                "progress": 0.0,        # Progression de la croissance (0.0 à 1.0)
                "soil_quality": 1.0,    # Qualité du sol (affecte K), de 0.0 à 1.0
                "water_level": 50.0,    # Niveau d'eau de la parcelle (0-100)
                "fertilizer_bonus": 0,  # Bonus de fertilisant (diminue avec le temps)
                "disease": None,        # Nom de la maladie (ex: "Mildiou")
                "disease_severity": 0.0 # Sévérité de la maladie (0.0 à 1.0)
            }
            self.plots.append(plot_data)

    def get_current_day_weather(self):
        """
        Récupère la météo pour le jour actuel de la simulation. 
        Utilise un cache pour ne calculer la météo qu'une fois par jour.
        Retourne des valeurs par défaut si les données API sont absentes.
        """
        # Vérifier le cache pour éviter de recalculer la météo à chaque image
        if self._weather_cache.get('day') == self.current_day:
            return self._weather_cache['weather']

        # Facteur saisonnier pour la température (simpliste)
        season = self.get_current_season()
        temp_offset_map = {"Printemps": 0, "Été": 8, "Automne": -2, "Hiver": -10,
                           "Petite saison des pluies": 0, "Grande saison sèche": 5, "Grande saison des pluies": -2, "Petite saison sèche": 3}
        precip_factor_map = {"Printemps": 1.0, "Été": 0.5, "Automne": 1.2, "Hiver": 0.8,
                             "Petite saison des pluies": 1.5, "Grande saison sèche": 0.1, "Grande saison des pluies": 3.0, "Petite saison sèche": 0.2}
        
        temp_offset = temp_offset_map.get(season, 0)
        precip_factor = precip_factor_map.get(season, 1.0)

        if not self.weather_data or not self.start_date:
            # Météo aléatoire si pas de données API
            rand_temp = random.uniform(12, 20) + temp_offset
            precip = (random.uniform(0, 7) if random.random() < 0.4 else 0) * precip_factor
            temp = rand_temp
            soil_temp = temp # Assigner une valeur par défaut pour la température du sol
        else:
            try:
                # --- LOGIQUE D'ÉCHELONNAGE MULTI-ANNÉES ---
                # 1. Déterminer la durée en jours d'une seule année de jeu
                region_data = self.config.get("region_data", {})
                base_season_durations = region_data.get("season_durations", [10, 10, 10, 10])
                days_in_one_game_year = sum(base_season_durations)
                if days_in_one_game_year == 0: days_in_one_game_year = 1

                # 2. Mapper le jour de jeu (ex: 1-80) à un jour dans une année de jeu (ex: 0-39)
                day_in_game_year = (self.current_day - 1) % days_in_one_game_year

                # 3. "Compresser" l'année de jeu (0-39) en une année météo réelle (0-364)
                scaling_factor = 365 / days_in_one_game_year
                day_in_real_year = int(day_in_game_year * scaling_factor)
                current_sim_date = self.start_date + timedelta(days=day_in_real_year)
                date_str = current_sim_date.strftime("%Y%m%d")
                
                params = self.weather_data['properties']['parameter']
                temp_from_api = params['T2M'].get(date_str, -999)
                precip_from_api = params['PRECTOTCORR'].get(date_str, -999)
                soil_temp_from_api = params['TS'].get(date_str, -999)

                # Gérer les données manquantes (-999) et appliquer les facteurs saisonniers
                temp = (temp_from_api if temp_from_api != -999 else 18) + temp_offset
                precip = (precip_from_api if precip_from_api > 0 else 0) * precip_factor
                soil_temp = soil_temp_from_api if soil_temp_from_api != -999 else temp

            except (KeyError, IndexError, TypeError):
                # En cas d'erreur avec les données API, on passe en mode aléatoire
                return self.get_current_day_weather()

        # Déterminer la condition en utilisant les seuils (spécifiques ou par défaut)
        if temp >= self.heatwave_threshold:
            condition = "heatwave"
        elif temp <= self.frost_threshold and precip > 0.5: # S'il gèle et qu'il y a des précipitations, c'est de la neige
            condition = "snow"
        elif temp <= self.frost_threshold: # S'il gèle sans précipitation, c'est du gel sec
            condition = "frost"
        elif precip > 10: # Seuil plus élevé pour "pluie forte"
            condition = "Pluie forte"
        elif precip > 2:
            condition = "Pluie légère"
        else:
            condition = "Ensoleillé"
        
        result = {"temp": temp, "precip": precip, "soil_temp": soil_temp, "condition": condition}

        # Mettre le résultat en cache pour la journée actuelle
        self._weather_cache = {'day': self.current_day, 'weather': result}

        return result

    def update_simulation(self):
        """Avance la simulation d'un jour et met à jour l'état du jeu."""
        if self.current_day > self.max_days:
            return

        # Récupérer la météo du jour
        weather_today = self.get_current_day_weather()
        temp = weather_today['temp']
        soil_temp = weather_today.get('soil_temp', temp) # Utilise la temp de l'air si celle du sol est absente
        precip = weather_today['precip']
        condition = weather_today['condition']

        # NOUVEAU: La pluie remplit aussi la réserve d'eau (collecte d'eau de pluie)
        if precip > 0:
            # Ajoute une fraction des précipitations à la réserve (ex: 50% de l'efficacité)
            self.water_reserve += precip * 0.5
            self.water_reserve = min(self.water_reserve, MAX_WATER_RESERVE)

        # Mise à jour de chaque parcelle
        for plot in self.plots:
            # 1. Mise à jour de l'eau dans la parcelle
            evaporation = max(0, (temp - 15) / 5) # Évaporation si > 15°C
            # La chaleur extrême augmente l'évaporation
            if condition == "heatwave":
                evaporation *= 2.0
            
            # La pluie forte peut "laver" les nutriments et le fertilisant du sol (lessivage)
            if condition == "Pluie forte":
                plot['fertilizer_bonus'] = max(0, plot['fertilizer_bonus'] - 0.01)
                plot['soil_quality'] = max(0.2, plot['soil_quality'] - 0.005)
            plot['water_level'] += precip - evaporation
            plot['water_level'] = np.clip(plot['water_level'], 0, 100)

            if plot["crop"]:
                plot["age"] += 1
                crop_def = self.crop_definitions.get(plot["crop"], {})

                # --- NOUVELLE LOGIQUE : GESTION DES MALADIES ---
                # 1. Risque d'apparition de maladie si la plante est sur-irriguée
                max_water_for_disease = crop_def.get("max_water_level", 95) # Seuil de tolérance à l'excès d'eau
                if plot.get('disease') is None and plot['water_level'] > max_water_for_disease and random.random() < 0.15: # 15% de chance par jour
                    plot['disease'] = "Mildiou"
                    plot['disease_severity'] = 0.1
                    # Le sur-arrosage dégrade aussi la qualité du sol
                    plot['soil_quality'] = max(0.2, plot['soil_quality'] - 0.02)
                    self.actions_taken.append("event:disease_start")

                # 2. Progression de la maladie si non traitée
                if plot.get('disease'):
                    plot['disease_severity'] = min(1.0, plot['disease_severity'] + 0.05)

                # --- MODÈLE DE CROISSANCE LOGISTIQUE AVEC ÉQUATION DIFFÉRENTIELLE ---
                # La croissance est modélisée par dP/dt = r * P * (1 - P), où P est la progression
                # et 'r' est le taux de croissance qui dépend des conditions environnementales.

                maturation_days = crop_def.get("maturation_days", 30)
                if maturation_days > 0 and plot["progress"] < 1.0:
                    # 1. Calculer le taux de croissance 'r' pour la journée
                    # Taux de base calibré pour atteindre la maturité en `maturation_days`
                    r_base = 10.0 / maturation_days
                    
                    # Effet du fertilisant : augmente le potentiel de croissance
                    fertilizer_effect = plot["fertilizer_bonus"] * 5 / maturation_days
                    r_potential = r_base + fertilizer_effect

                    # Facteurs environnementaux qui modulent le taux de croissance
                    water_factor = 1 - abs(plot['water_level'] - crop_def.get("water_need", 60)) / 100
                    season_factor_map = {"Printemps": 1.1, "Été": 1.0, "Automne": 0.9, "Hiver": 0.2,
                                         "Petite saison des pluies": 1.1, "Grande saison sèche": 0.8, "Grande saison des pluies": 1.0, "Petite saison sèche": 0.9}
                    season_factor = season_factor_map.get(self.get_current_season(), 1.0)
                    
                    temp_factor = 1.0
                    if not (crop_def.get("temp_min", 0) <= soil_temp <= crop_def.get("temp_max", 100)):
                        temp_factor = 0.5  # Pénalité si la température est hors de la plage optimale

                    # Multiplicateur de croissance global
                    growth_multiplier = water_factor * season_factor * temp_factor * plot["soil_quality"]

                    # Pénalité de croissance si la plante est sur-irriguée (noyée)
                    max_water_for_growth = crop_def.get("max_water_level", 95)
                    if plot['water_level'] > max_water_for_growth:
                        # La croissance ralentit fortement si la plante est "noyée"
                        overwater_penalty = 0.4 # Réduit la croissance de 60%
                        growth_multiplier *= overwater_penalty

                    # Application des pénalités (maladie, météo extrême, sécheresse)
                    if plot.get('disease'):
                        # Une maladie à 100% de sévérité peut réduire la croissance de 80%
                        growth_multiplier *= (1 - plot['disease_severity'] * 0.8)

                    if condition == "heatwave": 
                        growth_multiplier *= 0.5
                    elif condition == "frost": 
                        growth_multiplier *= 0.1
                        # Le gel peut endommager ou tuer les plantes non résistantes
                        if not crop_def.get("frost_resistant", False) and random.random() < 0.15: # 15% de chance
                            plot['progress'] = max(0, plot['progress'] - 0.5) # La plante subit de gros dégâts
                    
                    elif condition == "snow":
                        # La neige ralentit la croissance mais protège du gel extrême
                        growth_multiplier *= 0.2

                    # Pénalité de sécheresse sévère
                    if plot['water_level'] < 10:
                        growth_multiplier *= 0.2 # Croissance très faible
                        plot['progress'] = max(0, plot['progress'] - 0.02) # La plante régresse

                    # Taux de croissance réalisé pour la journée
                    r_realized = r_potential * growth_multiplier

                    # 2. Définir et résoudre l'équation différentielle pour un jour
                    def logistic_growth(t, P):
                        return r_realized * np.clip(P, 0, 1) * (1 - np.clip(P, 0, 1))

                    solution = solve_ivp(logistic_growth, [0, 1], [plot["progress"]], method='RK45')
                    
                    # 3. Mettre à jour la progression
                    plot["progress"] = np.clip(solution.y[0][-1], 0, 1.0)
            
            else:
                # --- NOUVEAU: Logique de jachère (fallow) ---
                # Si la parcelle est vide, le sol se régénère lentement.
                plot['soil_quality'] += SOIL_REGENERATION_RATE
                plot['soil_quality'] = min(1.0, plot['soil_quality'])

            # Diminution du bonus de fertilisant avec le temps
            plot["fertilizer_bonus"] = max(0, plot["fertilizer_bonus"] - 0.02)

        

        # Enregistrer la qualité moyenne du sol pour le graphique
        avg_soil_quality = np.mean([p['soil_quality'] for p in self.plots]) if self.plots else 1.0
        self.daily_soil_quality.append(avg_soil_quality)

        # Mettre à jour le score de durabilité pour qu'il reflète la qualité moyenne du sol
        self._update_sustainability_score()

        # Enregistrer le rendement du jour et réinitialiser pour le jour suivant
        self.daily_yields.append(self.harvested_today)
        self.harvested_today = 0

        # Déduire le coût de la vie quotidien
        self.money -= DAILY_COST_OF_LIVING

        # Avancer au jour suivant
        self.current_day += 1

        # Mettre à jour l'index de la saison si le seuil est dépassé
        if self.current_season_index < len(self.seasons) - 1 and self.current_day > self.season_end_days[self.current_season_index]:
            self.current_season_index += 1
            
    def get_current_season(self):
        """Retourne le nom de la saison actuelle."""
        if self.seasons:
            return self.seasons[self.current_season_index]
        return "Saison Indéfinie"

    def _update_sustainability_score(self):
        """Met à jour le score de durabilité pour qu'il corresponde à la qualité moyenne du sol."""
        if not self.plots:
            self.sustainability_score = 100
        else:
            avg_soil_quality = np.mean([p['soil_quality'] for p in self.plots])
            self.sustainability_score = int(avg_soil_quality * 100)

    # --- Actions du joueur ---

    def plant_action(self, plot_index, crop_name):
        """Plante une nouvelle culture sur une parcelle."""
        if 0 <= plot_index < len(self.plots) and self.plots[plot_index]["crop"] is None:
            self.plots[plot_index]["crop"] = crop_name
            self.plots[plot_index]["age"] = 0
            self.plots[plot_index]["progress"] = 0.01 # Démarrer avec une petite progression pour initier la croissance
            self.actions_taken.append(f"plant:{crop_name}")
            return True
        return False
      

    def water_action(self, plot_index):
        """Logique pour l'action d'arrosage."""
        if 0 <= plot_index < len(self.plots) and self.water_reserve >= WATER_CONSUMPTION_PER_ACTION:
            self.water_reserve -= WATER_CONSUMPTION_PER_ACTION
            self.plots[plot_index]["water_level"] = min(100, self.plots[plot_index]["water_level"] + 20)
            self.actions_taken.append("water")
            return True
        return False

    def drain_action(self, plot_index):
        """Logique pour l'action de drainage."""
        if 0 <= plot_index < len(self.plots):
            self.plots[plot_index]["water_level"] = max(0, self.plots[plot_index]["water_level"] - 30)
            self.actions_taken.append("drain")
            return True
        return False

    def treat_action(self, plot_index):
        """Traite une maladie sur une parcelle."""
        if 0 <= plot_index < len(self.plots) and self.money >= TREATMENT_COST:
            plot = self.plots[plot_index]
            if plot.get('disease'):
                self.money -= TREATMENT_COST
                plot['disease'] = None
                plot['disease_severity'] = 0.0
                self.actions_taken.append("treat")
                return True
        return False    

    def fertilize_action(self, plot_index):
        """Logique pour l'action de fertilisation."""
        if 0 <= plot_index < len(self.plots) and self.money >= FERTILIZER_COST:
            self.money -= FERTILIZER_COST
            # Le fertilisant donne un bonus de croissance mais dégrade le sol
            self.plots[plot_index]["fertilizer_bonus"] += 0.1
            self.plots[plot_index]["soil_quality"] = max(0.2, self.plots[plot_index]["soil_quality"] - 0.05)
            self.actions_taken.append("fertilize")
            self._update_sustainability_score() # Mettre à jour le score immédiatement
            return True
        return False

    def harvest_action(self, plot_index):
        """Logique pour l'action de récolte."""
        if 0 <= plot_index < len(self.plots):
            plot = self.plots[plot_index]
            if plot["crop"] and plot["progress"] >= 0.9: # Récolte possible si très mature
                crop_def = self.crop_definitions.get(plot["crop"], {})
                # Le rendement final dépend de la qualité du sol (K) et de la maturité finale
                final_yield = crop_def.get("max_k", 100) * plot["soil_quality"] * plot["progress"]
                self.money += final_yield
                self.harvested_today += final_yield # Ajouter au rendement du jour
                
                # Réinitialiser la parcelle
                plot["crop"] = None
                plot["age"] = 0
                plot["progress"] = 0.0
                
                self.food_harvested += final_yield
                self.actions_taken.append("harvest")
                return final_yield
        return 0
    
    # --- Sauvegarde et Chargement ---

    def save_game(self, filepath="data/savegame.json"):
        """Sauvegarde l'état actuel du jeu dans un fichier JSON."""
        state = {
            'config': self.config,
            'current_day': self.current_day,
            'current_season_index': self.current_season_index,
            'water_reserve': self.water_reserve,
            'money': self.money,
            'sustainability_score': self.sustainability_score,
            'food_harvested': self.food_harvested,
            'food_target': self.food_target,
            'daily_yields': self.daily_yields,
            'daily_soil_quality': self.daily_soil_quality,
            'actions_taken': self.actions_taken,
            'plots': self.plots,
        }

        def json_serializer(obj):
            """Gère la sérialisation des objets non-standard comme datetime."""
            if isinstance(obj, (datetime, date)):
                return obj.isoformat()
            raise TypeError(f"Le type {type(obj)} n'est pas sérialisable en JSON")

        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=4, default=json_serializer)
        print(f"Partie sauvegardée dans {filepath}")

    def load_game(self, filepath="data/savegame.json"):
        """Charge l'état du jeu depuis un fichier JSON."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            # Convertir la date de string à datetime après le chargement
            if 'config' in state and 'start_date' in state['config'] and isinstance(state['config']['start_date'], str):
                state['config']['start_date'] = datetime.fromisoformat(state['config']['start_date'])

            self.setup_from_config(state['config'])
            
            self.current_day = state['current_day']
            self.current_season_index = state['current_season_index']
            self.water_reserve = state['water_reserve']
            self.money = state['money']
            self.sustainability_score = state['sustainability_score']
            self.food_harvested = state['food_harvested']
            self.food_target = state.get('food_target', self.plots_config * 80)
            self.daily_yields = state['daily_yields']
            self.daily_soil_quality = state['daily_soil_quality']
            self.actions_taken = state['actions_taken']
            self.plots = state['plots']

            # Migration pour les anciennes sauvegardes
            for plot in self.plots:
                plot.setdefault('disease', None)
                plot.setdefault('disease_severity', 0.0)

            self.last_day_change = time.time()
            print(f"Partie chargée depuis {filepath}")
            return True
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            print(f"Erreur lors du chargement de la sauvegarde : {e}")
            return False

    # --- Conditions de fin de jeu ---

    def check_win_condition(self):
        """Vérifie si le joueur a gagné."""
        avg_soil_quality = np.mean([p['soil_quality'] for p in self.plots]) if self.plots else 0
        # Condition: objectif de nourriture atteint ET sol préservé
        return self.food_harvested >= self.food_target and avg_soil_quality > 0.2

    def check_loss_condition(self):
        """Vérifie si le joueur a perdu."""
        if self.money <= 0:
            print(f"Game over: No more money")
            return True
        if self.current_day >= self.max_days:
            return True

        avg_soil_quality = np.mean([p['soil_quality'] for p in self.plots]) if self.plots else 0
        # Exemple : le sol est devenu stérile
        return avg_soil_quality < 0.2

