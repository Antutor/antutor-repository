import React, { useState } from 'react';
import { Lock, ArrowRight, User } from 'lucide-react';
import { authAPI } from './api/services';
import { t } from './locales';
import './Login.css';

const Login = ({ onLogin, onGoToRegister, language, onLanguageChange }) => {
  const [userId, setUserId] = useState('');
  const [password, setPassword] = useState('');
  const [isFadingOut, setIsFadingOut] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!userId) {
      alert(t(language, 'enterUserId'));
      return;
    }
    if (!password) {
      alert(t(language, 'loginPasswordPlaceholder'));
      return;
    }
    try {
      const response = await authAPI.login({ username: userId, password });
      if (response.data.access_token) {
        localStorage.setItem('access_token', response.data.access_token);
      }
      setIsFadingOut(true);
      setTimeout(() => { onLogin(userId); }, 500);
    } catch (error) {
      alert(t(language, 'loginFailed'));
    }
  };

  return (
    <div className={`login-page ${isFadingOut ? 'fade-out' : ''}`}>
      <div className="login-card">
        {/* Left Side: Visual Panel */}
        <div className="login-visual-panel">
          <img src="/images/antutor%20standup.png" alt="Antutor" className="login-logo-img" />
          <div className="login-header">
            <h2>{t(language, 'loginWelcome')}</h2>
            <p>{t(language, 'loginSubtitle')}</p>
          </div>
        </div>

        {/* Right Side: Form Panel */}
        <div className="login-form-panel">
          {/* Language Toggle */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '20px' }}>
            <select
              value={language}
              onChange={(e) => onLanguageChange(e.target.value)}
              style={{
                padding: '6px 12px',
                borderRadius: '8px',
                border: '1px solid var(--color-border)',
                backgroundColor: 'var(--color-bg-light)',
                color: 'var(--color-deep-navy)',
                fontWeight: '600',
                fontSize: '0.85rem',
                cursor: 'pointer'
              }}
            >
              <option value="ko">🇰🇷 한국어</option>
              <option value="en">🇺🇸 English</option>
            </select>
          </div>

          {/* noValidate disables browser-native tooltips; JS handles validation */}
          <form onSubmit={handleSubmit} className="login-form" noValidate>
            <div className="input-group">
              <label>{t(language, 'loginUserId')}</label>
              <div className="input-field">
                <User size={18} className="input-icon" />
                <input
                  type="text"
                  placeholder={t(language, 'loginUserIdPlaceholder')}
                  value={userId}
                  onChange={(e) => setUserId(e.target.value)}
                />
              </div>
            </div>

            <div className="input-group">
              <label>{t(language, 'loginPassword')}</label>
              <div className="input-field">
                <Lock size={18} className="input-icon" />
                <input
                  type="text"
                  style={{ WebkitTextSecurity: 'disc' }}
                  autoComplete="off"
                  placeholder={t(language, 'loginPasswordPlaceholder')}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>
            </div>

            <button type="submit" className="login-submit-btn">
              <span>{t(language, 'loginBtn')}</span>
              <ArrowRight size={18} />
            </button>
          </form>

          <div className="login-footer" style={{ marginTop: '24px' }}>
            {t(language, 'noAccount')} <span className="signup-link" onClick={onGoToRegister}>{t(language, 'signUp')}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
