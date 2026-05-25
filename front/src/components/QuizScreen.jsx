import React, { useState, useEffect } from 'react';
import { ArrowRight, CheckCircle2, ShieldAlert, Target, Award, Brain, ChevronLeft, ChevronRight, Lightbulb } from 'lucide-react';
import { quizAPI } from '../api/services';
import { t } from '../locales';
import './QuizScreen.css';

const QuizScreen = ({ questions, sessionId, concept, userId, language, isPostTest = false, onComplete }) => {
    const [currentIndex, setCurrentIndex] = useState(0);
    const [answers, setAnswers] = useState([]);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [result, setResult] = useState(null);
    const [startedPostQuiz, setStartedPostQuiz] = useState(false);
    const [reviewPage, setReviewPage] = useState(0);
    const [showCommentary, setShowCommentary] = useState(false);

    // Initialize answers array when questions are loaded
    useEffect(() => {
        if (questions && questions.length > 0 && answers.length === 0) {
            setAnswers(questions.map(q => ({
                question_id: q.id,
                selected_choice: null,
                confidence_level: null
            })));
        }
    }, [questions]);

    const currentAnswer = answers[currentIndex] || { selected_choice: null, confidence_level: null };
    const selectedChoice = currentAnswer.selected_choice;
    const confidenceLevel = currentAnswer.confidence_level;

    const handleChoiceSelect = (choiceIdx) => {
        if (answers.length === 0) return;
        const newAnswers = [...answers];
        newAnswers[currentIndex] = { ...newAnswers[currentIndex], selected_choice: choiceIdx };
        setAnswers(newAnswers);
    };

    const handleConfidenceSelect = (confValue) => {
        if (answers.length === 0) return;
        const newAnswers = [...answers];
        newAnswers[currentIndex] = { ...newAnswers[currentIndex], confidence_level: confValue };
        setAnswers(newAnswers);
    };

    const handlePrev = () => {
        if (currentIndex > 0) setCurrentIndex(currentIndex - 1);
    };

    const handleNextOrSubmit = () => {
        if (currentIndex < questions.length - 1) {
            setCurrentIndex(currentIndex + 1);
        } else {
            const isAllFilled = answers.every(a => a.selected_choice !== null && a.confidence_level !== null);
            if (!isAllFilled) {
                alert(language === 'ko' ? '모든 문항의 정답과 확신도를 선택해주세요!' : 'Please complete all questions before submitting!');
                return;
            }
            submitQuiz(answers);
        }
    };

    const submitQuiz = async (finalAnswers) => {
        setIsSubmitting(true);
        try {
            const payload = {
                session_id: sessionId,
                user_id: userId,
                concept: concept,
                is_pre_test: !isPostTest,
                answers: finalAnswers
            };
            const response = await quizAPI.submitQuiz(payload);
            setResult(response.data);
        } catch (error) {
            console.error("Quiz submission failed", error);
            // Fallback: just proceed
            onComplete();
        } finally {
            setIsSubmitting(false);
        }
    };

    if (!questions || questions.length === 0) {
        return (
            <section className="quiz-container glass-panel fade-in" style={{ justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
                <div style={{ textAlign: 'center', color: 'var(--color-deep-navy)' }}>
                    <div className="spinner" style={{ margin: '0 auto 30px auto', width: '50px', height: '50px' }} />
                    <h2 style={{ fontSize: '1.8rem', marginBottom: '15px' }}>{language === 'ko' ? '퀴즈를 준비중입니다. 잠시만 기다려주세요.' : 'Preparing the quiz. Please wait a moment.'}</h2>
                    <p style={{ color: 'var(--color-text-secondary)', fontSize: '1.1rem', marginBottom: '30px', fontWeight: 'bold' }}>
                        {language === 'ko' ? '학습을 시작하기 전에 먼저 퀴즈를 응시해야 합니다.' : 'You must take the quiz before starting the lesson.'}
                    </p>
                    
                    <div style={{ display: 'flex', gap: '8px', justifyContent: 'center', marginTop: '20px' }}>
                        <div style={{ width: '12px', height: '12px', backgroundColor: 'var(--color-expert-academic)', borderRadius: '50%', animation: 'bounce 1.4s infinite ease-in-out both' }}></div>
                        <div style={{ width: '12px', height: '12px', backgroundColor: 'var(--color-expert-academic)', borderRadius: '50%', animation: 'bounce 1.4s infinite ease-in-out both', animationDelay: '0.2s' }}></div>
                        <div style={{ width: '12px', height: '12px', backgroundColor: 'var(--color-expert-academic)', borderRadius: '50%', animation: 'bounce 1.4s infinite ease-in-out both', animationDelay: '0.4s' }}></div>
                    </div>
                </div>
            </section>
        );
    }
    
    if (isPostTest && !startedPostQuiz && !result) {
        return (
            <section className="quiz-container glass-panel fade-in" style={{ justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
                <div style={{ textAlign: 'center', color: 'var(--color-deep-navy)' }}>
                    <h2 style={{ fontSize: '2rem', fontWeight: '800', marginBottom: '15px' }}>
                        {language === 'ko' ? '수고하셨습니다!' : 'Great Job!'}
                    </h2>
                    <p style={{ fontSize: '1.2rem', color: 'var(--color-text-secondary)', marginBottom: '30px' }}>
                        {language === 'ko' 
                            ? '마지막으로 다시 한번 퀴즈를 풀며 학습 성장을 체크해봅시다.' 
                            : 'Let us check your learning growth by taking the quiz one last time.'}
                    </p>
                    <button className="start-chat-btn" onClick={() => setStartedPostQuiz(true)}>
                        {language === 'ko' ? '사후 테스트 시작하기' : 'Start Post-test'} <ArrowRight size={18} />
                    </button>
                </div>
            </section>
        );
    }
    
    if (result) {
        if (isPostTest && result.details) {
            return (
                <section className="quiz-container glass-panel fade-in" style={{ maxWidth: '1400px', width: '95%', margin: '10px auto', padding: '0' }}>
                    <div className="quiz-result-card" style={{ padding: '20px 30px' }}>
                        {!showCommentary ? (
                            <div className="score-summary-container" style={{ padding: '0px 10px 10px 10px' }}>
                                <h2 style={{ fontSize: '2.5rem', fontWeight: '800', marginBottom: '25px', marginTop: '-15px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '12px' }}>
                                    <Award size={44} color="#f59e0b" />
                                    {language === 'ko' ? '사후 테스트 결과' : 'Post-test Results'}
                                </h2>
                                
                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '40px', alignItems: 'flex-start' }}>
                                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', background: 'rgba(241, 245, 249, 0.5)', padding: '40px 30px', borderRadius: '24px' }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '15px', marginBottom: '30px' }}>
                                            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                                                <span style={{ fontSize: '1.2rem', color: 'var(--color-text-secondary)', fontWeight: '600', marginBottom: '8px' }}>
                                                    {language === 'ko' ? '내 점수' : 'My Score'}
                                                </span>
                                                <span style={{ fontSize: '4rem', fontWeight: '800', color: 'var(--color-expert-academic)', lineHeight: '1' }}>
                                                    {result.score}
                                                </span>
                                            </div>
                                            <span style={{ fontSize: '3rem', color: '#cbd5e1', fontWeight: '300', margin: '0 10px' }}>/</span>
                                            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                                                <span style={{ fontSize: '1.2rem', color: 'var(--color-text-secondary)', fontWeight: '600', marginBottom: '8px' }}>
                                                    {language === 'ko' ? '총점' : 'Total'}
                                                </span>
                                                <span style={{ fontSize: '4rem', fontWeight: '800', color: 'var(--color-deep-navy)', lineHeight: '1' }}>
                                                    {result.max_score}
                                                </span>
                                            </div>
                                        </div>
                                        
                                        <div style={{ background: 'white', padding: '25px', borderRadius: '16px', boxShadow: '0 4px 15px rgba(0,0,0,0.03)', width: '100%' }}>
                                            <h4 style={{ color: 'var(--color-deep-navy)', marginBottom: '12px', fontSize: '1.1rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
                                                <Brain size={18} color="#8b5cf6" />
                                                {language === 'ko' ? 'CBM 채점 방식 적용' : 'CBM Scoring Applied'}
                                            </h4>
                                            <p style={{ fontSize: '0.95rem', color: 'var(--color-text-secondary)', lineHeight: '1.6', margin: 0, wordBreak: 'keep-all' }}>
                                                {language === 'ko' 
                                                    ? '단순한 정/오답을 넘어, 문제를 풀 때 표시한 확신도에 따라 점수가 차등 부여되었습니다. 높은 확신도로 오답을 선택할 경우 감점 폭이 커져 스스로의 메타인지(객관적 지식 수준)를 성찰할 수 있습니다.'
                                                    : 'Scores are weighted by your reported certainty level. Incorrect answers with high certainty carry heavier penalties to encourage accurate self-assessment.'}
                                            </p>
                                        </div>
                                    </div>

                                    <div style={{ display: 'flex', flexDirection: 'column' }}>
                                        <h3 style={{ marginBottom: '20px', color: 'var(--color-deep-navy)', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '1.4rem' }}>
                                            <Target size={24} color="#3b82f6" />
                                            {language === 'ko' ? '문항별 점수 상세 내역' : 'Score Details by Question'}
                                        </h3>
                                        <div style={{ width: '100%', backgroundColor: 'white', borderRadius: '16px', padding: '15px 25px', boxShadow: '0 4px 15px rgba(0,0,0,0.03)' }}>
                                            {result.details.map((detail, idx) => {
                                                const userAnswer = answers.find(a => a.question_id === detail.question_id);
                                                const isCorrect = userAnswer?.selected_choice === detail.correct_option;
                                                const earnedScore = detail.earned_score || 0;
                                                
                                                return (
                                                    <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px 0', borderBottom: '1px solid #e2e8f0' }}>
                                                        <span style={{ fontWeight: '600', fontSize: '1.15rem', color: 'var(--color-text-primary)' }}>
                                                            Q{idx + 1}. <span style={{ color: isCorrect ? '#10b981' : '#ef4444', marginLeft: '6px' }}>{isCorrect ? (language === 'ko' ? '정답' : 'Correct') : (language === 'ko' ? '오답' : 'Incorrect')}</span>
                                                        </span>
                                                        <span style={{ fontWeight: '800', fontSize: '1.3rem', color: earnedScore > 0 ? '#10b981' : (earnedScore < 0 ? '#ef4444' : '#64748b') }}>
                                                            {earnedScore > 0 ? `+${earnedScore}` : earnedScore} {language === 'ko' ? '점' : 'pts'}
                                                        </span>
                                                    </div>
                                                );
                                            })}
                                            <div style={{ marginTop: '20px' }}>
                                                <button className="start-chat-btn" onClick={() => setShowCommentary(true)} style={{ width: '100%', justifyContent: 'center', padding: '16px', fontSize: '1.1rem' }}>
                                                    {language === 'ko' ? '상세 해설 보기' : 'View Detailed Commentary'} <ArrowRight size={22} />
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <>
                                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginBottom: '20px' }}>
                                    <h2 style={{ fontSize: '2.2rem', fontWeight: '800', marginBottom: '15px', display: 'flex', alignItems: 'center', gap: '10px' }}>
                                        <Lightbulb size={36} color="#3b82f6" />
                                        {language === 'ko' ? '문제 해설' : 'Problem Commentary'}
                                    </h2>
                                </div>
                                <div className="review-list" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
                                    {result.details.slice(reviewPage * 2, reviewPage * 2 + 2).map((detail, idx) => {
                                        const actualIdx = reviewPage * 2 + idx;
                                        const question = questions.find(q => q.id === detail.question_id);
                                        const userAnswer = answers.find(a => a.question_id === detail.question_id);
                                        const isCorrect = userAnswer?.selected_choice === detail.correct_option;
                                        
                                        return (
                                            <div key={actualIdx} className={`review-item ${isCorrect ? 'correct' : 'incorrect'}`}>
                                                <div className="review-question-container" style={{ marginBottom: '15px' }}>
                                                    <p className="review-question" style={{ margin: 0, marginBottom: '8px' }}>
                                                        <span className="review-q-num" style={{ marginRight: '8px', color: 'var(--color-expert-academic)' }}>Q{actualIdx + 1}.</span>
                                                        {question?.question}
                                                    </p>
                                                    <div style={{ display: 'flex' }}>
                                                        <span className={`review-badge ${isCorrect ? 'badge-correct' : 'badge-incorrect'}`}>
                                                            {isCorrect ? (language === 'ko' ? '정답' : 'Correct') : (language === 'ko' ? '오답' : 'Incorrect')}
                                                        </span>
                                                    </div>
                                                </div>
                                                <div className="review-answers" style={{ marginBottom: '10px', padding: '10px' }}>
                                                    <div className="review-answer-row">
                                                        <span className="review-label">{language === 'ko' ? '내 답변:' : 'Your Answer:'}</span>
                                                        <span className={`review-choice ${isCorrect ? 'text-correct' : 'text-incorrect'}`}>
                                                            {question?.choices[userAnswer?.selected_choice - 1]}
                                                        </span>
                                                    </div>
                                                    {!isCorrect && (
                                                        <div className="review-answer-row">
                                                            <span className="review-label">{language === 'ko' ? '정답:' : 'Correct Answer:'}</span>
                                                            <span className="review-choice text-correct">
                                                                {question?.choices[detail.correct_option - 1]}
                                                            </span>
                                                        </div>
                                                    )}
                                                </div>
                                                <div className="review-commentary" style={{ padding: '12px' }}>
                                                    <div className="commentary-title" style={{ marginBottom: '5px' }}>
                                                        <Lightbulb size={16} /> {language === 'ko' ? '해설' : 'Commentary'}
                                                    </div>
                                                    <p>{detail.commentary}</p>
                                                </div>
                                            </div>
                                        );
                                    })}
                                    
                                    {(reviewPage * 2 + 1 >= result.details.length) && (
                                        <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', padding: '20px', background: 'rgba(255,255,255,0.5)', borderRadius: '12px' }}>
                                            <h3 style={{ marginBottom: '20px', color: 'var(--color-deep-navy)' }}>
                                                {language === 'ko' ? '모든 해설을 확인하셨나요?' : 'Finished reviewing?'}
                                            </h3>
                                            <button className="start-chat-btn" onClick={onComplete} style={{ width: '100%', justifyContent: 'center' }}>
                                                {language === 'ko' ? '최종 리포트 보기' : 'View Final Report'} <ArrowRight size={18} />
                                            </button>
                                        </div>
                                    )}
                                </div>

                                <div className="quiz-nav-footer" style={{ position: 'fixed', bottom: '20px', right: '50px', zIndex: 1000, display: 'flex', gap: '15px' }}>
                                    {reviewPage > 0 && (
                                        <button 
                                            className="nav-btn prev-btn" 
                                            onClick={() => setReviewPage(Math.max(0, reviewPage - 1))} 
                                        >
                                            <ChevronLeft size={20} />
                                            {language === 'ko' ? '이전 해설' : 'Prev'}
                                        </button>
                                    )}
                                    {reviewPage < Math.ceil(result.details.length / 2) - 1 && (
                                        <button 
                                            className="nav-btn next-btn" 
                                            onClick={() => setReviewPage(Math.min(Math.ceil(result.details.length / 2) - 1, reviewPage + 1))}
                                        >
                                            {language === 'ko' ? '다음 해설' : 'Next'} <ChevronRight size={20} />
                                        </button>
                                    )}
                                </div>
                            </>
                        )}
                    </div>
                </section>
            );
        }

        return (
            <section className="quiz-container glass-panel fade-in">
                <div className="quiz-result-card">
                    <div className="result-icon-wrapper">
                        <Award size={48} color="#f59e0b" />
                    </div>
                    <h2>{language === 'ko' ? '사전 테스트 완료!' : 'Pre-test Complete!'}</h2>
                    <p className="result-message" style={{ marginTop: '20px' }}>
                        {language === 'ko' 
                            ? '이제 AI 튜터와 함께 본격적인 학습을 시작해볼까요?' 
                            : 'Shall we start learning with the AI tutor now?'}
                    </p>
                    <button className="start-chat-btn" onClick={onComplete}>
                        {language === 'ko' ? '학습 시작하기' : 'Start Learning'} <ArrowRight size={18} />
                    </button>
                </div>
            </section>
        );
    }

    const question = questions[currentIndex];

    return (
        <section className="quiz-container glass-panel fade-in">
            <div className="quiz-header">
                <div className="quiz-progress-bar">
                    <div 
                        className="quiz-progress-fill" 
                        style={{ width: `${((currentIndex) / questions.length) * 100}%` }}
                    />
                </div>
                <div className="quiz-meta">
                    <span className="quiz-badge">{isPostTest ? 'Post-test' : 'Pre-test'}</span>
                    <span className="quiz-counter">Q {currentIndex + 1} / {questions.length}</span>
                </div>
                <h2 className="quiz-question-text">{question.question}</h2>
            </div>

            <div className="quiz-body">
                <div className="quiz-choices">
                    {question.choices.map((choice, idx) => (
                        <div 
                            key={idx}
                            className={`quiz-choice-item ${selectedChoice === idx + 1 ? 'selected' : ''}`}
                            onClick={() => handleChoiceSelect(idx + 1)}
                        >
                            <div className="choice-marker">{idx + 1}</div>
                            <div className="choice-text">{choice}</div>
                        </div>
                    ))}
                </div>

                <div className={`confidence-section ${selectedChoice === null ? 'disabled-section' : ''}`}>
                    <h3>{language === 'ko' ? '이 답에 얼마나 확신하시나요?' : 'How confident are you?'}</h3>
                    <div className="confidence-options">
                        <button 
                            className={`conf-btn conf-low ${confidenceLevel === 1 ? 'active' : ''}`}
                            disabled={selectedChoice === null}
                            onClick={() => handleConfidenceSelect(1)}
                        >
                            <ShieldAlert size={18} />
                            {language === 'ko' ? '확신 안 됨 (1)' : 'Not Sure (1)'}
                        </button>
                        <button 
                            className={`conf-btn conf-mid ${confidenceLevel === 2 ? 'active' : ''}`}
                            disabled={selectedChoice === null}
                            onClick={() => handleConfidenceSelect(2)}
                        >
                            <Target size={18} />
                            {language === 'ko' ? '보통 (2)' : 'Somewhat (2)'}
                        </button>
                        <button 
                            className={`conf-btn conf-high ${confidenceLevel === 3 ? 'active' : ''}`}
                            disabled={selectedChoice === null}
                            onClick={() => handleConfidenceSelect(3)}
                        >
                            <CheckCircle2 size={18} />
                            {language === 'ko' ? '확신함 (3)' : 'Confident (3)'}
                        </button>
                    </div>
                </div>
            </div>

            <div className="quiz-nav-footer">
                <button 
                    className="nav-btn prev-btn" 
                    onClick={handlePrev} 
                    disabled={currentIndex === 0}
                >
                    <ChevronLeft size={20} />
                    {language === 'ko' ? '이전' : 'Prev'}
                </button>
                <button 
                    className="nav-btn next-btn" 
                    onClick={handleNextOrSubmit}
                    disabled={selectedChoice === null || confidenceLevel === null}
                >
                    {currentIndex < questions.length - 1 ? (
                        <>{language === 'ko' ? '다음' : 'Next'} <ChevronRight size={20} /></>
                    ) : (
                        <>{language === 'ko' ? '제출하기' : 'Submit'} <CheckCircle2 size={20} /></>
                    )}
                </button>
            </div>

            {isSubmitting && (
                <div style={{ textAlign: 'center', marginTop: '20px' }}>
                    <div className="spinner" style={{ margin: '0 auto' }} />
                </div>
            )}
        </section>
    );
};

export default QuizScreen;
