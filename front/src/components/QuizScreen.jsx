import React, { useState } from 'react';
import { ArrowRight, CheckCircle2, ShieldAlert, Target, Award, Brain } from 'lucide-react';
import { quizAPI } from '../api/services';
import { t } from '../locales';
import './QuizScreen.css';

const QuizScreen = ({ questions, sessionId, concept, userId, language, onComplete }) => {
    const [currentIndex, setCurrentIndex] = useState(0);
    const [answers, setAnswers] = useState([]);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [result, setResult] = useState(null);

    // Current question state
    const [selectedChoice, setSelectedChoice] = useState(null);
    const [confidenceLevel, setConfidenceLevel] = useState(null);

    const handleNextWithConf = (confValue) => {
        if (selectedChoice === null || confValue === null) return;

        const newAnswer = {
            question_id: questions[currentIndex].id,
            selected_choice: selectedChoice,
            confidence_level: confValue
        };

        const updatedAnswers = [...answers, newAnswer];
        
        if (currentIndex < questions.length - 1) {
            setAnswers(updatedAnswers);
            setCurrentIndex(currentIndex + 1);
            setSelectedChoice(null);
            setConfidenceLevel(null);
        } else {
            // Submit quiz
            setAnswers(updatedAnswers);
            submitQuiz(updatedAnswers);
        }
    };

    const submitQuiz = async (finalAnswers) => {
        setIsSubmitting(true);
        try {
            const payload = {
                session_id: sessionId,
                user_id: userId,
                concept: concept,
                is_pre_test: true, // Always pre-test when before chat
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

    if (result) {
        return (
            <section className="quiz-container glass-panel fade-in">
                <div className="quiz-result-card">
                    <div className="result-icon-wrapper">
                        <Award size={48} color="#f59e0b" />
                    </div>
                    <h2>{language === 'ko' ? '사전 테스트 완료!' : 'Pre-test Complete!'}</h2>
                    <div className="score-display">
                        <span className="score-value">{result.score}</span>
                        <span className="score-max">/ {result.max_score}</span>
                    </div>
                    <p className="result-message">
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
                    <span className="quiz-badge">Pre-test</span>
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
                            onClick={() => setSelectedChoice(idx + 1)}
                        >
                            <div className="choice-marker">{idx + 1}</div>
                            <div className="choice-text">{choice}</div>
                        </div>
                    ))}
                </div>

                {selectedChoice !== null && (
                    <div className="confidence-section fade-in">
                        <h3>{language === 'ko' ? '이 답에 얼마나 확신하시나요?' : 'How confident are you?'}</h3>
                        <div className="confidence-options">
                            <button 
                                className={`conf-btn conf-low ${confidenceLevel === 1 ? 'active' : ''}`}
                                onClick={() => {
                                    setConfidenceLevel(1);
                                    setTimeout(() => handleNextWithConf(1), 300);
                                }}
                            >
                                <ShieldAlert size={18} />
                                {language === 'ko' ? '확신 안 됨 (1)' : 'Not Sure (1)'}
                            </button>
                            <button 
                                className={`conf-btn conf-mid ${confidenceLevel === 2 ? 'active' : ''}`}
                                onClick={() => {
                                    setConfidenceLevel(2);
                                    setTimeout(() => handleNextWithConf(2), 300);
                                }}
                            >
                                <Target size={18} />
                                {language === 'ko' ? '보통 (2)' : 'Somewhat (2)'}
                            </button>
                            <button 
                                className={`conf-btn conf-high ${confidenceLevel === 3 ? 'active' : ''}`}
                                onClick={() => {
                                    setConfidenceLevel(3);
                                    setTimeout(() => handleNextWithConf(3), 300);
                                }}
                            >
                                <CheckCircle2 size={18} />
                                {language === 'ko' ? '확신함 (3)' : 'Confident (3)'}
                            </button>
                        </div>
                    </div>
                )}
            </div>

            <div className="quiz-footer">
                <button 
                    className="quiz-next-btn"
                    disabled={selectedChoice === null || confidenceLevel === null || isSubmitting}
                    onClick={() => handleNextWithConf(confidenceLevel)}
                    style={{ visibility: isSubmitting || currentIndex >= questions.length - 1 ? 'visible' : 'hidden' }}
                >
                    {isSubmitting ? (
                        <div className="spinner" />
                    ) : (
                        <>{language === 'ko' ? '결과 확인' : 'Submit Quiz'} <CheckCircle2 size={18} /></>
                    )}
                </button>
            </div>
        </section>
    );
};

export default QuizScreen;
