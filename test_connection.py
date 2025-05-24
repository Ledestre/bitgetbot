import requests

url = "https://api.bitget.com/api/v2/mix/market/ticker"
params = {
    "symbol": "SETHSUSDT",
    "productType": "SUSDT-FUTURES"
}

try:
    response = requests.get(url, params=params, timeout=10)
    print("Statut HTTP :", response.status_code)
    print("Réponse JSON :", response.json())
except Exception as e:
    print("[ERREUR CONNEXION]", e)
