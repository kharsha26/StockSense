// // BacktestPage.jsx
// import React, { useState, useRef, useEffect } from 'react';
// import './BacktestPage.css';

// const BASE_URL   = 'http://localhost:8000/api';
// const SUGGESTIONS = [
//   'AAPL','TSLA','MSFT','NVDA','AMZN','GOOGL','META','NFLX',
//   'JPM','AMD','INFY.NS','TCS.NS','RELIANCE.NS','HDFCBANK.NS',
// ];

// export default function BacktestPage() {
//   const [symbols, setSymbols]   = useState([]);
//   const [input, setInput]       = useState('');
//   const [result, setResult]     = useState(null);
//   const [loading, setLoading]   = useState(false);
//   const [error, setError]       = useState(null);
//   const canvasRef               = useRef(null);

//   function addSymbol(sym) {
//     const s = sym.trim().toUpperCase();
//     if (!s || symbols.includes(s) || symbols.length >= 10) return;
//     setSymbols(prev => [...prev, s]);
//     setInput('');
//   }

//   function removeSymbol(sym) {
//     setSymbols(prev => prev.filter(s => s !== sym));
//   }

//   async function runBacktest() {
//     if (symbols.length === 0) {
//       setError('Add at least one stock symbol');
//       return;
//     }
//     setLoading(true);
//     setError(null);
//     setResult(null);

//     try {
//       const res  = await fetch(`${BASE_URL}/multi-backtest`, {
//         method:  'POST',
//         headers: { 'Content-Type': 'application/json' },
//         body:    JSON.stringify({ symbols }),
//       });
//       const data = await res.json();
//       if (data.error) {
//         setError(data.error);
//       } else {
//         setResult(data);
//       }
//     } catch (e) {
//       setError('Backend connection failed');
//     }
//     setLoading(false);
//   }

//   // Draw equity curve on canvas
//   useEffect(() => {
//     if (!result?.equity_curve || !canvasRef.current) return;
//     const canvas = canvasRef.current;
//     const ctx    = canvas.getContext('2d');
//     const curve  = result.equity_curve;
//     const W = canvas.offsetWidth;
//     const H = 200;
//     const dpr = window.devicePixelRatio || 1;
//     canvas.width  = W * dpr;
//     canvas.height = H * dpr;
//     canvas.style.width  = W + 'px';
//     canvas.style.height = H + 'px';
//     ctx.scale(dpr, dpr);
//     ctx.clearRect(0, 0, W, H);

//     const pad  = { t: 10, r: 10, b: 30, l: 50 };
//     const cW   = W - pad.l - pad.r;
//     const cH   = H - pad.t - pad.b;
//     const minV = Math.min(...curve);
//     const maxV = Math.max(...curve);
//     const rng  = maxV - minV || 1;

//     const toX = i  => pad.l + (i / (curve.length - 1)) * cW;
//     const toY = v  => pad.t + cH - ((v - minV) / rng) * cH;

//     // Grid
//     ctx.strokeStyle = 'rgba(26,45,66,0.8)';
//     ctx.lineWidth   = 1;
//     for (let i = 0; i <= 4; i++) {
//       const y = pad.t + (cH / 4) * i;
//       ctx.beginPath(); ctx.moveTo(pad.l, y); ctx.lineTo(W - pad.r, y); ctx.stroke();
//       const val = maxV - (rng / 4) * i;
//       ctx.fillStyle = '#5a7a94';
//       ctx.font = '10px DM Mono, monospace';
//       ctx.textAlign = 'right';
//       ctx.fillText('$' + val.toFixed(0), pad.l - 4, y + 4);
//     }

//     // Fill
//     const isProfit = curve[curve.length - 1] >= curve[0];
//     const grad     = ctx.createLinearGradient(0, pad.t, 0, H - pad.b);
//     grad.addColorStop(0, isProfit ? 'rgba(0,212,170,0.3)' : 'rgba(255,71,87,0.3)');
//     grad.addColorStop(1, 'rgba(0,0,0,0)');
//     ctx.beginPath();
//     ctx.moveTo(toX(0), toY(curve[0]));
//     curve.forEach((v, i) => ctx.lineTo(toX(i), toY(v)));
//     ctx.lineTo(toX(curve.length - 1), H - pad.b);
//     ctx.lineTo(toX(0), H - pad.b);
//     ctx.closePath();
//     ctx.fillStyle = grad;
//     ctx.fill();

//     // Line
//     ctx.beginPath();
//     ctx.strokeStyle = isProfit ? '#00d4aa' : '#ff4757';
//     ctx.lineWidth   = 2;
//     curve.forEach((v, i) => i === 0 ? ctx.moveTo(toX(0), toY(v)) : ctx.lineTo(toX(i), toY(v)));
//     ctx.stroke();

//     // X labels
//     ctx.fillStyle = '#5a7a94';
//     ctx.font      = '9px DM Mono, monospace';
//     ctx.textAlign = 'center';
//     const step = Math.max(1, Math.floor(curve.length / 5));
//     for (let i = 0; i < curve.length; i += step) {
//       ctx.fillText(`Day ${i}`, toX(i), H - 8);
//     }
//   }, [result]);

//   const isProfit = result && result.total_return >= 0;

//   return (
//     <div className="backtest-page">
//       <div className="backtest-header">
//         <div className="section-label">Strategy Backtesting</div>
//         <h1>Portfolio Backtest</h1>
//         <p>Test your DQN-powered portfolio allocation strategy against historical price data.</p>
//       </div>

//       {/* Symbol Input */}
//       <div className="bt-card">
//         <div className="card-title">Select Stocks (max 10)</div>

//         <div className="bt-input-row">
//           <input
//             type="text"
//             className="bt-input"
//             placeholder="Type symbol e.g. AAPL"
//             value={input}
//             onChange={e => setInput(e.target.value.toUpperCase())}
//             onKeyDown={e => e.key === 'Enter' && addSymbol(input)}
//             maxLength={15}
//           />
//           <button className="btn-add-sym" onClick={() => addSymbol(input)}>Add +</button>
//         </div>

//         {/* Quick add suggestions */}
//         <div className="bt-suggestions">
//           {SUGGESTIONS.filter(s => !symbols.includes(s)).slice(0, 8).map(s => (
//             <span key={s} className="bt-chip" onClick={() => addSymbol(s)}>
//               {s.replace('.NS', '')}
//             </span>
//           ))}
//         </div>

//         {/* Selected symbols */}
//         {symbols.length > 0 && (
//           <div className="bt-selected">
//             {symbols.map(s => (
//               <span key={s} className="bt-tag">
//                 {s}
//                 <button onClick={() => removeSymbol(s)}>✕</button>
//               </span>
//             ))}
//           </div>
//         )}

//         {error && <div className="bt-error">⚠ {error}</div>}

//         <button
//           className="btn-run-backtest"
//           onClick={runBacktest}
//           disabled={loading || symbols.length === 0}
//         >
//           {loading
//             ? <><span className="bt-spinner" /> Running backtest...</>
//             : `Run Backtest on ${symbols.length} stock${symbols.length !== 1 ? 's' : ''} →`
//           }
//         </button>
//       </div>

//       {/* Results */}
//       {result && (
//         <>
//           {/* Metrics */}
//           <div className="bt-metrics">
//             <div className="bt-metric-card">
//               <div className="btm-label">Initial Capital</div>
//               <div className="btm-val">${result.initial_capital?.toLocaleString()}</div>
//             </div>
//             <div className="bt-metric-card">
//               <div className="btm-label">Final Value</div>
//               <div className="btm-val">${result.final_portfolio_value?.toLocaleString()}</div>
//             </div>
//             <div className="bt-metric-card">
//               <div className="btm-label">Total Return</div>
//               <div className={`btm-val ${isProfit ? 'up' : 'dn'}`}>
//                 {isProfit ? '+' : ''}{(result.total_return * 100).toFixed(2)}%
//               </div>
//             </div>
//             <div className="bt-metric-card">
//               <div className="btm-label">Sharpe Ratio</div>
//               <div className="btm-val">{result.sharpe_ratio?.toFixed(4)}</div>
//             </div>
//             <div className="bt-metric-card">
//               <div className="btm-label">Sortino Ratio</div>
//               <div className="btm-val">{result.sortino_ratio?.toFixed(4)}</div>
//             </div>
//             <div className="bt-metric-card">
//               <div className="btm-label">Max Drawdown</div>
//               <div className="btm-val dn">-{(result.max_drawdown * 100).toFixed(2)}%</div>
//             </div>
//             <div className="bt-metric-card">
//               <div className="btm-label">Win Rate</div>
//               <div className="btm-val">{(result.win_rate * 100).toFixed(1)}%</div>
//             </div>
//             <div className="bt-metric-card">
//               <div className="btm-label">Trading Days</div>
//               <div className="btm-val">{result.total_days}</div>
//             </div>
//           </div>

//           {/* Equity Curve */}
//           <div className="bt-card">
//             <div className="card-title">Equity Curve</div>
//             <div style={{ width: '100%', height: 200, position: 'relative' }}>
//               <canvas ref={canvasRef} style={{ width: '100%', height: '200px' }} />
//             </div>
//             <div style={{ display: 'flex', gap: '1.5rem', marginTop: '0.8rem' }}>
//               <span style={{ fontFamily: 'DM Mono,monospace', fontSize: '0.72rem', color: 'var(--up)' }}>▮ Profit</span>
//               <span style={{ fontFamily: 'DM Mono,monospace', fontSize: '0.72rem', color: 'var(--down)' }}>▮ Loss</span>
//             </div>
//           </div>

//           {/* Skipped symbols */}
//           {result.skipped_symbols?.length > 0 && (
//             <div className="bt-skipped">
//               ⚠ Skipped (insufficient data): {result.skipped_symbols.join(', ')}
//             </div>
//           )}
//         </>
//       )}

//       <footer className="analysis-footer" style={{ marginTop: '3rem' }}>
//         <div className="logo-footer">Stock<span>Sense</span></div>
//         <p>Backtesting does not guarantee future results. Not financial advice.</p>
//       </footer>
//     </div>
//   );
// }