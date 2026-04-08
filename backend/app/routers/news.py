# news.py
from fastapi import APIRouter # type: ignore
import requests # type: ignore
import os
import logging
from dotenv import load_dotenv  # type: ignore 

load_dotenv()  # 

logger = logging.getLogger(__name__)
router = APIRouter()

SYMBOL_NAME_MAP = {
    "AAPL":         "Apple",
    "TSLA":         "Tesla",
    "MSFT":         "Microsoft",
    "NVDA":         "Nvidia",
    "AMZN":         "Amazon",
    "GOOGL":        "Google",
    "META":         "Meta",
    "NFLX":         "Netflix",
    "INFY.NS":      "Infosys",
    "TCS.NS":       "TCS Tata Consultancy",
    "RELIANCE.NS":  "Reliance Industries",
    "HDFCBANK.NS":  "HDFC Bank",
    "ICICIBANK.NS": "ICICI Bank",
    "WIPRO.NS":     "Wipro",
}


@router.get("/stock-news/{symbol}")
def get_stock_news(symbol: str):

    NEWS_API_KEY = os.getenv("NEWS_API_KEY")

    if not NEWS_API_KEY:
        logger.warning("⚠ NEWS_API_KEY not set in .env")
        return []

    symbol = symbol.upper().strip()
    name   = SYMBOL_NAME_MAP.get(symbol, symbol.replace(".NS", ""))
    query  = f"{name} stock market"

    try:
        response = requests.get(
            "https://newsapi.org/v2/everything",
            params={
                "q":        query,
                "language": "en",
                "sortBy":   "publishedAt",
                "pageSize": 10,
                "apiKey":   NEWS_API_KEY,
            },
            timeout=8,
        )

        if response.status_code == 401:
            logger.error("NEWS_API_KEY invalid or expired — regenerate at newsapi.org")
            return []
        if response.status_code == 426:
            logger.warning("NewsAPI requires HTTPS upgrade on this plan")
            return []
        if response.status_code == 429:
            logger.warning("News API rate limit hit")
            return []
        if response.status_code != 200:
            logger.warning(f"News API HTTP error: {response.status_code} — {response.text}")
            return []

        data = response.json()

        if data.get("status") != "ok":
            logger.warning(f"News API error: {data.get('message')}")
            return []

        articles = []
        for item in data.get("articles", []):
            title  = item.get("title", "")
            url    = item.get("url", "")
            source = item.get("source", {}).get("name", "Unknown")

            if not title or title == "[Removed]" or not url:
                continue

            articles.append({
                "title":  title,
                "url":    url,
                "source": source,
            })

        logger.info(f"{symbol} — returned {len(articles)} articles")
        return articles

    except requests.exceptions.Timeout:
        logger.error(f"News API timeout for {symbol}")
        return []
    except Exception as e:
        logger.error(f"News router error for {symbol}: {e}")
        return []