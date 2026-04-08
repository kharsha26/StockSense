# retrain.py
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import pandas as pd
import logging

from ..services.market_service import get_stock_features, get_stock_history
from ..services.lstm_model import train_lstm, save_lstm
from ..services.training_service import train_dqn_multi_asset

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_ASSETS   = 10
TRAIN_SYMBOLS = [
    "AAPL", "TSLA", "MSFT", "NVDA", "AMZN",
    "GOOGL", "META", "NFLX", "JPM", "AMD",
    "INFY.NS", "TCS.NS", "RELIANCE.NS", "HDFCBANK.NS",
    "WIPRO.NS", "ICICIBANK.NS", "HINDUNILVR.NS", "BAJFINANCE.NS",
]


@router.post("/retrain")
async def retrain(request: Request):
    lstm_model = request.app.state.lstm_model
    agent      = request.app.state.agent

    results = {}

    # ── Retrain LSTM ──────────────────────────────
    try:
        logger.info(" Retraining LSTM...")
        dfs = []
        for s in TRAIN_SYMBOLS:
            df = get_stock_features(s, period="5y")
            if df is not None:
                dfs.append(df)

        if not dfs:
            return JSONResponse(status_code=500, content={"error": "No data for LSTM training"})

        combined   = pd.concat(dfs)
        lstm_model = train_lstm(combined)
        save_lstm(lstm_model)

        # Update app state
        request.app.state.lstm_model = lstm_model
        results["lstm"] = f" Retrained on {len(dfs)} stocks"
        logger.info(" LSTM retrained")

    except Exception as e:
        logger.error(f" LSTM retrain error: {e}")
        results["lstm"] = f" Failed: {str(e)}"

    # ── Retrain DQN ───────────────────────────────
    try:
        logger.info(" Retraining DQN...")
        assets_prices = {}

        for s in TRAIN_SYMBOLS[:MAX_ASSETS]:
            prices = get_stock_history(s, period="2y")
            if prices and len(prices) >= 20:
                assets_prices[s] = prices

        if not assets_prices:
            results["dqn"] = "No price data available"
        else:
            dqn_result = train_dqn_multi_asset(agent, assets_prices, episodes=5)
            request.app.state.agent = agent
            results["dqn"] = f" Retrained — avg_reward: {dqn_result.get('avg_reward')}"
            logger.info(" DQN retrained")

    except Exception as e:
        logger.error(f" DQN retrain error: {e}")
        results["dqn"] = f" Failed: {str(e)}"

    return {
        "success": True,
        "results": results,
        "message": "Retraining complete — models updated in memory",
    }