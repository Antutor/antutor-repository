import React, { useState, useEffect } from 'react';
import { ChevronLeft, BookOpen, TrendingUp, Globe } from 'lucide-react';
import './ConceptDictionary.css';
import { t } from './locales';


const ConceptDictionary = ({ isOpen, onClose, initialSearchTerm, cameFromScaffolding, onReturnWithHint, language, onLanguageChange }) => {
  const [shouldRender, setShouldRender] = useState(false);

  const [concepts, setConcepts] = useState([]);

  useEffect(() => {
    // Re-fetch whenever language changes
    setConcepts([]);
  }, [language]);

  useEffect(() => {
    if (isOpen) {
      setShouldRender(true);
    } else {
      const timer = setTimeout(() => setShouldRender(false), 300);
      return () => clearTimeout(timer);
    }
  }, [isOpen, initialSearchTerm, concepts, language]);

  if (!shouldRender) return null;



  return (
    <div className={`dictionary-overlay ${isOpen ? 'active' : ''}`}>
      <div className="dictionary-container">

        {/* Header */}
        <header className="dict-header">
          <div className="dict-header-left">
            <button className="back-btn" onClick={onClose}>
              <ChevronLeft size={20} />
              <span>{t(language, 'backToSession')}</span>
            </button>
            <h2>{t(language, 'conceptDictTitle')}</h2>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            {onLanguageChange && (
              <select
                value={language}
                onChange={(e) => onLanguageChange(e.target.value)}
                style={{
                  padding: '6px 10px',
                  borderRadius: '8px',
                  border: '1px solid var(--color-border)',
                  backgroundColor: 'var(--color-bg-light)',
                  color: 'var(--color-deep-navy)',
                  fontWeight: '600',
                  fontSize: '0.8rem',
                  cursor: 'pointer'
                }}
              >
                <option value="ko">🇰🇷 한국어</option>
                <option value="en">🇺🇸 English</option>
              </select>
            )}
          </div>
        </header>

        {/* Content Body */}
        <div className="dict-body" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%', minHeight: '300px' }}>
          <div style={{ textAlign: 'center', color: 'var(--color-text-secondary)' }}>
            <BookOpen size={48} style={{ opacity: 0.2, marginBottom: '20px' }} />
            <h3 style={{ fontSize: '1.2rem', fontWeight: '600', marginBottom: '10px' }}>
              {language === 'ko' ? '테스트 기간이 끝난 후 다시 공개될 예정입니다' : 'It will be revealed again after the test period'}
            </h3>
            <p style={{ opacity: 0.7 }}>
              {language === 'ko' ? '불편을 드려 죄송합니다.' : 'We apologize for the inconvenience.'}
            </p>
          </div>
        </div>
      </div>
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default ConceptDictionary;
