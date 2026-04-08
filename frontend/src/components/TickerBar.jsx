// TickerBar.jsx
import React from 'react';
import { tickerItems } from '../data/stockData';
import './TickerBar.css';

export default function TickerBar() {
  const items = [...tickerItems, ...tickerItems];
  return (
    <div className="ticker-bar">
      <div className="ticker-track">
        {items.map((item, i) => (
          <span className="ticker-item" key={i}>
            <span className="sym">{item.sym}</span>
            {item.price}
            <span className={item.up ? 'up' : 'dn'}>{item.chg}</span>
            <span className="ticker-sep">·</span>
          </span>
        ))}
      </div>
    </div>
  );
}