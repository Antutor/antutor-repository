import React from 'react';
import { Play } from 'lucide-react';
import './ChatTutorialOverlay.css';
// eslint-disable-next-line no-unused-vars
import { t } from '../locales';

const ChatTutorialOverlay = ({ onClose, language }) => {
    return (
        <div className="chat-tutorial-overlay fade-in">
            {/* Left Sidebar Tooltips */}
            <div className="tutorial-tooltip left-tooltip">
                <div className="tooltip-content">
                    <h4>{language === 'ko' ? '학습 경로' : 'Learning Path'}</h4>
                    <ul>
                        <li><strong>{language === 'ko' ? '꺾은선 그래프:' : 'Line Graph:'}</strong>{language === 'ko' ? '학습을 진행하면서 누적된 점수가 턴마다 꺾은선 그래프에 반영됩니다. 턴 횟수가 증가하면서 점수도 누적되므로 최대 점수는 100점을 초과할 수 있습니다.' : 'Your accumulated score updates in real-time on the line graph as you progress. Since the score accumulates with each turn, the maximum score can exceed 100.'}</li>
                        <li><strong>{language === 'ko' ? '턴 횟수:' : 'Turn Count:'}</strong>{language === 'ko' ? '답변을 하나 보낼 때마다 턴 수가 1씩 증가합니다. (단, 힌트는 턴 횟수에서 제외됩니다.)' : 'Increases by 1 each time you send an answer. (Hints are excluded from the turn count.)'}</li>
                        <li><strong>{language === 'ko' ? '역량 평가 그래프:' : 'Competency Radar:'}</strong>{language === 'ko' ? '학습을 진행할 때 삼각형 그래프에 해당 턴에 대한 점수가 실시간으로 바뀌게 됩니다. 최대 점수는 100점입니다.' : 'The triangle graph updates your competency levels in real-time each turn. The maximum score is 100.'}</li>
                    </ul>
                </div>
                <div className="arrow left-arrow"></div>
            </div>

            {/* Right Sidebar Tooltips */}
            <div className="tutorial-tooltip right-tooltip">
                <div className="tooltip-content">
                    <h4>{language === 'ko' ? '전문가 다중 관점 분석' : 'Expert Multi-Perspective Analysis'}</h4>
                    <p>{language === 'ko' ? '학습을 진행할 때 턴마다 실시간으로 3명의 멀티 에이전트 전문가가 각자의 관점(학술, 시장, 거시)에서 사용자의 답변을 분석하고 피드백을 제공합니다.' : 'Each turn, 3 expert agents analyze your answers in real-time from their unique perspectives (Academic, Market, Macro) and provide feedback.'}</p>
                </div>
                <div className="arrow right-arrow"></div>
            </div>

            {/* Center Action Button */}
            <div className="tutorial-action-center">
                <button className="start-tutorial-btn" onClick={onClose}>
                    <Play fill="currentColor" size={20} />
                    {language === 'ko' ? '학습 채팅 시작하기' : 'Start Learning Chat'}
                </button>
            </div>
        </div>
    );
};

export default ChatTutorialOverlay;
