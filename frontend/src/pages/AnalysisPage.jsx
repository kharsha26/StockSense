
// AnalysisPage.jsx
import React, { useState, useRef, useEffect, useCallback } from 'react';
import PriceChart from '../components/PriceChart';
import {
  fetchPortfolioPredict,
  fetchStockHistory,
  fetchStockNews,
  searchStock,
  quickPicks,
  currencySymbol,
} from '../data/stockData';
import './AnalysisPage.css';

const BASE_URL = 'http://localhost:8000/api';

const LOADING_STEPS = [
  'Fetching market data...',
  'Running LSTM prediction model...',
  'Analysing sentiment...',
  'Computing portfolio allocation...',
  'Building dashboard...',
];

const PERIODS = [
  { label: '1 Month',  value: '1mo' },
  { label: '3 Months', value: '3mo' },
  { label: '6 Months', value: '6mo' },
  { label: '1 Year',   value: '1y'  },
];

export default function AnalysisPage() {
  const [ticker, setTicker]           = useState('');
  const [period, setPeriod]           = useState('3mo');
  const [loading, setLoading]         = useState(false);
  const [loadText, setLoadText]       = useState('');
  const [result, setResult]           = useState(null);
  const [candles, setCandles]         = useState([]);
  const [news, setNews]               = useState([]);
  const [error, setError]             = useState(null);
  const [suggestions, setSuggestions] = useState([]);
  const [showDrop, setShowDrop]       = useState(false);
  const [dropLoading, setDropLoading] = useState(false);
  const [activeIdx, setActiveIdx]     = useState(-1);

  // ✅ Model metrics state
  const [metrics, setMetrics]             = useState(null);
  const [metricsLoading, setMetricsLoading] = useState(false);

  const timerRef    = useRef(null);
  const debounceRef = useRef(null);
  const lastSym     = useRef('');
  const dropdownRef = useRef(null);
  const inputRef    = useRef(null);

  useEffect(() => {
    function onClickOutside(e) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setShowDrop(false);
      }
    }
    document.addEventListener('mousedown', onClickOutside);
    return () => document.removeEventListener('mousedown', onClickOutside);
  }, []);

  const handleTickerChange = useCallback((e) => {
    const val = e.target.value.toUpperCase();
    setTicker(val);
    setActiveIdx(-1);
    clearTimeout(debounceRef.current);

    if (!val) {
      setSuggestions([]);
      setShowDrop(false);
      return;
    }

    setDropLoading(true);
    setShowDrop(true);

    debounceRef.current = setTimeout(async () => {
      try {
        const results = await searchStock(val);
        setSuggestions(results.slice(0, 7));
      } catch {
        setSuggestions([]);
      } finally {
        setDropLoading(false);
      }
    }, 300);
  }, []);

  function selectSuggestion(sym) {
    setTicker(sym);
    setSuggestions([]);
    setShowDrop(false);
    setActiveIdx(-1);
    runAnalysis(sym);
  }

  function handleKeyDown(e) {
    if (!showDrop || suggestions.length === 0) {
      if (e.key === 'Enter') runAnalysis();
      return;
    }
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIdx(i => Math.min(i + 1, suggestions.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIdx(i => Math.max(i - 1, -1));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (activeIdx >= 0 && suggestions[activeIdx]) {
        selectSuggestion(suggestions[activeIdx].symbol);
      } else {
        setShowDrop(false);
        runAnalysis();
      }
    } else if (e.key === 'Escape') {
      setShowDrop(false);
      setActiveIdx(-1);
    }
  }

  // ✅ Fetch model performance metrics
  async function fetchMetrics(sym) {
    setMetricsLoading(true);
    setMetrics(null);
    try {
      const res  = await fetch(`${BASE_URL}/model-metrics/${sym}`);
      const data = await res.json();
      if (!data.error) setMetrics(data);
    } catch (e) {
      console.error('Metrics fetch error:', e);
    }
    setMetricsLoading(false);
  }

  async function runAnalysis(sym, per) {
    const raw = (sym || ticker).trim().toUpperCase();
    if (!raw) return;
    const usePeriod = per || period;
    setTicker(raw);
    lastSym.current = raw;
    setResult(null);
    setCandles([]);
    setError(null);
    setMetrics(null);
    setLoading(true);
    setShowDrop(false);
    setSuggestions([]);

    let si = 0;
    setLoadText(LOADING_STEPS[0]);
    clearInterval(timerRef.current);
    timerRef.current = setInterval(() => {
      si++;
      setLoadText(LOADING_STEPS[Math.min(si, LOADING_STEPS.length - 1)]);
    }, 600);

    try {
      const [predictData, candleData, newsData] = await Promise.all([
        fetchPortfolioPredict([raw]),
        fetchStockHistory(raw, usePeriod),
        fetchStockNews(raw),
      ]);

      clearInterval(timerRef.current);

      if (!predictData.success) {
        setError(predictData.message || 'Prediction failed');
        setLoading(false);
        return;
      }

      const asset = predictData?.portfolio_allocation?.[0];
      if (!asset) {
        setError('No data returned for this symbol.');
        setLoading(false);
        return;
      }

      setCandles(candleData || []);
      setNews(newsData || []);
      setResult({ sym: raw, ...asset });

      // ✅ Fetch metrics after main analysis
      fetchMetrics(raw);

    } catch (e) {
      clearInterval(timerRef.current);
      setError('Backend connection failed. Ensure FastAPI is running at http://localhost:8000');
    }

    setLoading(false);
  }

  async function handlePeriodChange(newPeriod) {
    setPeriod(newPeriod);
    if (!lastSym.current) return;
    const data = await fetchStockHistory(lastSym.current, newPeriod);
    setCandles(data || []);
  }

  const cur       = result ? currencySymbol(result.sym) : '$';
  const isUp      = result && result.predicted_price >= result.current_price;
  const sentScore = result ? Math.round(((result.news_sentiment_avg + 1) / 2) * 100) : 0;
  const priceDiff = result
    ? ((result.predicted_price - result.current_price) / result.current_price * 100).toFixed(2)
    : 0;

  const indicators = result ? [
    { k: 'Predicted Change',     v: `${priceDiff > 0 ? '+' : ''}${priceDiff}%`,       pct: Math.min(Math.abs(priceDiff) * 10, 100) },
    { k: 'News Sentiment Avg',   v: result.news_sentiment_avg?.toFixed(4),             pct: Math.round(((result.news_sentiment_avg + 1) / 2) * 100) },
    { k: 'Sentiment Volatility', v: result.news_sentiment_volatility?.toFixed(4),      pct: Math.min(result.news_sentiment_volatility * 100, 100) },
    { k: 'Trend Score',          v: result.trend_score?.toFixed(4),                    pct: Math.round(((result.trend_score + 1) / 2) * 100) },
    { k: 'Portfolio Weight',     v: `${(result.allocation_weight * 100).toFixed(1)}%`, pct: Math.round(result.allocation_weight * 100) },
  ] : [];

  const stats = result?.company_stats || {};

  return (
    <div className="analysis-page">
      <div className="analysis-header">
        <div className="section-label">Analysis Dashboard</div>
        <h1>Stock Analysis</h1>
        <p>Powered by LSTM predictions, DQN portfolio allocation &amp; live sentiment analysis.</p>
      </div>

      {/* Search */}
      <div className="search-row">
        <div className="search-box-wrap" ref={dropdownRef}>
          <div className="search-box">
            <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
            </svg>
            <input
              ref={inputRef}
              type="text"
              placeholder="Search stock e.g. AAPL, Tesla, INFY.NS"
              value={ticker}
              onChange={handleTickerChange}
              onKeyDown={handleKeyDown}
              onFocus={() => suggestions.length > 0 && setShowDrop(true)}
              maxLength={20}
              autoComplete="off"
            />
            {ticker && (
              <button className="search-clear" onClick={() => {
                setTicker(''); setSuggestions([]); setShowDrop(false);
                inputRef.current?.focus();
              }}>✕</button>
            )}
          </div>

          {showDrop && (
            <div className="search-dropdown">
              {dropLoading ? (
                <div className="drop-loading"><span className="drop-spinner" />Searching...</div>
              ) : suggestions.length === 0 ? (
                <div className="drop-empty">No results for "{ticker}"</div>
              ) : (
                suggestions.map((s, i) => (
                  <div
                    key={s.symbol}
                    className={`drop-item ${i === activeIdx ? 'active' : ''}`}
                    onMouseDown={() => selectSuggestion(s.symbol)}
                    onMouseEnter={() => setActiveIdx(i)}
                  >
                    <span className="drop-sym">{s.symbol}</span>
                    <span className="drop-name">{s.name}</span>
                    {s.exchange && <span className="drop-exch">{s.exchange}</span>}
                  </div>
                ))
              )}
            </div>
          )}
        </div>

        <select className="filter-sel" value={period} onChange={e => handlePeriodChange(e.target.value)}>
          {PERIODS.map(p => (
            <option key={p.value} value={p.value}>{p.label}</option>
          ))}
        </select>
        <button className="btn-analyse" onClick={() => runAnalysis()}>Analyse →</button>
      </div>

      {/* Quick picks */}
      <div className="quick-label">QUICK PICKS</div>
      <div className="quick-picks">
        {quickPicks.map(sym => (
          <span key={sym} className="quick-chip" onClick={() => runAnalysis(sym)}>
            {sym.replace('.NS', '')}
          </span>
        ))}
      </div>

      {error && <div className="error-box">⚠ {error}</div>}

      {loading && (
        <div className="loading-overlay">
          <div className="spinner" />
          <div className="loading-text">{loadText}</div>
        </div>
      )}

      {result && !loading && (
        <div className="dashboard">

          {/* Overview */}
          <div className="card full">
            <div className="card-title">Overview</div>
            <div className="overview-row">
              <div>
                <div className="stock-name">{result.sym}</div>
                <div className="stock-full">{stats.name || stats.sector || stats.industry || result.sym}</div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div className="price-big">{cur}{result.current_price?.toLocaleString()}</div>
                <div className={`price-change ${isUp ? 'up' : 'dn'}`}>
                  Predicted: {cur}{result.predicted_price?.toFixed(2)}
                  {' '}({priceDiff > 0 ? '+' : ''}{priceDiff}%)
                </div>
              </div>
            </div>
            <div className="overview-stats">
              <div className="ov-stat">
                <div className="lbl">Market Cap</div>
                <div className="v">{stats.market_cap ? `${cur}${(stats.market_cap / 1e9).toFixed(1)}B` : 'N/A'}</div>
              </div>
              <div className="ov-stat">
                <div className="lbl">P/E Ratio</div>
                <div className="v">{stats.pe_ratio ? Number(stats.pe_ratio).toFixed(1) + 'x' : 'N/A'}</div>
              </div>
              <div className="ov-stat">
                <div className="lbl">52W High</div>
                <div className="v">{stats['52_week_high'] ? `${cur}${stats['52_week_high']}` : 'N/A'}</div>
              </div>
              <div className="ov-stat">
                <div className="lbl">52W Low</div>
                <div className="v">{stats['52_week_low'] ? `${cur}${stats['52_week_low']}` : 'N/A'}</div>
              </div>
            </div>
          </div>

          {/* Candlestick Chart */}
          <div className="card">
            <div className="card-title" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>Candlestick Chart</span>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                {PERIODS.map(p => (
                  <span
                    key={p.value}
                    className={`period-btn ${period === p.value ? 'active' : ''}`}
                    onClick={() => handlePeriodChange(p.value)}
                  >
                    {p.label.split(' ')[0]}{p.label.includes('Month') ? 'M' : 'Y'}
                  </span>
                ))}
              </div>
            </div>
            {candles.length > 0
              ? <PriceChart candles={candles} />
              : <div className="no-data">No chart data available</div>
            }
            <div style={{ display: 'flex', gap: '1.5rem', marginTop: '0.8rem' }}>
              <span style={{ fontFamily: 'DM Mono,monospace', fontSize: '0.72rem', color: 'var(--up)' }}>▮ Bullish</span>
              <span style={{ fontFamily: 'DM Mono,monospace', fontSize: '0.72rem', color: 'var(--down)' }}>▮ Bearish</span>
            </div>
          </div>

          {/* Sentiment */}
          <div className="card">
            <div className="card-title">Market Sentiment</div>
            <div className="sentiment-gauge">
              <div className="gauge-wrap">
                <svg viewBox="0 0 160 90" className="gauge-svg">
                  <defs>
                    <linearGradient id="gauge-grad" x1="0" y1="0" x2="1" y2="0">
                      <stop offset="0%" stopColor="#ff4757"/>
                      <stop offset="50%" stopColor="#ffa502"/>
                      <stop offset="100%" stopColor="#00d4aa"/>
                    </linearGradient>
                  </defs>
                  <path d="M 15 85 A 65 65 0 0 1 145 85" fill="none" stroke="#1a2d42" strokeWidth="10" strokeLinecap="round"/>
                  <path d="M 15 85 A 65 65 0 0 1 145 85" fill="none" stroke="url(#gauge-grad)" strokeWidth="10" strokeLinecap="round" opacity="0.4"/>
                  <line
                    x1="80" y1="85"
                    x2={80 + 55 * Math.cos(Math.PI - (sentScore / 100) * Math.PI)}
                    y2={85 - 55 * Math.sin((sentScore / 100) * Math.PI)}
                    stroke="#e8f0f7" strokeWidth="2.5" strokeLinecap="round"
                  />
                  <circle cx="80" cy="85" r="5" fill="#e8f0f7"/>
                </svg>
              </div>
              <div className="sentiment-val" style={{ color: sentScore >= 60 ? 'var(--up)' : sentScore >= 40 ? 'var(--text)' : 'var(--down)' }}>
                {sentScore}/100
              </div>
              <div className="sentiment-label">
                {sentScore >= 60 ? 'Bullish Sentiment' : sentScore >= 40 ? 'Neutral Sentiment' : 'Bearish Sentiment'}
              </div>
            </div>
          </div>

          {/* Prediction */}
          <div className="card">
            <div className="card-title">LSTM + DQN Prediction</div>
            <div className="prediction-row">
              <div className={`pred-box ${isUp ? 'bull' : 'bear'}`}>
                <div className="pred-dir">{isUp ? '🐂' : '🐻'}</div>
                <div className="pred-pct">{cur}{result.predicted_price?.toFixed(2)}</div>
                <div className="pred-lbl">Predicted Price</div>
              </div>
              <div className="pred-box" style={{ borderColor: 'rgba(255,165,0,0.3)', background: 'rgba(255,165,0,0.05)' }}>
                <div className="pred-dir">⚖️</div>
                <div className="pred-pct">{(result.allocation_weight * 100).toFixed(1)}%</div>
                <div className="pred-lbl">Portfolio Weight</div>
              </div>
            </div>
            <div style={{ marginTop: '0.8rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
                <span className="conf-label">Trend Score</span>
                <span className="conf-val-text">{result.trend_score?.toFixed(3)}</span>
              </div>
              <div className="confidence-bar">
                <div className="confidence-fill" style={{ width: `${Math.round(((result.trend_score + 1) / 2) * 100)}%` }}/>
              </div>
            </div>
            <div className="signal-box">
              <div className="signal-lbl">DECISION</div>
              <div className="signal-val" style={{
                color: result.decision === 'BUY' ? 'var(--up)' : result.decision === 'SELL' ? 'var(--down)' : 'var(--text)'
              }}>
                {result.decision}
              </div>
            </div>
          </div>

          {/* Indicators */}
          <div className="card">
            <div className="card-title">Analysis Metrics</div>
            <div className="metrics-list">
              {indicators.map((m, i) => (
                <div key={i}>
                  <div className="metric-row">
                    <span className="mk">{m.k}</span>
                    <span className="mv">{m.v}</span>
                  </div>
                  <div className="metric-bar-wrap">
                    <div className="metric-bar-fill" style={{ width: `${Math.max(0, Math.min(100, m.pct))}%` }}/>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* ✅ Model Performance */}
          <div className="card full">
            <div className="card-title">Model Performance — Last 30 Days</div>
            {metricsLoading ? (
              <div className="no-data">
                <div className="spinner" style={{ margin: '0 auto 0.5rem' }} />
                Computing metrics...
              </div>
            ) : metrics ? (
              <div className="model-metrics">
                <div className="mm-group">
                  <div className="mm-group-title">Regression</div>
                  <div className="mm-row">
                    <span className="mm-label">RMSE</span>
                    <span className="mm-val">{cur}{metrics.rmse} <span className="mm-sub">({metrics.rmse_pct}% of price)</span></span>
                  </div>
                  <div className="mm-row">
                    <span className="mm-label">MAE</span>
                    <span className="mm-val">{cur}{metrics.mae} <span className="mm-sub">({metrics.mae_pct}% of price)</span></span>
                  </div>
                </div>
                <div className="mm-group">
                  <div className="mm-group-title">Classification</div>
                  <div className="mm-row">
                    <span className="mm-label">Accuracy</span>
                    <span className="mm-val">{(metrics.accuracy * 100).toFixed(1)}%</span>
                  </div>
                  <div className="mm-row">
                    <span className="mm-label">Precision</span>
                    <span className="mm-val">{(metrics.precision * 100).toFixed(1)}%</span>
                  </div>
                  <div className="mm-row">
                    <span className="mm-label">Recall</span>
                    <span className="mm-val">{(metrics.recall * 100).toFixed(1)}%</span>
                  </div>
                  <div className="mm-row">
                    <span className="mm-label">F1 Score</span>
                    <span className="mm-val">{(metrics.f1_score * 100).toFixed(1)}%</span>
                  </div>
                </div>
                <div className="mm-group">
                  <div className="mm-group-title">Backtest Strategy</div>
                  <div className="mm-row">
                    <span className="mm-label">Return</span>
                    <span className={`mm-val ${metrics.backtest_return >= 0 ? 'up' : 'dn'}`}>
                      {metrics.backtest_return >= 0 ? '+' : ''}{metrics.backtest_return}%
                    </span>
                  </div>
                  <div className="mm-row">
                    <span className="mm-label">Win Rate</span>
                    <span className="mm-val">{metrics.win_rate}%</span>
                  </div>
                  <div className="mm-row">
                    <span className="mm-label">Sharpe Ratio</span>
                    <span className="mm-val">{metrics.sharpe_ratio}</span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="no-data">Metrics unavailable for this symbol</div>
            )}
          </div>

          {/* News */}
          <div className="card full">
            <div className="card-title">
              Latest News
              {news.length === 0 && <span style={{ color: 'var(--muted)', fontWeight: 400, marginLeft: '0.5rem' }}>(showing related results)</span>}
            </div>
            {news.length > 0 ? (
              <div className="news-list">
                {news.map((n, i) => (
                  <a className="news-item" key={i} href={n.url} target="_blank" rel="noopener noreferrer">
                    <div className="news-dot pos"/>
                    <div>
                      <div className="news-text">{n.title}</div>
                      <div className="news-meta">{n.source} · Live</div>
                    </div>
                  </a>
                ))}
              </div>
            ) : (
              <div className="no-data">No news found for this symbol.</div>
            )}
          </div>

        </div>
      )}

      <footer className="analysis-footer">
        <div className="logo-footer">Stock<span>Sense</span></div>
        <p>Powered by LSTM · DQN · Sentiment Analysis · FastAPI</p>
        <p>Not financial advice.</p>
      </footer>
    </div>
  );
}