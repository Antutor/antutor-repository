import React, { useState, useRef, useEffect } from 'react';
import './App.css';
import { Menu, Send, BookOpen, TrendingUp, Gem, Radar, X, Library, CheckCircle, Lock, Star, Globe, Tag, Landmark, Scale, Circle } from 'lucide-react';
import SummaryModal from './SummaryModal';
import ConceptDictionary from './ConceptDictionary';
import ReviewModal from './ReviewModal';
import Login from './Login';

const missionConcepts = [
  {
    id: 'inflation',
    title: 'Inflation',
    icon: Tag,
    initMsg: "Welcome! Let's talk about Inflation. Can you explain how rising inflation affects the purchasing power of everyday consumers?"
  },
  {
    id: 'base_rate',
    title: 'Base Interest Rate',
    icon: Landmark,
    initMsg: "Welcome! The central bank just raised the Base Interest Rate. How do you think this impacts corporate investments and the stock market?"
  },
  {
    id: 'exchange_rate',
    title: 'Exchange Rate',
    icon: Globe,
    initMsg: "Why does the Exchange Rate in our country change when US interest rates rise? Can you explain the correlation?"
  },
  {
    id: 'opportunity_cost',
    title: 'Opportunity Cost',
    icon: Scale,
    initMsg: "Every choice has a cost. Can you explain the concept of Opportunity Cost with a real-life example?"
  },
  {
    id: 'compound_interest',
    title: 'Compound Interest',
    icon: TrendingUp,
    initMsg: "Albert Einstein allegedly called compound interest the 8th wonder of the world. Why is it so powerful for long-term investing compared to simple interest?"
  }
];

const initialPath = [
  { id: 'fundamentals', title: 'Fundamental Concepts', status: 'completed', summary: 'Core principles underlying the selected topic.' },
  { id: 'strategic', title: 'Strategic Analysis', status: 'active', subNode: 'Application & Context' },
  { id: 'market', title: 'Market Dynamics', status: 'locked' },
  { id: 'risk', title: 'Risk Management', status: 'locked' }
];

function App() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [activeExpert, setActiveExpert] = useState(null);
  const [expertDrawerMode, setExpertDrawerMode] = useState('feedback'); // 'feedback', 'dictionary'
  const [isSummaryModalOpen, setIsSummaryModalOpen] = useState(false);
  const [isDictionaryOpen, setIsDictionaryOpen] = useState(false);
  const [dictionarySearchTerm, setDictionarySearchTerm] = useState('');

  // Auth State
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [isProfileMenuOpen, setIsProfileMenuOpen] = useState(false);

  // Character UI States
  const [showWelcomeBubble, setShowWelcomeBubble] = useState(true);
  const [showAchievement, setShowAchievement] = useState(false);

  // Scaffolding Counter States
  const [helpCountLevel1, setHelpCountLevel1] = useState(0);
  const [helpCountLevel2, setHelpCountLevel2] = useState(0);

  // Review Modal State
  const [isReviewModalOpen, setIsReviewModalOpen] = useState(false);
  const [reviewNode, setReviewNode] = useState(null);

  // Learning Path State
  const [pathNodes, setPathNodes] = useState(initialPath);
  const [activeNodeId, setActiveNodeId] = useState(null); // Null implicitly defines the landing state
  const [selectedMission, setSelectedMission] = useState(null);

  // Chat & Scaffolding States
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isThinking, setIsThinking] = useState(false);

  const [consecutiveFailures, setConsecutiveFailures] = useState(0);
  const [highlightedSubNode, setHighlightedSubNode] = useState(null);
  const [academicGlow, setAcademicGlow] = useState(false);
  const [newFeedback, setNewFeedback] = useState({ academic: false, market: false, macro: false });

  const messagesEndRef = useRef(null);

  const experts = [
    { id: 'academic', name: 'Academic Expert', icon: BookOpen, color: 'var(--color-expert-academic)', role: 'Focuses on fundamental theories and academic rigor.' },
    { id: 'market', name: 'Market Analyst', icon: TrendingUp, color: 'var(--color-expert-market)', role: 'Focuses on real-world market trends and data.' },
    { id: 'macro', name: 'Macro Economist', icon: Globe, color: 'var(--color-expert-macro)', role: 'Focuses on global economic indicators and policies.' },
  ];

  // Dismiss welcome bubble after a few seconds
  useEffect(() => {
    if (isLoggedIn && showWelcomeBubble) {
      const timer = setTimeout(() => setShowWelcomeBubble(false), 5000);
      return () => clearTimeout(timer);
    }
  }, [isLoggedIn, showWelcomeBubble]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isThinking]);

  const handleSendMessage = () => {
    if (!inputValue.trim() || isThinking) return;

    const userText = inputValue.trim();
    const userMessage = {
      id: Date.now(),
      sender: 'user',
      text: userText
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsThinking(true);
    setNewFeedback({ academic: true, market: true, macro: true });

    // AI Simulated Delay
    setTimeout(() => {
      handleModeratorResponse(userText);
    }, 1500);
  };

  const handleModeratorResponse = (userText) => {
    const textLower = userText.toLowerCase();
    const wordCount = userText.split(/\s+/).length;

    // Auto-Progression Detection ("mastery")
    const isMastery = textLower.includes("i understand") || textLower.includes("got it") || wordCount > 15;

    // Failure Detection
    const isFailure = !isMastery && (wordCount < 5 || textLower.includes("i don't know") || textLower.includes("not sure"));

    let moderatorText = "";

    if (isMastery && activeNodeId === 'strategic') {
      // Automatic Progression to Market Dynamics
      moderatorText = "Excellent explanation! You've clearly mastered Strategic Analysis. I am unlocking 'Market Dynamics' for you now. Click it on the left when you are ready.";

      setPathNodes(prevNodes => prevNodes.map(node => {
        if (node.id === 'strategic') return { ...node, status: 'completed' };
        if (node.id === 'market') return { ...node, status: 'active' };
        return node;
      }));

      setConsecutiveFailures(0);
      setHighlightedSubNode(null);
      setAcademicGlow(false);
    }
    else if (!isFailure && !isMastery) {
      // Normal progression
      moderatorText = "I see your point. That's a valid perspective. Now, considering the relationship between money supply and inflation, how would that specifically affect interest rates in the short term versus the long term?";
      setConsecutiveFailures(0);
      setHighlightedSubNode(null);
      setAcademicGlow(false);
    }
    else if (isFailure) {
      // Reverse Learning Logic
      if (consecutiveFailures === 0) {
        // Level 1: Sub-concept Redirection
        moderatorText = "It seems a bit tricky. Let's break it down. Do you know the basic definition of Quantitative Easing first?";
        setHighlightedSubNode('qe');
        setConsecutiveFailures(1);
        setHelpCountLevel1(prev => prev + 1);
      } else {
        // Level 2: Concept Dictionary Bridge
        moderatorText = "No worries! I've opened the Concept Dictionary for you to review 'Quantitative Easing'. Please review the core definition before we move on.";
        setAcademicGlow(true);
        setDictionarySearchTerm('Quantitative Easing');
        setIsDictionaryOpen(true);
        setConsecutiveFailures(2);
        setHelpCountLevel2(prev => prev + 1);
      }
    }

    const moderatorMessage = {
      id: Date.now() + 1,
      sender: 'moderator',
      text: moderatorText
    };

    setMessages(prev => [...prev, moderatorMessage]);
    setIsThinking(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const openExpertPanel = (id) => {
    if (activeExpert === id) {
      setActiveExpert(null);
      setAcademicGlow(false);
    } else {
      setActiveExpert(id);
      setExpertDrawerMode('feedback'); // Default to feedback on manual click
      setNewFeedback(prev => ({ ...prev, [id]: false }));
      if (id === 'academic') setAcademicGlow(false);
    }
  };

  const handleMissionSelect = (mission) => {
    setSelectedMission(mission.id);

    // Jump straight into Node 2: Strategic Analysis
    setActiveNodeId('strategic');
    setPathNodes([
      { id: 'fundamentals', title: 'Fundamental Concepts', status: 'completed', summary: `Core mechanics underlying ${mission.title}.` },
      { id: 'strategic', title: 'Strategic Analysis', status: 'active', subNode: `${mission.title} Context` },
      { id: 'market', title: 'Market Dynamics', status: 'locked' },
      { id: 'risk', title: 'Risk Management', status: 'locked' }
    ]);

    setMessages([{
      id: Date.now(),
      sender: 'moderator',
      text: mission.initMsg
    }]);

    setConsecutiveFailures(0);
    setHighlightedSubNode(null);
    setAcademicGlow(false);
    setActiveExpert(null);
  };

  const handleNodeClick = (node) => {
    if (node.status === 'locked' || !selectedMission) return;

    if (node.status === 'completed' && node.id !== activeNodeId) {
      setReviewNode(node);
      setIsReviewModalOpen(true);
    } else {
      setActiveNodeId(node.id);
      if (node.id === 'strategic' && activeNodeId === 'fundamentals') {
        setMessages(prev => [...prev, {
          id: Date.now() + 1,
          sender: 'moderator',
          text: "Excellent! Let's resume Strategic Analysis."
        }]);
      } else if (node.id === 'fundamentals') {
        setMessages(prev => [...prev, {
          id: Date.now() + 1,
          sender: 'moderator',
          text: "Let's review the Fundamental Concepts."
        }]);
      }
    }
  };

  const handleSubNodeClick = (subNodeId, e) => {
    e.stopPropagation();
    setActiveNodeId('strategic');
    setHighlightedSubNode(subNodeId);
    setMessages([{
      id: Date.now(),
      sender: 'moderator',
      text: "Let's focus specifically on Quantitative Easing (QE). How does a central bank purchasing government bonds theoretically affect the broader money supply?"
    }]);
    setConsecutiveFailures(0);
    setAcademicGlow(false);
    setActiveExpert(null);
  };

  if (!isLoggedIn) {
    return <Login onLogin={() => setIsLoggedIn(true)} />;
  }

  return (
    <div className="app-container fade-in">
      <header className="app-header">
        <div className="header-left">
          <button className="icon-btn" onClick={() => setIsSidebarOpen(!isSidebarOpen)}>
            <Menu size={20} />
          </button>

          <div className="header-character-wrapper">
            <img src="/images/ant.jpg" alt="Anteacher" className="header-character" />
            {showWelcomeBubble && (
              <div className="speech-bubble">
                Let's learn!
              </div>
            )}
          </div>

          <h1>Anteacher Dashboard</h1>
        </div>
        <div className="header-right">
          <button className="summary-btn" style={{ backgroundColor: 'var(--color-bg-light)', color: 'var(--color-text-secondary)', borderColor: 'transparent' }} onClick={() => { setDictionarySearchTerm(''); setIsDictionaryOpen(true); }}>
            <Library size={16} />
            <span className="hide-mobile">Concept Dictionary</span>
          </button>
          <button className="summary-btn" onClick={() => setIsSummaryModalOpen(true)}>
            <Radar size={16} />
            <span className="hide-mobile">View Summary</span>
          </button>

          <div className="profile-container">
            <button className="profile-icon-btn" onClick={() => setIsProfileMenuOpen(!isProfileMenuOpen)}>
              <div className="avatar user">U</div>
            </button>
            {isProfileMenuOpen && (
              <div className="profile-dropdown">
                <div className="dropdown-stats">
                  <div className="stat-item"><span role="img" aria-label="streak">🔥</span> 5 Days</div>
                  <div className="stat-item"><span role="img" aria-label="badges">🏆</span> 3 Badges</div>
                </div>
                <button className="logout-btn" onClick={() => { setIsLoggedIn(false); setIsProfileMenuOpen(false); }}>
                  Logout
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      <div className="main-content">
        {/* Left Sidebar: Learning Path Stepper */}
        <aside className={`sidebar glass-panel ${isSidebarOpen ? 'open' : 'closed'}`}>
          <div className="sidebar-header">
            <h2>Learning Path</h2>
          </div>
          <div className="knowledge-graph stepper">
            {pathNodes.map((node, index) => (
              <React.Fragment key={node.id}>
                <div
                  className={`node ${node.status} ${activeNodeId === node.id ? 'current' : ''}`}
                  onClick={() => handleNodeClick(node)}
                  title={node.status === 'locked' ? "Complete the current stage to unlock." : ""}
                >
                  <div className="node-icon-wrapper">
                    {node.status === 'completed' ? (
                      <Star size={18} className="node-icon check" fill="var(--color-soft-gold)" color="var(--color-soft-gold)" />
                    ) : node.status === 'locked' ? (
                      <Lock size={16} className="node-icon locked" />
                    ) : (
                      <div className={`node-icon ${activeNodeId === node.id ? 'current' : ''}`}>
                        {index === 0 && <BookOpen size={16} />}
                        {index === 1 && <Gem size={16} />}
                        {index === 2 && <TrendingUp size={16} />}
                        {index === 3 && <Scale size={16} />}
                      </div>
                    )}
                  </div>
                  <span>{node.title}</span>
                </div>

                {/* Conditionally render sub-nodes if it's the strategic one */}
                {node.subNode && node.status !== 'locked' && (
                  <div
                    className={`sub-node ${highlightedSubNode === 'qe' && activeNodeId === 'strategic' ? 'highlighted' : ''}`}
                    onClick={(e) => handleSubNodeClick('qe', e)}
                  >
                    <span className="sub-node-dot"></span>
                    <span>{node.subNode}</span>
                  </div>
                )}

                {/* Vertical Connector */}
                {index < pathNodes.length - 1 && (
                  <div className={`node-connector ${node.status === 'completed' ? 'completed-line' : ''}`}></div>
                )}
              </React.Fragment>
            ))}
          </div>
        </aside>

        {/* Center: Main Focus */}
        {!selectedMission ? (
          <section className="mission-selection-container glass-panel">
            <h2 className="mission-title">Select Your Learning Mission</h2>
            <div className="mission-grid">
              {missionConcepts.map(mission => (
                <div key={mission.id} className="mission-card" onClick={() => handleMissionSelect(mission)}>
                  <div className="mission-card-icon">
                    <mission.icon size={32} color="var(--color-expert-academic)" />
                  </div>
                  <img src="/image_e560c7.jpg" alt="Ant-y Mission" className="mission-card-character" onError={(e) => e.target.src = '/images/ant.jpg'} />
                  <h3>{mission.title}</h3>
                </div>
              ))}
            </div>
          </section>
        ) : (
          <section className="chat-container glass-panel">
            <div className="chat-history">
              {messages.map((msg) => (
                <div key={msg.id} className={`message ${msg.sender}`}>
                  {msg.sender === 'moderator' ? (
                    <div className="avatar moderator character-avatar">
                      <img src="/images/ant.jpg" alt="Ant-y Moderator" className="bobbing-character" />
                    </div>
                  ) : (
                    <div className="avatar user">U</div>
                  )}
                  <div className="message-bubble">
                    {msg.text}
                  </div>
                </div>
              ))}

              {isThinking && (
                <div className="message agent is-thinking">
                  <div className="avatar moderator character-avatar">
                    <img src="/images/ant.jpg" alt="Ant-y Thinking" className="bobbing-character" />
                  </div>
                  <div className="message-bubble thinking-bubble">
                    <span className="dot"></span>
                    <span className="dot"></span>
                    <span className="dot"></span>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            <div className="chat-input-area">
              <div className="input-wrapper">
                <input
                  type="text"
                  placeholder={"Type your response... (e.g. 'I understand' to master the concept)"}
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyDown={handleKeyDown}
                  disabled={isThinking}
                />
                <button className="send-btn" onClick={handleSendMessage} disabled={isThinking || !inputValue.trim()}>
                  <Send size={18} />
                </button>
              </div>
            </div>
          </section>
        )}

        {/* Celebratory Overlay for Achievement */}
        {showAchievement && (
          <div className="achievement-overlay">
            <div className="achievement-content">
              <Star size={48} className="achievement-star" fill="var(--color-soft-gold)" color="var(--color-soft-gold)" />
              <img src="/images/ant.jpg" alt="Level Up!" className="achievement-character bounce-character" />
              <h2>Great Job!</h2>
              <p>You unlocked the next level!</p>
            </div>
          </div>
        )}

        {/* Right Edge: Expert Panel */}
        <aside className="expert-panel glass-panel">
          {experts.map(expert => {
            const isGlow = expert.id === 'academic' && academicGlow;
            const hasNewFeedback = newFeedback[expert.id];

            return (
              <button
                key={expert.id}
                className={`expert-icon-btn ${activeExpert === expert.id ? 'active' : ''} ${isGlow ? 'glow-animation' : ''} ${hasNewFeedback ? 'has-new-feedback' : ''}`}
                onClick={() => openExpertPanel(expert.id)}
                title={expert.name}
                style={{ '--expert-color': expert.color }}
              >
                <expert.icon size={26} style={{ color: activeExpert === expert.id ? 'white' : expert.color }} />
              </button>
            );
          })}
        </aside>

        {/* Slide-in Drawer */}
        <div className={`expert-drawer ${activeExpert ? 'open' : ''}`}>
          {activeExpert && (
            <>
              {experts.filter(e => e.id === activeExpert).map(expert => (
                <div key={expert.id} className="drawer-content">
                  <div className="drawer-header" style={{ borderBottomColor: expert.color }}>
                    <div className="expert-title">
                      <expert.icon size={20} color={expert.color} />
                      <h3>
                        {expertDrawerMode === 'dictionary' && expert.id === 'academic' ? 'Concept Dictionary' : expert.name}
                      </h3>
                    </div>
                    <button className="close-btn" onClick={() => { setActiveExpert(null); setAcademicGlow(false); }}>
                      <X size={20} />
                    </button>
                  </div>

                  <div className="drawer-body">
                    {expertDrawerMode === 'dictionary' && expert.id === 'academic' ? (
                      // Dictionary Mode UI
                      <div className="dictionary-mode">
                        <div className="dict-term">Quantitative Easing (QE)</div>
                        <div className="dict-definition">
                          <p><strong>Definition:</strong> A monetary policy in which a central bank purchases predetermined amounts of government bonds or other financial assets to inject money into the economy to expand economic activity.</p>
                        </div>
                        <div className="dict-key-points">
                          <h4>Key Mechanisms</h4>
                          <ul>
                            <li>Lowers interest rates on savings and loans.</li>
                            <li>Increases the money supply.</li>
                            <li>Aims to stimulate spending and investment.</li>
                          </ul>
                        </div>
                      </div>
                    ) : (
                      // Standard Feedback Mode UI
                      <>
                        <p className="expert-role">{expert.role}</p>
                        <div className="feedback-card">
                          <div className="feedback-card-header" style={{ borderBottomColor: expert.color }}>
                            <expert.icon size={16} color={expert.color} />
                            <span style={{ color: expert.color }}>Qualitative Feedback</span>
                          </div>
                          <h4>Observation</h4>
                          <p>Your point on asset prices is correct empirically. However, remember the Phillips curve and money velocity when discussing inflation risks.</p>

                          {expert.id === 'market' && (
                            <div style={{ marginTop: '15px' }}>
                              <h4>Current Context</h4>
                              <p>Recent data from the S&P 500 shows corresponding highs during similar policy cycles.</p>
                            </div>
                          )}
                        </div>
                      </>
                    )}
                  </div>
                </div>
              ))}
            </>
          )}
        </div>
      </div>

      <SummaryModal
        isOpen={isSummaryModalOpen}
        onClose={() => setIsSummaryModalOpen(false)}
        helpCountLevel1={helpCountLevel1}
        helpCountLevel2={helpCountLevel2}
      />

      <ConceptDictionary
        isOpen={isDictionaryOpen}
        onClose={() => setIsDictionaryOpen(false)}
        initialSearchTerm={dictionarySearchTerm}
        cameFromScaffolding={!!dictionarySearchTerm}
        onReturnWithHint={(hint) => {
          setInputValue(hint);
          setIsDictionaryOpen(false);
          setDictionarySearchTerm('');
        }}
      />

      <ReviewModal
        isOpen={isReviewModalOpen}
        onClose={() => setIsReviewModalOpen(false)}
        node={reviewNode}
      />
    </div>
  );
}

export default App;
