import React, { useState, useRef, useEffect } from 'react';
import './App.css';
import { Menu, Send, BookOpen, TrendingUp, Gem, Radar, X, Library, CheckCircle, Lock, Star, Globe, Tag, Landmark, Scale, Circle, AlertCircle, Lightbulb, Info } from 'lucide-react';
import SummaryModal from './SummaryModal';
import ConceptDictionary from './ConceptDictionary';
import ReviewModal from './ReviewModal';
import Login from './Login';
import Register from './Register';
// 1. 차트 컴포넌트 임포트
import RadarScoreChart from './components/RadarChart';
import LineScoreChart from './components/LineChart';
import { studyAPI } from './api/services';
const missionConcepts = [
    {
        id: '인플레이션',
        title: '인플레이션',
        icon: Tag
    },
    {
        id: '기준 금리',
        title: '기준금리',
        icon: Landmark
    },
    {
        id: '환율',
        title: '환율',
        icon: Globe
    },
    {
        id: '대안비용',
        title: '기회비용',
        icon: Scale
    },
    {
        id: '복리',
        title: '복리',
        icon: TrendingUp
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
    const [thinkingText, setThinkingText] = useState("질문을 분석 중입니다...");
    const [fallbackToast, setFallbackToast] = useState(false);

    const [consecutiveFailures, setConsecutiveFailures] = useState(0);
    const [highlightedSubNode, setHighlightedSubNode] = useState(null);
    const [academicGlow, setAcademicGlow] = useState(false);
    const [newFeedback, setNewFeedback] = useState({ academic: false, market: false, macro: false });
    const [currentScaffold, setCurrentScaffold] = useState(null);

    // 2. 차트에 표시할 실제 점수 데이터 (여기에 저장하면 됩니다)
    const [userScores, setUserScores] = useState({
        Academic: 0,
        Market: 0,
        Macro: 0,
        Independence: 0 // 이 값은 차트 컴포넌트 내부 filter에 의해 자동으로 무시됩니다.
    });
    const [reportData, setReportData] = useState(null);
    const [isErrorModalOpen, setIsErrorModalOpen] = useState(false);
    const [failedUserMessage, setFailedUserMessage] = useState(null);
    const [scoreHistory, setScoreHistory] = useState([]);

    const messagesEndRef = useRef(null);

    const experts = [
        { id: 'academic', name: '학술 전문가', icon: BookOpen, avatar: '/images/academic_ant_avatar.png', color: 'var(--color-expert-academic)', role: '기본 이론과 학문적 엄밀성에 중점을 둡니다.' },
        { id: 'market', name: '시장 실무자', icon: TrendingUp, avatar: '/images/market_ant_avatar.png', color: 'var(--color-expert-market)', role: '실제 시장 동향 및 데이터에 중점을 둡니다.' },
        { id: 'macro', name: '매크로 분석가', icon: Globe, avatar: '/images/macro_ant_avatar.png', color: 'var(--color-expert-macro)', role: '글로벌 경제 지표 및 정책에 중점을 둡니다.' },
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
        const actualRetryText = typeof retryText === 'string' ? retryText : null;
        const textToSend = actualRetryText || inputValue.trim();
        if (!textToSend || isThinking || !sessionId) return;
        
        if (!actualRetryText) {
            const userMessage = { id: Date.now(), sender: 'user', text: textToSend };
            setMessages(prev => [...prev, userMessage]);
            setInputValue('');
            setCurrentScaffold(null); // 답변 전송 시 Scaffolding 상태 초기화
        }
        setIsThinking(true);
        setNewFeedback({ academic: true, market: true, macro: true });
        setThinkingText("연결 중입니다...");

        const token = localStorage.getItem('access_token');
        // 백엔드 주소에 맞춰 WebSocket URL 설정 (기존 baseURL 기반으로 유추)
        const wsUrl = `ws://localhost:8000/ws/chat`;
        const ws = new WebSocket(wsUrl);

        let accumulatedString = "";
        let moderatorMessageId = Date.now() + 1;
        let hasAddedModeratorMessage = false;

        ws.onopen = () => {
            ws.send(JSON.stringify({
                token: token,
                session_id: sessionId,
                user_answer: textToSend
            }));
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);

                if (data.type === "status") {
                    // 에이전트들의 상태 업데이트
                    setThinkingText(data.message);
                } 
                else if (data.type === "stream") {
                    // 실시간 메시지 스트리밍
                    accumulatedString += data.chunk;
                    
                    // 백엔드 가이드의 정규식을 사용하여 텍스트 추출
                    const match = accumulatedString.match(/"message"\s*:\s*"([^"]*)/);
                    if (match && match[1]) {
                        // 유니코드 이스케이프 및 개행 문자 처리
                        const typingText = match[1]
                            .replace(/\\n/g, '\n')
                            .replace(/\\"/g, '"')
                            .replace(/\\u([0-9a-fA-F]{4})/g, (match, grp) => String.fromCharCode(parseInt(grp, 16)));
                        
                        if (!hasAddedModeratorMessage) {
                            setMessages(prev => [...prev, { id: moderatorMessageId, sender: 'moderator', text: typingText }]);
                            hasAddedModeratorMessage = true;
                        } else {
                            setMessages(prev => prev.map(m => m.id === moderatorMessageId ? { ...m, text: typingText } : m));
                        }
                    }
                } 
                else if (data.type === "final_result") {
                    // 최종 결과 처리 (기존 Axios 응답과 동일한 구조)
                    const finalData = data.data;

                    if (finalData.expert_feedback) {
                        setExpertFeedbackData(finalData.expert_feedback);
                        
                        const newScores = { ...userScores };
                        finalData.expert_feedback.forEach(f => {
                            if (f.persona === 'The Academic Auditor') newScores.Academic = Math.round(f.score * 100);
                            if (f.persona === 'The Market Practitioner') newScores.Market = Math.round(f.score * 100);
                            if (f.persona === 'The Macro-Connector') newScores.Macro = Math.round(f.score * 100);
                        });
                        setUserScores(newScores);

                        // Update Score History
                        setScoreHistory(prev => {
                            const last = prev.length > 0 ? prev[prev.length - 1] : { Academic: 0, Market: 0, Macro: 0 };
                            return [
                                ...prev,
                                {
                                    turn: prev.length + 1,
                                    Academic: last.Academic + newScores.Academic,
                                    Market: last.Market + newScores.Market,
                                    Macro: last.Macro + newScores.Macro
                                }
                            ];
                        });
                    }
                    
                    const decision = finalData?.moderator_decision;
                    let moderatorText = decision?.message || "";
                    const plan = decision?.scaffold_plan || decision?.scaffolding_plan;
                    
                    if (plan && plan.message) {
                        moderatorText = plan.message;
                    }

                    if (decision?.status === "scaffold") {
                        const step = plan?.step;
                        if (step === "Concept Dictionary Link" || String(step) === "1") {
                            setHelpCountLevel1(prev => prev + 1);
                        } else {
                            setHelpCountLevel2(prev => prev + 1);
                        }

                        // Scaffolding UI 상태 업데이트
                        if (step === "Sub-concept Nudge" || step === "Fill-in-the-Blank") {
                            setCurrentScaffold({
                                type: step,
                                message: plan.message
                            });
                        }
                    } else {
                        setCurrentScaffold(null);
                    }

                    // 최종 텍스트로 업데이트
                    if (moderatorText) {
                        setMessages(prev => {
                            const exists = prev.find(m => m.id === moderatorMessageId);
                            const msgWithScaffold = { 
                                id: moderatorMessageId, 
                                sender: 'moderator', 
                                text: moderatorText,
                                scaffold: decision?.status === "scaffold" ? plan : null 
                            };
                            if (exists) {
                                return prev.map(m => m.id === moderatorMessageId ? msgWithScaffold : m);
                            } else {
                                return [...prev, msgWithScaffold];
                            }
                        });
                    }

                    // Handle Fallback Response
                    if (finalData.is_fallback) {
                        setFallbackToast(true);
                        setTimeout(() => setFallbackToast(false), 5000);
                    }

                    setIsThinking(false);
                    ws.close();
                } 
                else if (data.type === "error") {
                    console.error("Server Error via WebSocket:", data.message);
                    setFailedUserMessage(textToSend);
                    setIsErrorModalOpen(true);
                    setIsThinking(false);
                    ws.close();
                }
            } catch (err) {
                console.error("Error parsing WebSocket message:", err);
            }
        };

        ws.onerror = (error) => {
            console.error("WebSocket Connection Error:", error);
            setFailedUserMessage(textToSend);
            setIsErrorModalOpen(true);
            setIsThinking(false);
        };

        ws.onclose = (event) => {
            console.log("WebSocket connection closed:", event.code);
            setIsThinking(false);
        };
    };

    const handleKeyDown = (e) => { if (e.key === 'Enter') { e.preventDefault(); handleSendMessage(); } };

    const openExpertPanel = (id) => {
        if (activeExpert === id) { setActiveExpert(null); }
        else { setActiveExpert(id); setExpertDrawerMode('feedback'); setNewFeedback(prev => ({ ...prev, [id]: false })); }
    };

    const handleMissionSelect = async (mission) => {
        // Optimistic UI Update: Switch to chat screen immediately
        setSelectedMission(mission.id);
        setActiveNodeId('strategic');
        setHoveredMission(null);
        
        // Hide initial question and show only loading state
        setMessages([]); 
        setIsThinking(true);
        setThinkingText("학습 세션을 준비하고 있습니다...");

        try {
            const response = await studyAPI.startSession(mission.id);
            const data = response.data;
            
            setSessionId(data.session_id);
            setIsResumePending(data.resume_available || false);
            
            // Populate messages only after the session is ready
            if (data.resume_available) {
                const resumeText = `${data.resume_prompt}\n\n(마지막 질문: ${data.last_ai_response})`;
                setMessages([{ id: Date.now(), sender: 'moderator', text: resumeText }]);
            } else {
                // Use backend question
                const finalStartText = data.initial_question || "첫 질문을 불러올 수 없습니다.";
                setMessages([{ id: Date.now(), sender: 'moderator', text: finalStartText }]);
            }
            
            setHelpCountLevel1(0);
            setHelpCountLevel2(0);
            setReportData(null);
            setExpertFeedbackData([]);
            setScoreHistory([]);
            setIsThinking(false);
        } catch (error) {
            console.error("Failed to start session:", error);
            alert("세션 시작에 실패했습니다. 다시 시도해주세요.");
            setSelectedMission(null);
            setIsThinking(false);
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
                let finalQuestion = response.data.question || "첫 질문을 불러올 수 없습니다.";
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
                            <div style={{ flex: 'none', padding: '0 10px', marginTop: '30px' }}>
                                <LineScoreChart history={scoreHistory} />
                            </div>
                            <div style={{ flex: 1 }}></div> {/* 스페이서로 공간 확보 */}
                            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '20px', borderTop: '1px solid var(--color-border)', backgroundColor: 'rgba(255,255,255,0.5)', marginBottom: '20px' }}>
                                <img src="/images/antutor%20standup.png" alt="Studying Ant" className="bobbing-character" style={{ width: '120px', height: '120px', objectFit: 'contain' }} />
                                <div style={{ marginTop: '8px', fontSize: '0.9rem', fontWeight: 'bold', color: '#000000' }}>정말 잘하고 있어요!</div>
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
                                        <mission.icon size={38} color="#4ade80" />
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
                                    <div className="message-bubble">
                                        {msg.text}
                                        {msg.scaffold?.step === "Sub-concept Nudge" && (
                                            <div className="scaffold-hint-badge">
                                                <Lightbulb size={14} />
                                                <span>개념 힌트가 포함되어 있습니다</span>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ))}
                            {isThinking && (
                                <div className="message moderator">
                                    <div className="message-bubble thinking-bubble" style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: '8px' }}>
                                        <div style={{ display: 'flex', gap: '5px' }}>
                                            <div className="dot"></div>
                                            <div className="dot"></div>
                                            <div className="dot"></div>
                                        </div>
                                        <div className="thinking-text" style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', fontWeight: 500, animation: 'fadeIn 0.5s ease-in-out' }}>
                                            {thinkingText}
                                        </div>
                                    </div>
                                </div>
                            )}
                            <div ref={messagesEndRef} />
                        </div>
                        <div className="chat-input-area">
                            {isResumePending ? (
                                <div style={{ display: 'flex', gap: '20px', width: '100%', justifyContent: 'center', padding: '20px 0', animation: 'fadeInUp 0.5s ease-out' }}>
                                    {/* ... 기존 버튼들 ... */}
                                    <button 
                                        onClick={() => handleResumeDecision('resume')}
                                        style={{ 
                                            padding: '16px 32px', 
                                            backgroundColor: '#22c55e', 
                                            color: 'white', 
                                            border: 'none', 
                                            borderRadius: '16px', 
                                            cursor: 'pointer', 
                                            fontWeight: '800',
                                            fontSize: '1.1rem',
                                            boxShadow: '0 10px 25px rgba(34, 197, 94, 0.3)',
                                            transition: 'all 0.2s',
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: '10px'
                                        }}
                                        onMouseEnter={(e) => { e.currentTarget.style.transform = 'translateY(-3px)'; e.currentTarget.style.boxShadow = '0 15px 30px rgba(34, 197, 94, 0.4)'; e.currentTarget.style.backgroundColor = '#16a34a'; }}
                                        onMouseLeave={(e) => { e.currentTarget.style.transform = 'none'; e.currentTarget.style.boxShadow = '0 10px 25px rgba(34, 197, 94, 0.3)'; e.currentTarget.style.backgroundColor = '#22c55e'; }}
                                    >
                                        <Radar size={22} />
                                        이어서 학습하기
                                    </button>
                                    <button 
                                        onClick={() => handleResumeDecision('fresh')}
                                        style={{ 
                                            padding: '16px 32px', 
                                            backgroundColor: 'rgba(255, 255, 255, 0.9)', 
                                            border: '1px solid var(--color-border)', 
                                            color: 'var(--color-text-secondary)', 
                                            borderRadius: '16px', 
                                            cursor: 'pointer', 
                                            fontWeight: '700',
                                            fontSize: '1.1rem',
                                            boxShadow: '0 4px 15px rgba(0, 0, 0, 0.05)',
                                            transition: 'all 0.2s'
                                        }}
                                        onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = 'white'; e.currentTarget.style.transform = 'translateY(-3px)'; e.currentTarget.style.boxShadow = '0 8px 20px rgba(0,0,0,0.1)'; }}
                                        onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.9)'; e.currentTarget.style.transform = 'none'; e.currentTarget.style.boxShadow = '0 4px 15px rgba(0,0,0,0.05)'; }}
                                    >
                                        처음부터 다시하기
                                    </button>
                                </div>
                            ) : (
                                <div style={{ width: '100%' }}>
                                    {currentScaffold && (
                                        <div className={`scaffold-info-banner ${currentScaffold.type === 'Fill-in-the-Blank' ? 'fill-mode' : 'nudge-mode'}`}>
                                            <div className="scaffold-info-content">
                                                {currentScaffold.type === 'Fill-in-the-Blank' ? <Info size={16} /> : <Lightbulb size={16} />}
                                                <span>{currentScaffold.type === 'Fill-in-the-Blank' ? '아래 문장의 빈칸을 채워주세요.' : '힌트를 참고하여 답변을 완성해 보세요.'}</span>
                                            </div>
                                        </div>
                                    )}
                                    <div className={`input-wrapper ${currentScaffold?.type === 'Fill-in-the-Blank' ? 'highlight-input' : ''}`}>
                                        <input 
                                            type="text" 
                                            value={inputValue} 
                                            onChange={(e) => setInputValue(e.target.value)} 
                                            onKeyDown={handleKeyDown} 
                                            placeholder={currentScaffold?.type === 'Fill-in-the-Blank' ? '빈칸에 들어갈 내용을 입력하세요...' : '답변을 입력하세요...'} 
                                            disabled={isResumePending} 
                                        />
                                        <button className="send-btn" onClick={handleSendMessage} disabled={isResumePending}><Send size={18} /></button>
                                    </div>
                                </div>
                            )}
                        </div>
                    </section>
                )}

                <aside className="expert-panel glass-panel" style={!selectedMission ? { width: '280px', alignItems: 'flex-start', padding: '24px' } : {}}>
                    {!selectedMission ? (
                        <div className="expert-team-container">
                            <h3 className="expert-team-title">나의 AI 전문가 팀</h3>
                            <div className="expert-profiles-list">
                                {experts.map(expert => (
                                    <div key={expert.id} className="expert-profile-card">
                                        <div className="expert-avatar-wrapper">
                                            <img src={expert.avatar} alt={expert.name} className="expert-avatar-img" />
                                            <div className="status-indicator online"></div>
                                        </div>
                                        <div className="expert-info">
                                            <div className="expert-name-row">
                                                <span className="expert-name" style={{ color: expert.color }}>{expert.name}</span>
                                                <span className="online-text">Online</span>
                                            </div>
                                            <p className="expert-role-text">{expert.role}</p>
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
                        <div className="drawer-header" style={{ borderBottomColor: 'var(--color-expert-market)', backgroundColor: 'transparent' }}>
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

            {fallbackToast && (
                <div className="fallback-toast-alert">
                    <AlertCircle size={18} />
                    <span>서버 혼잡으로 인해 임시 요약된 피드백을 제공합니다.</span>
                </div>
            )}
        </div>
    );
}

export default App;