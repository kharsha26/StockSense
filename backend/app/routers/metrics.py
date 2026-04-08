# metrics.py
from fastapi import APIRouter, Request
from ..services.market_service import get_stock_features
from ..services.lstm_model import predict_lstm
import numpy as np

router = APIRouter()


@router.get("/model-metrics/{symbol}")
def get_model_metrics(symbol: str, request: Request):
    lstm_model = request.app.state.lstm_model

    if lstm_model is None:
        return {"error": "Model not initialized"}

    try:
        df = get_stock_features(symbol.upper(), period="6mo")
        if df is None or df.empty or len(df) < 30:
            return {"error": "Not enough data"}

        # ── Walk-forward validation ──────────────────
        # Use last 30 days as test set, predict each day
        test_size   = 30
        train_df    = df.iloc[:-test_size]
        test_df     = df.iloc[-test_size:]

        actuals     = test_df["Close"].values.tolist()
        predictions = []

        for i in range(test_size):
            # Use data up to this point for prediction
            window = df.iloc[:-(test_size - i)] if i < test_size - 1 else df
            pred   = predict_lstm(lstm_model, window)
            predictions.append(pred if pred else actuals[i])

        actuals     = np.array(actuals,     dtype=np.float64)
        predictions = np.array(predictions, dtype=np.float64)

        # ── Regression metrics ───────────────────────
        rmse = float(np.sqrt(np.mean((actuals - predictions) ** 2)))
        mae  = float(np.mean(np.abs(actuals - predictions)))

        # Normalize by mean price for relative error
        mean_price    = float(np.mean(actuals))
        rmse_pct      = round((rmse / mean_price) * 100, 2)
        mae_pct       = round((mae  / mean_price) * 100, 2)

        # ── Classification metrics ───────────────────
        # Did we predict the correct direction (up/down)?
        actual_dir  = np.sign(np.diff(actuals))
        pred_dir    = np.sign(np.diff(predictions))

        correct     = (actual_dir == pred_dir)
        accuracy    = float(np.mean(correct))

        # Precision, Recall, F1 for "BUY" signal (predicted up)
        tp = float(np.sum((pred_dir == 1) & (actual_dir == 1)))
        fp = float(np.sum((pred_dir == 1) & (actual_dir != 1)))
        fn = float(np.sum((pred_dir != 1) & (actual_dir == 1)))

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1        = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        # ── Backtest metrics ─────────────────────────
        # Simple strategy: buy when predicted up, sell when predicted down
        daily_returns = np.diff(actuals) / actuals[:-1]
        strategy_returns = daily_returns * np.sign(pred_dir)

        backtest_return = float(np.sum(strategy_returns))
        win_rate        = float(np.mean(strategy_returns > 0))

        # Sharpe ratio
        std = np.std(strategy_returns)
        sharpe = float((np.mean(strategy_returns) / std) * np.sqrt(252)) if std > 0 else 0.0

        return {
            "symbol":           symbol.upper(),
            "test_days":        test_size,
            "mean_price":       round(mean_price, 2),

            # Regression
            "rmse":             round(rmse, 4),
            "rmse_pct":         rmse_pct,
            "mae":              round(mae, 4),
            "mae_pct":          mae_pct,

            # Classification
            "accuracy":         round(accuracy, 4),
            "precision":        round(precision, 4),
            "recall":           round(recall, 4),
            "f1_score":         round(f1, 4),

            # Backtest
            "backtest_return":  round(backtest_return * 100, 2),
            "win_rate":         round(win_rate * 100, 2),
            "sharpe_ratio":     round(sharpe, 4),
        }

    except Exception as e:
        return {"error": str(e)}