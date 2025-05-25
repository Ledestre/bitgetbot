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

# Configuration de base
LEVERAGE = int(os.getenv("LEVERAGE", 50))
INITIAL_CAPITAL = float(os.getenv("INITIAL_CAPITAL", 9175.47))
BET_AMOUNT = float(os.getenv("BET_AMOUNT", 100))
FETCH_INTERVAL = int(os.getenv("FETCH_INTERVAL", 60))
STATE_FILE = os.getenv("STATE_FILE", "bot_state.json")

API_KEY = os.getenv("BITGET_API_KEY")
API_SECRET = os.getenv("BITGET_API_SECRET")
API_PASSPHRASE = os.getenv("BITGET_API_PASSPHRASE")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

API_BASE_URL = "https://api.bitget.com"
SYMBOL = "SETHSUSDT"
PRODUCT_TYPE = "SUSDT-FUTURES"

position = None
entry_price = None
capital = INITIAL_CAPITAL
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
    query = '&'.join(f"{k}={v}" for k, v in items)
    return '?' + query

def sign_bitget(method, path, body="", params=None):
    timestamp = get_timestamp()
    request_path = path + parse_params_to_str(params) if method == "GET" and params else path
    pre_hash_str = timestamp + method.upper() + request_path + body
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
        params = {"symbol": SYMBOL, "productType": PRODUCT_TYPE}
        headers = sign_bitget("GET", "/api/v2/mix/market/ticker", params=params)
        full_url = url + parse_params_to_str(params)
        res = requests.get(full_url, headers=headers, timeout=10)
        data = res.json()
        if data.get("code") == "00000":
            return float(data["data"][0]["lastPr"])
        return None
    except Exception as e:
        print(f"[ERREUR] fetch_price : {e}")
        return None

def place_order(side, price):
    url = f"{API_BASE_URL}/api/v2/mix/order/place-order"
    path = "/api/v2/mix/order/place-order"
    tp = round(price * 1.30, 2)
    sl = round(price * 0.85, 2)
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
        "clientOid": get_timestamp(),
        "reduceOnly": "NO",
        "presetStopSurplusPrice": str(tp),
        "presetStopLossPrice": str(sl)
    }
    headers = sign_bitget("POST", path, body=json.dumps(body_dict))
    if DRY_RUN:
        print(f"[SIMULATION] {side.upper()} simulé à {price:.2f}")
        return
    try:
        res = requests.post(url, headers=headers, data=json.dumps(body_dict))
        print(f"[ORDER] {side.upper()} @ {price:.2f} | Status: {res.status_code}")
    except Exception as e:
        print(f"[ORDER] Erreur : {e}")

@app.route("/webhook", methods=["POST"])
def webhook():
    global last_signal
    try:
        data = request.get_json(force=True)
        if data.get("signal") in ["buy", "sell"]:
            with signal_lock:
                last_signal = data["signal"]
            return "OK", 200
        return "Signal invalide", 400
    except Exception as e:
        return f"Erreur : {str(e)}", 500

def trading_loop():
    global position, entry_price, capital, realized_pnl, last_signal, running
    send_telegram("Bot Bitget lancé.")
    try:
        while running:
            with signal_lock:
                signal = last_signal
                last_signal = None
            price = fetch_price()
            if not signal or not price:
                time.sleep(FETCH_INTERVAL)
                continue
            if position and ((price - entry_price) / entry_price) * (1 if position == "buy" else -1) <= -0.15:
                pnl = ((price - entry_price) / entry_price) * capital * LEVERAGE
                capital += pnl
                realized_pnl += pnl
                send_telegram(f"❌ STOP LOSS | PnL: {pnl:.2f} USDT")
                position = None
                continue
            if signal == position:
                continue
            if signal == "buy":
                if position == "sell":
                    pnl = (entry_price - price) / entry_price * capital * LEVERAGE
                    capital += pnl
                    realized_pnl += pnl
                    send_telegram(f"[EXIT SHORT] PnL: {pnl:.2f} USDT")
                entry_price = price
                position = "buy"
                place_order("buy", price)
                send_telegram(f"[BUY] Entrée long à {price:.2f}")
            elif signal == "sell":
                if position == "buy":
                    pnl = (price - entry_price) / entry_price * capital * LEVERAGE
                    capital += pnl
                    realized_pnl += pnl
                    send_telegram(f"[EXIT LONG] PnL: {pnl:.2f} USDT")
                entry_price = price
                position = "sell"
                place_order("sell", price)
                send_telegram(f"[SELL] Entrée short à {price:.2f}")
            with open(STATE_FILE, "w") as f:
                json.dump({"time": datetime.now().isoformat(), "capital": capital, "realized_pnl": realized_pnl, "position": position}, f)
            time.sleep(FETCH_INTERVAL)
    except KeyboardInterrupt:
        running = False
        send_telegram("Bot arrêté proprement")

if __name__ == "__main__":
    print("🟢 Bot prêt. En attente de signal webhook...")
    trading_thread = threading.Thread(target=trading_loop)
    trading_thread.start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
    trading_thread.join()
