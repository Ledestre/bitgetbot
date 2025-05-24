import requests

symbol = "SETHUSDT"
product_type = "umcbl"
granularity = "60"
limit = 2

url = "https://api.bitget.com/api/mix/v1/market/candles"
params = {
    "symbol": symbol,
    "product_type": product_type,  # <-- correction ici
    "granularity": granularity,
    "limit": limit
}

try:
    response = requests.get(url, params=params)
    response.raise_for_status()
    candles = response.json()
    print("✅ Données reçues :")
    for candle in candles.get("data", []):
        print(candle)
except requests.exceptions.RequestException as e:
    print(f"❌ Erreur : {e}")
    print("Réponse brute :", response.text)
