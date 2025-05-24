import requests

API_URL = "https://api.bitget.com/api/v2/mix/market/ticker"
SYMBOL = "SETHSUSDT"
PRODUCT_TYPE = "SUSDT-FUTURES"

params = {
    "symbol": SYMBOL,
    "productType": PRODUCT_TYPE
}

try:
    response = requests.get(API_URL, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    if data.get("code") == "00000":
        price = data["data"][0]["lastPr"]
        print(f"[OK] Prix actuel de {SYMBOL} : {price} USDT")
    else:
        print(f"[ERREUR API] Code : {data.get('code')} | Message : {data.get('msg')}")
except requests.exceptions.RequestException as e:
    print(f"[ERREUR CONNEXION] {e}")

