# backtest_service.py
import numpy as np
import torch
import logging

from .lstm_model import predict_lstm
from .sentiment_service import get_multi_source_sentiment
from .trends_service import get_trend_score

logger = logging.getLogger(__name__)

MAX_ASSETS       = 10
FEATURES_PER_ASSET = 4


# ---------------------------------------
# SHARPE RATIO
# ---------------------------------------
def calculate_sharpe_ratio(returns, risk_free_rate: float = 0.01) -> float:
    returns = np.array(returns, dtype=np.float64)
    if len(returns) < 2:
        return 0.0

    excess = returns - (risk_free_rate / 252)
    std    = np.std(excess)

    if std == 0 or not np.isfinite(std):
        return 0.0

    sharpe = (np.mean(excess) / std) * np.sqrt(252)
    return float(np.clip(sharpe, -10, 10))  

# ---------------------------------------
# SORTINO RATIO  
# ---------------------------------------
def calculate_sortino_ratio(returns, risk_free_rate: float = 0.01) -> float:
    returns = np.array(returns, dtype=np.float64)
    if len(returns) < 2:
        return 0.0

    excess    = returns - (risk_free_rate / 252)
    downside  = excess[excess < 0]

    if len(downside) == 0:
        return 0.0

    downside_std = np.std(downside)
    if downside_std == 0 or not np.isfinite(downside_std):
        return 0.0

    sortino = (np.mean(excess) / downside_std) * np.sqrt(252)
    return float(np.clip(sortino, -10, 10))


# ---------------------------------------
# MAX DRAWDOWN
# ---------------------------------------
def calculate_max_drawdown(equity_curve) -> float:
    if not equity_curve or len(equity_curve) < 2:
        return 0.0

    curve  = np.array(equity_curve, dtype=np.float64)
    peak   = curve[0]
    max_dd = 0.0

    for value in curve:
        if value > peak:
            peak = value
        if peak > 0:  
            dd     = (peak - value) / peak
            max_dd = max(max_dd, dd)

    return float(max_dd)


# ---------------------------------------
# WIN RATE  
# ---------------------------------------
def calculate_win_rate(daily_returns) -> float:
    if not daily_returns:
        return 0.0
    wins = sum(1 for r in daily_returns if r > 0)
    return round(wins / len(daily_returns), 4)


# ---------------------------------------
# BACKTEST
# ---------------------------------------
def backtest_multi_asset(agent, lstm_model, assets_data: dict) -> dict:

    if agent is None or lstm_model is None:
        return {"error": "Model not initialized"}

    asset_list = list(assets_data.keys())

    if len(asset_list) == 0:
        return {"error": "No assets provided"}

    if len(asset_list) > MAX_ASSETS:
        asset_list = asset_list[:MAX_ASSETS]

    min_length = min(len(assets_data[a]) for a in asset_list)

    if min_length < 10:
        return {"error": "Not enough historical data (need at least 10 days)"}

    sentiment_cache = {}
    trend_cache     = {}
    for asset in asset_list:
        try:
            sentiment_cache[asset] = get_multi_source_sentiment(asset)
        except Exception:
            sentiment_cache[asset] = (0.0, 0.0)
        try:
            trend_cache[asset] = get_trend_score(asset)
        except Exception:
            trend_cache[asset] = 0.5

    initial_capital = 10_000
    capital         = float(initial_capital)
    equity_curve    = []
    daily_returns   = []

    for i in range(5, min_length - 1):

        state = []

        for asset in asset_list:
            prices  = assets_data[asset]
            current = float(prices[i])

            try:
                price_ratio = float(prices[i]) / (float(prices[i - 1]) + 1e-6)
            except Exception:
                price_ratio = 1.0

            news_avg, news_vol = sentiment_cache[asset]
            trend_score        = trend_cache[asset]

            state.extend([
                float(np.clip(price_ratio, 0.5, 2.0)),  # normalized price momentum
                float(news_avg),
                float(news_vol),
                float(trend_score),
            ])

        remaining = MAX_ASSETS - len(asset_list)
        state.extend([0.0, 0.0, 0.0, 0.0] * remaining)

        state = [v if np.isfinite(v) else 0.0 for v in state]

        state_tensor = torch.FloatTensor(state).unsqueeze(0)

        # Portfolio allocation via DQN
        try:
            weights = agent.predict(state_tensor)
            if weights is None:
                raise ValueError("DQN returned None")
        except Exception as e:
            logger.warning(f"DQN backtest step {i} failed: {e} — using uniform weights")
            weights = np.ones(len(asset_list)) / len(asset_list)

        weights = weights[:len(asset_list)]
        weights = weights / np.sum(weights) if np.sum(weights) > 0 else np.ones(len(asset_list)) / len(asset_list)

        # Compute portfolio daily return
        daily_return = 0.0
        for idx, asset in enumerate(asset_list):
            prices = assets_data[asset]
            p_now  = float(prices[i])
            p_next = float(prices[i + 1])

            if p_now == 0:
                continue

            r             = (p_next - p_now) / p_now
            r             = float(np.clip(r, -0.5, 0.5)) 
            daily_return += weights[idx] * r

        if not np.isfinite(daily_return):
            daily_return = 0.0

        capital *= (1 + daily_return)
        equity_curve.append(round(capital, 2))
        daily_returns.append(daily_return)

    if not equity_curve:
        return {"error": "Backtest produced no results"}

    total_return = (capital - initial_capital) / initial_capital

    return {
        "initial_capital":      initial_capital,
        "final_portfolio_value": round(capital, 2),
        "total_return":          round(total_return, 4),
        "total_return_pct":      round(total_return * 100, 2),   
        "sharpe_ratio":          round(calculate_sharpe_ratio(daily_returns), 4),
        "sortino_ratio":         round(calculate_sortino_ratio(daily_returns), 4),  
        "max_drawdown":          round(calculate_max_drawdown(equity_curve), 4),
        "max_drawdown_pct":      round(calculate_max_drawdown(equity_curve) * 100, 2),   
        "win_rate":              calculate_win_rate(daily_returns),  
        "total_days":            len(equity_curve),                  
        "assets_traded":         asset_list,                         
        "equity_curve":          [round(v, 2) for v in equity_curve],
    }