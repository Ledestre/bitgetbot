import requests
from bs4 import BeautifulSoup
from textblob import TextBlob
from datetime import datetime, timedelta

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

SOURCES = [
    {
        "name": "CoinTelegraph",
        "url": "https://cointelegraph.com/",
        "parser": lambda soup: soup.select("a.post-card-inline__title-link")
    },
    {
        "name": "Decrypt",
        "url": "https://decrypt.co/",
        "parser": lambda soup: soup.select("a.card-title")
    },
    {
        "name": "Investing",
        "url": "https://www.investing.com/news/cryptocurrency-news",
        "parser": lambda soup: soup.select("article a.title")
    }
]

KEYWORDS = ["ethereum", "eth", "bitcoin", "btc"]
MAX_AGE_DAYS = 15


def get_sentiment(text):
    analysis = TextBlob(text)
    polarity = analysis.sentiment.polarity
    if polarity > 0.1:
        return "positif"
    elif polarity < -0.1:
        return "négatif"
    return "neutre"


def get_recent_crypto_news():
    news = []
    now = datetime.utcnow()

    for source in SOURCES:
        try:
            resp = requests.get(source["url"], headers=HEADERS, timeout=10)
            soup = BeautifulSoup(resp.text, "html.parser")
            articles = source["parser"](soup)

            for tag in articles:
                title = tag.get_text(strip=True)
                url = tag.get("href")

                if not url:
                    continue
                if not url.startswith("http"):
                    url = source["url"].rstrip("/") + "/" + url.lstrip("/")

                title_lower = title.lower()
                if any(k in title_lower for k in KEYWORDS):
                    sentiment = get_sentiment(title)
                    coin = "ETH" if "eth" in title_lower or "ethereum" in title_lower else "BTC"
                    article = {
                        "date": now,
                        "coin": coin,
                        "title": title,
                        "source": source["name"],
                        "summary": title,
                        "sentiment": sentiment,
                        "url": url
                    }
                    # Filtrage temporel (ici on simule une date actuelle car le scraping du temps exact dépend des sites)
                    if article["date"] >= now - timedelta(days=MAX_AGE_DAYS):
                        news.append(article)

        except Exception as e:
            print(f"Erreur sur {source['name']}: {e}")

    return news