from datetime import datetime, timedelta import pandas as pd import time import os from selenium import webdriver from selenium.webdriver.chrome.service import Service from selenium.webdriver.common.by import By from selenium.webdriver.support.ui import WebDriverWait from selenium.webdriver.support import expected_conditions as EC from webdriver_manager.chrome import ChromeDriverManager from dotenv import load_dotenv

=== Chargement des configs ===

load_dotenv() SYMBOL = os.getenv("SYMBOL", "SETHUSDT") INTERVAL = int(os.getenv("INTERVAL", 1))  # en minutes DURATION_DAYS = int(os.getenv("DOWNLOAD_DAYS", 1))  # nombre de jours à télécharger

=== Scraping price live pour stockage ===

def get_live_price(): url = f"https://www.bitgetapp.com/fr/futures/susdt/{SYMBOL}" options = webdriver.ChromeOptions() options.add_argument("--no-sandbox") options.add_argument("--disable-dev-shm-usage") options.add_experimental_option("detach", True) driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

try:
    driver.get(url)
    time.sleep(5)
    element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "ivNC5KKsEsgBCGtqwVhC"))
    )
    price = float(element.text.replace(",", ""))
    return price
except Exception as e:
    print(f"Erreur scraping : {e}")
    return None
finally:
    driver.quit()

=== Boucle de téléchargement ===

if name == "main": print(f"📥 Début téléchargement données live pour {SYMBOL}") interval_sec = INTERVAL * 60 end_time = datetime.utcnow() start_time = end_time - timedelta(days=DURATION_DAYS)

rows = []
now = datetime.utcnow()

while now < end_time:
    price = get_live_price()
    if price:
        row = {
            "open_time": datetime.utcnow(),
            "open": price,
            "high": price,
            "low": price,
            "close": price,
            "volume": 1
        }
        rows.append(row)
        print(f"✅ {row['open_time']} | Prix : {price}")
    else:
        print("⚠ Échec récupération prix")

    time.sleep(interval_sec)
    now = datetime.utcnow()

df = pd.DataFrame(rows)
if not df.empty:
    filename = f"scraped_{SYMBOL}_{INTERVAL}m.csv"
    df.to_csv(filename, index=False)
    print(f"✅ Données sauvegardées dans '{filename}'")
else:
    print("❌ Aucune donnée enregistrée.")
