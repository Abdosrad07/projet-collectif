# Farm Navigator - MVP

**Farm Navigator** est un jeu interactif qui transforme la gestion d'une ferme en défi stratégique et éducatif.
Le joueur cultive, arrose, fertilise et récolte ses plantes tout en tenant compte de la météo réelle fournie par la NASA et de conseils d'un assistant IA intégré.

---

## Pourquoi c'est cool

-   **Météo réaliste** : données NASA pour influencer la croissance des plantes.
-   **Assistant IA** : guide le joueur sur l'état des cultures et la rentabilité.
-   **Gestion et stratégie** : décisions sur l'eau, fertilisation et récolte affectent le score et les finances.
-   **Interface dynamique** : visuelle et interactive grâce à Pygame.

---

## Tech et outils

-   Python 3
-   Pygame (animations 2D)
-   Requests (API NASA POWER)
-   Rule-based AI pour l'assistant agricole

---

## Objectifs MVP

-   Jouer et gérer une ferme complète sur 7 jours.
-   Montrer les conséquences de chaque action sur rendement, finances et durabilité.
-   Tester l'intégration de données réelles pour des décisions éclairées.

---

## Rôles & Branches GitHub
-   main => Code stable & version finale
-   gameplay => logique du jeu
-   ui => design interface
-   data => intégration des données NASA
-   ai => module d'intelligence (même si simple au début)

---

## Installation rapide
``` bash
git clone https://github.com/Abdosrad07/projet-collectif.git
cd projet-collectif
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py

```
---

## Perspectives

-   IA prédictive pour optimiser rendement et durabilité.
-   Plus de types de cultures et saisons.
-   Visualisation graphique de l'impact environnemental.
-   déploiement multiplateforme.

---

## Architecture du projet

PROJET-COLLECTIF/
    venv/
        main.py                             # Point d'entrée principal du jeu
        assets/                             # Ressources (images, sons, icônes)
            images/
            sounds/
        core/                               # Logique et backend
            nasa_api.py                     # Récupération des données NASA
            farm_logic.py                   # Croissance des cultures, règles de jeu
            utils.py                        # Fonctions utilitaires (ex: conversions)
        data/                               # Données (NASA, cultures, sauvegardes)
            samples/                        # Données JSON/CSV récupérées de l'API
            crops.json                      # Tableau des cultures par climat
            savegame.json                   
        ui/                                 # Interfaces utilisateur 
            menu.py                         # Ecran d'accueil (menu principal)
            config.py                       # Ecran de configuration des parcelles
            game.py                         # Interface principale du jeu (ferme interactive)
            results.py                      # Ecran de résultats 
        README.md                           # Documentation
        requirements.txt                    # Librairies Python nécessaires
