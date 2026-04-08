# predict.py
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
import torch
import numpy as np
import traceback
import yfinance as yf

from ..services.market_service import (
    get_stock_features,
    get_company_stats
)
from ..services.lstm_model import predict_lstm
from ..services.sentiment_service import get_multi_source_sentiment
from ..services.trends_service import get_trend_score

router = APIRouter()

MAX_ASSETS       = 10
FEATURES_PER_ASSET = 4


# ---------------------------------------
# SYMBOL NORMALIZATION
# ---------------------------------------
def normalize_symbol(symbol: str) -> str:
    symbol = symbol.upper().strip()
    mapping = {
        "INFY":      "INFY.NS",
        "TCS":       "TCS.NS",
        "RELIANCE":  "RELIANCE.NS",
        "HDFCBANK":  "HDFCBANK.NS",
        "ICICIBANK": "ICICIBANK.NS",
        "WIPRO":     "WIPRO.NS",
        "INFOSYS":   "INFY.NS",
    }
    return mapping.get(symbol, symbol)


# ---------------------------------------
# ANALYST RECOMMENDATION (yfinance)
# ---------------------------------------
def get_analyst_decision(symbol: str) -> str | None:
    try:
        stock = yf.Ticker(symbol)
        rec   = stock.recommendations

        if rec is None or rec.empty:
            return None

        # Use last 10 recommendation entries
        latest = rec.tail(10)

        # yfinance columns: strongBuy, buy, hold, sell, strongSell
        required = {'strongBuy', 'buy', 'hold', 'sell', 'strongSell'}
        if not required.issubset(set(latest.columns)):
            return None

        strong_buy  = int(latest['strongBuy'].sum())
        buy         = int(latest['buy'].sum())
        hold        = int(latest['hold'].sum())
        sell        = int(latest['sell'].sum())
        strong_sell = int(latest['strongSell'].sum())

        total_buy  = strong_buy + buy
        total_sell = sell + strong_sell

        print(f"{symbol} analyst | BUY:{total_buy} HOLD:{hold} SELL:{total_sell}")

        if total_buy > total_sell and total_buy > hold:
            return "BUY"
        elif total_sell > total_buy and total_sell > hold:
            return "SELL"
        else:
            return "HOLD"

    except Exception as e:
        print(f"⚠ Analyst decision failed for {symbol}: {e}")
        return None


# ---------------------------------------
# FALLBACK DECISION (price + sentiment + trend)
# ---------------------------------------
def get_fallback_decision(price_change: float, news_avg: float, trend_score: float) -> str:
    # Price-led
    if price_change > 0.001:
        return "BUY"
    elif price_change < -0.001:
        return "SELL"

    # Sentiment-led
    elif news_avg > 0.1:
        return "BUY"
    elif news_avg < -0.1:
        return "SELL"

    # Trend-led
    elif trend_score > 0.6:
        return "BUY"
    elif trend_score < 0.4:
        return "SELL"

    return "HOLD"


# ---------------------------------------
# REQUEST MODEL
# ---------------------------------------
class PortfolioRequest(BaseModel):
    symbols: List[str]


# ---------------------------------------
# PORTFOLIO PREDICTION
# ---------------------------------------
@router.post("/portfolio-predict")
def portfolio_predict(request: Request, data: PortfolioRequest):

    agent      = request.app.state.agent
    lstm_model = request.app.state.lstm_model

    if agent is None or lstm_model is None:
        return JSONResponse(
            status_code=503,
            content={"success": False, "message": "Model not initialized"}
        )

    symbols       = data.symbols[:MAX_ASSETS]
    state         = []
    asset_outputs = []

    for symbol in symbols:
        try:
            symbol = normalize_symbol(symbol)
            print(f"Processing: {symbol}")

            df = get_stock_features(symbol, period="2y")

            if df is None or df.empty:
                print(f"No data: {symbol}")
                continue

            current_price = float(df["Close"].iloc[-1])

            pred = predict_lstm(lstm_model, df)

            if pred is None or np.isnan(pred):
                print(f"Invalid LSTM output: {symbol}")
                continue

            predicted_price = float(pred)

            news_avg, news_vol = get_multi_source_sentiment(symbol)
            trend_score        = get_trend_score(symbol)
            company_stats      = get_company_stats(symbol)

            price_change = (
                (predicted_price - current_price) / current_price
                if current_price != 0 else 0
            )

            # PRIMARY: use real analyst recommendations from yfinance
            decision = get_analyst_decision(symbol)

            # FALLBACK: use price/sentiment/trend if no analyst data
            if decision is None:
                decision = get_fallback_decision(price_change, news_avg, trend_score)
                print(f"No analyst data for {symbol} — using fallback: {decision}")

            print(f"{symbol} | price_change: {price_change:.4f} | news_avg: {news_avg:.4f} | trend: {trend_score:.4f} | decision: {decision}")

            state.extend([
                float(predicted_price / (current_price + 1e-6)),
                float(news_avg),
                float(news_vol),
                float(trend_score)
            ])

            asset_outputs.append({
                "symbol":                    symbol,
                "current_price":             round(current_price, 2),
                "predicted_price":           round(predicted_price, 2),
                "decision":                  decision,
                "news_sentiment_avg":        round(news_avg, 4),
                "news_sentiment_volatility": round(news_vol, 4),
                "trend_score":               round(trend_score, 4),
                "company_stats":             company_stats,
            })

        except Exception as e:
            print(f"Error processing {symbol}: {e}")
            traceback.print_exc()
            continue

    if len(asset_outputs) == 0:
        return JSONResponse(
            status_code=404,
            content={"success": False, "message": "No valid stocks found"}
        )

    # PAD / TRIM STATE
    expected_size = MAX_ASSETS * FEATURES_PER_ASSET
    if len(state) < expected_size:
        state += [0.0] * (expected_size - len(state))
    else:
        state = state[:expected_size]

    state_tensor = torch.tensor(state, dtype=torch.float32).view(1, expected_size)

    # DQN ALLOCATION WEIGHTS
    try:
        with torch.no_grad():
            logits  = agent.model(state_tensor)
            weights = torch.softmax(logits, dim=-1)[0].cpu().numpy()
    except Exception as e:
        print(f"DQN error: {e}")
        weights = np.ones(len(asset_outputs)) / len(asset_outputs)

    weights = weights[:len(asset_outputs)]
    weights = (
        weights / np.sum(weights)
        if np.sum(weights) > 0
        else np.ones(len(asset_outputs)) / len(asset_outputs)
    )

    for i in range(len(asset_outputs)):
        asset_outputs[i]["allocation_weight"] = round(float(weights[i]), 4)

    return {
        "success":              True,
        "portfolio_allocation": asset_outputs,
        "total_assets":         len(asset_outputs),
    }


# ---------------------------------------
# STOCK HISTORY API (FOR CANDLESTICK CHART)
# ---------------------------------------
@router.get("/stock-history/{symbol}")
def get_stock_history_api(symbol: str, period: str = "3mo"):

    symbol = normalize_symbol(symbol)

    valid_periods = ["1mo", "3mo", "6mo", "1y", "2y", "5y"]
    if period not in valid_periods:
        period = "3mo"

    try:
        stock = yf.Ticker(symbol)
        hist  = stock.history(period=period)

        if hist is None or hist.empty:
            print(f"No history for {symbol}")
            return []

        data = []
        for date, row in hist.iterrows():
            data.append({
                "time":   date.strftime("%Y-%m-%d"),
                "open":   round(float(row["Open"]),   4),
                "high":   round(float(row["High"]),   4),
                "low":    round(float(row["Low"]),    4),
                "close":  round(float(row["Close"]),  4),
                "volume": int(row["Volume"]) if "Volume" in row else 0,
            })

        print(f"Returning {len(data)} candles for {symbol} [{period}]")
        return data

    except Exception as e:
        print(f"Chart error: {e}")
        traceback.print_exc()
        return []