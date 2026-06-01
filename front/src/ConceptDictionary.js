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
    if (isOpen && concepts.length === 0) {
      setLoading(true);
      dictionaryAPI.getList(language)
        .then(res => {
          const formatted = res.data.map(c => ({
            id: c.term,
            title: c.term,
            definition: c.simple_definition || c.definition || (language === 'ko' ? '내용이 없습니다.' : 'No content available.')
          }));
          setConcepts(formatted);
          if (initialSearchTerm) {
            setSearchTerm(initialSearchTerm);
            setExpandedCardId(initialSearchTerm);
          }
        })
        .catch(err => console.error("Failed to fetch dictionary", err))
        .finally(() => setLoading(false));
    }
  }, [isOpen, language, concepts.length, initialSearchTerm]);

  useEffect(() => {
    if (isOpen) {
      setShouldRender(true);
    } else {
      const timer = setTimeout(() => setShouldRender(false), 300);
      return () => clearTimeout(timer);
    }
  }, [isOpen]);

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

          <div className="dict-search-wrapper">
            <Search size={18} className="search-icon" />
            <input 
              type="text" 
              placeholder={language === 'ko' ? "개념 검색..." : "Search concepts..."} 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
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
        <div className="dict-body">
          {loading ? (
            <div style={{ textAlign: 'center', padding: '60px 20px' }}>
              <div style={{ display: 'inline-block', width: '30px', height: '30px', border: '3px solid rgba(59, 130, 246, 0.3)', borderTopColor: 'var(--color-expert-academic)', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
            </div>
          ) : filteredConcepts.length > 0 ? (
            <div className="concepts-grid">
              {filteredConcepts.map(concept => (
                <div 
                  key={concept.id} 
                  className={`concept-card ${expandedCardId === concept.id ? 'extended' : ''} ${concept.id === initialSearchTerm ? 'highlighted-card' : ''}`}
                  onClick={() => setExpandedCardId(expandedCardId === concept.id ? null : concept.id)}
                >
                  <div className="card-top">
                    <h3>{concept.title}</h3>
                  </div>
                  
                  {expandedCardId !== concept.id ? (
                    <p className="card-definition">
                      {splitFirstParagraph(concept.definition).first}
                      <span style={{ color: 'var(--color-expert-academic)', fontSize: '0.85rem', fontWeight: '600', marginLeft: '5px' }}>
                        {language === 'ko' ? '... 더 보기' : '... Read More'}
                      </span>
                    </p>
                  ) : (
                    <div className="card-expanded-content" onClick={e => e.stopPropagation()}>
                      <p className="card-definition">{formatTextWithLineBreaks(concept.definition)}</p>
                      
                      {cameFromScaffolding && concept.id === initialSearchTerm && (
                        <div className="scaffolding-hint-bridge">
                          <button className="hint-btn" onClick={() => onReturnWithHint && onReturnWithHint(concept.definition)}>
                            <ArrowRight size={16} />
                            {language === 'ko' ? '이 개념을 힌트로 답변하기' : 'Use this concept as a hint'}
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="no-results">
              {language === 'ko' ? '검색 결과가 없습니다.' : 'No results found.'}
            </div>
          )}
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
