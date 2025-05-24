import os
import requests
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    print("Erreur : le token Telegram n'est pas défini dans le fichier .env")
    exit(1)

def get_chat_id():
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if data["ok"]:
            results = data.get("result", [])
            if results:
                last_message = results[-1]
                chat_id = last_message["message"]["chat"]["id"]
                print(f"Ton chat_id est : {chat_id}")
                return chat_id
            else:
                print("Aucun message reçu par le bot. Envoie-lui un message dans Telegram puis relance ce script.")
                return None
        else:
            print(f"Erreur API Telegram : {data}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la requête HTTP : {e}")
        return None

if __name__ == "__main__":
    get_chat_id()

