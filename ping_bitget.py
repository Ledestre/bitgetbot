import requests
from datetime import datetime

def ping_bitget():
    url = "https://api.bitget.com/api/mix/v1/market/ticker?symbol=ETHUSDT_UMCBL"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        price = data.get("data", {}).get("last", "N/A")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] ✅ Connexion réussie à Bitget | Prix ETH/USDT : {price}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur de connexion à Bitget : {e}")

if __name__ == "__main__":
    ping_bitget()
