# search.py
from fastapi import APIRouter
import requests
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

HEADERS = {
    "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept":          "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer":         "https://finance.yahoo.com/",
}


@router.get("/search-stock")
def search_stock(q: str):

    if not q or not q.strip():
        return []

    try:
        response = requests.get(
            "https://query1.finance.yahoo.com/v1/finance/search",
            headers=HEADERS,
            params={
                "q":           q.strip(),
                "quotesCount": 10,
                "newsCount":   0,
                "enableFuzzyQuery": True,   
            },
            timeout=8,   # 
        )

        # status check
        if response.status_code != 200:
            logger.warning(f"⚠ Yahoo Finance search returned {response.status_code}")
            return []

        data = response.json()

        results = []
        for item in data.get("quotes", []):
            symbol    = item.get("symbol")
            name      = item.get("shortname") or item.get("longname")
            type_     = item.get("quoteType", "")
            exchange  = item.get("exchange", "")

            if not symbol or not name:
                continue
            if type_ not in ("EQUITY", "ETF", ""):
                continue

            results.append({
                "symbol":   symbol,
                "name":     name,
                "type":     type_,      
                "exchange": exchange,   
            })

        return results

    except requests.exceptions.Timeout:
        logger.error(f"Yahoo Finance search timeout for: {q}")
        return []

    except Exception as e:
        logger.error(f"Search API error for '{q}': {e}")
        return []