import React, { useState, useEffect } from 'react';
import { Search, ChevronLeft, BookOpen, TrendingUp, Globe, ArrowRight } from 'lucide-react';
import './ConceptDictionary.css';
import { dictionaryAPI } from './api/services';

const EXPERT_TAGS = {
  academic: { name: '학술', icon: BookOpen, color: 'var(--color-expert-academic)', bg: 'rgba(59, 130, 246, 0.1)' },
  market: { name: '시장', icon: TrendingUp, color: 'var(--color-expert-market)', bg: 'rgba(16, 185, 129, 0.1)' },
  macro: { name: '매크로', icon: Globe, color: 'var(--color-expert-macro)', bg: 'rgba(139, 92, 246, 0.1)' }
};

const ConceptDictionary = ({ isOpen, onClose, initialSearchTerm, cameFromScaffolding, onReturnWithHint }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [shouldRender, setShouldRender] = useState(false);
  const [expandedCardId, setExpandedCardId] = useState(null);
  
  const [concepts, setConcepts] = useState([]);
  const [loading, setLoading] = useState(false);

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
                  const listRes = await dictionaryAPI.getList();
                  const detailedConcepts = await Promise.all(
                      listRes.data.map(async (term) => {
                          const detailRes = await dictionaryAPI.getDetail(term);
                          return {
                              id: detailRes.data.term,
                              title: detailRes.data.term,
                              definition: detailRes.data.simple_definition,
                              details: detailRes.data.example,
                              expert: 'academic',
                              hint: detailRes.data.simple_definition
                          };
                      })
                  );
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
  }, [isOpen, initialSearchTerm, concepts]);

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
              <span>세션으로 돌아가기</span>
            </button>
            <h2>개념 사전</h2>
          </div>
          
          <div className="dict-search-wrapper">
            <Search size={18} className="search-icon" />
            <input 
              type="text" 
              placeholder="경제 용어 검색..." 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </header>

        {/* Content Body */}
        <div className="dict-body">
          {loading ? (
             <div className="loading-state" style={{ textAlign: 'center', padding: '40px', color: 'var(--color-text-secondary)' }}>
                <div style={{ display: 'inline-block', width: '30px', height: '30px', border: '3px solid rgba(59, 130, 246, 0.3)', borderTopColor: 'var(--color-expert-academic)', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
                <p style={{ marginTop: '15px' }}>사전 불러오는 중...</p>
             </div>
          ) : filteredConcepts.length === 0 ? (
            <div className="no-results">
              <p>"{searchTerm}"에 대한 검색 결과가 없습니다.</p>
            </div>
          ) : (
            <div className="concepts-grid">
              {filteredConcepts.map(concept => {
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
                            <h4>예시:</h4>
                            <p>{concept.details}</p>
                          </div>

                          {/* Scaffolding Dynamic Integration */}
                          {cameFromScaffolding && (
                            <div className="scaffolding-hint-bridge">
                               <button className="hint-btn" onClick={(e) => { e.stopPropagation(); onReturnWithHint(concept.hint); }}>
                                 <span>힌트와 함께 채팅으로 돌아가기</span>
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
