
// PriceChart.jsx
import React, { useEffect, useRef } from 'react';

export default function PriceChart({ candles }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    if (!candles || candles.length === 0 || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.parentElement.getBoundingClientRect();
    const W = rect.width;
    const H = 220;
    canvas.width = W * dpr;
    canvas.height = H * dpr;
    canvas.style.width = W + 'px';
    canvas.style.height = H + 'px';
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, W, H);

    const padL = 10, padR = 10, padT = 10, padB = 30;
    const chartW = W - padL - padR;
    const chartH = H - padT - padB;

    const validCandles = candles.filter(
      c => c.open != null && c.high != null && c.low != null && c.close != null
    );
    if (validCandles.length === 0) return;

    const highs  = validCandles.map(c => c.high);
    const lows   = validCandles.map(c => c.low);
    const minVal = Math.min(...lows);
    const maxVal = Math.max(...highs);
    const range  = maxVal - minVal;
    if (!isFinite(range) || range === 0) return;

    const toY = v => padT + chartH - ((v - minVal) / range) * chartH;
    const n   = validCandles.length;
    const candleW = Math.max(2, Math.floor(chartW / n) - 1);
    const halfW   = Math.max(1, Math.floor(candleW / 2));

    // Grid lines
    ctx.strokeStyle = 'rgba(26,45,66,0.8)';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
      const y = padT + (chartH / 4) * i;
      ctx.beginPath();
      ctx.moveTo(padL, y);
      ctx.lineTo(W - padR, y);
      ctx.stroke();
      const val = maxVal - (range / 4) * i;
      ctx.fillStyle = '#5a7a94';
      ctx.font = '10px DM Mono, monospace';
      ctx.textAlign = 'right';
      ctx.fillText(val.toFixed(0), padL + 42, y - 3);
    }

    // Candles
    validCandles.forEach((c, i) => {
      const x      = padL + (i / n) * chartW + candleW / 2;
      const openY  = toY(c.open);
      const closeY = toY(c.close);
      const highY  = toY(c.high);
      const lowY   = toY(c.low);
      const isUp   = c.close >= c.open;
      const color  = isUp ? '#00d4aa' : '#ff4757';

      // Wick
      ctx.strokeStyle = color;
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(x, highY);
      ctx.lineTo(x, lowY);
      ctx.stroke();

      // Body
      const bodyTop = Math.min(openY, closeY);
      const bodyH   = Math.max(1, Math.abs(closeY - openY));
      ctx.fillStyle = color;
      ctx.globalAlpha = isUp ? 0.9 : 0.75;
      ctx.fillRect(x - halfW, bodyTop, candleW, bodyH);
      ctx.globalAlpha = 1;
    });

    // X-axis labels
    ctx.fillStyle = '#5a7a94';
    ctx.font = '9px DM Mono, monospace';
    ctx.textAlign = 'center';
    const step = Math.max(1, Math.floor(n / 6));
    for (let i = 0; i < n; i += step) {
      const c     = validCandles[i];
      const x     = padL + (i / n) * chartW + candleW / 2;
      const label = c.time ? c.time.slice(5) : '';
      ctx.fillText(label, x, H - 8);
    }
  }, [candles]);

  if (!candles || candles.length === 0) {
    return <div>No chart data available</div>;
  }

  return (
    <div style={{ width: '100%', height: 220, position: 'relative', overflow: 'hidden' }}>
      <canvas ref={canvasRef} />
    </div>
  );
}