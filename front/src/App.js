import React, { useState, useRef, useEffect } from 'react';
import './App.css';
import { Menu, Send, BookOpen, TrendingUp, Gem, Radar, X, Library, CheckCircle, Lock, Star, Globe, Tag, Landmark, Scale, Circle } from 'lucide-react';
import SummaryModal from './SummaryModal';
import ConceptDictionary from './ConceptDictionary';
import ReviewModal from './ReviewModal';
import Login from './Login';
// 1. 차트 컴포넌트 임포트
import RadarScoreChart from './components/RadarChart';

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
    const [expertDrawerMode, setExpertDrawerMode] = useState('feedback');
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
    const [activeNodeId, setActiveNodeId] = useState(null);
    const [selectedMission, setSelectedMission] = useState(null);
    const [hoveredMission, setHoveredMission] = useState(null);

    // Chat & Scaffolding States
    const [messages, setMessages] = useState([]);
    const [inputValue, setInputValue] = useState('');
    const [isThinking, setIsThinking] = useState(false);

    const [consecutiveFailures, setConsecutiveFailures] = useState(0);
    const [highlightedSubNode, setHighlightedSubNode] = useState(null);
    const [academicGlow, setAcademicGlow] = useState(false);
    const [newFeedback, setNewFeedback] = useState({ academic: false, market: false, macro: false });

    // 2. 차트에 표시할 실제 점수 데이터 (여기에 저장하면 됩니다)
    const [userScores, setUserScores] = useState({
        Academic: 80,
        Market: 65,
        Macro: 45,
        Independence: 0 // 이 값은 차트 컴포넌트 내부 filter에 의해 자동으로 무시됩니다.
    });

    const messagesEndRef = useRef(null);

    const experts = [
        { id: 'academic', name: 'The Academic Auditor', icon: BookOpen, color: 'var(--color-expert-academic)', role: 'Focuses on fundamental theories and academic rigor.' },
        { id: 'market', name: 'The Market Practitioner', icon: TrendingUp, color: 'var(--color-expert-market)', role: 'Focuses on real-world market trends and data.' },
        { id: 'macro', name: 'The Macro-Connector', icon: Globe, color: 'var(--color-expert-macro)', role: 'Focuses on global economic indicators and policies.' },
    ];

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
        const userMessage = { id: Date.now(), sender: 'user', text: userText };
        setMessages(prev => [...prev, userMessage]);
        setInputValue('');
        setIsThinking(true);
        setNewFeedback({ academic: true, market: true, macro: true });
        setTimeout(() => { handleModeratorResponse(userText); }, 1500);
    };

    const handleModeratorResponse = (userText) => {
        const textLower = userText.toLowerCase();
        const wordCount = userText.split(/\s+/).length;
        const isMastery = textLower.includes("i understand") || textLower.includes("got it") || wordCount > 15;
        const isFailure = !isMastery && (wordCount < 5 || textLower.includes("i don't know") || textLower.includes("not sure"));

        let moderatorText = "";
        if (isMastery && activeNodeId === 'strategic') {
            moderatorText = "Excellent explanation! You've clearly mastered Strategic Analysis.";
            setPathNodes(prevNodes => prevNodes.map(node => {
                if (node.id === 'strategic') return { ...node, status: 'completed' };
                if (node.id === 'market') return { ...node, status: 'active' };
                return node;
            }));
        } else if (isFailure) {
            moderatorText = "It seems a bit tricky. Let's break it down.";
        } else {
            moderatorText = "I see your point. That's a valid perspective.";
        }

        setMessages(prev => [...prev, { id: Date.now() + 1, sender: 'moderator', text: moderatorText }]);
        setIsThinking(false);
    };

    const handleKeyDown = (e) => { if (e.key === 'Enter') { e.preventDefault(); handleSendMessage(); } };

    const openExpertPanel = (id) => {
        if (activeExpert === id) { setActiveExpert(null); }
        else { setActiveExpert(id); setExpertDrawerMode('feedback'); setNewFeedback(prev => ({ ...prev, [id]: false })); }
    };

    const handleMissionSelect = (mission) => {
        setSelectedMission(mission.id);
        setActiveNodeId('strategic');
        setMessages([{ id: Date.now(), sender: 'moderator', text: mission.initMsg }]);
        setHoveredMission(null);
    };

    const handleNodeClick = (node) => {
        if (node.status === 'locked' || !selectedMission) return;
        if (node.status === 'completed' && node.id !== activeNodeId) {
            setReviewNode(node);
            setIsReviewModalOpen(true);
        } else {
            setActiveNodeId(node.id);
        }
    };

    if (!isLoggedIn) return <Login onLogin={() => setIsLoggedIn(true)} />;

    return (
        <div className="app-container fade-in">
            <header className="app-header">
                <div className="header-left">
                    <button className="icon-btn" onClick={() => setIsSidebarOpen(!isSidebarOpen)}>
                        <Menu size={20} />
                    </button>
                    <div
                        className="logo-section"
                        onClick={() => { setSelectedMission(null); setHoveredMission(null); }}
                        style={{ display: 'flex', alignItems: 'center', cursor: 'pointer', gap: '15px' }}
                    >
                        <div className="header-character-wrapper">
                            <img src={!selectedMission ? "/images/sleeping_ant.png" : "/images/reading_ant.png"} alt="Antutor Character" className="header-character" />
                            {showWelcomeBubble && !selectedMission && <div className="speech-bubble">Zzz...</div>}
                            {showWelcomeBubble && selectedMission && <div className="speech-bubble">Let's learn!</div>}
                        </div>
                        <img src="/images/antutor%20logo.png" alt="Antutor Logo" style={{ height: '28px', marginLeft: '5px' }} />
                    </div>
                </div>
                <div className="header-right">
                    {selectedMission && (
                        <button className="summary-btn" onClick={() => {
                            setIsSummaryModalOpen(true);
                        }}>
                            <CheckCircle size={16} />
                            <span className="hide-mobile">End Learning</span>
                        </button>
                    )}

                    <button className="summary-btn" style={{ padding: '8px 16px', backgroundColor: 'var(--color-bg-light)', border: '1px solid var(--color-border)', color: 'var(--color-deep-navy)' }} onClick={() => setIsLoggedIn(false)}>
                        Logout
                    </button>
                </div>
            </header>

            <div className="main-content">
                <aside className={`sidebar glass-panel ${isSidebarOpen ? 'open' : 'closed'}`}>
                    {!selectedMission ? (
                        <div className="welcome-sidebar-content" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', padding: '20px', textAlign: 'center' }}>
                            <div style={{ position: 'relative', marginBottom: '20px' }}>
                                <div className="speech-bubble" style={{ position: 'relative', top: 0, left: 0, marginBottom: '20px', display: 'inline-block', fontSize: '1.1rem', padding: '10px 18px' }}>
                                    {hoveredMission ? "Ready to learn?" : "Zzz... Select a mission..."}
                                </div>
                                <img src={hoveredMission ? "/images/reading_ant.png" : "/images/sleeping_ant.png"} alt="Ant" className="mission-card-character bobbing-character" style={{ width: '180px', height: '180px', margin: '0 auto', display: 'block', mixBlendMode: 'darken' }} />
                            </div>
                        </div>
                    ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                            <div className="sidebar-header"><h2>Learning Path</h2></div>
                            <div className="knowledge-graph stepper" style={{ flex: 1, paddingBottom: '10px' }}>
                                {pathNodes.map((node, index) => (
                                    <React.Fragment key={node.id}>
                                        <div className={`node ${node.status} ${activeNodeId === node.id ? 'current' : ''}`} onClick={() => handleNodeClick(node)}>
                                            <div className="node-icon-wrapper">
                                                {node.status === 'completed' ? <Star size={18} fill="var(--color-soft-gold)" color="var(--color-soft-gold)" /> : (node.status === 'locked' ? <Lock size={16} /> : <Circle size={16} />)}
                                            </div>
                                            <span>{node.title}</span>
                                        </div>
                                        {index < pathNodes.length - 1 && <div className="node-connector"></div>}
                                    </React.Fragment>
                                ))}
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '20px', borderTop: '1px solid var(--color-border)', backgroundColor: 'rgba(255,255,255,0.5)' }}>
                                <img src="/images/reading_ant.png" alt="Studying Ant" className="bobbing-character" style={{ width: '140px', height: '140px', objectFit: 'contain', mixBlendMode: 'darken' }} />
                                <div style={{ marginTop: '10px', fontSize: '0.9rem', fontWeight: 'bold', color: 'var(--color-expert-academic)' }}>You're doing great!</div>
                            </div>
                        </div>
                    )}
                </aside>

                {!selectedMission ? (
                    <section className="mission-selection-container glass-panel">
                        <h2 className="mission-title">Select Your Learning Mission</h2>
                        <div className="mission-grid">
                            {missionConcepts.map(mission => (
                                <div 
                                    key={mission.id} 
                                    className="mission-card" 
                                    onClick={() => handleMissionSelect(mission)}
                                    onMouseEnter={() => setHoveredMission(mission.id)}
                                    onMouseLeave={() => setHoveredMission(null)}
                                >
                                    <div className="mission-card-icon">
                                        <mission.icon size={38} color="var(--color-expert-academic)" />
                                    </div>
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
                                    <div className="message-bubble">{msg.text}</div>
                                </div>
                            ))}
                            <div ref={messagesEndRef} />
                        </div>
                        <div className="chat-input-area">
                            <div className="input-wrapper">
                                <input type="text" value={inputValue} onChange={(e) => setInputValue(e.target.value)} onKeyDown={handleKeyDown} placeholder="Type your response..." />
                                <button className="send-btn" onClick={handleSendMessage}><Send size={18} /></button>
                            </div>
                        </div>
                    </section>
                )}

                <aside className="expert-panel glass-panel" style={!selectedMission ? { width: '280px', alignItems: 'flex-start', padding: '24px' } : {}}>
                    {!selectedMission ? (
                        <div className="expert-list-preview" style={{ width: '100%', display: 'flex', flexDirection: 'column', height: '100%' }}>
                            <h3 style={{ fontSize: '1.2rem', marginBottom: '24px', color: 'var(--color-deep-navy)' }}>Meet Our Experts</h3>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                                {experts.map(expert => (
                                    <div key={expert.id} style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
                                        <div className="expert-icon-btn" style={{ '--expert-color': expert.color, width: '50px', height: '50px', flexShrink: 0, cursor: 'default' }}>
                                            <expert.icon size={24} color={expert.color} />
                                        </div>
                                        <div style={{ display: 'flex', flexDirection: 'column' }}>
                                            <span style={{ fontWeight: '700', fontSize: '1rem', color: expert.color }}>{expert.name}</span>
                                            <span style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)', lineHeight: '1.4' }}>{expert.role}</span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                            
                            <div style={{ marginTop: '40px', borderTop: '1px solid var(--color-border)', paddingTop: '10px', width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                                <h3 style={{ fontSize: '1.2rem', marginBottom: '16px', color: 'var(--color-deep-navy)', alignSelf: 'flex-start' }}>Your Profile</h3>
                                <div style={{ width: '100px', height: '100px', borderRadius: '50%', backgroundColor: 'var(--color-white)', border: '2px dashed var(--color-text-secondary)', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', overflow: 'hidden', boxShadow: '0 4px 15px rgba(0,0,0,0.03)' }}>
                                    <span style={{ fontSize: '2.5rem', color: 'var(--color-text-secondary)', fontWeight: '300' }}>+</span>
                                </div>
                            </div>
                        </div>
                    ) : (
                        experts.map(expert => (
                            <button key={expert.id} className="expert-icon-btn" onClick={() => openExpertPanel(expert.id)} style={{ '--expert-color': expert.color }}>
                                <expert.icon size={26} color={expert.color} />
                            </button>
                        ))
                    )}
                </aside>

                <div className={`expert-drawer ${activeExpert ? 'open' : ''}`}>
                    {activeExpert && (
                        <div className="drawer-content">
                            <div className="drawer-header" style={{ borderBottomColor: experts.find(e => e.id === activeExpert)?.color }}>
                                <div className="expert-title">
                                    {experts.find(e => e.id === activeExpert)?.icon && React.createElement(experts.find(e => e.id === activeExpert).icon, { size: 24, color: experts.find(e => e.id === activeExpert).color })}
                                    <h3>{experts.find(e => e.id === activeExpert)?.name}</h3>
                                </div>
                                <button className="close-btn" onClick={() => setActiveExpert(null)}>
                                    <X size={20} />
                                </button>
                            </div>
                            <div className="drawer-body">
                                <p className="expert-role">{experts.find(e => e.id === activeExpert)?.role}</p>
                                <div className="feedback-card" style={{ '--expert-color': experts.find(e => e.id === activeExpert)?.color }}>
                                    <div className="feedback-card-header">
                                        <Star size={16} color={experts.find(e => e.id === activeExpert)?.color} fill={experts.find(e => e.id === activeExpert)?.color} />
                                        <span>Expert Insight</span>
                                    </div>
                                    <h4>Suggested Perspective</h4>
                                    <p>Based on your progress, {experts.find(e => e.id === activeExpert)?.name} recommends exploring this topic further to solidify your understanding and connect it to broader concepts.</p>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Summary Modal에 차트 전달 */}
            <SummaryModal
                isOpen={isSummaryModalOpen}
                onClose={() => setIsSummaryModalOpen(false)}
                helpCountLevel1={helpCountLevel1}
                helpCountLevel2={helpCountLevel2}
                // 아래 줄을 추가하여 모달 안에서 차트를 그릴 수 있게 합니다.
                scoreChart={<RadarScoreChart scores={userScores} />}
            />

            <ConceptDictionary isOpen={isDictionaryOpen} onClose={() => setIsDictionaryOpen(false)} />
            <ReviewModal isOpen={isReviewModalOpen} onClose={() => setIsReviewModalOpen(false)} node={reviewNode} />
        </div>
    );
}

export default App;