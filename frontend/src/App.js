
// App.js
import { useState } from 'react';
import Navbar        from './components/Navbar';
import HomePage      from './pages/HomePage';
import AnalysisPage  from './pages/AnalysisPage';
import PortfolioPage from './pages/PortfolioPage';
import BacktestPage  from './pages/BacktestPage';
import AuthPage      from './pages/AuthPage';
import './index.css';

function App() {
  const [page, setPage] = useState('home');
  const [user, setUser] = useState(() => {
    const token    = localStorage.getItem('token');
    const username = localStorage.getItem('username');
    return token ? { token, username } : null;
  });

  const navigateTo = (target) => {
    setPage(target);
    window.scrollTo({ top: 0, behavior: 'smooth' });
    document.title = {
      home:      'StockSense',
      analysis:  'StockSense — Analysis',
      portfolio: 'StockSense — Portfolio',
      backtest:  'StockSense — Backtest',
      auth:      'StockSense — Login',
    }[target] || 'StockSense';
  };

  function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    localStorage.removeItem('userId');
    setUser(null);
    navigateTo('home');
  }

  return (
    <div>
      <Navbar page={page} setPage={navigateTo} user={user} logout={logout} />
      {page === 'home'      && <HomePage      setPage={navigateTo} />}
      {page === 'analysis'  && <AnalysisPage  />}
      {page === 'portfolio' && <PortfolioPage setPage={navigateTo} />}
      {page === 'backtest'  && <BacktestPage  />}
      {page === 'auth'      && <AuthPage      setPage={navigateTo} setUser={setUser} />}
    </div>
  );
}

export default App;