import requests

PRODUCT_TYPE = "umcbl"  # Futures USDT margined
url = f"https://api.bitget.com/api/mix/v1/market/contracts?productType={PRODUCT_TYPE}"

try:
    response = requests.get(url)
    data = response.json()

    if data.get("code") == "00000":
        symbols = [item["symbol"] for item in data.get("data", [])]
        print(f"✅ Symboles valides ({len(symbols)} paires) sur Bitget ({PRODUCT_TYPE}):\n")
        for s in symbols:
            print(f"• {s}")
    else:
        print(f"❌ Erreur API Bitget : {data}")
except Exception as e:
    print(f"❌ Exception lors de l'appel API : {e}")
