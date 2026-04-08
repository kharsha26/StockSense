# market_service.py
import pandas as pd
import numpy as np
import yfinance as yf
import time


# ---------------------------------------
# STOCK FEATURES (WITH FLEXIBLE PERIOD)
# ---------------------------------------
def get_stock_features(symbol: str, period: str = "2yr"):

    try:
        symbol = symbol.upper().strip()

        df = None

        for attempt in range(3):
            try:
                df = yf.Ticker(symbol).history(period=period)
                if not df.empty:
                    break
                print(f" Empty data for {symbol}, retry {attempt + 1}...")
                time.sleep(1.5)
            except Exception as e:
                print(f" Fetch attempt {attempt + 1} failed for {symbol}: {e}")
                time.sleep(1.5)

        if df is None or df.empty:
            print(f" No data returned for {symbol}")
            return None

        if len(df) < 30:
            print(f" Not enough rows for {symbol}: got {len(df)}")
            return None

        df = df.copy()

        if "Close" not in df.columns:
            print(f" Missing Close column for {symbol}")
            return None

        # ---------------------------------------
        # FEATURE ENGINEERING
        # ---------------------------------------

        # RETURNS
        df["returns"] = df["Close"].pct_change()

        # MOVING AVERAGES
        df["ma10"] = df["Close"].rolling(10).mean()
        df["ma50"] = df["Close"].rolling(min(50, len(df) // 2)).mean()  
        # RSI
        delta = df["Close"].diff()
        gain  = delta.where(delta > 0, 0).rolling(14).mean()
        loss  = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs    = gain / (loss + 1e-6)
        df["rsi"] = 100 - (100 / (1 + rs))

        # VOLATILITY
        df["volatility"] = df["returns"].rolling(10).std()

        ema12        = df["Close"].ewm(span=12, adjust=False).mean()
        ema26        = df["Close"].ewm(span=26, adjust=False).mean()
        df["macd"]   = ema12 - ema26
        df["signal"] = df["macd"].ewm(span=9, adjust=False).mean()

        rolling_mean     = df["Close"].rolling(20).mean()
        rolling_std      = df["Close"].rolling(20).std()
        df["bb_upper"]   = rolling_mean + (2 * rolling_std)
        df["bb_lower"]   = rolling_mean - (2 * rolling_std)
        df["bb_position"] = (df["Close"] - df["bb_lower"]) / (df["bb_upper"] - df["bb_lower"] + 1e-6)

        df = df.dropna()

        if len(df) < 10:
            print(f" After indicators, insufficient rows for {symbol}: {len(df)}")
            return None

        print(f" Features ready for {symbol} ({period}) — {len(df)} rows")
        return df

    except Exception as e:
        print(f" Feature error {symbol}: {e}")
        return None


# ---------------------------------------
# COMPANY STATS
# ---------------------------------------
def get_company_stats(symbol: str) -> dict:

    try:
        stock = yf.Ticker(symbol)
        info  = {}

        try:
            info = stock.info or {}
        except Exception as e:
            print(f" Info fetch failed for {symbol}: {e}")

        return {
            "market_cap":    info.get("marketCap"),
            "pe_ratio":      info.get("trailingPE"),
            "52_week_high":  info.get("fiftyTwoWeekHigh"),
            "52_week_low":   info.get("fiftyTwoWeekLow"),
            "sector":        info.get("sector"),
            "industry":      info.get("industry"),
            "name":          info.get("longName") or info.get("shortName"),  
            "exchange":      info.get("exchange"),                            
            "currency":      info.get("currency"),                            
        }

    except Exception as e:
        print(f" Company stats error {symbol}: {e}")
        return {}


# ---------------------------------------
# SIMPLE HISTORY (FOR BACKTEST)
# ---------------------------------------
def get_stock_history(symbol: str, period: str = "2yr"):  
    try:
        symbol = symbol.upper().strip()

        df = yf.Ticker(symbol).history(period=period)

        if df is None or df.empty:
            print(f" No history for {symbol}")
            return None

        if "Close" not in df.columns:
            print(f" Missing Close column for {symbol}")
            return None

        return df["Close"].dropna().tolist()

    except Exception as e:
        print(f" History error {symbol}: {e}")
        return None