// HomePage.jsx
import React from 'react';
import TickerBar from '../components/TickerBar';
import './HomePage.css';

const features = [
  { icon: '📈', title: 'Real-Time Price Data',  desc: 'Live stock prices, OHLCV data, and historical charts pulled directly from market feeds with sub-second latency.' },
  { icon: '🤖', title: 'ML Price Predictions',  desc: 'Machine learning models trained on historical patterns deliver next-day and short-term price movement forecasts.' },
  { icon: '🧠', title: 'Sentiment Analysis',    desc: 'NLP-powered analysis of news articles and social media to gauge market sentiment around any ticker symbol.' },
  { icon: '📊', title: 'Technical Indicators',  desc: 'RSI, MACD, Bollinger Bands, moving averages and 20+ other indicators computed automatically for every stock.' },
  { icon: '⚡', title: 'Fast REST API',         desc: 'Python FastAPI backend delivers analysis results in milliseconds. Easily integrate with your own trading systems.' },
  { icon: '🐳', title: 'Docker Ready',          desc: 'Containerised with Docker Compose. Deploy the full stack anywhere in minutes — backend, frontend, all services included.' },
];

const stack = [
  'Python', 'FastAPI', 'JavaScript', 'yfinance',
  'scikit-learn', 'pandas', 'NumPy', 'Docker',
  'Docker Compose', 'REST API', 'NLP / Sentiment', 'CSS3',
];

const steps = [
  { num: '01', title: 'Enter Ticker', desc: 'Type any NSE / BSE or US market ticker symbol into the search box.' },
  { num: '02', title: 'Fetch Data',   desc: 'The backend pulls live price data, financials, and recent news via market APIs.' },
  { num: '03', title: 'Run Models',   desc: 'ML models and NLP pipelines process the data to generate predictions and sentiment scores.' },
  { num: '04', title: 'View Results', desc: 'Interactive dashboard displays signals, charts, indicators, and news — all in one place.' },
];

const scrollToFeatures = () => {
  document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' });
};

export default function HomePage({ setPage }) {

  const goAnalysis = () => setPage('analysis');

  return (
    <div className="home-page">

      <section className="hero">
        <div className="grid-bg" />
        <TickerBar />

        <div className="hero-content">
          <div className="hero-tag">Real-Time Stock Intelligence</div>
          <h1>Analyse Markets<br />with <em>Precision</em></h1>
          <p>StockSense combines real-time market data, machine learning predictions, and sentiment analysis to give you an analytical edge in every trade decision.</p>
          <div className="hero-btns">
            <button className="btn-primary" onClick={goAnalysis}>Start Analysing</button>
            <button type="button" className="btn-ghost" onClick={scrollToFeatures}>Learn More</button>
          </div>
        </div>

        <div className="hero-visual" aria-hidden="true">
          <div className="mini-card mini-card-1">
            <div className="mini-sym">NVDA · NASDAQ</div>
            <div className="mini-val up">▲ +3.42%</div>
          </div>
          <div className="chart-card">
            <div className="chart-header">
              <div>
                <div className="chart-title">AAPL · NASDAQ</div>
                <div className="chart-price">$189.42</div>
              </div>
              <div className="badge-up">▲ +1.2%</div>
            </div>
            <svg viewBox="0 0 300 80" preserveAspectRatio="none" className="sparkline" aria-hidden="true">
              <defs>
                <linearGradient id="spark-grad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%"   stopColor="#00d4aa" stopOpacity="0.8" />
                  <stop offset="100%" stopColor="#00d4aa" stopOpacity="0"   />
                </linearGradient>
              </defs>
              <polygon fill="url(#spark-grad)" opacity="0.3" points="0,70 30,60 60,65 90,45 120,50 150,35 180,40 210,25 240,30 270,15 300,20 300,80 0,80" />
              <polyline fill="none" stroke="#00d4aa" strokeWidth="2" points="0,70 30,60 60,65 90,45 120,50 150,35 180,40 210,25 240,30 270,15 300,20" />
            </svg>
            <div className="chart-stats">
              <div className="stat-item"><div className="label">Open</div>  <div className="val">$187.10</div></div>
              <div className="stat-item"><div className="label">High</div>  <div className="val">$191.80</div></div>
              <div className="stat-item"><div className="label">Volume</div><div className="val">62.4M</div></div>
            </div>
          </div>
          <div className="mini-card mini-card-2">
            <div className="mini-sym">Signal: BUY</div>
            <div className="mini-val up">Confidence 87%</div>
          </div>
        </div>
      </section>

      <section className="features-section" id="features">
        <div className="section-label">What We Offer</div>
        <div className="section-title">Everything you need to trade smarter</div>
        <div className="features-grid">
          {features.map((f, i) => (
            <div className="feat-card" key={i}>
              <div className="feat-icon" aria-hidden="true">{f.icon}</div>
              <h3>{f.title}</h3>
              <p>{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="stack-section">
        <div className="section-label">Tech Stack</div>
        <div className="section-title">Built with modern tools</div>
        <div className="stack-pills">
          {stack.map((s, i) => (
            <span className={`pill ${i < 3 ? 'accent' : ''}`} key={i}>{s}</span>
          ))}
        </div>
      </section>

      <section className="how-section">
        <div className="section-label">How It Works</div>
        <div className="section-title">Analysis in four steps</div>
        <div className="steps">
          {steps.map((s, i) => (
            <div className="step" key={i}>
              <div className="step-num" aria-hidden="true">{s.num}</div>
              <h4>{s.title}</h4>
              <p>{s.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="cta-section">
        <h2>Ready to analyse your first stock?</h2>
        <p>Enter any ticker symbol and get a full analysis in seconds.</p>
        <button className="btn-primary" onClick={goAnalysis}>Open Analysis Dashboard →</button>
      </section>

      <footer className="home-footer">
        <div className="logo-footer">Stock<span>Sense</span></div>
        <p>Built by kharsha26 · Open Source · GitHub</p>
        <p className="disclaimer">For informational purposes only. Not financial advice.</p>
      </footer>

    </div>
  );
}