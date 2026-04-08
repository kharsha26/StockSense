# StockSense 📈

A full-stack stock analysis platform powered by LSTM price prediction, DQN portfolio allocation, and real-time sentiment analysis.

![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110-green?style=flat-square&logo=fastapi)
![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react)
![PyTorch](https://img.shields.io/badge/PyTorch-2.2-EE4C2C?style=flat-square&logo=pytorch)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

---

## 🖥️ Demo

| Homepage | Analysis Dashboard |
|---|---|
| Real-time ticker, features overview | Candlestick chart, ML prediction, sentiment gauge |

---

## ✨ Features

- **Candlestick Charts** — Interactive OHLCV charts with 1M / 3M / 6M / 1Y period selection
- **LSTM Price Prediction** — Deep learning model trained on multi-stock historical data predicts next-day price
- **DQN Portfolio Allocation** — Reinforcement learning agent allocates optimal portfolio weights across assets
- **Sentiment Analysis** — Multi-source NLP sentiment scoring using VADER + TextBlob on live news
- **Google Trends Integration** — Trend score per stock using pytrends
- **Live News Feed** — Real-time news fetched via NewsAPI with fallback to related results
- **Company Stats** — Market cap, P/E ratio, 52-week high/low pulled live from Yahoo Finance
- **Stock Search** — Autocomplete search powered by Yahoo Finance search API
- **Docker Ready** — Full stack deployable with a single `docker-compose up`

---

## 🏗️ Tech Stack

### Backend
| Tool | Purpose |
|---|---|
| FastAPI | REST API framework |
| PyTorch | LSTM & DQN deep learning models |
| yfinance | Stock price & company data |
| VADER + TextBlob | Sentiment analysis |
| pytrends | Google Trends scoring |
| SQLAlchemy + SQLite | Database ORM |
| NewsAPI | Live news articles |

### Frontend
| Tool | Purpose |
|---|---|
| React 18 | UI framework |
| Canvas API | Custom candlestick chart renderer |
| CSS3 | Styling with CSS variables |
| DM Sans + Playfair Display | Typography |

---

## 📁 Project Structure

```
Stock_sense/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app & startup events
│   │   ├── models.py            # Database models
│   │   ├── database.py          # SQLite connection
│   │   ├── auth_utils.py        # Auth utilities
│   │   ├── routers/
│   │   │   ├── predict.py       # /portfolio-predict, /stock-history
│   │   │   ├── news.py          # /stock-news
│   │   │   ├── search.py        # /search-stock
│   │   │   ├── backtest.py      # /backtest
│   │   │   └── portfolio.py     # /portfolio
│   │   ├── services/
│   │   │   ├── lstm_model.py    # LSTM training & inference
│   │   │   ├── dqn_agent.py     # DQN reinforcement learning agent
│   │   │   ├── sentiment_service.py  # Multi-source sentiment
│   │   │   ├── market_service.py     # yfinance data fetching
│   │   │   ├── news_service.py       # News fetching
│   │   │   └── trends_service.py     # Google Trends
│   │   └── models_store/
│   │       └── lstm.pth         # Pre-trained LSTM weights
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.js               # Page router
│   │   ├── index.js             # React entry point
│   │   ├── components/
│   │   │   ├── Navbar.jsx       # Navigation bar
│   │   │   ├── TickerBar.jsx    # Live ticker strip
│   │   │   └── PriceChart.jsx   # Canvas candlestick chart
│   │   ├── pages/
│   │   │   ├── HomePage.jsx     # Landing page
│   │   │   └── AnalysisPage.jsx # Analysis dashboard
│   │   └── data/
│   │       └── stockData.js     # API fetch functions
│   ├── public/
│   │   └── index.html
│   └── Dockerfile
└── docker-compose.yml
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- npm

### 1. Clone the repository
```bash
git clone https://github.com/adityaa-08/Stock_sense.git
cd Stock_sense
```

### 2. Start the Backend
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

On first run, the LSTM model will auto-train on AAPL, TSLA, MSFT, NVDA, AMZN data (~2 minutes).

### 3. Start the Frontend
Open a new terminal:
```bash
cd frontend
npm install
npm start
```

Visit **http://localhost:3000** 🎉

### 4. Or use Docker
```bash
docker-compose up --build
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/portfolio-predict` | LSTM + DQN prediction for list of symbols |
| `GET` | `/stock-history/{symbol}?period=3mo` | OHLCV candlestick data |
| `GET` | `/stock-news/{symbol}` | Latest news articles |
| `GET` | `/search-stock?q=apple` | Symbol search autocomplete |
| `GET` | `/backtest` | Strategy backtesting |

### Example Request
```bash
curl -X POST http://localhost:8000/portfolio-predict \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["AAPL", "TSLA"]}'
```

### Example Response
```json
{
  "portfolio_allocation": [
    {
      "symbol": "AAPL",
      "current_price": 189.42,
      "predicted_price": 191.80,
      "decision": "BUY",
      "news_sentiment_avg": 0.312,
      "trend_score": 0.654,
      "allocation_weight": 0.6231,
      "company_stats": {
        "market_cap": 2940000000000,
        "pe_ratio": 31.2,
        "52_week_high": 198.23,
        "52_week_low": 164.08
      }
    }
  ],
  "total_assets": 1
}
```

---

## 🧠 How the Models Work

### LSTM Price Prediction
- Trained on 2 years of closing prices across 5 major stocks
- Sliding window of 60 days → predicts next closing price
- Saved to `models_store/lstm.pth` and auto-loaded on startup

### DQN Portfolio Allocation
- State: predicted price, sentiment avg, sentiment volatility, trend score per asset
- Action: portfolio weight allocation across up to 10 assets
- Softmax output normalized to 100% allocation

### Sentiment Pipeline
- VADER sentiment on news headlines
- TextBlob subjectivity scoring
- Google Trends momentum score
- Combined weighted average → score from -1 (bearish) to +1 (bullish)

---

## 📊 Decision Logic

| Condition | Decision |
|---|---|
| Price change > 0.3% AND sentiment > 0 | **BUY** |
| Price change < -0.3% AND sentiment < 0 | **SELL** |
| Price change > 0.1% | **BUY** |
| Price change < -0.1% | **SELL** |
| Otherwise | **HOLD** |

---

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first.

1. Fork the repo
2. Create your branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add your feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

---

## ⚠️ Disclaimer

StockSense is for **educational and informational purposes only**. It is not financial advice. Do not make investment decisions based solely on this tool. Always consult a qualified financial advisor.

---


## 👨‍💻 Author

**K.Sree Harsha**  
GitHub: [@kharsha26](https://github.com/kharsha26)
