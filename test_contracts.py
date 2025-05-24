import time
import hmac
import hashlib
import base64
import requests

# Remplace par tes vraies clés API démo Bitget
API_KEY = "bg_4eb3307f6c91829a7d0f152a9e248534"
API_SECRET = "66a23b5d0da6fb3a401fabb6cad2591e4354fbaaf73ea85a605d543bbaf0a3e7"
API_PASSPHRASE = "Deltabot"

def get_timestamp():
    return str(int(time.time() * 1000))

def sign(message, secret_key):
    mac = hmac.new(secret_key.encode('utf-8'), message.encode('utf-8'), hashlib.sha256)
    return base64.b64encode(mac.digest()).decode()

def parse_params_to_str(params):
    if not params:
        return ''
    items = sorted(params.items())
    query = '&'.join(f"{k}={v}" for k, v in items)
    return '?' + query if query else ''

def main():
    method = "GET"
    path = "/api/v2/mix/market/contracts"
    params = {"productType": "SUSDT-FUTURES"}
    timestamp = get_timestamp()
    request_path = path + parse_params_to_str(params)
    body = ""

    pre_hash = timestamp + method + request_path + body
    signature = sign(pre_hash, API_SECRET)

    headers = {
        "ACCESS-KEY": API_KEY,
        "ACCESS-SIGN": signature,
        "ACCESS-TIMESTAMP": timestamp,
        "ACCESS-PASSPHRASE": API_PASSPHRASE,
        "papTrading": "1",
        "locale": "en-US"
    }

    url = "https://api.bitget.com" + request_path

    response = requests.get(url, headers=headers, timeout=10)
    print(f"Status code: {response.status_code}")
    print("Response:", response.text)

if __name__ == "__main__":
    main()
