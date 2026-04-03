import React, { useState, useEffect } from 'react';
import { Search, ChevronLeft, BookOpen, TrendingUp, Globe, PenTool, ArrowRight, CheckCircle, XCircle } from 'lucide-react';
import './ConceptDictionary.css';

const EXPERT_TAGS = {
  academic: { name: 'Academic', icon: BookOpen, color: 'var(--color-expert-academic)', bg: 'rgba(59, 130, 246, 0.1)' },
  market: { name: 'Market', icon: TrendingUp, color: 'var(--color-expert-market)', bg: 'rgba(16, 185, 129, 0.1)' },
  macro: { name: 'Macro', icon: Globe, color: 'var(--color-expert-macro)', bg: 'rgba(139, 92, 246, 0.1)' }
};

const CONCEPTS = [
  {
    id: 'qe',
    title: 'Quantitative Easing',
    definition: 'A monetary policy in which a central bank purchases predetermined amounts of government bonds or other financial assets in order to inject money into the economy to expand economic activity.',
    expert: 'academic',
    details: 'Increases money supply, lowers interest rates, aims to stimulate spending.',
    caseStudy: 'In response to the 2008 financial crisis, the U.S. Federal Reserve implemented massive QE to stabilize the plummeting stock market and lower long-term interest rates.',
    testQuestion: {
      question: 'True or False: Quantitative Easing generally decreases the overall money supply in an economy.',
      answer: false,
      explanation: 'False. QE involves central banks buying assets, which directly injects cash and *increases* the money supply.'
    },
    hint: 'Quantitative Easing involves central banks injecting money to stimulate the economy.'
  },
  {
    id: 'inflation',
    title: 'Inflation',
    definition: 'The rate at which the general level of prices for goods and services is rising, and, consequently, the purchasing power of currency is falling.',
    expert: 'macro',
    details: 'Central banks attempt to limit this, and avoid deflation, to keep the economy running smoothly.',
    caseStudy: 'During the 1970s, the US experienced "stagflation" – a period of high inflation combined with economic stagnation, prompting extreme interest rate hikes.',
    testQuestion: {
      question: 'True or False: High inflation means your savings can buy fewer goods today than they could yesterday.',
      answer: true,
      explanation: 'True. Inflation erodes the purchasing power of money over time.'
    },
    hint: 'Inflation means prices rise, so money buys less than it used to.'
  },
  {
    id: 'gdp',
    title: 'Gross Domestic Product (GDP)',
    definition: 'The total monetary or market value of all the finished goods and services produced within a country borders in a specific time period.',
    expert: 'market',
    details: 'Functions as a comprehensive scorecard of a given country’s economic health.',
    caseStudy: 'China experienced explosive GDP growth starting in the 1990s due to globalization and manufacturing booms, becoming the world\'s second-largest economy.',
    testQuestion: {
      question: 'True or False: If you buy a used car, it adds to this year\'s GDP calculation.',
      answer: false,
      explanation: 'False. GDP only calculates the value of newly produced goods and services during a specific period.'
    },
    hint: 'GDP measures total new goods/services produced by a country in a year.'
  },
  {
    id: 'interest_rates',
    title: 'Interest Rates',
    definition: 'The amount charged on top of the principal by a lender to a borrower for the use of assets.',
    expert: 'macro',
    details: 'A tool used by central banks to control monetary policy.',
    caseStudy: 'In 2022, central banks globally raised interest rates rapidly to combat persistent post-pandemic inflation by cooling down borrowing and spending.',
    testQuestion: {
      question: 'True or False: Lowering interest rates makes it cheaper for businesses to borrow money for expansion.',
      answer: true,
      explanation: 'True. Lower rates reduce the cost of loans, encouraging spending and investment.'
    },
    hint: 'Interest rates regulate borrowing costs; lower rates encourage borrowing and spending.'
  },
  {
    id: 'supply_demand',
    title: 'Supply and Demand',
    definition: 'An economic model of price determination in a market. It postulates that in a competitive market, the unit price for a particular good will vary until it settles at a point where the quantity demanded will equal the quantity supplied.',
    expert: 'academic',
    details: 'The fundamental concept underlying all market economics.',
    caseStudy: 'During the early pandemic, the demand for semiconductor chips outstripped supply drastically, causing huge delays and price spikes in the automotive and tech industries.',
    testQuestion: {
      question: 'True or False: If demand increases while supply stays the same, prices typically go down.',
      answer: false,
      explanation: 'False. If demand is high and supply is limited, prices will naturally increase.'
    },
    hint: 'Prices rise when demand exceeds supply, and fall when supply exceeds demand.'
  }
];

const ConceptDictionary = ({ isOpen, onClose, initialSearchTerm, cameFromScaffolding, onReturnWithHint }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [shouldRender, setShouldRender] = useState(false);
  const [expandedCardId, setExpandedCardId] = useState(null);
  const [testState, setTestState] = useState({}); // { cardId: { active: boolean, answered: boolean, result: boolean } }

  useEffect(() => {
    if (isOpen) {
      setShouldRender(true);
      if (initialSearchTerm) {
        setSearchTerm(initialSearchTerm);
        // Expand specifically if it matches exactly
        const match = CONCEPTS.find(c => c.title.toLowerCase().includes(initialSearchTerm.toLowerCase()));
        if (match) {
           setExpandedCardId(match.id);
        }
      } else {
        setSearchTerm('');
        setExpandedCardId(null);
      }
      setTestState({}); // resets test state on reopen
    } else {
      const timer = setTimeout(() => setShouldRender(false), 300);
      return () => clearTimeout(timer);
    }
  }, [isOpen, initialSearchTerm]);

  if (!shouldRender) return null;

  const filteredConcepts = CONCEPTS.filter(concept =>
    concept.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    concept.definition.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const startTest = (e, id) => {
    e.stopPropagation();
    setTestState(prev => ({ ...prev, [id]: { active: true, answered: false, result: null } }));
  };

  const handleAnswer = (e, id, answerGiven, correctAnswer) => {
    e.stopPropagation();
    setTestState(prev => ({ 
      ...prev, 
      [id]: { active: true, answered: true, result: answerGiven === correctAnswer } 
    }));
  };

  return (
    <div className={`dictionary-overlay ${isOpen ? 'active' : ''}`}>
      <div className="dictionary-container">
        
        {/* Header */}
        <header className="dict-header">
          <div className="dict-header-left">
            <button className="back-btn" onClick={onClose}>
              <ChevronLeft size={20} />
              <span>Back to Session</span>
            </button>
            <h2>Concept Dictionary</h2>
          </div>
          
          <div className="dict-search-wrapper">
            <Search size={18} className="search-icon" />
            <input 
              type="text" 
              placeholder="Search economic concepts..." 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </header>

        {/* Content Body */}
        <div className="dict-body">
          {filteredConcepts.length === 0 ? (
            <div className="no-results">
              <p>No concepts found for "{searchTerm}".</p>
            </div>
          ) : (
            <div className="concepts-grid">
              {filteredConcepts.map(concept => {
                const tag = EXPERT_TAGS[concept.expert];
                const TagIcon = tag.icon;
                const isExpanded = expandedCardId === concept.id || (initialSearchTerm && concept.title.toLowerCase().includes(initialSearchTerm.toLowerCase()));
                const currentTest = testState[concept.id];

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
                            <h4>Key Insights:</h4>
                            <p>{concept.details}</p>
                          </div>
                          
                          {/* Case Study */}
                          <div className="case-study-box">
                            <div className="case-study-header">
                              <TrendingUp size={16} />
                              <h4>Real-world Case Study</h4>
                            </div>
                            <p>{concept.caseStudy}</p>
                          </div>

                          {/* Test Yourself Section */}
                          <div className="test-yourself-wrapper">
                            {!currentTest?.active ? (
                              <button className="test-start-btn" onClick={(e) => startTest(e, concept.id)}>
                                <PenTool size={16} />
                                Test Yourself
                              </button>
                            ) : (
                              <div className="test-active-box">
                                <h5>{concept.testQuestion.question}</h5>
                                
                                {!currentTest?.answered ? (
                                  <div className="test-options">
                                    <button className="test-opt-btn true" onClick={(e) => handleAnswer(e, concept.id, true, concept.testQuestion.answer)}>True</button>
                                    <button className="test-opt-btn false" onClick={(e) => handleAnswer(e, concept.id, false, concept.testQuestion.answer)}>False</button>
                                  </div>
                                ) : (
                                  <div className={`test-result ${currentTest.result ? 'correct' : 'incorrect'}`}>
                                    <div className="result-header">
                                      {currentTest.result ? <CheckCircle size={18} /> : <XCircle size={18} />}
                                      <span>{currentTest.result ? 'Correct!' : 'Incorrect.'}</span>
                                    </div>
                                    <p className="result-explanation">{concept.testQuestion.explanation}</p>
                                  </div>
                                )}
                              </div>
                            )}
                          </div>

                          {/* Scaffolding Dynamic Integration */}
                          {cameFromScaffolding && (
                            <div className="scaffolding-hint-bridge">
                               <button className="hint-btn" onClick={(e) => { e.stopPropagation(); onReturnWithHint(concept.hint); }}>
                                 <span>Return to Chat with Hint</span>
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
    </div>
  );
};

export default ConceptDictionary;
