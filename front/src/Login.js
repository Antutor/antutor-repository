import React, { useState } from 'react';
import { Mail, Lock, ArrowRight, User } from 'lucide-react';
import { authAPI } from './api/services';
import './Login.css';

const Login = ({ onLogin, onGoToRegister }) => {
  const [userId, setUserId] = useState('');
  const [password, setPassword] = useState('');
  const [isFadingOut, setIsFadingOut] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (userId && password) {
      try {
        const response = await authAPI.login({ username: userId, password });
        if (response.data.access_token) {
          localStorage.setItem('access_token', response.data.access_token);
        }
        setIsFadingOut(true);
        setTimeout(() => {
          onLogin();
        }, 500); // 500ms coordinates with the CSS transition length
      } catch (error) {
        alert("Login failed! Please check your credentials.");
      }
    }
  };

  return (
    <div className={`login-page ${isFadingOut ? 'fade-out' : ''}`}>
      <div className="login-card">

        <div className="login-header">
          <img src="/images/antutor%20standup.png" alt="Antutor" className="login-logo-img" />
          <h2>Antutor에 오신 것을 환영합니다</h2>
          <p>학습 대시보드에 접속하려면 로그인하세요.</p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          <div className="input-group">
            <label>아이디</label>
            <div className="input-field">
              <User size={18} className="input-icon" />
              <input
                type="text"
                placeholder="아이디를 입력하세요"
                value={userId}
                onChange={(e) => setUserId(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="input-group">
            <label>비밀번호</label>
            <div className="input-field">
              <Lock size={18} className="input-icon" />
              <input
                type="password"
                placeholder="비밀번호를 입력하세요"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
          </div>

          <button type="submit" className="login-submit-btn">
            <span>로그인</span>
            <ArrowRight size={18} />
          </button>
        </form>

        <div className="login-footer">
          계정이 없으신가요? <span className="signup-link" onClick={onGoToRegister}>회원가입</span>
        </div>
      </div>
    </div>
  );
};

export default Login;
