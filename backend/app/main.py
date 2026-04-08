# main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import predict, portfolio, backtest, search, news, market, retrain, auth, metrics
from .services.dqn_agent import DQNAgent
from .services.market_service import get_stock_features, get_stock_history
from .services.lstm_model import train_lstm, load_lstm, save_lstm
from .services.training_service import train_dqn_multi_asset
from dotenv import load_dotenv
from .database import init_db
import os
import pandas as pd

load_dotenv()

MAX_ASSETS       = 10
FEATURES_PER_ASSET = 4
STATE_DIM        = MAX_ASSETS * FEATURES_PER_ASSET
ACTION_DIM       = MAX_ASSETS

agent = DQNAgent(STATE_DIM, ACTION_DIM)

TRAIN_SYMBOLS = [
    # US stocks
    "AAPL", "TSLA", "MSFT", "NVDA", "AMZN",
    "GOOGL", "META", "NFLX", "JPM", "AMD",
    # Indian stocks
    "INFY.NS", "TCS.NS", "RELIANCE.NS", "HDFCBANK.NS",
    "WIPRO.NS", "ICICIBANK.NS", "HINDUNILVR.NS", "BAJFINANCE.NS",
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Backend Starting...")
    init_db()
    print("Database tables ready")

    # ── LSTM ──────────────────────────────────────
    lstm_model = load_lstm()

    if lstm_model is None:
        print(" Training LSTM from scratch...")
        dfs = []
        for s in TRAIN_SYMBOLS:
            df = get_stock_features(s, period="5y")
            if df is not None:
                dfs.append(df)
                print(f"  {s} — {len(df)} rows")

        if len(dfs) == 0:
            print(" No data for LSTM training")
            lstm_model = None
        else:
            combined   = pd.concat(dfs)
            lstm_model = train_lstm(combined)
            save_lstm(lstm_model)
            print(" LSTM trained and saved")
    else:
        print("LSTM loaded from disk")

    # ── DQN ───────────────────────────────────────
    dqn_loaded = agent.load()

    if not dqn_loaded:
        print("🏋 Training DQN from scratch...")
        assets_prices = {}

        for s in TRAIN_SYMBOLS[:MAX_ASSETS]:
            prices = get_stock_history(s, period="2y")
            if prices and len(prices) >= 20:
                assets_prices[s] = prices
                print(f"   {s} — {len(prices)} price points")

        if assets_prices:
            result = train_dqn_multi_asset(agent, assets_prices, episodes=10)
            print(f" DQN trained — avg_reward: {result.get('avg_reward')}, steps: {result.get('final_train_steps')}")
        else:
            print("No price data for DQN training — using random weights")
    else:
        print("DQN loaded from disk")

    app.state.agent      = agent
    app.state.lstm_model = lstm_model

    print(" Backend ready")
    yield
    print("Backend shutting down...")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {"message": "TradeMind API is running"}


app.include_router(predict.router,   prefix="/api")
app.include_router(portfolio.router, prefix="/api")
app.include_router(backtest.router,  prefix="/api")
app.include_router(search.router,    prefix="/api")
app.include_router(news.router,      prefix="/api")
app.include_router(market.router,    prefix="/api")
app.include_router(retrain.router,   prefix="/api")
app.include_router(auth.router,      prefix="/api")
app.include_router(metrics.router,    prefix="/api")