import hmac
import hashlib
import base64
import time
import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("BITGET_API_KEY")
API_SECRET = os.getenv("BITGET_API_SECRET")
API_PASSPHRASE = os.getenv("BITGET_API_PASSPHRASE")

API_BASE_URL = "https://api.bitget.com"  # API live

def get_timestamp():
    return str(int(time.time() * 1000))

def parse_params_to_str(params: dict) -> str:
    if not params:
        return ''
    items = sorted(params.items())
    query = '&'.join(f"{k}={v}" for k, v in items)
    return '?' + query if query else ''

def sign_bitget(method, path, body="", params=None):
    timestamp = get_timestamp()
    request_path = path
    if method.upper() == "GET" and params:
        request_path += parse_params_to_str(params)
    pre_hash_str = timestamp + method.upper() + request_path + body
    signature = base64.b64encode(hmac.new(API_SECRET.encode(), pre_hash_str.encode(), hashlib.sha256).digest()).decode()
    headers = {
        "ACCESS-KEY": API_KEY,
        "ACCESS-SIGN": signature,
        "ACCESS-TIMESTAMP": timestamp,
        "ACCESS-PASSPHRASE": API_PASSPHRASE,
        "locale": "en-US"
    }
    if method.upper() != "GET":
        headers["Content-Type"] = "application/json"
    return headers

def test_get_account():
    path = "/api/v2/mix/account/account"
    params = {"marginCoin": "USDT"}
    headers = sign_bitget("GET", path, params=params)
    url = API_BASE_URL + path + parse_params_to_str(params)
    response = requests.get(url, headers=headers)
    print("Status code:", response.status_code)
    print("Response:", response.text)

if __name__ == "__main__":
    test_get_account()
