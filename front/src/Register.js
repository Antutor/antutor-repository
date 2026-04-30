import React, { useState } from 'react';
import { Lock, ArrowRight, User, CheckCircle } from 'lucide-react';
import { authAPI } from './api/services';
import './Login.css'; // Reusing Login.css for identical styling

const Register = ({ onGoToLogin }) => {
  const [userId, setUserId] = useState('');
  const [password, setPassword] = useState('');
  const [isIdChecked, setIsIdChecked] = useState(false);
  const [isFadingOut, setIsFadingOut] = useState(false);

  const handleCheckId = async (e) => {
    e.preventDefault();
    if (!userId) {
      alert("아이디를 입력해주세요.");
      return;
    }
    if (!/^[A-Za-z0-9]{4,}$/.test(userId)) {
      alert("아이디는 영어 또는 숫자로만 4자리 이상 입력해야 합니다.");
      return;
    }
    try {
      const response = await authAPI.checkUsername(userId);
      if (response.data && response.data.available) {
        alert("사용 가능한 아이디입니다!");
        setIsIdChecked(true);
      } else {
        alert("이미 사용중인 아이디입니다.");
        setIsIdChecked(false);
      }
    } catch (error) {
      console.error("Duplicate check error:", error);
      if (!error.response) {
        alert("서버와 연결할 수 없습니다. 로컬 백엔드 서버가 실행 중인지 확인해주세요.");
      } else if (error.response.status === 400 || error.response.status === 409) {
        alert("이미 사용중인 아이디입니다.");
      } else {
        alert("중복 확인에 실패했습니다.");
      }
      setIsIdChecked(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!isIdChecked) {
      alert("아이디 중복 확인을 해주세요.");
      return;
    }
    if (!/^[A-Za-z0-9]{4,}$/.test(password)) {
      alert("비밀번호는 영어 또는 숫자로만 4자리 이상 입력해야 합니다.");
      return;
    }
    if (userId && password) {
      try {
        await authAPI.register({ username: userId, password });
        alert("가입 성공!");
        setIsFadingOut(true);
        setTimeout(() => {
          onGoToLogin();
        }, 500);
      } catch (error) {
        alert("회원가입에 실패했습니다.");
      }
    }
  };

  return (
    <div className={`login-page ${isFadingOut ? 'fade-out' : ''}`}>
      <div className="login-card">
        <div className="login-header">
          <img src="/images/antutor%20standup.png" alt="Antutor" className="login-logo-img" />
          <h2>Antutor 가입하기</h2>
          <p>계정을 만들고 학습을 시작하세요.</p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          <div className="input-group">
            <label>아이디</label>
            <div style={{ display: 'flex', gap: '8px' }}>
              <div className="input-field" style={{ flex: 1 }}>
                <User size={18} className="input-icon" />
                <input 
                  type="text" 
                  placeholder="아이디를 입력하세요"
                  value={userId}
                  onChange={(e) => { setUserId(e.target.value); setIsIdChecked(false); }}
                  required
                  disabled={isIdChecked}
                />
              </div>
              <button 
                type="button" 
                onClick={handleCheckId}
                style={{
                  padding: '0 12px',
                  borderRadius: '10px',
                  border: isIdChecked ? 'none' : '1px solid var(--color-border)',
                  background: isIdChecked ? '#10b981' : 'var(--color-bg-light)', /* green 500 equivalent */
                  color: isIdChecked ? 'white' : 'var(--color-deep-navy)',
                  fontWeight: '600',
                  cursor: 'pointer',
                  minWidth: '95px'
                }}
              >
                {isIdChecked ? <CheckCircle size={18} style={{ margin: '0 auto' }} /> : '중복 확인'}
              </button>
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
            <span>가입하기</span>
            <ArrowRight size={18} />
          </button>
        </form>

        <div className="login-footer">
          이미 계정이 있으신가요? <span className="signup-link" onClick={onGoToLogin}>로그인</span>
        </div>
      </div>
    </div>
  );
};

export default Register;
