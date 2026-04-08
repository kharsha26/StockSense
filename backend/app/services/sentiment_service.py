# sentiment_service.py
import numpy as np
import time
import logging
import threading
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from .news_service import fetch_news

logger = logging.getLogger(__name__)

# -------------------------------------------------
# Sentiment Analyzer
# -------------------------------------------------
analyzer = SentimentIntensityAnalyzer()

# -------------------------------------------------
# In-Memory Cache
# -------------------------------------------------
CACHE      = {}
CACHE_TTL  = 60 * 30        # 30 minutes
_cache_lock = threading.Lock() 


# -------------------------------------------------
# CACHE CLEANUP
# -------------------------------------------------
def clean_cache(current_time: float):
    with _cache_lock:
        expired = [k for k, v in CACHE.items() if current_time - v["timestamp"] > CACHE_TTL]
        for k in expired:
            del CACHE[k]
        if expired:
            logger.debug(f" Cache cleaned: removed {len(expired)} expired entries")


# -------------------------------------------------
# Analyze Headlines
# -------------------------------------------------
def analyze_headlines(headlines: list, symbol: str = "") -> tuple:

    scores = []

    for text in headlines:
        try:
            text = str(text).strip()
            if not text:
                continue

            sentiment = analyzer.polarity_scores(text)
            score     = sentiment["compound"]

            if abs(score) > 0.05:
                scores.append(score)

        except Exception as e:
            logger.warning(f" {symbol} sentiment parse error: {e}")

    if not scores:
        return 0.0, 0.0

    avg_sentiment        = float(np.mean(scores))
    sentiment_volatility = float(np.std(scores))

    avg_sentiment = float(np.clip(avg_sentiment, -1.0, 1.0))

    logger.debug(f" {symbol} sentiment — avg: {avg_sentiment:.4f}, vol: {sentiment_volatility:.4f}, n={len(scores)}")

    return avg_sentiment, sentiment_volatility


# -------------------------------------------------
# Multi-Source Sentiment with Caching
# -------------------------------------------------
def get_multi_source_sentiment(symbol: str) -> tuple:

    symbol       = symbol.upper().strip()
    current_time = time.time()

    clean_cache(current_time)

    # CACHE HIT
    with _cache_lock:
        if symbol in CACHE:
            cached = CACHE[symbol]
            if current_time - cached["timestamp"] < CACHE_TTL:
                logger.debug(f" Cache hit for {symbol}")
                return cached["avg"], cached["vol"]

    # FETCH NEWS
    try:
        headlines = fetch_news(symbol)
    except Exception as e:
        logger.error(f" News fetch failed for {symbol}: {e}")
        return 0.0, 0.0

    if not headlines:
        logger.warning(f" No headlines found for {symbol}")
        return 0.0, 0.0

    headlines = headlines[:30]

    avg, vol = analyze_headlines(headlines, symbol)

    # CACHE STORE
    with _cache_lock:
        CACHE[symbol] = {
            "avg":       avg,
            "vol":       vol,
            "timestamp": current_time,
            "count":     len(headlines),  
        }

    return avg, vol