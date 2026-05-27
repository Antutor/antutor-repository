/* eslint-disable no-unused-vars */
import React, { useState, useEffect } from 'react';
import { Search, ChevronLeft, BookOpen, TrendingUp, Globe, ArrowRight } from 'lucide-react';
import './ConceptDictionary.css';
import { dictionaryAPI } from './api/services';
import { t } from './locales';

const getExpertTags = (lang) => ({
  academic: { name: t(lang, 'dictCatAcademic'), icon: BookOpen, color: '#10b981', bg: 'rgba(16, 185, 129, 0.1)' },
  market: { name: t(lang, 'dictCatMarket'), icon: TrendingUp, color: '#059669', bg: 'rgba(5, 150, 105, 0.1)' },
  macro: { name: t(lang, 'dictCatMacro'), icon: Globe, color: '#8b5cf6', bg: 'rgba(139, 92, 246, 0.1)' }
});

const formatTextWithLineBreaks = (text) => {
    if (!text) return null;
    
    // Convert any form of literal \n or escaped newlines to a standard marker
    let processedText = String(text)
        .replace(/\\\\n/g, '\n')
        .replace(/\\n/g, '\n')
        .replace(/\\r/g, '')
        .replace(/\r\n/g, '\n')
        .replace(/\r/g, '\n');
        
    return processedText.split('\n').map((line, index) => {
        // Identify mathematical expressions within brackets or parentheses that contain numbers and operators
        const mathRegex = /(\[[^\]]+\]|\([^)]+\))/g;
        const parts = line.split(mathRegex);
        
        return (
            <span key={index} style={{ lineHeight: '1.8' }}>
                {parts.map((part, pIndex) => {
                    // Match pattern like [ ... ] or ( ... ) containing numbers and math operators
                    if (mathRegex.test(part) && /[+\-×/^%]/.test(part) && /\d/.test(part)) {
                        const subParts = part.split(/(\^\d+)/);
                        return (
                            <span key={pIndex} className="math-formula" style={{
                                backgroundColor: '#f0fdf4',
                                border: '1px solid #bbf7d0',
                                padding: '1px 6px',
                                borderRadius: '6px',
                                fontFamily: "'Consolas', 'Courier New', monospace",
                                fontWeight: '600',
                                color: '#166534',
                                margin: '0 3px',
                                display: 'inline-block',
                                letterSpacing: '0.5px'
                            }}>
                                {subParts.map((sp, spIndex) => {
                                    if (sp.startsWith('^')) {
                                        return <sup key={spIndex} style={{ fontSize: '0.7em', marginLeft: '1px' }}>{sp.slice(1)}</sup>;
                                    }
                                    return sp;
                                })}
                            </span>
                        );
                    }
                    return part;
                })}
                <br />
            </span>
        );
    });
};

const splitFirstParagraph = (text) => {
    if (!text) return { first: "", rest: "" };
    
    let processedText = String(text)
        .replace(/\\\\n/g, '\n')
        .replace(/\\n/g, '\n')
        .replace(/\\r/g, '')
        .replace(/\r\n/g, '\n')
        .replace(/\r/g, '\n');
        
    const lines = processedText.split('\n');
    let firstLine = "";
    let restLines = [];
    
    for (let i = 0; i < lines.length; i++) {
        if (!firstLine && lines[i].trim().length > 0) {
            firstLine = lines[i];
        } else if (firstLine) {
            restLines.push(lines[i]);
        }
    }
    
    return {
        first: firstLine,
        rest: restLines.join('\n').trim()
    };
};

const ConceptDictionary = ({ isOpen, onClose, initialSearchTerm, cameFromScaffolding, onReturnWithHint, language, onLanguageChange }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [shouldRender, setShouldRender] = useState(false);
  const [expandedCardId, setExpandedCardId] = useState(null);

  const [concepts, setConcepts] = useState([]);
  const [loading, setLoading] = useState(false);

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

  const filteredConcepts = concepts.filter(concept =>
    concept.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    concept.definition.toLowerCase().includes(searchTerm.toLowerCase())
  );

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
