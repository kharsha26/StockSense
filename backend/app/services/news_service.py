# news_service.py
from dotenv import load_dotenv
load_dotenv()
import requests
import os
import logging

logger = logging.getLogger(__name__)

NEWS_API_KEY = os.getenv("NEWS_API_KEY")

SYMBOL_NAME_MAP = {
    "AAPL":        "Apple",
    "TSLA":        "Tesla",
    "MSFT":        "Microsoft",
    "NVDA":        "Nvidia",
    "AMZN":        "Amazon",
    "GOOGL":       "Google",
    "META":        "Meta",
    "NFLX":        "Netflix",
    "INFY.NS":     "Infosys",
    "TCS.NS":      "TCS Tata Consultancy",
    "RELIANCE.NS": "Reliance Industries",
    "HDFCBANK.NS": "HDFC Bank",
    "ICICIBANK.NS":"ICICI Bank",
    "WIPRO.NS":    "Wipro",
}


def fetch_news(symbol: str) -> list:

    NEWS_API_KEY = os.getenv("NEWS_API_KEY")

    if not NEWS_API_KEY:
        logger.warning(" NEWS_API_KEY not set in .env")
        return []

    try:
        symbol = symbol.upper().strip()

        name  = SYMBOL_NAME_MAP.get(symbol, symbol.replace(".NS", ""))
        query = f"{name} stock market"

        url = (
            "https://newsapi.org/v2/everything"
            f"?q={requests.utils.quote(query)}"   
            f"&pageSize=30"                         
            f"&language=en"
            f"&sortBy=publishedAt"
            f"&apiKey={NEWS_API_KEY}"
        )

        response = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=8,   
        )

        if response.status_code == 401:
            logger.error(" NEWS_API_KEY is invalid or expired")
            return []

        if response.status_code == 429:
            logger.warning(" News API rate limit hit")
            return []

        if response.status_code != 200:
            logger.warning(f" News API HTTP error: {response.status_code}")
            return []

        data = response.json()

        if data.get("status") != "ok":
            logger.warning(f" News API error response: {data.get('message', data)}")
            return []

        articles = data.get("articles", [])

        headlines = []
        for a in articles:
            text = a.get("title") or a.get("description")
            if text and text.lower() != "[removed]":  
                headlines.append(text.strip())

        seen = set()
        unique_headlines = []
        for h in headlines:
            if h not in seen:
                seen.add(h)
                unique_headlines.append(h)

        logger.info(f" {symbol} — fetched {len(unique_headlines)} headlines")
        return unique_headlines

    except requests.exceptions.Timeout:
        logger.error(f" News API timeout for {symbol}")
        return []

    except Exception as e:
        logger.error(f" News fetch error for {symbol}: {e}")
        return []