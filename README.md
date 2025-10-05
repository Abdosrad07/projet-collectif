🌾 FarmNavigator — Cultivate Smarter, Play Greener

> An educational farming simulator powered by NASA’s open climate data.
Learn sustainable agriculture through play — manage your crops, water, and soil while witnessing the impact of your actions on yield, environment, and sustainability.




---

🚀 Overview

FarmNavigator is an interactive farming simulator that helps players understand the importance of data-driven agriculture and sustainability.
The game blends NASA’s open datasets, scientific modeling (via SciPy), and AI-based recommendations to simulate realistic agricultural decision-making.

Players can plant, irrigate, drain, fertilize, and harvest their virtual crops — while monitoring how each decision affects the ecosystem and overall farm productivity.


---

🌍 Challenge Addressed

This project was developed as part of the NASA Space Apps Challenge 2025, under the theme:

> 🛰 “Leveraging Earth Observation Data for Informed Agricultural Decision-Making”



The goal is to make NASA’s environmental data accessible to everyone — by turning it into a game-based learning experience that teaches sustainable farming practices.


---

🧩 Key Features

🎮 Gameplay Features

🌱 Dynamic Farm Simulation — Create your own plots, choose location and crops.

☀ Real NASA Climate Data Integration — Weather, soil moisture, and solar radiation via the NASA POWER API.

💧 Water Management System — Simulate irrigation, drainage, and droughts.

🌿 Fertilization and Soil Health — Boost yield at the cost of long-term soil quality.

🧠 AI Advisor — Real-time smart suggestions for better sustainability decisions.

⚙ Growth Modeling — Crop evolution simulated using differential equations (SciPy).

🌦 Weather Effects — Rain, snow, and wind animations affecting gameplay.

📊 Results Dashboard — Detailed sustainability score, yield analysis, and AI feedback after each session.



---

🧠 Educational Impact

FarmNavigator transforms scientific datasets into interactive lessons.
Players learn:

How climate affects agricultural productivity.

How unsustainable actions (overwatering, overfertilizing) damage soil and yield.

How data from NASA satellites can guide better decisions in real life.


This makes it an effective STEM educational tool for students, researchers, and farmers alike.


---

🛰 NASA Data Integration

FarmNavigator uses NASA’s POWER API for real climate and environmental parameters:

Data Type	Description	Source

Temperature	Daily surface temperature	NASA POWER API
Precipitation	Rainfall data for the selected region	NASA POWER API
Solar Radiation	Energy input for photosynthesis modeling	NASA POWER API
Wind Speed	Influences evapotranspiration rate	NASA POWER API
Humidity	Impacts water loss and disease probability	NASA POWER API


Additional data sources (optional):

🌎 AppEEARS for advanced satellite subsets.

🛰 NASA EarthData for vegetation and soil datasets.



---

🧮 Scientific Modeling

We employ SciPy’s odeint() to simulate plant growth over time using a system of differential equations.

Example concept:

\frac{dG}{dt} = α \cdot f(\text{temperature}, \text{humidity}) - β \cdot g(\text{water\_stress}, \text{soil\_degradation})


---

🧑‍💻 Technology Stack

Category	Tools

Programming Language	Python 3
Game Engine	Pygame
Scientific Computing	NumPy, SciPy
Data Access	Requests (NASA POWER API)
Visualization	Matplotlib
AI System	Rule-based AI for contextual tips
Version Control	Git + GitHub
Design	Figma (UI/UX prototype)



---

🧱 Project Architecture

projet-collectif/
├── core/
│   ├── farm_logic.py  # Core game logic for farming simulation
│   └── nasa_api.py    # (Not provided, but implied) Interface for NASA data
├── data/
│   ├── regions_fr.json  # Region data (climate, soil, crops)
│   └── samples/
│       └── crops.json   # Crop definitions (growth, water needs, etc.)
├── ui/
│   ├── config.py      # Configuration interface (plots, years, location)
│   ├── game.py        # Main game interface (plot management, actions)
│   ├── menu.py        # Main menu interface
│   ├── results.py     # Results interface (yields, soil quality, stats)
│   ├── constants.py   # Shared constants (colors, fonts)
│   └── widgets.py     # Shared UI widgets (buttons, text rendering)
├── main.py            # (Not provided, but implied) Entry point of the game
├── requirements.txt   # (Not provided, but should exist) Project dependencies
└── README.md          # Project description and instructions

🕹 How to Run Locally

1. Clone the repository

git clone https://github.com/Abdosrad07/projet-collectif.git
cd projet-collectif

2. Create a virtual environment

python -m venv venv
source venv/bin/activate    # On Linux/Mac
venv\Scripts\activate       # On Windows

3. Install dependencies

pip install -r requirements.txt

4. Launch the game

python main.py


---

🌱 Gameplay Overview

Choose your region (climate, soil type, and crops auto-adjust).

Configure plot count and size.

Manage resources: water, fertilizer, and soil quality.

Watch crops evolve through five visual growth stages.

Monitor NASA weather data updates dynamically.

Reach end of the season → get sustainability and yield reports.


Victory:
🌾 High yield + high sustainability score.

Failure:
💧 Overwatering, 🧪 over-fertilizing, or 🌍 soil depletion leading to low final score.


---

🤖 Future Improvements

Integration with AppEEARS for real satellite-based soil and vegetation data.

Addition of machine learning models to predict yield trends.

Mobile version using Kivy or Flutter.

Online leaderboard for comparing sustainability scores globally.



---

👥 Team GaiaTech

Name	Role

Njimongba Fochivé Mama Abdourahim	 / Developer (Python, Pygame)
Lekane Kounlag Briand Durrande /	AI & Logic Developer
Hadja Bebbe Hassimatou Bah /	Project Leader / Tester / Documentation / UX




---

💬 Quote

> “FarmNavigator turns NASA data into a living classroom —
where every drop of water, every seed, and every decision matters.”




---

📜 License

This project uses NASA’s Open Data in compliance with their data use policy.
Developed for the NASA Space Apps Challenge 2025.
Code released under the MIT License.
