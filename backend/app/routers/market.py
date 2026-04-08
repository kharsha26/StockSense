# market.py
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from ..services.market_service import get_stock_history, get_stock_features
import logging
import numpy as np

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/stock-stats/{symbol}")
def stock_stats(symbol: str):

    symbol = symbol.upper().strip()
    prices = get_stock_history(symbol)

    if not prices or len(prices) < 2:
        return JSONResponse(
            status_code=404,
            content={"error": f"No price data found for {symbol}"}
        )

    prices_arr = np.array(prices, dtype=np.float64)

    daily_returns = np.diff(prices_arr) / (prices_arr[:-1] + 1e-6)

    return {
        "symbol":          symbol,
        "current_price":   round(float(prices_arr[-1]), 2),
        "price_7d_ago":    round(float(prices_arr[-min(7,  len(prices_arr))]), 2),
        "price_30d_ago":   round(float(prices_arr[-min(30, len(prices_arr))]), 2),
        "high_52w":        round(float(np.max(prices_arr)), 2),
        "low_52w":         round(float(np.min(prices_arr)), 2),
        "avg_price":       round(float(np.mean(prices_arr)), 2),
        "volatility_30d":  round(float(np.std(daily_returns[-30:])) * np.sqrt(252), 4),
        "data_points":     len(prices),
    }