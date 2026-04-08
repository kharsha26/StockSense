
// PortfolioPage.jsx
import React, { useState, useEffect } from 'react';
import './PortfolioPage.css';

const BASE_URL = 'http://localhost:8000/api';

export default function PortfolioPage({ setPage }) {
  const [portfolio, setPortfolio] = useState([]);
  const [loading, setLoading]     = useState(true);
  const [adding, setAdding]       = useState(false);
  const [error, setError]         = useState(null);
  const [showForm, setShowForm]   = useState(false);

  const [symbol, setSymbol]     = useState('');
  const [quantity, setQuantity] = useState('');
  const [avgPrice, setAvgPrice] = useState('');
  const [addError, setAddError] = useState(null);

  //  Get user id from localStorage — portfolio is per user
  const userId   = localStorage.getItem('userId');
  const username = localStorage.getItem('username');
  const isLoggedIn = !!userId;

  useEffect(() => {
    fetchPortfolio();
  }, []);

  function getHeaders() {
    return {
      'x-user-id': userId || '',
    };
  }

  async function fetchPortfolio() {
    setLoading(true);
    setError(null);
    try {
      const res  = await fetch(`${BASE_URL}/portfolio`, {
        headers: getHeaders(),  
      });
      const data = await res.json();
      setPortfolio(Array.isArray(data) ? data : []);
    } catch (e) {
      setError('Failed to load portfolio — is the backend running?');
    }
    setLoading(false);
  }

  async function handleAdd(e) {
    e.preventDefault();
    if (!symbol || !quantity || !avgPrice) {
      setAddError('All fields required');
      return;
    }
    setAdding(true);
    setAddError(null);
    try {
      const res = await fetch(
        `${BASE_URL}/portfolio/add?symbol=${symbol.toUpperCase()}&quantity=${quantity}&avg_price=${avgPrice}`,
        {
          method:  'POST',
          headers: getHeaders(),  
        }
      );
      if (!res.ok) {
        setAddError('Failed to add stock');
      } else {
        setSymbol('');
        setQuantity('');
        setAvgPrice('');
        setShowForm(false);
        fetchPortfolio();
      }
    } catch (e) {
      setAddError('Backend connection failed');
    }
    setAdding(false);
  }

  async function handleDelete(id) {
    if (!window.confirm('Remove this stock from portfolio?')) return;
    try {
      await fetch(`${BASE_URL}/portfolio/delete/${id}`, {
        method:  'DELETE',
        headers: getHeaders(),  
      });
      fetchPortfolio();
    } catch (e) {
      setError('Failed to delete stock');
    }
  }

  // Summary calculations
  const totalInvested = portfolio.reduce((s, h) => s + h.avg_price * h.quantity, 0);
  const totalCurrent  = portfolio.reduce((s, h) => s + h.current_price * h.quantity, 0);
  const totalPnL      = portfolio.reduce((s, h) => s + h.pnl, 0);
  const totalPnLPct   = totalInvested > 0 ? ((totalPnL / totalInvested) * 100).toFixed(2) : '0.00';
  const isUp          = totalPnL >= 0;

  return (
    <div className="portfolio-page">
      <div className="portfolio-header">
        <div className="section-label">Portfolio Tracker</div>
        <h1>My Portfolio</h1>
        <p>
          {isLoggedIn
            ? <>Showing portfolio for <strong style={{ color: 'var(--accent)' }}>{username}</strong></>
            : 'Track your holdings, monitor P&L and current prices in real time.'
          }
        </p>
      </div>

      {/* ✅ Not logged in warning */}
      {!isLoggedIn && (
        <div className="port-not-logged-in">
          ⚠ You are not logged in. Your portfolio will not be saved per user.
          <button onClick={() => setPage('auth')}>Login →</button>
        </div>
      )}

      {/* Summary Cards */}
      <div className="port-summary">
        <div className="port-stat-card">
          <div className="psc-label">Total Invested</div>
          <div className="psc-val">
            ${totalInvested.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
        </div>
        <div className="port-stat-card">
          <div className="psc-label">Current Value</div>
          <div className="psc-val">
            ${totalCurrent.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
        </div>
        <div className="port-stat-card">
          <div className="psc-label">Total P&amp;L</div>
          <div className={`psc-val ${isUp ? 'up' : 'dn'}`}>
            {isUp ? '+' : ''}${totalPnL.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            <span className="psc-pct"> ({isUp ? '+' : ''}{totalPnLPct}%)</span>
          </div>
        </div>
        <div className="port-stat-card">
          <div className="psc-label">Holdings</div>
          <div className="psc-val">{portfolio.length}</div>
        </div>
      </div>

      {/* Actions */}
      <div className="port-actions">
        <button className="btn-add-stock" onClick={() => setShowForm(!showForm)}>
          {showForm ? '✕ Cancel' : '+ Add Stock'}
        </button>
        <button className="btn-refresh" onClick={fetchPortfolio}>↻ Refresh</button>
      </div>

      {/* Add Form */}
      {showForm && (
        <div className="add-stock-form">
          <div className="form-title">Add New Holding</div>
          {addError && <div className="auth-error">⚠ {addError}</div>}
          <form onSubmit={handleAdd} className="add-form-row">
            <div className="add-field">
              <label>Symbol</label>
              <input
                type="text"
                placeholder="e.g. AAPL"
                value={symbol}
                onChange={e => setSymbol(e.target.value.toUpperCase())}
                maxLength={15}
              />
            </div>
            <div className="add-field">
              <label>Quantity</label>
              <input
                type="number"
                placeholder="e.g. 10"
                value={quantity}
                onChange={e => setQuantity(e.target.value)}
                min="1"
              />
            </div>
            <div className="add-field">
              <label>Avg Buy Price</label>
              <input
                type="number"
                placeholder="e.g. 180.00"
                value={avgPrice}
                onChange={e => setAvgPrice(e.target.value)}
                step="0.01"
                min="0"
              />
            </div>
            <button type="submit" className="btn-add-submit" disabled={adding}>
              {adding ? 'Adding...' : 'Add →'}
            </button>
          </form>
        </div>
      )}

      {/* Error */}
      {error && <div className="auth-error">⚠ {error}</div>}

      {/* Holdings Table */}
      {loading ? (
        <div className="port-loading">
          <div className="spinner" />
          <div className="loading-text">Loading portfolio...</div>
        </div>
      ) : portfolio.length === 0 ? (
        <div className="port-empty">
          <div className="port-empty-icon">📭</div>
          <div>No holdings yet</div>
          <div className="port-empty-sub">Add your first stock using the button above</div>
        </div>
      ) : (
        <div className="port-table-wrap">
          <table className="port-table">
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Qty</th>
                <th>Avg Price</th>
                <th>Current Price</th>
                <th>Invested</th>
                <th>Current Value</th>
                <th>P&amp;L</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {portfolio.map((h, i) => {
                const invested = h.avg_price * h.quantity;
                const current  = h.current_price * h.quantity;
                const pnlPct   = ((h.pnl / invested) * 100).toFixed(2);
                const up       = h.pnl >= 0;
                return (
                  <tr key={i}>
                    <td><span className="port-sym">{h.symbol}</span></td>
                    <td>{h.quantity}</td>
                    <td>${h.avg_price.toFixed(2)}</td>
                    <td>${h.current_price.toFixed(2)}</td>
                    <td>${invested.toFixed(2)}</td>
                    <td>${current.toFixed(2)}</td>
                    <td>
                      <span className={up ? 'up' : 'dn'}>
                        {up ? '+' : ''}${h.pnl.toFixed(2)}
                        <span className="pnl-pct"> ({up ? '+' : ''}{pnlPct}%)</span>
                      </span>
                    </td>
                    <td style={{ display: 'flex', gap: '0.5rem' }}>
                      <button
                        className="btn-analyse-sym"
                        onClick={() => setPage('analysis')}
                      >Analyse</button>
                      <button
                        className="btn-delete-sym"
                        onClick={() => handleDelete(h.id)}
                      >Delete</button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      <footer className="analysis-footer">
        <div className="logo-footer">Stock<span>Sense</span></div>
        <p>Not financial advice.</p>
      </footer>
    </div>
  );
}