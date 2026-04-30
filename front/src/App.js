import React, { useState, useRef, useEffect } from 'react';
import './App.css';
import { Menu, Send, BookOpen, TrendingUp, Gem, Radar, X, Library, CheckCircle, Lock, Star, Globe, Tag, Landmark, Scale, Circle, AlertCircle } from 'lucide-react';
import SummaryModal from './SummaryModal';
import ConceptDictionary from './ConceptDictionary';
import ReviewModal from './ReviewModal';
import Login from './Login';
import Register from './Register';
// 1. 차트 컴포넌트 임포트
import RadarScoreChart from './components/RadarChart';
import { studyAPI } from './api/services';
const missionConcepts = [
    {
        id: 'Inflation',
        title: '인플레이션',
        icon: Tag,
        initMsg: "환영합니다! 인플레이션에 대해 이야기해 봅시다. 물가 상승이 소비자의 구매력에 어떤 영향을 미치는지 설명할 수 있나요?"
    },
    {
        id: 'Base Interest Rate',
        title: '기준금리',
        icon: Landmark,
        initMsg: "환영합니다! 중앙은행이 방금 기준금리를 인상했습니다. 이것이 기업 투자와 주식 시장에 어떤 영향을 미친다고 생각하시나요?"
    },
    {
        id: 'Exchange Rate',
        title: '환율',
        icon: Globe,
        initMsg: "미국 금리가 오를 때 우리나라 환율은 왜 변할까요? 그 상관관계를 설명할 수 있나요?"
    },
    {
        id: 'Opportunity Cost',
        title: '기회비용',
        icon: Scale,
        initMsg: "모든 선택에는 대가가 따릅니다. 실생활의 예를 들어 기회비용의 개념을 설명해 볼까요?"
    },
    {
        id: 'Compound Interest',
        title: '복리',
        icon: TrendingUp,
        initMsg: "알버트 아인슈타인은 복리를 세계 8대 불가사의라고 불렀다고 합니다. 단리에 비해 장기 투자에서 복리가 그토록 강력한 이유는 무엇일까요?"
    }
];

const initialPath = [
    { id: 'fundamentals', title: '기본 개념', status: 'completed', summary: '선택한 주제의 핵심 원리입니다.' },
    { id: 'strategic', title: '전략적 분석', status: 'active', subNode: '적용 및 맥락' },
    { id: 'market', title: '시장 동향', status: 'locked' },
    { id: 'risk', title: '리스크 관리', status: 'locked' }
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
    const [authPage, setAuthPage] = useState('login'); // 'login' or 'register'
    const [isProfileMenuOpen, setIsProfileMenuOpen] = useState(false);
    const [showLeftSidebarProfile, setShowLeftSidebarProfile] = useState(false);
    const [profileImage, setProfileImage] = useState(null);
    const fileInputRef = useRef(null);

    const handleImageUpload = (e) => {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onloadend = () => {
                setProfileImage(reader.result);
            };
            reader.readAsDataURL(file);
        }
    };

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
    const [sessionId, setSessionId] = useState(null);
    const [isResumePending, setIsResumePending] = useState(false);

    // Chat & Scaffolding States
    const [messages, setMessages] = useState([]);
    const [expertFeedbackData, setExpertFeedbackData] = useState([]);
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
    const [reportData, setReportData] = useState(null);
    const [isErrorModalOpen, setIsErrorModalOpen] = useState(false);
    const [failedUserMessage, setFailedUserMessage] = useState(null);

    const messagesEndRef = useRef(null);

    const experts = [
        { id: 'academic', name: '학술 전문가', icon: BookOpen, color: 'var(--color-expert-academic)', role: '기본 이론과 학문적 엄밀성에 중점을 둡니다.' },
        { id: 'market', name: '시장 실무자', icon: TrendingUp, color: 'var(--color-expert-market)', role: '실제 시장 동향 및 데이터에 중점을 둡니다.' },
        { id: 'macro', name: '매크로 분석가', icon: Globe, color: 'var(--color-expert-macro)', role: '글로벌 경제 지표 및 정책에 중점을 둡니다.' },
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

    const handleSendMessage = async (retryText = null) => {
        // If it's an event (e.g. from onClick, e.type usually exists), reset retryText to null. 
        // But since we define it as `retryText = null`, if an event is passed it's an object.
        const actualRetryText = typeof retryText === 'string' ? retryText : null;
        
        const textToSend = actualRetryText || inputValue.trim();
        if (!textToSend || isThinking || !sessionId) return;
        
        if (!actualRetryText) {
            const userMessage = { id: Date.now(), sender: 'user', text: textToSend };
            setMessages(prev => [...prev, userMessage]);
            setInputValue('');
        }
        setIsThinking(true);
        setNewFeedback({ academic: true, market: true, macro: true });

        let success = false;
        let currentAttempt = 0;
        const MAX_RETRIES = 2; // 무한 재시도 시 UI가 먹통이 되므로 최대 2회로 제한

        while (currentAttempt < MAX_RETRIES && !success) {
            try {
                const response = await studyAPI.sendChat({
                    session_id: sessionId,
                    concept: selectedMission,
                    user_answer: textToSend
                });
                const data = response.data;
                if (data.expert_feedback) {
                    setExpertFeedbackData(data.expert_feedback);
                    
                    // 전문가별 점수 매핑 및 업데이트
                    const newScores = { ...userScores };
                    data.expert_feedback.forEach(f => {
                        if (f.persona === 'The Academic Auditor') newScores.Academic = Math.round(f.score * 100);
                        if (f.persona === 'The Market Practitioner') newScores.Market = Math.round(f.score * 100);
                        if (f.persona === 'The Macro-Connector') newScores.Macro = Math.round(f.score * 100);
                    });
                    setUserScores(newScores);
                }
                
                const decision = data?.moderator_decision;
                let moderatorText = decision?.message || "피드백이 수신되었습니다.";
                
                const plan = decision?.scaffold_plan || decision?.scaffolding_plan;
                if (plan && plan.message) {
                    moderatorText = plan.message;
                }

                if (decision?.status === "scaffold") {
                    if (plan?.step === "Concept Dictionary Link" || String(plan?.step) === "1") {
                        setHelpCountLevel1(prev => prev + 1);
                    } else {
                        setHelpCountLevel2(prev => prev + 1);
                    }
                }
                
                setMessages(prev => [...prev, { id: Date.now() + 1, sender: 'moderator', text: moderatorText }]);
                success = true;
            } catch (error) {
                currentAttempt++;
                console.error(`Chat communication error (attempt ${currentAttempt}):`, error);
                
                // 4xx 에러(예: 422 Validation Error)인 경우 즉시 에러 모달을 띄우고 루프 중단
                if (error.response && error.response.status >= 400 && error.response.status < 500 && error.response.status !== 408) {
                    setFailedUserMessage(textToSend);
                    setIsErrorModalOpen(true);
                    break;
                }
                
                if (currentAttempt < MAX_RETRIES) {
                    // 5xx 등 서버/네트워크 에러 시 잠깐 대기 후 재시도
                    await new Promise(resolve => setTimeout(resolve, 3000));
                } else {
                    // 최대 재시도 횟수 초과 시 에러 모달 노출 및 UI 락 해제
                    setFailedUserMessage(textToSend);
                    setIsErrorModalOpen(true);
                }
            }
        }
        
        setIsThinking(false);
    };

    const handleKeyDown = (e) => { if (e.key === 'Enter') { e.preventDefault(); handleSendMessage(); } };

    const openExpertPanel = (id) => {
        if (activeExpert === id) { setActiveExpert(null); }
        else { setActiveExpert(id); setExpertDrawerMode('feedback'); setNewFeedback(prev => ({ ...prev, [id]: false })); }
    };

    const handleMissionSelect = async (mission) => {
        try {
            const response = await studyAPI.startSession(mission.id);
            setSessionId(response.data.session_id);
            setIsResumePending(response.data.resume_available || false);
            setSelectedMission(mission.id);
            setActiveNodeId('strategic');
            
            // Fix translation fallback: prioritize hardcoded Korean text
            let startText = mission.initMsg || response.data.initial_question;
            if (response.data.resume_available) {
                startText = `${response.data.resume_prompt}\n\n(마지막 질문: ${response.data.last_ai_response})`;
            }
            
            setMessages([{ id: Date.now(), sender: 'moderator', text: startText }]);
            setHoveredMission(null);
            setHelpCountLevel1(0);
            setHelpCountLevel2(0);
            setReportData(null);
            setExpertFeedbackData([]);
            setIsThinking(false);
        } catch (error) {
            console.error("Failed to start session:", error);
            alert("세션 시작에 실패했습니다.");
        }
    };

    const handleResumeDecision = async (decision) => {
        if (!selectedMission) return;
        setIsThinking(true);
        try {
            const response = await studyAPI.resolveResume({ concept: selectedMission, decision });
            setSessionId(response.data.session_id);
            setIsResumePending(false);
            setMessages(prev => [...prev, { id: Date.now(), sender: 'user', text: decision === 'resume' ? '이어서 학습하기' : '처음부터 다시하기' }]);
            
            // Add the real initial question/resumed question
            setTimeout(() => {
                let finalQuestion = response.data.question;
                if (decision === 'fresh') {
                    const missionObj = missionConcepts.find(m => m.id.toLowerCase() === selectedMission.toLowerCase());
                    if (missionObj && missionObj.initMsg) {
                        finalQuestion = missionObj.initMsg;
                    }
                }
                setMessages(prev => [...prev, { id: Date.now() + 1, sender: 'moderator', text: finalQuestion }]);
                setIsThinking(false);
            }, 500);
        } catch (error) {
            console.error("Failed to resolve resume:", error);
            alert("세션 재개 처리에 실패했습니다.");
            setIsThinking(false);
        }
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

    if (!isLoggedIn) {
        if (authPage === 'login') return <Login onLogin={() => setIsLoggedIn(true)} onGoToRegister={() => setAuthPage('register')} />;
        if (authPage === 'register') return <Register onGoToLogin={() => setAuthPage('login')} />;
    }

    return (
        <div className="app-container fade-in">
            <header className="app-header">
                <div className="header-left">
                    <button className="icon-btn" onClick={() => setShowLeftSidebarProfile(!showLeftSidebarProfile)}>
                        <Menu size={20} />
                    </button>
                    <div
                        className="logo-section"
                        onClick={() => { setSelectedMission(null); setHoveredMission(null); }}
                        style={{ display: 'flex', alignItems: 'center', cursor: 'pointer', gap: '10px' }}
                    >
                        <img src="/images/antutor%20logo%20final.png" alt="Antutor Logo" style={{ height: '60px', marginLeft: '5px' }} />
                    </div>
                </div>
                <div className="header-right">
                    {selectedMission && (
                        <button className="summary-btn" onClick={async () => {
                            if (sessionId) {
                                try {
                                    const response = await studyAPI.endSession({ session_id: sessionId });
                                    setReportData(response.data);
                                } catch (error) {
                                    console.error("End session failed", error);
                                }
                            }
                            setIsSummaryModalOpen(true);
                        }}>
                            <CheckCircle size={16} />
                            <span className="hide-mobile">학습 종료</span>
                        </button>
                    )}

                    <button className="summary-btn" style={{ padding: '8px 16px', backgroundColor: 'var(--color-bg-light)', border: '1px solid var(--color-border)', color: 'var(--color-deep-navy)' }} onClick={() => setIsLoggedIn(false)}>
                        로그아웃
                    </button>
                </div>
            </header>

            <div className="main-content">
                <aside className="sidebar glass-panel open">
                    {!selectedMission ? (
                        <div className="welcome-sidebar-content" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', padding: '20px', textAlign: 'center' }}>
                            <div style={{ position: 'relative', marginBottom: '20px' }}>
                                <div className="speech-bubble" style={{ position: 'relative', top: 0, left: 0, marginBottom: '20px', display: 'inline-block', fontSize: '1.1rem', padding: '10px 18px' }}>
                                    {hoveredMission ? "학습할 준비가 되셨나요?" : "Zzz... 미션을 선택해주세요..."}
                                </div>
                                <img src="/images/antutor%20standup.png" alt="Ant" className="mission-card-character bobbing-character" style={{ width: '180px', height: '180px', margin: '0 auto', display: 'block' }} />
                            </div>
                        </div>
                    ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                            <div className="sidebar-header"><h2>학습 경로</h2></div>
                            {/* 학습 경로 노드 제거됨 */}
                            <div style={{ flex: 'none', padding: '0 10px', marginTop: '60px' }}>
                                <RadarScoreChart scores={userScores} isSidebar={true} />
                            </div>
                            <div style={{ flex: 1 }}></div> {/* 스페이서로 공간 확보 */}
                            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '20px', borderTop: '1px solid var(--color-border)', backgroundColor: 'rgba(255,255,255,0.5)', marginBottom: '20px' }}>
                                <img src="/images/antutor%20standup.png" alt="Studying Ant" className="bobbing-character" style={{ width: '120px', height: '120px', objectFit: 'contain' }} />
                                <div style={{ marginTop: '8px', fontSize: '0.9rem', fontWeight: 'bold', color: 'var(--color-expert-academic)' }}>정말 잘하고 있어요!</div>
                            </div>
                        </div>
                    )}
                </aside>

                {!selectedMission ? (
                    <section className="mission-selection-container glass-panel">
                        <h2 className="mission-title">학습 미션을 선택하세요</h2>
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
                                        <mission.icon size={38} color="#22c55e" />
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
                            {isThinking && (
                                <div className="message moderator">
                                    <div className="message-bubble thinking-bubble">
                                        <div className="dot"></div>
                                        <div className="dot"></div>
                                        <div className="dot"></div>
                                    </div>
                                </div>
                            )}
                            <div ref={messagesEndRef} />
                        </div>
                        <div className="chat-input-area">
                            {isResumePending ? (
                                <div style={{ display: 'flex', gap: '10px', width: '100%', justifyContent: 'center' }}>
                                    <button 
                                        onClick={() => handleResumeDecision('resume')}
                                        style={{ padding: '10px 20px', backgroundColor: 'var(--color-primary)', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: 'bold' }}>
                                        이어서 학습하기
                                    </button>
                                    <button 
                                        onClick={() => handleResumeDecision('fresh')}
                                        style={{ padding: '10px 20px', backgroundColor: 'var(--color-bg-light)', border: '1px solid var(--color-border)', color: 'var(--color-deep-navy)', borderRadius: '8px', cursor: 'pointer', fontWeight: 'bold' }}>
                                        처음부터 다시하기
                                    </button>
                                </div>
                            ) : (
                                <div className="input-wrapper">
                                    <input type="text" value={inputValue} onChange={(e) => setInputValue(e.target.value)} onKeyDown={handleKeyDown} placeholder="답변을 입력하세요..." disabled={isResumePending} />
                                    <button className="send-btn" onClick={handleSendMessage} disabled={isResumePending}><Send size={18} /></button>
                                </div>
                            )}
                        </div>
                    </section>
                )}

                <aside className="expert-panel glass-panel" style={!selectedMission ? { width: '280px', alignItems: 'flex-start', padding: '24px' } : {}}>
                    {!selectedMission ? (
                        <div className="expert-list-preview" style={{ width: '100%', display: 'flex', flexDirection: 'column', height: '100%' }}>
                            <h3 style={{ fontSize: '1.2rem', marginBottom: '24px', color: 'var(--color-deep-navy)' }}>전문가들을 만나보세요</h3>
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
                            
                            {/* Dictionary Banner */}
                            <div style={{ marginTop: '40px', paddingBottom: '10px' }}>
                                <h3 style={{ fontSize: '1.2rem', marginBottom: '20px', color: 'var(--color-deep-navy)' }}>개념 사전</h3>
                                <div 
                                    className="dictionary-banner" 
                                    onClick={() => setIsDictionaryOpen(true)}
                                    style={{ padding: '16px', backgroundColor: 'rgba(34, 197, 94, 0.1)', color: '#15803d', borderRadius: '14px', display: 'flex', alignItems: 'center', gap: '15px', cursor: 'pointer', transition: 'transform 0.2s, background-color 0.2s' }}
                                    onMouseEnter={(e) => { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.backgroundColor = 'rgba(34, 197, 94, 0.15)'; }}
                                    onMouseLeave={(e) => { e.currentTarget.style.transform = 'none'; e.currentTarget.style.backgroundColor = 'rgba(34, 197, 94, 0.1)'; }}
                                >
                                    <div style={{ backgroundColor: 'white', padding: '10px', borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 2px 5px rgba(0,0,0,0.05)' }}>
                                        <Library size={24} color="#15803d" />
                                    </div>
                                    <div style={{ display: 'flex', flexDirection: 'column' }}>
                                        <span style={{ fontWeight: '600', fontSize: '0.95rem' }}>모든 경제 용어 살펴보기</span>
                                    </div>
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

                <div className={`profile-drawer ${showLeftSidebarProfile ? 'open' : ''}`}>
                    <div className="drawer-content">
                        <div className="drawer-header" style={{ borderBottomColor: 'var(--color-soft-blue)', backgroundColor: 'transparent' }}>
                            <div className="expert-title">
                                <h3>내 프로필</h3>
                            </div>
                            <button className="close-btn" onClick={() => setShowLeftSidebarProfile(false)}>
                                <X size={20} />
                            </button>
                        </div>
                        <div className="drawer-body" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', paddingTop: '40px' }}>
                            <div 
                              onClick={(e) => { e.stopPropagation(); fileInputRef.current?.click(); }}
                              style={{ width: '140px', height: '140px', borderRadius: '50%', backgroundColor: 'var(--color-bg-light)', border: profileImage ? 'none' : '2px dashed var(--color-text-secondary)', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', overflow: 'hidden', boxShadow: '0 4px 15px rgba(0,0,0,0.03)' }}
                            >
                                {profileImage ? (
                                    <img src={profileImage} alt="Profile" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                                ) : (
                                    <span style={{ fontSize: '3rem', color: 'var(--color-text-secondary)', fontWeight: '300' }}>+</span>
                                )}
                            </div>
                            <input type="file" ref={fileInputRef} onChange={handleImageUpload} accept="image/*" style={{ display: 'none' }} />
                            <p style={{ marginTop: '20px', color: 'var(--color-text-secondary)', fontSize: '0.95rem' }}>클릭하여 프로필 사진 업로드</p>
                        </div>
                    </div>
                </div>

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
                                {(() => {
                                    const expertIdToName = { academic: 'The Academic Auditor', market: 'The Market Practitioner', macro: 'The Macro-Connector' };
                                    const activeFeedback = expertFeedbackData?.find(f => f.persona === expertIdToName[activeExpert]);
                                    return (
                                        <div className="feedback-card" style={{ '--expert-color': experts.find(e => e.id === activeExpert)?.color }}>
                                            <div className="feedback-card-header">
                                                <Star size={16} color={experts.find(e => e.id === activeExpert)?.color} fill={experts.find(e => e.id === activeExpert)?.color} />
                                                <span>전문가 통찰력</span>
                                            </div>
                                            <h4>제안하는 관점</h4>
                                            <p>{activeFeedback ? activeFeedback.feedback : '아직 이 전문가의 평가가 없습니다. 메시지를 보내보세요.'}</p>
                                            {activeFeedback && <div style={{ marginTop: '10px', fontSize: '0.9rem', color: experts.find(e => e.id === activeExpert)?.color }}><b>스코어:</b> {Math.round(activeFeedback.score * 100)}점</div>}
                                        </div>
                                    );
                                })()}
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
                reportData={reportData}
                // 아래 줄을 추가하여 모달 안에서 차트를 그릴 수 있게 합니다.
                scoreChart={<RadarScoreChart scores={userScores} />}
            />

            <ConceptDictionary isOpen={isDictionaryOpen} onClose={() => setIsDictionaryOpen(false)} />
            <ReviewModal isOpen={isReviewModalOpen} onClose={() => setIsReviewModalOpen(false)} node={reviewNode} />

            {isErrorModalOpen && (
                <div className="review-overlay active" onClick={() => setIsErrorModalOpen(false)}>
                    <div className="review-modal-card" onClick={(e) => e.stopPropagation()}>
                        <div className="review-modal-header">
                            <h2 style={{margin: 0, fontSize: '1.25rem', color: '#e11d48'}}>연결 지연</h2>
                            <button className="close-btn" onClick={() => setIsErrorModalOpen(false)}><X size={20} /></button>
                        </div>
                        <div className="review-modal-body" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', padding: '30px 20px' }}>
                            <AlertCircle size={48} color="#e11d48" style={{ marginBottom: '20px' }} />
                            <p style={{ margin: 0, color: 'var(--color-text-secondary)', lineHeight: 1.6, fontSize: '1.05rem', fontWeight: 500 }}>
                                현재 접속자가 많아 AI 연결이 지연되고 있습니다.<br/>잠시 후 다시 시도해 주세요.
                            </p>
                        </div>
                        <div className="review-modal-footer" style={{padding: '20px', borderTop: '1px solid var(--color-border)', display: 'flex', gap: '10px', justifyContent: 'flex-end'}}>
                            <button 
                                className="summary-btn" 
                                style={{backgroundColor: 'var(--color-bg-light)', color: 'var(--color-text-secondary)', border: 'none'}}
                                onClick={() => setIsErrorModalOpen(false)}
                            >
                                취소
                            </button>
                            <button 
                                className="send-btn" 
                                style={{width: 'auto', padding: '12px 24px', borderRadius: '12px', gap: '8px', fontSize: '1rem', fontWeight: 700}} 
                                onClick={() => {
                                    setIsErrorModalOpen(false);
                                    handleSendMessage(failedUserMessage);
                                }}
                            >
                                재시도
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default App;