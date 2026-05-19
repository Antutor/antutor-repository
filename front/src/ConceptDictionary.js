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
      if (initialSearchTerm) {
        setSearchTerm(initialSearchTerm);
        const match = concepts.find(c => c.title.toLowerCase().includes(initialSearchTerm.toLowerCase()));
        if (match) setExpandedCardId(match.id);
      } else {
        setSearchTerm('');
        setExpandedCardId(null);
      }

      if (concepts.length === 0) {
        const fetchConcepts = async () => {
          setLoading(true);
          try {
            const listRes = await dictionaryAPI.getList(language);
            const detailedConcepts = listRes.data.map((item) => ({
              id: item.term,
              title: item.term,
              definition: item.simple_definition,
              details: item.example || "",
              expert: 'academic',
              hint: item.simple_definition
            }));
            setConcepts(detailedConcepts);
          } catch (error) {
            console.error("Failed to load dictionary:", error);
          } finally {
            setLoading(false);
          }
        };
        fetchConcepts();
      }
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
            <div className="dict-search-wrapper">
              <Search size={18} className="search-icon" />
              <input
                type="text"
                placeholder={t(language, 'searchTermsPlaceholder')}
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          </div>
        </header>

        {/* Content Body */}
        <div className="dict-body">
          {loading ? (
            <div className="loading-state" style={{ textAlign: 'center', padding: '40px', color: 'var(--color-text-secondary)' }}>
              <div style={{ display: 'inline-block', width: '30px', height: '30px', border: '3px solid rgba(59, 130, 246, 0.3)', borderTopColor: 'var(--color-expert-academic)', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
              <p style={{ marginTop: '15px' }}>{t(language, 'loadingDict')}</p>
            </div>
          ) : filteredConcepts.length === 0 ? (
            <div className="no-results">
              <p>"{searchTerm}"{t(language, 'noResult')}</p>
            </div>
          ) : (
            <div className="concepts-grid">
              {filteredConcepts.map(concept => {
                const EXPERT_TAGS = getExpertTags(language);
                const tag = EXPERT_TAGS[concept.expert];
                const TagIcon = tag.icon;
                const isExpanded = expandedCardId === concept.id || (initialSearchTerm && concept.title.toLowerCase().includes(initialSearchTerm.toLowerCase()));

                return (
                  <div
                    key={concept.id}
                    className={`concept-card ${isExpanded ? 'highlighted-card extended' : ''}`}
                    onClick={() => setExpandedCardId(isExpanded ? null : concept.id)}
                  >
                    <div className="card-top">
                      <div className="expert-tag" style={{ color: tag.color, backgroundColor: tag.bg, borderColor: tag.color }}>
                        <TagIcon size={14} />
                        <span>{tag.name}</span>
                      </div>
                      <h3>{concept.title}</h3>
                    </div>

                    <p className="card-definition">{concept.definition}</p>

                    {isExpanded && (
                      <div className="card-expanded-content" onClick={e => e.stopPropagation()}>

                        <div className="insights-block">
                          <h4>{t(language, 'example')}</h4>
                          <p>{concept.details}</p>
                        </div>

                        {/* Scaffolding Dynamic Integration */}
                        {cameFromScaffolding && (
                          <div className="scaffolding-hint-bridge">
                            <button className="hint-btn" onClick={(e) => { e.stopPropagation(); onReturnWithHint(concept.hint); }}>
                              <span>{t(language, 'returnWithHint')}</span>
                              <ArrowRight size={16} />
                            </button>
                          </div>
                        )}

                      </div>
                    )}
                  </div>
                );
              })}
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
