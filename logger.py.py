import os
import sys
import subprocess
import time
import json
import logging
from logging.handlers import RotatingFileHandler
import pandas as pd
from datetime import datetime, timezone
from dotenv import load_dotenv
from tradingview_ta import TA_Handler, Interval
import requests

# === Installation automatique des dépendances ===
REQUIRED_PACKAGES = [
    "python-dotenv",
    "requests",
    "pandas",
    "tradingview-ta",
    "numpy",
    "flask",
    "psutil"
]

for package in REQUIRED_PACKAGES:
    try:
        __import__(package.replace('-', '_'))
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# === Logger avancé ===
def setup_logger(name: str = "bot", level=logging.INFO) -> logging.Logger:
    logs_dir = "logs"
    os.makedirs(logs_dir, exist_ok=True)
    today = datetime.utcnow().strftime("%Y-%m-%d")
    log_file = os.path.join(logs_dir, f"bot_{today}.log")

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    file_handler = RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=5, encoding='utf-8')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.propagate = False

    return logger

log = setup_logger()

# === Environnement ===
load_dotenv()

TV_SYMBOL = os.getenv("TV_SYMBOL", "ETHUSDT.P")
FETCH_INTERVAL = int(os.getenv("FETCH_INTERVAL", 60))
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"
HISTORICAL_DATA_FILE = os.getenv("HISTORICAL_DATA_FILE", "historical_prices.csv")
STATE_FILE = os.getenv("STATE_FILE", "bot_state.json")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

LEVERAGE = 50
current_bet = 70

STOP_LOSS_INITIAL = 0.15
STOP_GAIN_RULES = [
    (0.13, 0.00, 0.20),
    (0.15, 0.02, 0.20),
    (0.17, 0.04, 0.23),
    (0.21, 0.13, 0.24),
    (0.25, 0.16, 0.27),
    (0.30, 0.19, 0.30),
]

position = None
entry_price = None
realized_pnl = 0.0
stop_gain_price = None
take_profit_price = None

def send_telegram_message(text):
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        try:
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                data={"chat_id": TELEGRAM_CHAT_ID, "text": text}
            )
        except Exception as e:
            log.error(f"Erreur Telegram : {e}")

def update_status_file(signal, price, timestamp):
    with open("bot_status.json", "w") as f:
        json.dump({
            "status": "running",
            "last_signal": signal or "None",
            "last_price": round(price, 2),
            "last_update": timestamp.isoformat(),
            "interval_seconds": FETCH_INTERVAL
        }, f, indent=2)

def fetch_live_price():
    try:
        handler = TA_Handler(
            symbol=TV_SYMBOL, screener="crypto", exchange="BITGET", interval=Interval.INTERVAL_1_MINUTE
        )
        return {
            "timestamp": datetime.now(timezone.utc),
            "close": handler.get_analysis().indicators["close"]
        }
    except Exception as e:
        log.error(f"Erreur TradingView : {e}")
        return None

def load_historical_data():
    if os.path.exists(HISTORICAL_DATA_FILE):
        df = pd.read_csv(HISTORICAL_DATA_FILE, parse_dates=["timestamp"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        return df
    return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])

def save_historical_data(df):
    df.to_csv(HISTORICAL_DATA_FILE, index=False)
    log.info(f"💾 {len(df)} bougies sauvegardées")

def update_stop_levels(price):
    global stop_gain_price, take_profit_price
    if not entry_price or not position:
        return

    roi = (price - entry_price) / entry_price if position == "buy" else (entry_price - price) / entry_price

    for threshold, new_sg, new_tp in STOP_GAIN_RULES:
        if roi >= threshold:
            stop_gain_price = entry_price * (1 + new_sg) if position == "buy" else entry_price * (1 - new_sg)
            take_profit_price = entry_price * (1 + new_tp) if position == "buy" else entry_price * (1 - new_tp)

def check_exit(price):
    global position, entry_price, stop_gain_price, take_profit_price, realized_pnl, current_bet
    if not entry_price:
        return False

    roi = (price - entry_price) / entry_price if position == "buy" else (entry_price - price) / entry_price
    pnl = roi * entry_price * LEVERAGE * current_bet
    reason = None

    if stop_gain_price and ((position == "buy" and price <= stop_gain_price) or (position == "sell" and price >= stop_gain_price)):
        reason = "🔐 Stop Gain"
    elif take_profit_price and ((position == "buy" and price >= take_profit_price) or (position == "sell" and price <= take_profit_price)):
        reason = "🎯 Take Profit"
    elif roi <= -STOP_LOSS_INITIAL:
        reason = "⛔ Stop Loss"

    if reason:
        realized_pnl += pnl
        if pnl > 0 and current_bet < 200:
            current_bet = min(current_bet + 15, 200)
        elif pnl < 0 and current_bet > 30:
            current_bet = max(current_bet - 10, 30)

        send_telegram_message(f"{reason} {position.upper()} à {price:.2f} | P&L : {pnl:.2f} USD")
        log.info(f"{reason} à {price:.2f} | P&L : {pnl:.2f}")
        reset_position()
        return True
    return False

def reset_position():
    global position, entry_price, stop_gain_price, take_profit_price
    position = None
    entry_price = None
    stop_gain_price = None
    take_profit_price = None

def open_position(signal, price):
    global position, entry_price
    position = signal
    entry_price = price
    send_telegram_message(f"📈 Nouvelle position {signal.upper()} à {price:.2f} | Mise : {current_bet}$ | Levier : {LEVERAGE}x")
    log.info(f"📈 Nouvelle position {signal.upper()} à {price:.2f} | Mise : {current_bet}$ | Levier : {LEVERAGE}x")

def get_utbot_signal(df):
    if len(df) < 7:
        return None
    recent_close = df["close"].iloc[-1]
    highest = df["high"].iloc[-7:-1].max()
    lowest = df["low"].iloc[-7:-1].min()
    if recent_close > highest:
        return "buy"
    elif recent_close < lowest:
        return "sell"
    return None

def transfer_excess_to_spot():
    capital = realized_pnl + current_bet
    if capital >= 500:
        send_telegram_message(f"Transfert de 250$ vers le compte spot (Capital = {capital:.2f}$)")
        log.info(f"Transfert simulé de 250$ vers le compte spot")

def place_order(signal, price, timestamp):
    if check_exit(price):
        return
    if signal is None:
        return

    if position is None:
        open_position(signal, price)
    elif signal != position:
        if check_exit(price):
            open_position(signal, price)

    update_status_file(signal, price, timestamp)

    with open(STATE_FILE, "w") as f:
        json.dump({
            "timestamp": timestamp.isoformat(),
            "last_price": price,
            "position": position,
            "entry_price": entry_price,
            "realized_pnl": realized_pnl,
            "stop_gain_price": stop_gain_price,
            "take_profit_price": take_profit_price
        }, f, indent=2)

    transfer_excess_to_spot()

def trading_loop():
    log.info("🚀 Bot scalping lancé")
    send_telegram_message("🤖 Bot SCALPING actif (SIMULATION)" if DRY_RUN else "🤖 Bot LIVE")
    hist_df = load_historical_data()

    while True:
        live = fetch_live_price()
        if not live:
            time.sleep(FETCH_INTERVAL)
            continue

        price = live["close"]
        timestamp = live["timestamp"]

        if hist_df.empty or timestamp > hist_df["timestamp"].max():
            row = {
                "timestamp": timestamp,
                "open": price,
                "high": price,
                "low": price,
                "close": price,
                "volume": 1
            }
            hist_df = pd.concat([hist_df, pd.DataFrame([row])], ignore_index=True)
            save_historical_data(hist_df)

        signal = get_utbot_signal(hist_df)
        update_stop_levels(price)
        log.info(f"📊 Prix : {price:.2f} | Signal : {signal or 'Aucun'} | Position : {position or 'Aucune'}")
        place_order(signal, price, timestamp)
        time.sleep(FETCH_INTERVAL)

if __name__ == "__main__":
    trading_loop()

