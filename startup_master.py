import os
import time
import json
import hmac
import hashlib
import base64
import requests
import threading
from flask import Flask, request
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# === CONFIG ===
API_BASE_URL = "https://api.bitget.com"
PRODUCT_TYPE = "SUSDT-FUTURES"
SYMBOL = "SETHSUSDT"  # basé sur info symboles valides

API_KEY = os.getenv("BITGET_API_KEY")
API_SECRET = os.getenv("BITGET_API_SECRET")
API_PASSPHRASE = os.getenv("BITGET_API_PASSPHRASE")
LEVERAGE = int(os.getenv("LEVERAGE", 50))
BET_AMOUNT = float(os.getenv("BET_AMOUNT", 100))
FETCH_INTERVAL = int(os.getenv("FETCH_INTERVAL", 60))
STATE_FILE = os.getenv("STATE_FILE", "bot_state.json")
DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# === GLOBALS ===
position = None
entry_price = None
capital = float(os.getenv("INITIAL_CAPITAL", 1000))
realized_pnl = 0
last_signal = None
running = True
signal_lock = threading.Lock()

app = Flask(__name__)

def send_telegram(text):
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": text}, timeout=5)
        except Exception as e:
            print(f"[TELEGRAM] Erreur : {e}")

def get_timestamp():
    return str(int(time.time() * 1000))

def parse_params_to_str(params):
    if not params:
        return ''
    items = sorted(params.items())
    return '?' + '&'.join(f"{k}={v}" for k, v in items)

def sign_bitget(method, path, body="", params=None):
    timestamp = get_timestamp()
    request_path = path + parse_params_to_str(params) if method == "GET" and params else path
    pre_hash_str = timestamp + method + request_path + body
    signature = base64.b64encode(hmac.new(API_SECRET.encode(), pre_hash_str.encode(), hashlib.sha256).digest()).decode()
    headers = {
        "ACCESS-KEY": API_KEY,
        "ACCESS-SIGN": signature,
        "ACCESS-TIMESTAMP": timestamp,
        "ACCESS-PASSPHRASE": API_PASSPHRASE,
        "locale": "en-US",
        "papTrading": "1"
    }
    if method != "GET":
        headers["Content-Type"] = "application/json"
    return headers

def fetch_price():
    try:
        url = f"{API_BASE_URL}/api/v2/mix/market/ticker"
        path = "/api/v2/mix/market/ticker"
        params = {"symbol": SYMBOL, "productType": PRODUCT_TYPE}
        headers = sign_bitget("GET", path, params=params)
        full_url = url + parse_params_to_str(params)
        res = requests.get(full_url, headers=headers, timeout=10)
        if DEBUG:
            print(f"[DEBUG] fetch_price HTTP {res.status_code}: {res.text}")
        if res.status_code != 200:
            return None
        data = res.json()
        return float(data['data'][0]['lastPr']) if 'data' in data else None
    except Exception as e:
        print(f"[ERREUR] fetch_price : {e}")
        return None

def place_order(side, price):
    url = f"{API_BASE_URL}/api/v2/mix/order/place-order"
    path = "/api/v2/mix/order/place-order"
    size = round(BET_AMOUNT * LEVERAGE / price, 3)
    body_dict = {
        "symbol": SYMBOL,
        "productType": PRODUCT_TYPE,
        "marginMode": "isolated",
        "marginCoin": "SUSDT",
        "size": str(size),
        "price": str(price),
        "side": side,
        "tradeSide": "open",
        "orderType": "market",
        "force": "gtc",
        "clientOid": str(int(time.time() * 1000)),
        "reduceOnly": "NO"
    }
    body = json.dumps(body_dict)
    headers = sign_bitget("POST", path, body=body)
    if DRY_RUN:
        print(f"[SIMULATION] {side.upper()} à {price} | SIZE: {size}")
        return
    res = requests.post(url, headers=headers, data=body)
    print(f"[ORDER] {side.upper()} @ {price:.2f} | Status: {res.status_code}")
    if DEBUG:
        print(res.text)

@app.route("/webhook", methods=["POST"])
def webhook():
    global last_signal
    data = request.get_json(force=True)
    if not data:
        return "Requête invalide", 400
    signal = data.get("signal")
    if signal in ["buy", "sell"]:
        with signal_lock:
            last_signal = signal
        return "OK", 200
    return "Signal invalide", 400

def trading_loop():
    global position, entry_price, capital, realized_pnl, last_signal
    send_telegram("🚀 Bot lancé (Bitget Demo, symbol: SETHSUSDT)")
    while running:
        with signal_lock:
            signal = last_signal
            last_signal = None
        price = fetch_price()
        if not price or not signal:
            time.sleep(FETCH_INTERVAL)
            continue

        if signal == position:
            continue

        if position:
            pnl = ((price - entry_price) / entry_price * LEVERAGE * BET_AMOUNT) * (1 if position == "buy" else -1)
            capital += pnl
            realized_pnl += pnl
            send_telegram(f"[CLOSE] {position.upper()} | PnL: {pnl:.2f} USDT")

        entry_price = price
        position = signal
        place_order(signal, price)
        send_telegram(f"[{signal.upper()}] Entrée à {price:.2f}")

        with open(STATE_FILE, "w") as f:
            json.dump({"time": datetime.now().isoformat(), "capital": capital, "realized_pnl": realized_pnl, "position": position}, f)

        time.sleep(FETCH_INTERVAL)

if __name__ == "__main__":
    print("🟢 Bot prêt. En attente de signal webhook...")
    threading.Thread(target=trading_loop).start()
    app.run(host="127.0.0.1", port=5000)
