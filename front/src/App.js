/* eslint-disable no-unused-vars */
import React, { useState, useRef, useEffect } from 'react';
import './App.css';
import { Menu, Send, BookOpen, TrendingUp, Gem, Radar, X, Library, CheckCircle, Lock, Star, Globe, Tag, Landmark, Scale, Circle, AlertCircle, Lightbulb, Info, HelpCircle, PlusCircle, Award } from 'lucide-react';
import SummaryModal from './SummaryModal';
import ConceptDictionary from './ConceptDictionary';
import ReviewModal from './ReviewModal';
import Login from './Login';
import Register from './Register';
// 1. 차트 컴포넌트 임포트
import RadarScoreChart from './components/RadarChart';
import LineScoreChart from './components/LineChart';
import AttendanceTracker from './components/AttendanceTracker';
import QuizScreen from './components/QuizScreen';
import ChatTutorialOverlay from './components/ChatTutorialOverlay';
import { studyAPI, dictionaryAPI, quizAPI } from './api/services';
import { t } from './locales';

const getInitialPath = (lang) => [
    { id: 'fundamentals', title: t(lang, 'fundamentals'), status: 'completed', summary: t(lang, 'fundamentalsSummary') },
    { id: 'strategic', title: t(lang, 'strategic'), status: 'active', subNode: t(lang, 'strategicSub') },
    { id: 'market', title: t(lang, 'market'), status: 'locked' },
    { id: 'risk', title: t(lang, 'risk'), status: 'locked' }
];

function App() {
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);
    const [activeExpert, setActiveExpert] = useState(null);
    const [expertDrawerMode, setExpertDrawerMode] = useState('feedback');
    const [isSummaryModalOpen, setIsSummaryModalOpen] = useState(false);
    const [isDictionaryOpen, setIsDictionaryOpen] = useState(false);
    const [dictionarySearchTerm, setDictionarySearchTerm] = useState('');
    const [language, setLanguage] = useState('ko');
    const [expandedSidebarExpert, setExpandedSidebarExpert] = useState(null);

    const [showQuiz, setShowQuiz] = useState(false);
    const [showPostQuiz, setShowPostQuiz] = useState(false);
    const [quizQuestions, setQuizQuestions] = useState([]);

    const [missionConcepts, setMissionConcepts] = useState([]);
    const [isLoadingMissions, setIsLoadingMissions] = useState(true);
    
    useEffect(() => {
        const fetchMissions = async () => {
            setIsLoadingMissions(true);
            try {
                const res = await dictionaryAPI.getList(language);
                const icons = [Tag, Landmark, Globe, TrendingUp, Scale, BookOpen, Star, AlertCircle];
                let iconIndex = 0;
                
                const mappedMissions = res.data.map((item) => {
                    const isAlternativeCost = item.term === '대안비용';
                    let IconComponent = isAlternativeCost ? PlusCircle : icons[iconIndex % icons.length];
                    if (!isAlternativeCost) iconIndex++;
                    
                    if (item.term === '인플레이션') IconComponent = Tag;
                    else if (item.term.includes('금리')) IconComponent = Landmark;
                    else if (item.term === '환율') IconComponent = Globe;
                    else if (item.term === '기회비용' && !isAlternativeCost) IconComponent = Scale;
                    else if (item.term === '복리') IconComponent = TrendingUp;

                    return {
                        id: isAlternativeCost ? 'coming_soon' : item.term,
                        originalId: item.term,
                        title: isAlternativeCost ? (language === 'ko' ? '추가 예정' : 'Coming Soon') : item.term,
                        icon: IconComponent
                    };
                });
                
                mappedMissions.sort((a, b) => (a.id === 'coming_soon') === (b.id === 'coming_soon') ? 0 : (a.id === 'coming_soon' ? 1 : -1));
                
                setMissionConcepts(mappedMissions);
            } catch (error) {
                console.error("Failed to load missions:", error);
                setMissionConcepts([
                    { id: 'coming_soon', title: language === 'ko' ? '추가 예정' : 'Coming Soon', icon: PlusCircle }
                ]);
            } finally {
                setIsLoadingMissions(false);
            }
        };
        fetchMissions();
    }, [language]);

    // Auth State
    const [isLoggedIn, setIsLoggedIn] = useState(false);
    const [authPage, setAuthPage] = useState('login'); // 'login' or 'register'
    const [showSplash, setShowSplash] = useState(false);
    const [isProfileMenuOpen, setIsProfileMenuOpen] = useState(false);
    const [showLeftSidebarProfile, setShowLeftSidebarProfile] = useState(false);
    const [userName, setUserName] = useState('');
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
    const [helpCountLevel3, setHelpCountLevel3] = useState(0);

    // Review Modal State
    const [isReviewModalOpen, setIsReviewModalOpen] = useState(false);
    const [reviewNode, setReviewNode] = useState(null);

    // Learning Path State
    const [pathNodes, setPathNodes] = useState(getInitialPath(language));
    
    useEffect(() => {
        setPathNodes(getInitialPath(language));
    }, [language]);
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
    const [thinkingText, setThinkingText] = useState(t(language, 'analyzingQuestion'));
    const [fallbackToast, setFallbackToast] = useState(false);

    const [consecutiveFailures, setConsecutiveFailures] = useState(0);
    const [highlightedSubNode, setHighlightedSubNode] = useState(null);
    const [academicGlow, setAcademicGlow] = useState(false);
    const [newFeedback, setNewFeedback] = useState({ academic: false, market: false, macro: false });
    const [currentScaffold, setCurrentScaffold] = useState(null);
    const [isEndSuggested, setIsEndSuggested] = useState(false);
    const [showChatTutorial, setShowChatTutorial] = useState(false);

    // 2. 차트에 표시할 실제 점수 데이터 (여기에 저장하면 됩니다)
    const [userScores, setUserScores] = useState(() => {
        const saved = localStorage.getItem('lastUserScores');
        if (saved) {
            try { return JSON.parse(saved); } catch (e) {}
        }
        return { Academic: 0, Market: 0, Macro: 0, Independence: 0 };
    });
    
    const [reportData, setReportData] = useState(() => {
        const saved = localStorage.getItem('lastReportData');
        if (saved) {
            try { return JSON.parse(saved); } catch (e) {}
        }
        return null;
    });

    useEffect(() => {
        if (reportData) {
            localStorage.setItem('lastReportData', JSON.stringify(reportData));
        } else {
            localStorage.removeItem('lastReportData');
        }
    }, [reportData]);

    useEffect(() => {
        localStorage.setItem('lastUserScores', JSON.stringify(userScores));
    }, [userScores]);
    const [isErrorModalOpen, setIsErrorModalOpen] = useState(false);
    const [failedUserMessage, setFailedUserMessage] = useState(null);
    const [scoreHistory, setScoreHistory] = useState([]);

    const messagesEndRef = useRef(null);
    const expertDrawerRef = useRef(null);

    const experts = [
        { id: 'academic', name: t(language, 'academicName'), icon: BookOpen, avatar: '/images/academic_ant_avatar.png', color: 'var(--color-expert-academic)', role: t(language, 'academicRole') },
        { id: 'market', name: t(language, 'marketName'), icon: TrendingUp, avatar: '/images/market_ant_avatar.png', color: 'var(--color-expert-market)', role: t(language, 'marketRole') },
        { id: 'macro', name: t(language, 'macroName'), icon: Globe, avatar: '/images/macro_ant_avatar.png', color: 'var(--color-expert-macro)', role: t(language, 'macroRole') },
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

    // 전문가 창 외부 클릭 시 닫기 및 시작 화면 이동 시 닫기 로직
    useEffect(() => {
        function handleClickOutside(event) {
            if (expertDrawerRef.current && !expertDrawerRef.current.contains(event.target)) {
                // 전문가 아이콘 버튼 클릭 시에는 해당 버튼의 onClick 이벤트가 우선 처리되도록 제외
                if (event.target.closest('.expert-icon-btn')) return;
                setActiveExpert(null);
            }
        }

        if (activeExpert) {
            document.addEventListener('mousedown', handleClickOutside);
        }
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, [activeExpert]);

    useEffect(() => {
        if (!selectedMission) {
            setActiveExpert(null);
        }
    }, [selectedMission]);

    const handleSendMessage = async (retryText = null) => {
        const actualRetryText = typeof retryText === 'string' ? retryText : null;
        const textToSend = actualRetryText || inputValue.trim();
        if (!textToSend || isThinking || !sessionId) return;
        
        const userMessage = { id: Date.now(), sender: 'user', text: textToSend };
        setMessages(prev => [...prev, userMessage]);
        setInputValue('');
        setCurrentScaffold(null); 
        setIsEndSuggested(false);
        
        const thinkingStartTime = Date.now();
        setIsThinking(true);
        setNewFeedback({ academic: true, market: true, macro: true });
        setThinkingText(t(language, 'connecting'));

        const token = localStorage.getItem('access_token');
        const apiBase = process.env.REACT_APP_API_URL || 'http://localhost:8080';
        const wsProtocol = apiBase.startsWith('https') ? 'wss' : 'ws';
        const wsUrl = `${wsProtocol}://${apiBase.replace(/^https?:\/\//, '')}/ws/chat`;
        const ws = new WebSocket(wsUrl);

        let accumulatedString = "";
        let moderatorMessageId = Date.now() + 1;
        let hasAddedModeratorMessage = false;

        ws.onopen = () => {
            ws.send(JSON.stringify({
                token: token,
                session_id: sessionId,
                user_answer: textToSend,
                language: language
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

                    const decision = finalData?.moderator_decision;

                    if (decision?.status !== "scaffold" && finalData.expert_feedback) {
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
                    
                    let moderatorText = decision?.message || "";
                    const plan = decision?.scaffold_plan;
                    
                    if (decision?.status === "mastery" || decision?.status === "suggest_termination") {
                        setIsEndSuggested(true);
                    }

                    
                    if (plan && plan.message) {
                        moderatorText = plan.message;
                    }

                    if (decision?.status === "scaffold") {
                        const step = plan?.step;
                        if (step === "Sub-concept Nudge") {
                            setHelpCountLevel1(prev => prev + 1);
                        } else if (step === "Concept Explanation") {
                            setHelpCountLevel2(prev => prev + 1);
                        } else if (step === "Fill-in-the-Blank") {
                            setHelpCountLevel3(prev => prev + 1);
                        }

                        // Scaffolding UI 상태 업데이트
                        if (["Sub-concept Nudge", "Concept Explanation", "Fill-in-the-Blank", "Solution Reveal"].includes(step)) {
                            setCurrentScaffold({
                                type: step,
                                message: plan.message
                            });
                        }
                    } else if (decision?.probe_triggered) {
                        setHelpCountLevel3(prev => prev + 1);
                        setCurrentScaffold({
                            type: 'Counterfactual Probe',
                            message: decision.counterfactual_probe
                        });
                        if (!moderatorText) {
                            moderatorText = decision.counterfactual_probe;
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

                    const elapsed = Date.now() - thinkingStartTime;
                    setTimeout(() => setIsThinking(false), Math.max(0, 600 - elapsed));
                    ws.close();
                } 
                else if (data.type === "error") {
                    console.error("Server Error via WebSocket:", data.message);
                    
                    if (data.message.includes("[Guardrail")) {
                        setMessages(prev => [...prev, {
                            id: Date.now(),
                            sender: 'moderator',
                            text: data.message
                        }]);
                    } else {
                        setFailedUserMessage(textToSend);
                        setIsErrorModalOpen(true);
                    }

                    const elapsed = Date.now() - thinkingStartTime;
                    setTimeout(() => setIsThinking(false), Math.max(0, 600 - elapsed));
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
            const elapsed = Date.now() - thinkingStartTime;
            setTimeout(() => setIsThinking(false), Math.max(0, 600 - elapsed));
        };

        ws.onclose = (event) => {
            console.log("WebSocket connection closed:", event.code);
            const elapsed = Date.now() - thinkingStartTime;
            setTimeout(() => setIsThinking(false), Math.max(0, 600 - elapsed));
        };
    };

    const handleKeyDown = (e) => { 
        if (e.nativeEvent.isComposing) return;
        if (e.key === 'Enter' && !e.shiftKey) { 
            e.preventDefault(); 
            handleSendMessage(); 
        } 
    };

    const openExpertPanel = (id) => {
        if (activeExpert === id) { setActiveExpert(null); }
        else { setActiveExpert(id); setExpertDrawerMode('feedback'); setNewFeedback(prev => ({ ...prev, [id]: false })); }
    };

    const handleMissionSelect = async (mission) => {
        if (mission.id === 'coming_soon') return;
        
        // Support both Korean and English terms since mission.id is derived from the localized term
        const isInflation = mission.id === '인플레이션' || mission.id.toLowerCase() === 'inflation';
        if (!isInflation) {
            alert(language === 'ko' ? '해당 주제는 퀴즈 출시 예정입니다.' : 'Quiz for this topic is coming soon.');
            return;
        }
        // Switch to chat view to show loading state (quiz will be shown conditionally)
        setSelectedMission(mission.id);
        setActiveNodeId('strategic');
        setHoveredMission(null);
        setShowPostQuiz(false);
        setQuizQuestions([]);
        setIsEndSuggested(false);
        
        // Hide initial question and show only loading state
        setMessages([]); 
        
        const thinkingStartTime = Date.now();
        setIsThinking(true);
        setThinkingText(t(language, 'preparingSession'));

        try {
            const response = await studyAPI.startSession(mission.id, language);
            const data = response.data;
            
            setSessionId(data.session_id);
            setIsResumePending(data.resume_available || false);
            
            // Populate messages only after the session is ready
            if (data.resume_available) {
                setShowQuiz(false);
            } else {
                setShowQuiz(true);
            }
            
            // Fetch Quiz Questions
            try {
                const quizRes = await quizAPI.getQuestions(mission.id);
                if (quizRes.data && quizRes.data.length > 0) {
                    setQuizQuestions(quizRes.data);
                } else {
                    alert(`[DB 알림] '${mission.id}'에 대한 퀴즈 데이터가 비어있습니다. (빈 배열 반환)`);
                    setShowQuiz(false); // Fallback
                }
            } catch (qError) {
                console.error("Quiz API Error:", qError);
                const errorDetail = qError.response?.data?.detail || qError.message;
                alert(`[API 에러] 퀴즈를 불러오지 못했습니다.\n이유: ${errorDetail}`);
            }

            // Populate messages only after the session is ready
            if (data.resume_available) {
                const resumeText = `${data.resume_prompt}\n\n(${t(language, 'lastQuestion')}: ${data.last_ai_response})`;
                setMessages([{ id: Date.now(), sender: 'moderator', text: resumeText }]);
            } else {
                // Use backend question
                const finalStartText = data.initial_question || t(language, 'questionFailed');
                setMessages([{ id: Date.now(), sender: 'moderator', text: finalStartText }]);
            }
            
            setHelpCountLevel1(0);
            setHelpCountLevel2(0);
            setHelpCountLevel3(0);
            setReportData(null);
            setExpertFeedbackData([]);
            setScoreHistory([]);
            setIsSummaryModalOpen(false);
            
            const elapsed = Date.now() - thinkingStartTime;
            setTimeout(() => setIsThinking(false), Math.max(0, 600 - elapsed));
        } catch (error) {
            console.error("Failed to start session:", error);
            alert(t(language, 'startFailed'));
            setSelectedMission(null);
            
            const elapsed = Date.now() - thinkingStartTime;
            setTimeout(() => setIsThinking(false), Math.max(0, 600 - elapsed));
        }
    };

    const handleResumeDecision = async (decision) => {
        if (!selectedMission) return;
        
        setIsEndSuggested(false);
        const thinkingStartTime = Date.now();
        setIsThinking(true);
        try {
            const response = await studyAPI.resolveResume({ concept: selectedMission, decision, language });
            setSessionId(response.data.session_id);
            setIsResumePending(false);
            setMessages(prev => [...prev, { id: Date.now(), sender: 'user', text: decision === 'resume' ? t(language, 'resumeSession') : t(language, 'startFresh') }]);
            
            if (decision === 'fresh') {
                setShowQuiz(true);
            }
            
            // Add the real initial question/resumed question
            setTimeout(() => {
                let finalQuestion = response.data.question || t(language, 'questionFailed');
                setMessages(prev => [...prev, { id: Date.now() + 1, sender: 'moderator', text: finalQuestion }]);
                const elapsed = Date.now() - thinkingStartTime;
                setTimeout(() => setIsThinking(false), Math.max(0, 600 - elapsed));
            }, 500);
        } catch (error) {
            console.error("Failed to resolve resume:", error);
            alert(t(language, 'resumeFailed'));
            const elapsed = Date.now() - thinkingStartTime;
            setTimeout(() => setIsThinking(false), Math.max(0, 600 - elapsed));
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
        if (authPage === 'login') return <Login onLogin={(uid) => { setUserName(uid); setIsLoggedIn(true); setShowSplash(true); }} onGoToRegister={() => setAuthPage('register')} language={language} onLanguageChange={setLanguage} />;
        if (authPage === 'register') return <Register onGoToLogin={() => setAuthPage('login')} language={language} onLanguageChange={setLanguage} />;
    }

    if (showSplash) {
        return (
            <div className="splash-screen fade-in" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', backgroundColor: 'var(--color-bg-main)', textAlign: 'center' }}>
                <h1 style={{ fontSize: '2.5rem', color: 'var(--color-deep-navy)', marginBottom: '50px', fontWeight: '800', animation: 'fadeInDown 0.8s ease-out' }}>
                    {language === 'ko' ? '저희와 함께 경제 지식을 학습해볼까요?' : 'Shall we learn economics together?'}
                </h1>
                <div style={{ display: 'flex', gap: '40px', alignItems: 'center', justifyContent: 'center', flexWrap: 'wrap' }}>
                    {experts.map((expert, index) => (
                        <div key={expert.id} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', animation: `fadeInUp 0.8s ease-out ${index * 0.15}s both` }}>
                            <div style={{ width: '180px', height: '180px', borderRadius: '50%', backgroundColor: '#ffffff', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '20px', boxShadow: '0 10px 30px rgba(0,0,0,0.15)', border: '1px solid rgba(0,0,0,0.05)' }}>
                                <img src={expert.avatar} alt={expert.name} style={{ width: '140px', height: '140px', objectFit: 'contain' }} />
                            </div>
                            <h3 style={{ fontSize: '1.4rem', color: expert.color, fontWeight: '700', margin: '0 0 10px 0' }}>{expert.name}</h3>
                            <p style={{ color: 'var(--color-text-secondary)', fontSize: '1rem', maxWidth: '180px', margin: 0, lineHeight: 1.4 }}>{expert.role}</p>
                        </div>
                    ))}
                </div>
                <button
                    onClick={() => setShowSplash(false)}
                    style={{
                        marginTop: '60px',
                        padding: '16px 40px',
                        backgroundColor: '#22c55e',
                        color: 'white',
                        border: 'none',
                        borderRadius: '30px',
                        cursor: 'pointer',
                        fontWeight: '800',
                        fontSize: '1.2rem',
                        boxShadow: '0 10px 25px rgba(34, 197, 94, 0.3)',
                        transition: 'all 0.2s ease',
                        animation: 'fadeInUp 1s ease-out 0.8s both'
                    }}
                    onMouseEnter={(e) => { e.currentTarget.style.transform = 'translateY(-3px)'; e.currentTarget.style.boxShadow = '0 15px 30px rgba(34, 197, 94, 0.4)'; e.currentTarget.style.backgroundColor = '#16a34a'; }}
                    onMouseLeave={(e) => { e.currentTarget.style.transform = 'none'; e.currentTarget.style.boxShadow = '0 10px 25px rgba(34, 197, 94, 0.3)'; e.currentTarget.style.backgroundColor = '#22c55e'; }}
                >
                    {language === 'ko' ? '학습 시작하기' : 'Start Learning'}
                </button>
            </div>
        );
    }

    return (
        <div className="app-container fade-in">
            <header className="app-header" style={{ height: '75px' }}>
                <div className="header-left">
                    <div
                        className="logo-section"
                        onClick={() => { setSelectedMission(null); setHoveredMission(null); setShowQuiz(false); setShowPostQuiz(false); setIsSummaryModalOpen(false); }}
                        style={{ display: 'flex', alignItems: 'center', cursor: 'pointer', gap: '10px' }}
                    >
                        <img 
                            src="/images/antutor%20logo%20final.png" 
                            alt="Antutor Logo" 
                            style={{ 
                                height: '72px', 
                                marginLeft: '5px'
                            }} 
                        />
                    </div>
                </div>
                <div className="header-right">
                    <select 
                        value={language} 
                        onChange={(e) => setLanguage(e.target.value)}
                        style={{ padding: '6px 12px', borderRadius: '8px', border: '1px solid var(--color-border)', marginRight: '10px', backgroundColor: 'var(--color-bg-light)', color: 'var(--color-deep-navy)', fontWeight: '600' }}
                    >
                        <option value="ko">한국어</option>
                        <option value="en">English</option>
                    </select>
                    {selectedMission && (
                        <button className="summary-btn" onClick={() => {
                            // 원래는 여기서 endSession하고 SummaryModal을 바로 띄웠으나, 사후 퀴즈로 연결
                            setShowPostQuiz(true);
                        }}>
                            <CheckCircle size={16} />
                            <span className="hide-mobile">{t(language, 'endSession')}</span>
                        </button>
                    )}

                    <button className="summary-btn" style={{ padding: '8px 16px', backgroundColor: 'var(--color-bg-light)', border: '1px solid var(--color-border)', color: 'var(--color-deep-navy)' }} onClick={() => {
                        localStorage.removeItem('access_token');
                        window.location.reload();
                    }}>
                        {t(language, 'logout')}
                    </button>
                </div>
            </header>

            <div className="main-content">
                {!(selectedMission && (showQuiz || showPostQuiz)) && (
                    <aside className="sidebar glass-panel open">
                        {!selectedMission ? (
                            <div className="welcome-sidebar-content" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', padding: '20px', textAlign: 'center' }}>
                                <div style={{ position: 'relative', marginbottom: '20px' }}>
                                    <div className="speech-bubble" style={{ position: 'relative', top: 0, left: 0, marginBottom: '20px', display: 'inline-block', fontSize: '1.1rem', padding: '10px 18px' }}>
                                        {hoveredMission ? t(language, 'antReady') : t(language, 'antSleeping')}
                                    </div>
                                    <img src="/images/antutor%20standup.png" alt="Ant" className="mission-card-character bobbing-character" style={{ width: '180px', height: '180px', margin: '0 auto', display: 'block' }} />
                                </div>
                                
                                {/* Motivation Section: Streak & Attendance */}
                                <AttendanceTracker language={language} />
                                
                                {reportData && (
                                    <button 
                                        onClick={() => setIsSummaryModalOpen(true)} 
                                        className="summary-btn" 
                                        style={{marginTop: '20px', width: '100%', justifyContent: 'center', backgroundColor: 'var(--color-bg-light)', color: 'var(--color-deep-navy)', border: '1px solid var(--color-border)', boxShadow: '0 4px 15px rgba(0,0,0,0.05)'}}
                                        onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = 'white'; e.currentTarget.style.transform = 'translateY(-2px)'; }}
                                        onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = 'var(--color-bg-light)'; e.currentTarget.style.transform = 'none'; }}
                                    >
                                        <Award size={18} color="#f59e0b" /> {language === 'ko' ? '최근 리포트 다시보기' : 'View Recent Report'}
                                    </button>
                                )}
                            </div>
                        ) : (
                            <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                                <div className="sidebar-header"><h2>{t(language, 'learningPath')}</h2></div>
                                {/* 학습 경로 노드 제거됨 */}
                                <div style={{ flex: 'none', padding: '0 10px', marginTop: '20px' }}>
                                    <div style={{ fontSize: '1rem', fontWeight: '800', color: 'var(--color-deep-navy)', marginBottom: '8px' }}>
                                        {language === 'ko' ? '누적 점수' : 'Cumulative Score'}
                                    </div>
                                    <LineScoreChart history={scoreHistory} language={language} />
                                </div>
                                <div style={{ flex: 1 }}></div> {/* 스페이서로 공간 확보 */}
                                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '10px 15px', borderTop: '1px solid var(--color-border)', backgroundColor: 'rgba(255,255,255,0.5)', marginBottom: '10px' }}>
                                    <div style={{ alignSelf: 'flex-start', fontSize: '1rem', fontWeight: '800', color: 'var(--color-deep-navy)', marginBottom: '5px' }}>
                                        {language === 'ko' ? '현재 점수' : 'Current Score'}
                                    </div>
                                    <RadarScoreChart scores={userScores} isSidebar={true} language={language} />
                                    <div style={{ marginTop: '-30px', fontSize: '0.75rem', color: 'var(--color-text-secondary)', textAlign: 'center', lineHeight: '1.4' }}>
                                        {language === 'ko' ? (
                                            <>
                                                <div><strong style={{color: 'var(--color-expert-academic)'}}>정확성</strong> - 학술 개념 전문가</div>
                                                <div><strong style={{color: 'var(--color-expert-market)'}}>현실성</strong> - 시장 실무 전문가</div>
                                                <div><strong style={{color: 'var(--color-expert-macro)'}}>통찰력</strong> - 거시 경제 전문가</div>
                                            </>
                                        ) : (
                                            <>
                                                <div><strong style={{color: 'var(--color-expert-academic)'}}>Accuracy</strong> - Academic Expert</div>
                                                <div><strong style={{color: 'var(--color-expert-market)'}}>Realism</strong> - Market Expert</div>
                                                <div><strong style={{color: 'var(--color-expert-macro)'}}>Insight</strong> - Macro Expert</div>
                                            </>
                                        )}
                                    </div>
                                </div>
                            </div>
                        )}
                    </aside>
                )}

                {!selectedMission ? (
                    <section className="mission-selection-container glass-panel">
                        <div className="mission-selection-content-wrapper">
                            <h2 className="mission-title">
                                {language === 'ko' ? (
                                    <>{userName}<span style={{ fontWeight: '400' }}>{t(language, 'missionSelectTitleUser')}</span></>
                                ) : (
                                    <>{userName}{t(language, 'missionSelectTitleUser')}</>
                                )}
                            </h2>
                            <div className="mission-grid">
                                {isLoadingMissions ? (
                                    <div style={{ textAlign: 'center', width: '100%', padding: '40px', color: 'var(--color-text-secondary)' }}>
                                        <div style={{ display: 'inline-block', width: '30px', height: '30px', border: '3px solid rgba(59, 130, 246, 0.3)', borderTopColor: 'var(--color-expert-academic)', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
                                    </div>
                                ) : missionConcepts.map(mission => (
                                    <div 
                                        key={mission.id} 
                                        className="mission-card" 
                                        onClick={() => handleMissionSelect(mission)}
                                        onMouseEnter={() => mission.id !== 'coming_soon' && setHoveredMission(mission.id)}
                                        onMouseLeave={() => setHoveredMission(null)}
                                        style={mission.id === 'coming_soon' ? { cursor: 'default', opacity: 0.7, transform: 'none', boxShadow: 'none' } : {}}
                                    >
                                        <div className="mission-card-icon" style={mission.id === 'coming_soon' ? { backgroundColor: 'transparent' } : {}}>
                                            <mission.icon size={38} color={mission.id === 'coming_soon' ? "#cbd5e1" : "#4ade80"} />
                                        </div>
                                        <h3 style={mission.id === 'coming_soon' ? { color: '#94a3b8' } : {}}>{mission.title}</h3>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </section>
                ) : showQuiz ? (
                    <QuizScreen 
                        questions={quizQuestions}
                        sessionId={sessionId}
                        concept={selectedMission}
                        userId={userName}
                        language={language}
                        onComplete={() => {
                            setShowQuiz(false);
                            setShowChatTutorial(true);
                        }}
                    />
                ) : showPostQuiz ? (
                    <QuizScreen 
                        questions={quizQuestions}
                        sessionId={sessionId}
                        concept={selectedMission}
                        userId={userName}
                        language={language}
                        isPostTest={true}
                        onComplete={async () => {
                            if (sessionId) {
                                try {
                                    const response = await studyAPI.endSession({ session_id: sessionId, language });
                                    setReportData(response.data);
                                } catch (error) {
                                    console.error("End session failed", error);
                                }
                            }
                            setIsSummaryModalOpen(true);
                            setShowPostQuiz(false);
                        }}
                    />
                ) : (
                    <section className="chat-container glass-panel">
                        <div className="chat-history">
                            {messages.map((msg) => (
                                <div key={msg.id} className={`message ${msg.sender}`}>
                                    <div className="message-bubble">
                                        {msg.text}
                                        {msg.scaffold?.step && ["Sub-concept Nudge", "Concept Explanation", "Fill-in-the-Blank", "Solution Reveal"].includes(msg.scaffold.step) && (
                                            <div className="scaffold-hint-badge">
                                                {msg.scaffold.step === "Solution Reveal" ? <CheckCircle size={14} /> : msg.scaffold.step === "Fill-in-the-Blank" ? <Info size={14} /> : <Lightbulb size={14} />}
                                                <span>
                                                    {msg.scaffold.step === "Sub-concept Nudge" ? t(language, 'hintIncludedL1') : 
                                                     msg.scaffold.step === "Concept Explanation" ? t(language, 'hintIncludedL2') : 
                                                     msg.scaffold.step === "Fill-in-the-Blank" ? t(language, 'hintIncludedL3') :
                                                     t(language, 'hintIncludedL4')}
                                                </span>
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
                            {isEndSuggested && (
                                <div className="message moderator" style={{ animation: 'fadeInUp 0.3s ease-out' }}>
                                    <div className="message-bubble" style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '15px', padding: '15px 20px', backgroundColor: 'var(--color-primary-light)', border: '2px solid var(--color-primary)' }}>
                                        <div style={{ flex: 1, minWidth: '250px', whiteSpace: 'pre-line' }}>
                                            {language === 'ko' 
                                                ? '🎉 평균 60점 이상 3연속을 달성했습니다!\n해당 개념에 대한 학습이 잘 이루어진 것 같네요!\n세션을 종료하시겠습니까, 더 이어서 학습하시겠습니까?'
                                                : '🎉 You have achieved an average score of 60 or higher 3 times in a row!\nIt seems you have a good understanding of this concept!\nWould you like to end the session, or continue learning?'}
                                        </div>
                                        <div style={{ display: 'flex', gap: '10px' }}>
                                            <button 
                                                onClick={() => setIsEndSuggested(false)}
                                                style={{ 
                                                    padding: '8px 16px', 
                                                    backgroundColor: 'white', 
                                                    border: '1px solid var(--color-border)', 
                                                    color: 'var(--color-text-secondary)', 
                                                    borderRadius: '8px', 
                                                    cursor: 'pointer', 
                                                    fontWeight: '600',
                                                    fontSize: '0.9rem',
                                                    whiteSpace: 'nowrap',
                                                    transition: 'all 0.2s'
                                                }}
                                                onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = '#f1f5f9'; }}
                                                onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = 'white'; }}
                                            >
                                                {language === 'ko' ? '계속 학습하기' : 'Continue'}
                                            </button>
                                            <button 
                                                onClick={() => {
                                                    setIsEndSuggested(false);
                                                    setShowPostQuiz(true);
                                                }}
                                                style={{ 
                                                    padding: '8px 16px', 
                                                    backgroundColor: '#22c55e', 
                                                    color: 'white', 
                                                    border: 'none', 
                                                    borderRadius: '8px', 
                                                    cursor: 'pointer', 
                                                    fontWeight: '600',
                                                    fontSize: '0.9rem',
                                                    whiteSpace: 'nowrap',
                                                    transition: 'all 0.2s',
                                                }}
                                                onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = '#16a34a'; }}
                                                onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = '#22c55e'; }}
                                            >
                                                {language === 'ko' ? '세션 종료' : 'End Session'}
                                            </button>
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
                                        {t(language, 'resumeSessionBtn')}
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
                                        {t(language, 'startFreshBtn')}
                                    </button>
                                </div>
                            ) : (
                                <div style={{ width: '100%' }}>
                                    <div className="help-action-chips" style={{ display: 'flex', gap: '10px', marginBottom: '12px', animation: 'fadeInUp 0.4s ease-out', alignItems: 'center' }}>
                                        <button 
                                            className="help-action-chip" 
                                            onClick={() => handleSendMessage(t(language, 'requestHint'))}
                                            disabled={isThinking}
                                        >
                                            <Lightbulb size={14} />
                                            <span>{t(language, 'requestHint')}</span>
                                        </button>
                                        <span style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', fontWeight: '500' }}>
                                            {language === 'ko' ? '💡 답변하기 어려운 경우엔 왼쪽 힌트요청 버튼을 눌러주세요.' : '💡 If you find it difficult to answer, please click the hint button on the left.'}
                                        </span>
                                    </div>
                                    {currentScaffold && (
                                        <div className={`scaffold-info-banner ${currentScaffold.type === 'Fill-in-the-Blank' ? 'fill-mode' : 'nudge-mode'}`}>
                                            <div className="scaffold-info-content">
                                                {currentScaffold.type === 'Fill-in-the-Blank' ? <Info size={16} /> : <Lightbulb size={16} />}
                                                <span>{currentScaffold.type === 'Fill-in-the-Blank' ? t(language, 'fillBlankHelp') : currentScaffold.type === 'Counterfactual Probe' ? t(language, 'cfProbeHelp') : t(language, 'nudgeHelp')}</span>
                                            </div>
                                        </div>
                                    )}
                                    <div className={`input-wrapper ${currentScaffold?.type === 'Fill-in-the-Blank' ? 'highlight-input' : ''}`}>
                                        <textarea 
                                            value={inputValue} 
                                            onChange={(e) => setInputValue(e.target.value)} 
                                            onKeyDown={handleKeyDown} 
                                            placeholder={currentScaffold?.type === 'Fill-in-the-Blank' ? t(language, 'fillBlankPlaceholder') : t(language, 'answerPlaceholder')} 
                                            disabled={isResumePending} 
                                            rows={1}
                                        />
                                        <button className="send-btn" onClick={handleSendMessage} disabled={isResumePending}><Send size={18} /></button>
                                    </div>
                                </div>
                            )}
                        </div>
                        
                        {/* Chat Tutorial Overlay */}
                        {showChatTutorial && (
                            <ChatTutorialOverlay 
                                language={language} 
                                onClose={() => setShowChatTutorial(false)} 
                            />
                        )}
                    </section>
                )}

                {!(selectedMission && (showQuiz || showPostQuiz)) && (
                    <aside className="expert-panel glass-panel" style={!selectedMission ? { width: '280px', alignItems: 'flex-start', padding: '24px' } : {}}>
                        {!selectedMission ? (
                            <div className="expert-team-container">
                                <h3 className="expert-team-title">{t(language, 'myAiTeam')}</h3>
                                <div className="expert-profiles-list">
                                    {experts.map(expert => (
                                        <div 
                                            key={expert.id} 
                                            className={`expert-profile-card ${expandedSidebarExpert === expert.id ? 'expanded' : ''}`}
                                            onClick={() => setExpandedSidebarExpert(prev => prev === expert.id ? null : expert.id)}
                                            style={{ cursor: 'pointer' }}
                                        >
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
                                <div style={{ marginTop: language === 'en' ? '10px' : '40px', paddingBottom: '10px' }}>
                                    <h3 style={{ fontSize: '1.2rem', marginBottom: language === 'en' ? '12px' : '20px', color: 'var(--color-deep-navy)' }}>{t(language, 'conceptDictTitle')}</h3>
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
                                            <span style={{ fontWeight: '600', fontSize: '0.95rem' }}>{t(language, 'exploreAllConcepts')}</span>
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
                )}

                <div className={`profile-drawer ${showLeftSidebarProfile ? 'open' : ''}`}>
                    <div className="drawer-content">
                        <div className="drawer-header" style={{ borderBottomColor: 'var(--color-expert-market)', backgroundColor: 'transparent' }}>
                            <div className="expert-title">
                                <h3>{t(language, 'myProfile')}</h3>
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
                            <p style={{ marginTop: '20px', color: 'var(--color-text-secondary)', fontSize: '0.95rem' }}>{t(language, 'uploadProfilePic')}</p>
                        </div>
                    </div>
                </div>

                <div ref={expertDrawerRef} className={`expert-drawer ${activeExpert ? 'open' : ''}`}>
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
                                                <span>{t(language, 'expertInsights')}</span>
                                            </div>
                                            <h4>{t(language, 'suggestedPerspective')}</h4>
                                            <p>{activeFeedback ? activeFeedback.feedback : t(language, 'noFeedbackYet')}</p>
                                            {activeFeedback && <div style={{ marginTop: '10px', fontSize: '0.9rem', color: experts.find(e => e.id === activeExpert)?.color }}><b>{t(language, 'score')}</b> {Math.round(activeFeedback.score * 100)}</div>}
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
                onClose={() => { setSelectedMission(null); setHoveredMission(null); setShowQuiz(false); setShowPostQuiz(false); setIsSummaryModalOpen(false); }}
                helpCountLevel1={helpCountLevel1}
                helpCountLevel2={helpCountLevel2}
                helpCountLevel3={helpCountLevel3}
                reportData={reportData}
                language={language}
                scoreChart={<RadarScoreChart scores={userScores} language={language} />}
            />

            <ConceptDictionary isOpen={isDictionaryOpen} onClose={() => setIsDictionaryOpen(false)} language={language} onLanguageChange={setLanguage} />
            <ReviewModal isOpen={isReviewModalOpen} onClose={() => setIsReviewModalOpen(false)} node={reviewNode} language={language} />

            {isErrorModalOpen && (
                <div className="review-overlay active" onClick={() => setIsErrorModalOpen(false)}>
                    <div className="review-modal-card" onClick={(e) => e.stopPropagation()}>
                        <div className="review-modal-header">
                            <h2 style={{margin: 0, fontSize: '1.25rem', color: '#e11d48'}}>{t(language, 'connectionDelay')}</h2>
                            <button className="close-btn" onClick={() => setIsErrorModalOpen(false)}><X size={20} /></button>
                        </div>
                        <div className="review-modal-body" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', padding: '30px 20px' }}>
                            <AlertCircle size={48} color="#e11d48" style={{ marginBottom: '20px' }} />
                            <p style={{ margin: 0, color: 'var(--color-text-secondary)', lineHeight: 1.6, fontSize: '1.05rem', fontWeight: 500, whiteSpace: 'pre-line' }}>
                                {t(language, 'delayMessage')}
                            </p>
                        </div>
                        <div className="review-modal-footer" style={{padding: '20px', borderTop: '1px solid var(--color-border)', display: 'flex', gap: '10px', justifyContent: 'flex-end'}}>
                            <button 
                                className="summary-btn" 
                                style={{backgroundColor: 'var(--color-bg-light)', color: 'var(--color-text-secondary)', border: 'none'}}
                                onClick={() => setIsErrorModalOpen(false)}
                            >
                                {t(language, 'cancel')}
                            </button>
                            <button 
                                className="send-btn" 
                                style={{width: 'auto', padding: '12px 24px', borderRadius: '12px', gap: '8px', fontSize: '1rem', fontWeight: 700}} 
                                onClick={() => {
                                    setIsErrorModalOpen(false);
                                    handleSendMessage(failedUserMessage);
                                }}
                            >
                                {t(language, 'retry')}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {fallbackToast && (
                <div className="fallback-toast-alert">
                    <AlertCircle size={18} />
                    <span>{t(language, 'fallbackToast')}</span>
                </div>
            )}
        </div>
    );
}

export default App;