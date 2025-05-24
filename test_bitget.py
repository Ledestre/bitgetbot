import requests

def test_bitget_candles():
    url = "https://api.bitget.com/api/mix/v1/market/candles"
    params = {
        "symbol": "SETHUSDT",
        "granularity": "1m",  # granularity corrigée ici
        "limit": 2
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        print("Réponse API Bitget :")
        print(data)
    except requests.exceptions.HTTPError as errh:
        print(f"HTTP Error: {errh}")
    except requests.exceptions.ConnectionError as errc:
        print(f"Connection Error: {errc}")
    except requests.exceptions.Timeout as errt:
        print(f"Timeout Error: {errt}")
    except requests.exceptions.RequestException as err:
        print(f"Error: {err}")

if __name__ == "__main__":
    test_bitget_candles()
