import requests
import hmac
import time
import base64
import hashlib
import os

# Données utilisateur Bitget (LIVE API + papTrading pour DEMO)
API_KEY = "bg_4eb3307f6c91829a7d0f152a9e248534"
API_SECRET = "66a23b5d0da6fb3a401fabb6cad2591e4354fbaaf73ea85a605d543bbaf0a3e7"
API_PASSPHRASE = "Deltabot"
BASE_URL = "https://api.bitget.com"
PATH = "/api/v2/mix/market/contracts"
PARAMS = "productType=SUSDT-FUTURES"

def get_timestamp():
    return str(int(time.time() * 1000))

def sign(method, path, query, body=""):
    timestamp = get_timestamp()
    pre_hash = f"{timestamp}{method.upper()}{path}?{query}{body}"
    sign = hmac.new(API_SECRET.encode(), pre_hash.encode(), hashlib.sha256).digest()
    return timestamp, base64.b64encode(sign).decode()

timestamp, signature = sign("GET", PATH, PARAMS)

headers = {
    "ACCESS-KEY": API_KEY,
    "ACCESS-SIGN": signature,
    "ACCESS-TIMESTAMP": timestamp,
    "ACCESS-PASSPHRASE": API_PASSPHRASE,
    "locale": "en-US",
    "papTrading": "1"
}

response = requests.get(f"{BASE_URL}{PATH}?{PARAMS}", headers=headers)
print("Status Code:", response.status_code)
print("Response:")
print(response.text)
