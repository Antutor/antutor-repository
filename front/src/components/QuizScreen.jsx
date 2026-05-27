/* eslint-disable */
import React, { useState, useEffect } from 'react';
import { ArrowRight, CheckCircle2, ShieldAlert, Target, Award, Brain, ChevronLeft, ChevronRight, Lightbulb, Calculator } from 'lucide-react';
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
    const [showInstructions, setShowInstructions] = useState(!isPostTest);
    const [isMinLoadingDone, setIsMinLoadingDone] = useState(isPostTest);

    useEffect(() => {
        if (isPostTest) return;
        const timer = setTimeout(() => {
            setIsMinLoadingDone(true);
        }, 5000);
        return () => clearTimeout(timer);
    }, [isPostTest]);

    const displayQuestions = React.useMemo(() => {
        if (!questions) return [];
        if (isPostTest && questions.length >= 5) {
            return [
                questions[4],
                questions[0],
                questions[3],
                questions[1],
                questions[2],
                ...questions.slice(5)
            ];
        }
        return questions;
    }, [questions, isPostTest]);

    // Initialize answers array when questions are loaded
    useEffect(() => {
        if (displayQuestions && displayQuestions.length > 0 && answers.length === 0) {
            setAnswers(displayQuestions.map(q => ({
                question_id: q.id,
                selected_choice: null,
                confidence_level: null
            })));
        }
    }, [displayQuestions]);

    const currentAnswer = answers[currentIndex] || { selected_choice: null, confidence_level: null };
    const selectedChoice = currentAnswer.selected_choice;
    const confidenceLevel = currentAnswer.confidence_level;

    const handleChoiceSelect = (choiceIdx) => {
        if (answers.length === 0) return;
        const newAnswers = [...answers];
        
        const isIdk = choiceIdx === displayQuestions[currentIndex].choices.length + 1;
        
        newAnswers[currentIndex] = { 
            ...newAnswers[currentIndex], 
            selected_choice: choiceIdx,
            confidence_level: isIdk ? 0 : (newAnswers[currentIndex].confidence_level === 0 ? null : newAnswers[currentIndex].confidence_level)
        };
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
        if (currentIndex < displayQuestions.length - 1) {
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
                is_pre_test: isPostTest === true ? false : true,
                answers: finalAnswers
            };
            const response = await quizAPI.submitQuiz(payload);
            setResult(response.data);
        } catch (error) {
            console.error("Quiz submission failed", error);
            alert(language === 'ko' ? '퀴즈 제출 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.' : 'An error occurred while submitting the quiz. Please try again.');
            // Do not call onComplete() here so it doesn't skip directly to the final report
        } finally {
            setIsSubmitting(false);
        }
    };

    if (!displayQuestions || displayQuestions.length === 0 || !isMinLoadingDone) {
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
    
    if (showInstructions) {
        return (
            <section className="quiz-container glass-panel fade-in" style={{ maxWidth: '800px', width: '95%', margin: '10px auto', padding: '15px' }}>
                <div style={{ padding: '25px 30px', borderRadius: '16px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '12px', marginBottom: '20px' }}>
                        <Calculator size={34} color="#8b5cf6" />
                        <h2 style={{ fontSize: '1.8rem', color: 'var(--color-deep-navy)', margin: 0 }}>
                            {language === 'ko' ? '테스트 방식 안내' : 'Test Method Guide'}
                        </h2>
                    </div>

                    <div style={{ fontSize: '1rem', color: 'var(--color-text-secondary)', lineHeight: '1.6', marginBottom: '20px', wordBreak: 'keep-all' }}>
                        {language === 'ko' ? (
                            <p style={{ margin: 0 }}>
                                <strong>확신도 기반 채점(CBM: Certainty-Based Marking)</strong>은 정답에 대해 '얼마나 확신하는지'를 함께 평가하는 방식입니다. 단순한 정/오답 평가를 넘어, 무작위 찍기를 방지하고 학생의 실제 이해도와 메타인지(객관적 지식 수준)를 측정하기 위해 고안되었습니다.
                            </p>
                        ) : (
                            <p style={{ margin: 0 }}>
                                <strong>Certainty-Based Marking (CBM)</strong> assesses how confident you are in your answer. It goes beyond simple correct/incorrect grading to prevent random guessing and measure actual understanding and metacognition.
                            </p>
                        )}
                        <ul style={{ marginTop: '12px', paddingLeft: '25px', display: 'flex', flexDirection: 'column', gap: '6px', marginBottom: 0 }}>
                            <li><strong>{language === 'ko' ? 'C=3 (확신함)' : 'C=3 (Confident)'}</strong>: {language === 'ko' ? '정답이면 +3점이지만, 틀리면 -6점입니다.' : '+3 if correct, -6 if incorrect.'}</li>
                            <li><strong>{language === 'ko' ? 'C=2 (보통)' : 'C=2 (Somewhat)'}</strong>: {language === 'ko' ? '정답이면 +2점, 틀리면 -2점입니다.' : '+2 if correct, -2 if incorrect.'}</li>
                            <li><strong>{language === 'ko' ? 'C=1 (확신 안 됨)' : 'C=1 (Not Sure)'}</strong>: {language === 'ko' ? '정답이면 +1점, 틀려도 감점이 없습니다 (0점).' : '+1 if correct, 0 if incorrect.'}</li>
                        </ul>
                    </div>
                    
                    <div style={{ overflowX: 'auto', display: 'flex', justifyContent: 'center', marginBottom: '20px' }}>
                        <table style={{ borderCollapse: 'collapse', fontSize: '0.9rem', textAlign: 'center', color: '#000', border: '1px solid #000', width: '100%', maxWidth: '600px' }}>
                            <thead>
                                <tr style={{ backgroundColor: '#f8fafc' }}>
                                    <th style={{ border: '1px solid #000', padding: '10px', fontWeight: '600', textAlign: 'left' }}>Confidence level :</th>
                                    <th style={{ border: '1px solid #000', padding: '10px', fontWeight: '600' }}>C=1<br/>(low)</th>
                                    <th style={{ border: '1px solid #000', padding: '10px', fontWeight: '600' }}>C=2<br/>(mid)</th>
                                    <th style={{ border: '1px solid #000', padding: '10px', fontWeight: '600' }}>C=3<br/>(high)</th>
                                    <th style={{ border: '1px solid #000', padding: '10px', fontWeight: '600' }}>No<br/>Reply</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td style={{ border: '1px solid #000', padding: '10px', textAlign: 'left', fontWeight: '500' }}>Mark if correct :</td>
                                    <td style={{ border: '1px solid #000', padding: '10px' }}>1</td>
                                    <td style={{ border: '1px solid #000', padding: '10px' }}>2</td>
                                    <td style={{ border: '1px solid #000', padding: '10px' }}>3</td>
                                    <td style={{ border: '1px solid #000', padding: '10px' }}>(0)</td>
                                </tr>
                                <tr>
                                    <td style={{ border: '1px solid #000', padding: '10px', textAlign: 'left', fontWeight: '500' }}>Penalty if wrong :</td>
                                    <td style={{ border: '1px solid #000', padding: '10px' }}>0</td>
                                    <td style={{ border: '1px solid #000', padding: '10px' }}>- 2</td>
                                    <td style={{ border: '1px solid #000', padding: '10px' }}>- 6</td>
                                    <td style={{ border: '1px solid #000', padding: '10px' }}>(0)</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>

                    <div style={{ backgroundColor: 'rgba(239, 68, 68, 0.08)', borderLeft: '4px solid #ef4444', padding: '12px 18px', borderRadius: '8px', marginBottom: '25px' }}>
                        <p style={{ margin: 0, color: '#b91c1c', fontWeight: '700', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '1rem' }}>
                            {language === 'ko' ? '🚨 참고사항: 문제에서 \'모르겠어요\' 선지를 체크하시면 확신도는 클릭하지 않고 넘어갑니다.' : '🚨 Note: If you select \'I don\'t know\', the confidence level check is bypassed.'}
                        </p>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'center' }}>
                        <button className="start-chat-btn" onClick={() => setShowInstructions(false)}>
                            {language === 'ko' ? '퀴즈 시작하기' : 'Start Quiz'} <ArrowRight size={18} />
                        </button>
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
                    <p style={{ fontSize: '1.2rem', color: 'var(--color-text-secondary)', marginBottom: '30px', lineHeight: '1.6' }}>
                        {language === 'ko' 
                            ? (
                                <>
                                    참여해주셔서 정말 감사합니다. 저희의 테스트 데이터 수집을 위하여 <strong>사후 테스트</strong>까지 꼭 진행해주세요.<br/>
                                    귀한 시간 내주셔서 진심으로 감사드립니다.
                                </>
                            )
                            : (
                                <>
                                    Thank you so much for participating. For our test data collection, please proceed with the <strong>post-test</strong>.<br/>
                                    We really appreciate your valuable time.
                                </>
                            )}
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
                                
                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', alignItems: 'flex-start' }}>
                                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', background: 'rgba(241, 245, 249, 0.5)', padding: '20px', borderRadius: '24px', gap: '15px' }}>
                                        <div style={{ display: 'flex', flexDirection: 'column', gap: '15px', width: '100%', background: 'white', padding: '25px', borderRadius: '16px', boxShadow: '0 4px 15px rgba(0,0,0,0.03)' }}>
                                            {/* 사전 테스트 점수 */}
                                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: '15px', borderBottom: '1px dashed #cbd5e1' }}>
                                                <span style={{ fontSize: '1.2rem', color: 'var(--color-text-secondary)', fontWeight: '600' }}>
                                                    {language === 'ko' ? '사전 테스트 점수' : 'Pre-test Score'}
                                                </span>
                                                <span style={{ fontSize: '1.4rem', fontWeight: '700', color: 'var(--color-text-secondary)' }}>
                                                    {result.pre_test_score !== undefined && result.pre_test_score !== null ? result.pre_test_score : 0} <span style={{ fontSize: '1rem', fontWeight: '500' }}>/ {result.max_score}{language === 'ko' ? '점' : 'pts'}</span>
                                                </span>
                                            </div>
                                            
                                            {/* 사후 테스트 점수 */}
                                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '5px' }}>
                                                <span style={{ fontSize: '1.4rem', color: 'var(--color-deep-navy)', fontWeight: '700' }}>
                                                    {language === 'ko' ? '사후 테스트 결과 점수' : 'Post-test Score'}
                                                </span>
                                                <span style={{ fontSize: '2rem', fontWeight: '800', color: 'var(--color-expert-academic)' }}>
                                                    {result.score} <span style={{ fontSize: '1.4rem', fontWeight: '600', color: '#94a3b8' }}>/ {result.max_score}{language === 'ko' ? '점' : 'pts'}</span>
                                                </span>
                                            </div>
                                        </div>
                                        
                                        <div style={{ width: '100%', textAlign: 'center', padding: '15px', borderRadius: '16px', background: result.score > (result.pre_test_score || 0) ? 'rgba(16, 185, 129, 0.1)' : 'rgba(245, 158, 11, 0.1)' }}>
                                            <span style={{ fontSize: '1.15rem', fontWeight: '700', color: result.score > (result.pre_test_score || 0) ? '#10b981' : '#d97706', lineHeight: '1.4', display: 'block' }}>
                                                {result.score > (result.pre_test_score || 0) 
                                                    ? (language === 'ko' ? '참 잘했어요! 경제 지식이 높아졌습니다!' : 'Great job! Your economic knowledge has improved!')
                                                    : (language === 'ko' ? '경제 학습을 더 하러 가볼까요?' : 'Shall we go study more economics?')}
                                            </span>
                                        </div>
                                        
                                        <div style={{ background: 'white', padding: '15px', borderRadius: '16px', boxShadow: '0 4px 15px rgba(0,0,0,0.03)', width: '100%' }}>
                                            <h4 style={{ color: 'var(--color-deep-navy)', marginBottom: '8px', fontSize: '1.05rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
                                                <Calculator size={18} color="#8b5cf6" />
                                                {language === 'ko' ? 'CBM 채점 방식' : 'CBM Scoring'}
                                            </h4>
                                            
                                            <div style={{ overflowX: 'auto', display: 'flex', justifyContent: 'center' }}>
                                                <table style={{ borderCollapse: 'collapse', fontSize: '0.8rem', textAlign: 'center', color: '#000', border: '1px solid #cbd5e1', width: '100%' }}>
                                                    <thead>
                                                        <tr style={{ backgroundColor: '#f8fafc' }}>
                                                            <th style={{ border: '1px solid #cbd5e1', padding: '6px', fontWeight: '600' }}>C=1 (low)</th>
                                                            <th style={{ border: '1px solid #cbd5e1', padding: '6px', fontWeight: '600' }}>C=2 (mid)</th>
                                                            <th style={{ border: '1px solid #cbd5e1', padding: '6px', fontWeight: '600' }}>C=3 (high)</th>
                                                        </tr>
                                                    </thead>
                                                    <tbody>
                                                        <tr>
                                                            <td style={{ border: '1px solid #cbd5e1', padding: '6px' }}>+1 / 0</td>
                                                            <td style={{ border: '1px solid #cbd5e1', padding: '6px' }}>+2 / -2</td>
                                                            <td style={{ border: '1px solid #cbd5e1', padding: '6px' }}>+3 / -6</td>
                                                        </tr>
                                                    </tbody>
                                                </table>
                                            </div>
                                            <p style={{ margin: '8px 0 0 0', fontSize: '0.8rem', color: 'var(--color-text-secondary)', textAlign: 'center' }}>
                                                * {language === 'ko' ? '정답 시 획득 점수 / 오답 시 감점' : 'Points earned / Penalty'}
                                            </p>
                                        </div>
                                    </div>

                                    <div style={{ display: 'flex', flexDirection: 'column' }}>
                                        <h3 style={{ marginBottom: '10px', color: 'var(--color-deep-navy)', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '1.3rem' }}>
                                            <Target size={22} color="#3b82f6" />
                                            {language === 'ko' ? '문항별 점수 상세 내역' : 'Score Details by Question'}
                                        </h3>
                                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px', marginBottom: '10px' }}>
                                            {/* 사전 테스트 상세 내역 */}
                                            <div style={{ width: '100%', backgroundColor: 'white', borderRadius: '16px', padding: '12px 15px', boxShadow: '0 4px 15px rgba(0,0,0,0.03)' }}>
                                                <h4 style={{ marginBottom: '10px', color: 'var(--color-text-secondary)', fontSize: '1.05rem', textAlign: 'center' }}>
                                                    {language === 'ko' ? '사전 테스트' : 'Pre-test'}
                                                </h4>
                                                {result.pre_test_details && result.pre_test_details.length > 0 ? result.pre_test_details.map((detail, idx) => {
                                                    const earnedScore = detail.earned_score || 0;
                                                    const isCorrect = earnedScore > 0;
                                                    
                                                    return (
                                                        <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 0', borderBottom: '1px solid #e2e8f0' }}>
                                                            <span style={{ fontWeight: '600', fontSize: '1.0rem', color: 'var(--color-text-primary)' }}>
                                                                Q{idx + 1}. <span style={{ color: isCorrect ? '#10b981' : '#ef4444', marginLeft: '6px' }}>{isCorrect ? (language === 'ko' ? '정답' : 'Correct') : (language === 'ko' ? '오답' : 'Incorrect')}</span>
                                                            </span>
                                                            <span style={{ fontWeight: '800', fontSize: '1.1rem', color: earnedScore > 0 ? '#10b981' : (earnedScore < 0 ? '#ef4444' : '#64748b') }}>
                                                                {earnedScore > 0 ? `+${earnedScore}` : earnedScore} {language === 'ko' ? '점' : 'pts'}
                                                            </span>
                                                        </div>
                                                    );
                                                }) : (
                                                    <div style={{ padding: '20px', textAlign: 'center', color: 'var(--color-text-secondary)' }}>
                                                        {language === 'ko' ? '기록 없음' : 'No records'}
                                                    </div>
                                                )}
                                            </div>
                                            
                                            {/* 사후 테스트 상세 내역 */}
                                            <div style={{ width: '100%', backgroundColor: 'white', borderRadius: '16px', padding: '12px 15px', boxShadow: '0 4px 15px rgba(0,0,0,0.03)' }}>
                                                <h4 style={{ marginBottom: '10px', color: 'var(--color-expert-academic)', fontSize: '1.05rem', textAlign: 'center' }}>
                                                    {language === 'ko' ? '사후 테스트' : 'Post-test'}
                                                </h4>
                                                {result.details.map((detail, idx) => {
                                                    const userAnswer = answers.find(a => a.question_id === detail.question_id);
                                                    const isCorrect = userAnswer?.selected_choice === detail.correct_option;
                                                    const earnedScore = detail.earned_score || 0;
                                                    
                                                    return (
                                                        <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 0', borderBottom: '1px solid #e2e8f0' }}>
                                                            <span style={{ fontWeight: '600', fontSize: '1.0rem', color: 'var(--color-text-primary)' }}>
                                                                Q{idx + 1}. <span style={{ color: isCorrect ? '#10b981' : '#ef4444', marginLeft: '6px' }}>{isCorrect ? (language === 'ko' ? '정답' : 'Correct') : (language === 'ko' ? '오답' : 'Incorrect')}</span>
                                                            </span>
                                                            <span style={{ fontWeight: '800', fontSize: '1.1rem', color: earnedScore > 0 ? '#10b981' : (earnedScore < 0 ? '#ef4444' : '#64748b') }}>
                                                                {earnedScore > 0 ? `+${earnedScore}` : earnedScore} {language === 'ko' ? '점' : 'pts'}
                                                            </span>
                                                        </div>
                                                    );
                                                })}
                                            </div>
                                        </div>

                                        <div style={{ width: '100%', backgroundColor: 'white', borderRadius: '16px', padding: '10px 15px', boxShadow: '0 4px 15px rgba(0,0,0,0.03)' }}>
                                            <button className="start-chat-btn" onClick={() => setShowCommentary(true)} style={{ width: '100%', justifyContent: 'center', padding: '12px', fontSize: '1.05rem' }}>
                                                {language === 'ko' ? '상세 해설 보기' : 'View Detailed Commentary'} <ArrowRight size={22} />
                                            </button>
                                            <p style={{ textAlign: 'center', marginTop: '8px', fontSize: '0.85rem', color: 'var(--color-text-secondary)', fontWeight: '500' }}>
                                                {language === 'ko' ? '💡 최종 평가 지표는 상세 해설을 모두 확인한 후 나타납니다.' : '💡 The final evaluation metrics will appear after reviewing all detailed commentaries.'}
                                            </p>
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
                                        const question = displayQuestions.find(q => q.id === detail.question_id);
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
                    <h2>{language === 'ko' ? (isPostTest ? '사후 테스트 완료!' : '사전 테스트 완료!') : (isPostTest ? 'Post-test Complete!' : 'Pre-test Complete!')}</h2>
                    <p className="result-message" style={{ marginTop: '20px' }}>
                        {language === 'ko' 
                            ? (isPostTest ? '최종 리포트를 확인해볼까요?' : '이제 AI 튜터와 함께 본격적인 학습을 시작해볼까요?') 
                            : (isPostTest ? 'Shall we view the final report?' : 'Shall we start learning with the AI tutor now?')}
                    </p>
                    <button className="start-chat-btn" onClick={onComplete}>
                        {language === 'ko' ? (isPostTest ? '결과 보기' : '학습 시작하기') : (isPostTest ? 'View Results' : 'Start Learning')} <ArrowRight size={18} />
                    </button>
                    {!isPostTest && (
                        <p style={{ margin: '35px auto 0', fontSize: '0.9rem', color: '#ef4444', fontWeight: '600', width: '100%', textAlign: 'center', lineHeight: '1.6', wordBreak: 'keep-all' }}>
                            {language === 'ko' 
                                ? (
                                    <>
                                        🚨 안내사항: 학습이 끝나면 반드시 '학습 종료' 버튼을 눌러 사후 테스트까지 진행해 주시길 바랍니다.<br/>
                                        사후 테스트도 사전 테스트와 동일하게 진행됩니다.
                                    </>
                                ) 
                                : (
                                    <>
                                        🚨 Notice: After finishing the learning, please make sure to click the 'End Learning' button to proceed with the post-test.<br/>
                                        The post-test will be conducted in the same manner as the pre-test.
                                    </>
                                )}
                        </p>
                    )}
                </div>
            </section>
        );
    }

    const question = displayQuestions[currentIndex];
    const displayChoices = question ? [...question.choices, language === 'ko' ? '모르겠어요' : "I don't know"] : [];
    const isIdkSelected = selectedChoice === displayChoices.length;
    const isConfidenceDisabled = selectedChoice === null || isIdkSelected;

    return (
        <section className="quiz-container glass-panel fade-in">
            <div className="quiz-header">
                <div className="quiz-progress-bar">
                    <div 
                        className="quiz-progress-fill" 
                        style={{ width: `${((currentIndex) / displayQuestions.length) * 100}%` }}
                    />
                </div>
                <div className="quiz-meta">
                    <span className="quiz-badge">{isPostTest ? 'Post-test' : 'Pre-test'}</span>
                    <span className="quiz-counter">Q {currentIndex + 1} / {displayQuestions.length}</span>
                </div>
                <h2 className="quiz-question-text">{question.question}</h2>
            </div>

            <div className="quiz-body">
                <div className="quiz-choices">
                    {displayChoices.map((choice, idx) => (
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

                <div className="quiz-right-panel" style={{ flex: '0 0 280px', paddingLeft: '30px', borderLeft: '1px dashed rgba(0,0,0,0.1)', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                    <div className={`confidence-section ${isConfidenceDisabled ? 'disabled-section' : ''}`} style={{ flex: 'none', paddingLeft: 0, borderLeft: 'none' }}>
                        <h3>{language === 'ko' ? '이 답에 얼마나 확신하시나요?' : 'How confident are you?'}</h3>
                        <div className="confidence-options">
                            <button 
                                className={`conf-btn conf-low ${confidenceLevel === 1 ? 'active' : ''}`}
                                disabled={isConfidenceDisabled}
                                onClick={() => handleConfidenceSelect(1)}
                            >
                                <ShieldAlert size={18} />
                                {language === 'ko' ? '확신 안 됨 (1)' : 'Not Sure (1)'}
                            </button>
                            <button 
                                className={`conf-btn conf-mid ${confidenceLevel === 2 ? 'active' : ''}`}
                                disabled={isConfidenceDisabled}
                                onClick={() => handleConfidenceSelect(2)}
                            >
                                <Target size={18} />
                                {language === 'ko' ? '보통 (2)' : 'Somewhat (2)'}
                            </button>
                            <button 
                                className={`conf-btn conf-high ${confidenceLevel === 3 ? 'active' : ''}`}
                                disabled={isConfidenceDisabled}
                                onClick={() => handleConfidenceSelect(3)}
                            >
                                <CheckCircle2 size={18} />
                                {language === 'ko' ? '확신함 (3)' : 'Confident (3)'}
                            </button>
                        </div>
                    </div>
                    
                    <div className="quiz-nav-footer" style={{ justifyContent: 'center', marginTop: '40px', borderTop: 'none', paddingTop: 0, gap: '10px' }}>
                        <button 
                            className="nav-btn prev-btn" 
                            onClick={handlePrev} 
                            disabled={currentIndex === 0}
                            style={{ padding: '10px 18px', fontSize: '1rem' }}
                        >
                            <ChevronLeft size={18} />
                            {language === 'ko' ? '이전' : 'Prev'}
                        </button>
                        <button 
                            className="nav-btn next-btn" 
                            onClick={handleNextOrSubmit}
                            disabled={selectedChoice === null || confidenceLevel === null || isSubmitting}
                            style={{ padding: '10px 18px', fontSize: '1rem' }}
                        >
                            {currentIndex < displayQuestions.length - 1 ? (
                                <>{language === 'ko' ? '다음' : 'Next'} <ChevronRight size={18} /></>
                            ) : (
                                <>{language === 'ko' ? '제출하기' : 'Submit'} <CheckCircle2 size={18} /></>
                            )}
                        </button>
                    </div>
                </div>
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
