# backtest.py
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
import logging

from ..services.market_service import get_stock_history
from ..services.backtest_service import backtest_multi_asset

logger = logging.getLogger(__name__)

router = APIRouter()

MAX_SYMBOLS = 10  # 


class AssetRequest(BaseModel):
    symbols: List[str]


@router.post("/multi-backtest")
def multi_asset_backtest(request: Request, data: AssetRequest):

    agent      = request.app.state.agent
    lstm_model = request.app.state.lstm_model

    if agent is None or lstm_model is None:
        return JSONResponse(
            status_code=503,
            content={"error": "Model not initialized"}
        )

    if not data.symbols:
        return JSONResponse(
            status_code=400,
            content={"error": "No symbols provided"}
        )

    symbols = data.symbols[:MAX_SYMBOLS]

    assets_data = {}
    skipped     = []

    for symbol in symbols:
        symbol = symbol.upper().strip()  

        prices = get_stock_history(symbol)

        # was returning error and aborting entire request on one bad symbol
        # Now skips bad symbols and continues with the rest
        if not prices or len(prices) < 10:
            logger.warning(f"Skipping {symbol} — insufficient data ({len(prices) if prices else 0} rows)")
            skipped.append(symbol)
            continue

        assets_data[symbol] = prices

    if not assets_data:
        return JSONResponse(
            status_code=404,
            content={
                "error":   "No valid symbols found",
                "skipped": skipped,
            }
        )

    try:
        result = backtest_multi_asset(agent, lstm_model, assets_data)
    except Exception as e:
        logger.error(f"Backtest error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Backtest computation failed"}
        )

    if isinstance(result, dict) and skipped:
        result["skipped_symbols"] = skipped

    return result