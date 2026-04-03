import React, { useState } from 'react';
import { studyAPI } from '../api/services';

function ChatInterface({ concept, sessionId }) {
    const [answer, setAnswer] = useState("");
    const [feedback, setFeedback] = useState(null);

    const handleSubmit = async () => {
        try {
            const response = await studyAPI.sendChat({
                session_id: sessionId,
                concept: concept,
                user_answer: answer
            });

            const data = response.data;
            setFeedback(data);

            // 💡 백엔드 지침에 따른 스캐폴딩 분기 처리
            if (data.moderator_decision.status === "scaffold") {
                const plan = data.moderator_decision.scaffolding_plan;

                if (plan.step === "Sub-concept Nudge") {
                    alert(`힌트: ${plan.message}`); // 화면에 힌트 메시지 노출
                } else if (plan.step === "Concept Dictionary Link") {
                    // 사전 링크와 정의 노출 (Level 1)
                    console.log("사전 확인:", plan.definition, plan.dictionary_link);
                }
            }
        } catch (error) {
            console.error("통신 에러", error);
        }
    };

    return (
        <div>
            <input value={answer} onChange={(e) => setAnswer(e.target.value)} />
            <button onClick={handleSubmit}>답변 전송</button>
            {/* 여기에 feedback 데이터를 기반으로 UI 렌더링 */}
        </div>
    );
}
export default ChatInterface;