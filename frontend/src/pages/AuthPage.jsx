
// AuthPage.jsx
import React, { useState } from 'react';
import './AuthPage.css';

const BASE_URL = 'http://localhost:8000/api';

export default function AuthPage({ setPage, setUser }) {
  const [mode, setMode]         = useState('login');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState(null);
  const [success, setSuccess]   = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!username.trim() || !password.trim()) {
      setError('Please fill in all fields');
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const res = await fetch(`${BASE_URL}/${mode}`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ username: username.trim(), password }),
      });

      const data = await res.json();

      if (!res.ok) {
        setError(data.detail || 'Something went wrong');
        setLoading(false);
        return;
      }

      if (mode === 'signup') {
        setSuccess('Account created! Please log in.');
        setMode('login');
        setPassword('');
      } else {
        //  Save all user data to localStorage
        localStorage.setItem('token',    data.access_token);
        localStorage.setItem('username', username.trim());
        localStorage.setItem('userId',   String(data.user_id)); 
        setUser({
          username: username.trim(),
          token:    data.access_token,
          id:       data.user_id,
        });
        setPage('analysis');
      }

    } catch (e) {
      setError('Backend connection failed');
    }

    setLoading(false);
  }

  function switchMode(newMode) {
    setMode(newMode);
    setError(null);
    setSuccess(null);
    setUsername('');
    setPassword('');
  }

  return (
    <div className="auth-page">
      <div className="auth-bg" />

      <div className="auth-card">
        <div className="auth-logo">Stock<span>Sense</span></div>
        <div className="auth-subtitle">
          {mode === 'login' ? 'Sign in to your account' : 'Create a new account'}
        </div>

        {/* Mode toggle */}
        <div className="auth-toggle">
          <button
            className={mode === 'login' ? 'active' : ''}
            onClick={() => switchMode('login')}
          >Login</button>
          <button
            className={mode === 'signup' ? 'active' : ''}
            onClick={() => switchMode('signup')}
          >Sign Up</button>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          {error   && <div className="auth-error">⚠ {error}</div>}
          {success && <div className="auth-success">✓ {success}</div>}

          <div className="auth-field">
            <label>Username</label>
            <input
              type="text"
              placeholder="e.g. john_doe"
              value={username}
              onChange={e => setUsername(e.target.value)}
              autoComplete="username"
              maxLength={50}
            />
          </div>

          <div className="auth-field">
            <label>Password</label>
            <input
              type="password"
              placeholder="Min 6 characters"
              value={password}
              onChange={e => setPassword(e.target.value)}
              autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
            />
          </div>

          <button type="submit" className="auth-btn" disabled={loading}>
            {loading
              ? <><span className="auth-spinner" />{mode === 'login' ? 'Signing in...' : 'Creating account...'}</>
              : mode === 'login' ? 'Sign In →' : 'Create Account →'
            }
          </button>
        </form>

        {/* ✅ Show which account is currently logged in */}
        {localStorage.getItem('username') && (
          <div className="auth-logged-in">
            Currently logged in as <strong>{localStorage.getItem('username')}</strong>
          </div>
        )}

        <div className="auth-footer">
          <button className="auth-skip" onClick={() => setPage('home')}>
            ← Back to Home
          </button>
        </div>
      </div>
    </div>
  );
}