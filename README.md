# 📈 StockSense — AI-Powered Stock Market Prediction & Portfolio Analytics

StockSense is an **AI-driven full-stack stock intelligence platform** that combines **technical indicators, news sentiment analysis, machine learning classification, backtesting, and portfolio tracking** into a single modern dashboard.

It helps users analyze stocks like **AAPL, MSFT, AMZN, TSLA, NVDA**, predict **BUY / HOLD / SELL** actions, and validate trading performance using **accuracy, win rate, returns, and Sharpe ratio**.

---

# 🚀 Features

## 🧠 AI Prediction Engine

* Next-day **direction classification (UP / DOWN)**
* **BUY / HOLD / SELL** recommendation engine
* Multi-feature ML pipeline
* Technical + sentiment hybrid modeling
* Multi-stock extensibility

## 📰 News Sentiment Intelligence

* Real-time stock news fetching
* NLP-based sentiment scoring
* Average sentiment polarity (`news_avg`)
* Sentiment volatility tracking
* Bullish / Bearish gauge

## 📊 Quant Analytics Dashboard

* Candlestick & trend visualization
* Predicted % price movement
* Trend strength score
* Sentiment confidence gauge
* AI analysis metrics cards
* Portfolio weight insights

## 📈 Model Evaluation & Backtesting

* Classification Accuracy
* Precision / Recall / F1
* Win Rate
* Backtest Return
* Sharpe Ratio
* Historical strategy validation

## 💼 Portfolio Management

* Add / remove stocks
* Track holdings
* Position sizing
* User-wise portfolio storage
* SQLite persistence

## 🔐 Authentication System

* User registration
* Login session support
* Secure SQLite user table
* Portfolio linked to user ID

---

# 🏗️ Tech Stack

## Frontend

* **React.js**
* **Vite**
* **Tailwind CSS**
* Recharts / Chart.js
* Responsive futuristic dashboard UI

## Backend

* **FastAPI / Flask**
* Python REST APIs
* WebSocket-ready metrics
* SQLite database

## Machine Learning

* **Scikit-learn**
* Random Forest / XGBoost-ready pipeline
* LSTM extensibility
* Feature engineering pipeline
* Backtesting engine

## NLP / Sentiment

* News sentiment scoring
* Transformer / VADER compatible
* Market polarity extraction

## Database

* **SQLite**
* `users` table
* `portfolio` table
* historical trade storage

---

# 🧠 ML Features Used

The model uses engineered hybrid features:

* `price_change`
* `news_avg`
* `trend_score`
* moving averages
* RSI
* momentum
* volume spikes
* volatility
* portfolio weight

These are used to classify:

```text
UP / DOWN
BUY / HOLD / SELL
```

---

# 📂 Project Structure

```bash
StockSense/
│
├── backend/
│   ├── app.py
│   ├── routes/
│   ├── models/
│   ├── ml/
│   ├── database/
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   ├── components/
│   ├── pages/
│   └── package.json
│
├── docker-compose.yml
├── README.md
└── .gitignore
```

---

# ⚙️ Installation

## 1) Clone Repository

```bash
git clone https://github.com/kharsha26/StockSense.git
cd StockSense
```

## 2) Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
```

## 3) Frontend Setup

```bash
cd ../frontend
npm install
npm run dev
```

---

# ▶️ Run the Project

## Start Backend

```bash
cd backend
python app.py
```

## Start Frontend

```bash
cd frontend
npm run dev
```

---

# 📊 Model Performance

Typical realistic performance on unseen financial data:

| Metric       |   Value |
| ------------ | ------: |
| Accuracy     |  53–66% |
| Precision    |  53–66% |
| Recall       |  53–66% |
| F1 Score     |  53–66% |
| Win Rate     |  55–65% |
| Sharpe Ratio | 1.5–2.9 |

> In stock forecasting, even a small edge above **50% random baseline** can produce meaningful profits when combined with risk management.

---

# 🗃️ Database Tables

## Users

```sql
SELECT * FROM users;
```

Stores:

* user id
* username
* email
* credentials

## Portfolio

```sql
SELECT * FROM portfolio;
```

Stores:

* stock symbol
* quantity
* buy price
* user ownership

---

# 🔍 Example API Endpoints

```bash
GET /api/stock-news/AAPL
GET /api/stock-history/AAPL?period=3mo
GET /api/predict/AAPL
POST /api/portfolio/add
GET /api/backtest/AAPL
```

---

# 🎯 Use Cases

* AI stock direction prediction
* sentiment-aware trading assistant
* portfolio analytics dashboard
* ML + NLP finance research
* hackathon / final year project
* quant trading prototype

---

# 🔮 Future Enhancements

* XGBoost ensemble pipeline
* LSTM + attention forecasting
* options chain analytics
* live WebSocket streaming
* multi-user cloud deployment
* risk optimization engine
* sector ETF correlation
* reinforcement learning trading bot

---

# 👨‍💻 Author

**Sree Harsha**

AI/ML • Quant Analytics • Full Stack Development • Generative AI

---

# 📜 License

This project is developed for **academic, portfolio, and research demonstration purposes**.

---

# ⭐ Support

If you found this useful:

* ⭐ Star the repository
* 🍴 Fork it
* 🧠 Use it for AI/ML finance learning
* 📈 Build your own quant extensions

