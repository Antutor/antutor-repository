import React, { useState } from 'react';
import { Lock, ArrowRight, User, CheckCircle } from 'lucide-react';
import { authAPI } from './api/services';
import { t } from './locales';
import './Login.css';

const Register = ({ onGoToLogin, language = 'ko', onLanguageChange }) => {
  const [userId, setUserId] = useState('');
  const [password, setPassword] = useState('');
  const [isIdChecked, setIsIdChecked] = useState(false);
  const [isFadingOut, setIsFadingOut] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleCheckId = async (e) => {
    e.preventDefault();
    if (isSubmitting) return;
    if (!userId) {
      alert(t(language, 'enterUserId'));
      return;
    }
    if (!/^[a-z0-9]{4,}$/.test(userId)) {
      alert(t(language, 'invalidUserId'));
      return;
    }
    setIsSubmitting(true);
    try {
      const response = await authAPI.checkUsername(userId);
      if (response.data && response.data.available) {
        alert(t(language, 'usernameAvailable'));
        setIsIdChecked(true);
      } else {
        alert(t(language, 'usernameTaken'));
        setIsIdChecked(false);
      }
    } catch (error) {
      console.error("Duplicate check error:", error);
      if (!error.response) {
        alert(t(language, 'serverConnectionError'));
      } else if (error.response.status === 400 || error.response.status === 409) {
        alert(t(language, 'usernameTaken'));
      } else {
        alert(t(language, 'registerFailed'));
      }
      setIsIdChecked(false);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (isSubmitting) return;
    if (!isIdChecked) {
      alert(t(language, 'checkIdFirst'));
      return;
    }
    if (!password) {
      alert(t(language, 'loginPasswordPlaceholder'));
      return;
    }
    if (!/^[a-z0-9]{4,}$/.test(password)) {
      alert(t(language, 'invalidPassword'));
      return;
    }
    setIsSubmitting(true);
    try {
      await authAPI.register({ username: userId, password });
      alert(t(language, 'registerSuccess'));
      setIsFadingOut(true);
      setTimeout(() => { onGoToLogin(); }, 500);
    } catch (error) {
      alert(t(language, 'registerFailed'));
      setIsSubmitting(false);
    }
  };

  return (
    <div className={`login-page ${isFadingOut ? 'fade-out' : ''}`}>
      <div className="login-card">
        {/* Left Side: Visual Panel */}
        <div className="login-visual-panel">
          <img src="/images/antutor%20standup.png" alt="Antutor" className="login-logo-img" />
          <div className="login-header">
            <h2>{t(language, 'registerTitle')}</h2>
            <p>{t(language, 'registerSubtitle')}</p>
          </div>
        </div>

        {/* Right Side: Form Panel */}
        <div className="login-form-panel">
          {/* Language Toggle */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '20px' }}>
            <select
              value={language}
              onChange={(e) => onLanguageChange && onLanguageChange(e.target.value)}
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

          {/* noValidate: disable browser-native validation tooltips, JS handles all */}
          <form onSubmit={handleSubmit} className="login-form" noValidate>
            <div className="input-group">
              <label>{t(language, 'loginUserId')}</label>
              <div style={{ display: 'flex', gap: '8px' }}>
                <div className="input-field" style={{ flex: 1 }}>
                  <User size={18} className="input-icon" />
                  <input
                    type="text"
                    placeholder={t(language, 'loginUserIdPlaceholder')}
                    value={userId}
                    onChange={(e) => { setUserId(e.target.value); setIsIdChecked(false); }}
                    disabled={isIdChecked}
                  />
                </div>
                <button
                  type="button"
                  onClick={handleCheckId}
                  disabled={isIdChecked || isSubmitting}
                  style={{
                    padding: '0 12px',
                    borderRadius: '10px',
                    border: isIdChecked ? 'none' : '1px solid var(--color-border)',
                    background: isIdChecked ? '#10b981' : (isSubmitting ? 'var(--color-border)' : 'var(--color-bg-light)'),
                    color: isIdChecked ? 'white' : 'var(--color-deep-navy)',
                    fontWeight: '600',
                    cursor: (isIdChecked || isSubmitting) ? 'not-allowed' : 'pointer',
                    minWidth: '95px'
                  }}
                >
                  {isIdChecked ? <CheckCircle size={18} style={{ margin: '0 auto' }} /> : (isSubmitting ? '...' : t(language, 'checkDuplicate'))}
                </button>
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
            
            <div style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)', marginBottom: '20px', textAlign: 'left', paddingLeft: '5px' }}>
              * {t(language, 'inputRule')}
            </div>

            <button type="submit" className="login-submit-btn" disabled={isSubmitting} style={{ opacity: isSubmitting ? 0.7 : 1, cursor: isSubmitting ? 'not-allowed' : 'pointer' }}>
              <span>{isSubmitting ? '처리 중...' : t(language, 'registerBtn')}</span>
              <ArrowRight size={18} />
            </button>
          </form>

          <div className="login-footer" style={{ marginTop: '24px' }}>
            {t(language, 'alreadyHaveAccount')} <span className="signup-link" onClick={onGoToLogin}>{t(language, 'goToLogin')}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Register;
