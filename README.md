```markdown
# 🌿 FarmNavigator — Cultiver intelligemment, apprendre durablement

> Simulateur agricole éducatif alimenté par des données climatiques ouvertes.
> Découvrez l'agriculture durable à travers une expérience interactive fondée sur la science, la simulation et l'analyse de données.

---

## 🚀 Présentation

**FarmNavigator** est un simulateur agricole interactif conçu pour sensibiliser aux enjeux de l'agriculture durable et de la prise de décision basée sur les données.

Le projet combine :

- des données climatiques ouvertes,
- des modèles scientifiques de croissance végétale,
- des mécanismes de gestion agricole,
- un système d'assistance intelligent.

L'utilisateur gère une exploitation virtuelle en prenant des décisions liées aux cultures, à l'irrigation, à la fertilisation et à la qualité du sol, tout en observant leurs impacts sur la production et l'environnement.

---

## 🌍 Contexte du projet

Développé dans le cadre du **NASA Space Apps Challenge 2025**, ce projet répond au thème :

> 🛰 **Leveraging Earth Observation Data for Informed Agricultural Decision-Making**

L'objectif est de rendre les données environnementales accessibles au grand public à travers un outil pédagogique ludique et concret.

---

## 🎯 Objectifs

FarmNavigator vise à :

- vulgariser l'utilisation des données spatiales en agriculture ;
- sensibiliser à la gestion durable des ressources ;
- démontrer l'impact des décisions agricoles sur les rendements ;
- encourager l'apprentissage par la simulation ;
- promouvoir l'agriculture intelligente et résiliente.

---

## 🧩 Fonctionnalités principales

### 🎮 Simulation agricole dynamique

- Création et gestion de parcelles agricoles ;
- Choix de la région et des cultures ;
- Paramétrage des saisons de culture.

### 🌦 Intégration de données climatiques réelles

Connexion à la **NASA POWER API** pour récupérer :

- température,
- précipitations,
- humidité,
- rayonnement solaire,
- vitesse du vent.

### 💧 Gestion de l'eau

- Irrigation manuelle ;
- Drainage ;
- Gestion des périodes de sécheresse ;
- Risques liés au sur-arrosage.

### 🌱 Fertilité du sol

- Utilisation d'engrais ;
- Dégradation progressive du sol ;
- Arbitrage entre rendement immédiat et durabilité.

### 🧠 Assistant intelligent

Système de recommandations en temps réel :

- conseils d'arrosage,
- optimisation des ressources,
- alertes environnementales,
- stratégies durables.

### 📊 Tableau de bord analytique

En fin de simulation :

- rendement obtenu,
- score de durabilité,
- qualité finale du sol,
- bilan des décisions prises.

---

## 🧠 Impact pédagogique

FarmNavigator transforme des données scientifiques complexes en expérience interactive.

L'utilisateur apprend notamment :

- l'influence du climat sur les cultures ;
- les conséquences du gaspillage en eau ;
- les effets du surdosage d'engrais ;
- l'importance des données pour décider efficacement ;
- les bases de l'agriculture de précision.

Le projet peut servir d'outil pédagogique pour :

- établissements scolaires,
- formations STEM,
- sensibilisation agricole,
- ateliers technologiques.

---

## 🛰 Sources de données utilisées

### NASA POWER API

| Type de donnée      | Description                                    |
|---------------------|------------------------------------------------|
| Température         | Température journalière de surface             |
| Précipitations      | Données pluviométriques                        |
| Rayonnement solaire | Énergie disponible pour la photosynthèse       |
| Vent                | Influence l'évapotranspiration                 |
| Humidité            | Impact sur les pertes d'eau et les maladies    |

### Extensions possibles

- **NASA EarthData**
- **AppEEARS**
- Données satellitaires sur la végétation et les sols

---

## 🧮 Modélisation scientifique

La croissance des cultures est simulée grâce à des équations différentielles résolues avec **SciPy**.

Exemple conceptuel :

$$\frac{dG}{dt} = \alpha \cdot f(\text{température, humidité}) - \beta \cdot g(\text{stress hydrique, dégradation du sol})$$

où :

- $G$ représente la croissance ;
- $\alpha$ le facteur de développement ;
- $\beta$ l'impact des contraintes environnementales.

---

## 🧑‍💻 Technologies utilisées

| Catégorie            | Outils                          |
|----------------------|---------------------------------|
| Langage principal    | Python 3                        |
| Interface graphique  | Pygame                          |
| Calcul scientifique  | NumPy, SciPy                    |
| API / Web            | Requests                        |
| Visualisation        | Matplotlib                      |
| IA                   | Système de règles contextuelles |
| Versioning           | Git / GitHub                    |
| Conception UI/UX     | Figma                           |

---

## 🧱 Architecture du projet

```text
projet-collectif/
├── core/
│   ├── farm_logic.py
│   └── nasa_api.py
├── data/
│   ├── regions_fr.json
│   └── samples/
│       └── crops.json
├── ui/
│   ├── config.py
│   ├── game.py
│   ├── menu.py
│   ├── results.py
│   ├── constants.py
│   └── widgets.py
├── main.py
├── requirements.txt
└── README.md
```

---

## 🕹 Installation et exécution

### 1. Cloner le dépôt

```bash
git clone https://github.com/Abdosrad07/projet-collectif.git
cd projet-collectif
```

### 2. Créer un environnement virtuel

```bash
python -m venv venv
```

### 3. Activer l'environnement

**Linux / macOS**

```bash
source venv/bin/activate
```

**Windows**

```bash
venv\Scripts\activate
```

### 4. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 5. Lancer l'application

```bash
python main.py
```

---

## 🌱 Déroulement d'une partie

1. Sélection de la région.
2. Choix des cultures.
3. Gestion des ressources (eau, engrais, sol).
4. Suivi de la croissance des plantes.
5. Analyse des conditions climatiques.
6. Bilan final de performance.

### Succès

🌾 Rendement élevé + score de durabilité élevé.

### Échec

- 💧 Sur-arrosage
- 🧪 Sur-fertilisation
- 🌍 Dégradation du sol

---

## 🤖 Perspectives d'évolution

- Version mobile Android / iOS ;
- Connexion à de vrais capteurs IoT ;
- Intelligence artificielle prédictive ;
- Mode multijoueur ou classement mondial ;
- Cartographie avancée ;
- Recommandations personnalisées selon la région.

---

## 💬 Citation

> « Chaque décision agricole a un impact. FarmNavigator permet de le comprendre avant d'agir. »

---

## 📜 Licence

Ce projet utilise des données ouvertes conformément aux politiques d'utilisation des fournisseurs concernés.

Développé dans un cadre éducatif et expérimental.  
Code distribué sous licence **MIT**.
```