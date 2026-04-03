import React, { useState } from 'react';
import { Mail, Lock, ArrowRight, User } from 'lucide-react';
import './Login.css';

const Login = ({ onLogin }) => {
  const [userId, setUserId] = useState('');
  const [password, setPassword] = useState('');
  const [isFadingOut, setIsFadingOut] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    if(userId && password) {
      setIsFadingOut(true);
      setTimeout(() => {
        onLogin();
      }, 500); // 500ms coordinates with the CSS transition length
    }
  };

  return (
    <div className={`login-page ${isFadingOut ? 'fade-out' : ''}`}>
      <div className="login-card">
        
        <div className="login-header">
          <img src="/images/reading_ant.png" alt="Antutor" className="login-logo-img" />
          <h2>Welcome to Antutor</h2>
          <p>Login to access your personalized learning dashboard.</p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          <div className="input-group">
            <label>ID</label>
            <div className="input-field">
              <User size={18} className="input-icon" />
              <input 
                type="text" 
                placeholder="Enter your ID"
                value={userId}
                onChange={(e) => setUserId(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="input-group">
            <label>Password</label>
            <div className="input-field">
              <Lock size={18} className="input-icon" />
              <input 
                type="password" 
                placeholder="Enter password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
          </div>

          <button type="submit" className="login-submit-btn">
            <span>Sign In</span>
            <ArrowRight size={18} />
          </button>
        </form>

        <div className="login-footer">
          Don't have an account? <span className="signup-link">Sign up</span>
        </div>
      </div>
    </div>
  );
};

export default Login;
