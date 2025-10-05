import requests
from typing import Dict, Any

def get_nasa_power_data(latitude: float, longitude: float, start_date: str, end_date: str, api_key: str) -> Dict[str, Any]:
    """
    Récupère les données météo et sol de l'API NASA POWER.

    Args:
        latitude: La latitude du lieu.
        longitude: La longitude du lieu.
        start_date: La date de début au format 'YYYYMMDD'.
        end_date: La date de fin au format 'YYYYMMDD'.
        api_key: Votre clé API pour NASA POWER.

    Returns:
        Un dictionnaire contenant les données JSON de l'API.
    """
    api_url = "https://power.larc.nasa.gov/api/temporal/daily/point"
    
    # T2M: Température à 2m
    # PRECTOTCORR: Précipitations corrigées
    # TS: Température de la surface du sol (Earth Skin Temperature)
    params = {
        "parameters": "T2M,PRECTOTCORR,TS",
        "community": "AG", # Agroclimatology
        "longitude": longitude,
        "latitude": latitude,
        "start": start_date,
        "end": end_date,
        "format": "JSON",
        "api_key": api_key
    }

    print(f"Interrogation de l'API NASA POWER pour la période du {start_date} au {end_date}...")

    response = requests.get(api_url, params=params)
    response.raise_for_status()  # Lève une exception pour les codes d'erreur HTTP

    data = response.json()
    print("Données NASA POWER récupérées avec succès !")
    return data

