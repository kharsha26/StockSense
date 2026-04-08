
// Navbar.jsx
import React from 'react';
import './Navbar.css';

export default function Navbar({ page, setPage, user, logout }) {

  const nav = (e, target) => {
    e.preventDefault();
    setPage(target);
  };

  return (
    <nav className="navbar">
      <div className="logo" onClick={e => nav(e, 'home')} style={{ cursor: 'pointer' }}>
        Stock<span>Sense</span>
      </div>
      <ul>
        <li>
          <a href="#" className={page === 'home' ? 'active' : ''} onClick={e => nav(e, 'home')}>
            Home
          </a>
        </li>
        <li>
          <a href="#" className={page === 'analysis' ? 'active' : ''} onClick={e => nav(e, 'analysis')}>
            Analyse
          </a>
        </li>
        <li>
          <a href="#" className={page === 'portfolio' ? 'active' : ''} onClick={e => nav(e, 'portfolio')}>
            Portfolio
          </a>
        </li>
        {/* <li>
          <a href="#" className={page === 'backtest' ? 'active' : ''} onClick={e => nav(e, 'backtest')}>
            Backtest
          </a>
        </li> */}
        {user ? (
          <>
            <li>
              <span style={{
                fontFamily: 'DM Mono, monospace', fontSize: '0.78rem',
                color: 'var(--accent)', padding: '0.4rem 0.8rem'
              }}>
                {user.username}
              </span>
            </li>
            <li>
              <a href="#" className="nav-cta" onClick={e => { e.preventDefault(); logout(); }}>
                Logout
              </a>
            </li>
          </>
        ) : (
          <li>
            <a href="#" className="nav-cta" onClick={e => nav(e, 'auth')}>
              Login
            </a>
          </li>
        )}
      </ul>
    </nav>
  );
}