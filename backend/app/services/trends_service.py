# trends_service.py
from pytrends.request import TrendReq  # type: ignore
import time
import logging
import threading

logger = logging.getLogger(__name__)

# -----------------------------
# CACHE
# -----------------------------
CACHE       = {}
CACHE_TTL   = 60 * 60       # 1 hour
_cache_lock = threading.Lock()  

SYMBOL_QUERY_MAP = {
    "AAPL":         "Apple stock",
    "TSLA":         "Tesla stock",
    "MSFT":         "Microsoft stock",
    "NVDA":         "Nvidia stock",
    "AMZN":         "Amazon stock",
    "GOOGL":        "Google stock",
    "META":         "Meta stock",
    "NFLX":         "Netflix stock",
    "INFY.NS":      "Infosys stock",
    "TCS.NS":       "TCS stock",
    "RELIANCE.NS":  "Reliance Industries stock",
    "HDFCBANK.NS":  "HDFC Bank stock",
    "ICICIBANK.NS": "ICICI Bank stock",
    "WIPRO.NS":     "Wipro stock",
}


# -----------------------------
# CLEAN CACHE
# -----------------------------
def clean_cache(current_time: float):
    with _cache_lock:
        expired = [k for k, v in CACHE.items() if current_time - v["timestamp"] > CACHE_TTL]
        for k in expired:
            del CACHE[k]


# -----------------------------
# MAIN FUNCTION
# -----------------------------
def get_trend_score(symbol: str) -> float:

    symbol       = symbol.upper().strip()
    current_time = time.time()

    clean_cache(current_time)

    # CACHE HIT
    with _cache_lock:
        if symbol in CACHE:
            cached = CACHE[symbol]
            if current_time - cached["timestamp"] < CACHE_TTL:
                logger.debug(f" Trend cache hit for {symbol}")
                return cached["value"]

    query = SYMBOL_QUERY_MAP.get(symbol, symbol.replace(".NS", "") + " stock")

    # FETCH WITH RETRIES
    for attempt in range(3):  
        try:
            pytrends = TrendReq(hl="en-US", tz=330, timeout=(10, 25))  

            pytrends.build_payload([query], timeframe="now 7-d")
            data = pytrends.interest_over_time()

            if data.empty or query not in data.columns:
                logger.warning(f" Empty trend data for {symbol} (query: {query})")
                value = 0.5  
            else:
                raw   = float(data[query].mean())        
                value = round(raw / 100.0, 4)            
                value = float(max(0.0, min(1.0, value))) 

            with _cache_lock:
                CACHE[symbol] = {"value": value, "timestamp": current_time}

            logger.info(f" Trend score for {symbol}: {value}")
            return value

        except Exception as e:
            logger.warning(f" Trend fetch attempt {attempt + 1}/3 failed for {symbol}: {e}")
            time.sleep(2 ** attempt) 
    # FINAL FALLBACK
    logger.error(f" Trend completely failed for {symbol} — using neutral fallback")
    return 0.5  #  FIXED: neutral 0.5 instead of pessimistic 0.4