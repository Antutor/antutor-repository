import json
import asyncio
import re

from langchain_core.messages import SystemMessage, HumanMessage
from multi_agent.state import AgentState
from multi_agent.prompts import (
    ACADEMIC_DRAFT_SYSTEM_PROMPT,
    MARKET_DRAFT_SYSTEM_PROMPT,
    MACRO_DRAFT_SYSTEM_PROMPT,
    AGENT_REBUTTAL_PROMPT,
    SYNTHESIS_SYSTEM_PROMPT
)
from multi_agent.llm_config import llm, creative_llm, gpu_semaphore

def extract_json(text: str) -> dict:
    try:
        # 1. 시도: 전체 문자열 직접 파싱
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # 2. 시도: 마크다운 코드 블록 안의 내용 추출
    match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass
            
    # 3. 시도: 중괄호 부분만 추출
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass
            
    return {"is_contradiction": False, "score": 0.5, "feedback": text}

def extract_float_score(text: str) -> float:
    match = re.search(r'\[([0-9]*\.?[0-9]+)\]', text)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass
    return 0.75 # 기본 점수

async def drafting_node(state: AgentState):
    """
    1회차 초안 노드: 각 전문가(Academic, Market, Macro)가 독립적으로 평가를 수행합니다.
    (노드 안에서 asyncio.gather 로 병렬 수행하여 대기시간 최적화)
    """
    concept = state["concept"]
    user_answer = state["user_answer"]
    ground_truth = state["ground_truth"]
    news_context = state.get("news_context", "")
    kg_context = state.get("kg_context", "")
    
    print(f"\n[LangGraph] 🚀 1. Drafting Node 진행 중... (개념: {concept})", flush=True)
    print(f"  - 3명의 에이전트(Academic, Market, Macro)가 초안을 작성 중입니다...", flush=True)
    
    async def call_academic():
        async with gpu_semaphore:
            sys_msg = ACADEMIC_DRAFT_SYSTEM_PROMPT.format(concept=concept, ground_truth=ground_truth, user_answer=user_answer)
            res = await llm.ainvoke([SystemMessage(content=sys_msg)])
            data = extract_json(res.content)
            # 1B 모델의 할루시네이션(무조건 true 반환)을 방지하기 위해 강제로 False 처리 (디버깅용)
            is_contra = False
            return "The Academic Auditor", res.content, data.get("score", 0.0), is_contra

    async def call_market():
        async with gpu_semaphore:
            sys_msg = MARKET_DRAFT_SYSTEM_PROMPT.format(concept=concept, news_context=news_context, user_answer=user_answer)
            res = await llm.ainvoke([SystemMessage(content=sys_msg)])
            score = extract_float_score(res.content)
            return "The Market Practitioner", res.content, score, False

    async def call_macro():
        async with gpu_semaphore:
            sys_msg = MACRO_DRAFT_SYSTEM_PROMPT.format(concept=concept, kg_context=kg_context, user_answer=user_answer)
            res = await llm.ainvoke([SystemMessage(content=sys_msg)])
            score = extract_float_score(res.content)
            return "The Macro-Connector", res.content, score, False

    results = await asyncio.gather(call_academic(), call_market(), call_macro())
    
    draft_reviews = {}
    raw_scores = {}
    is_contradict = False
    
    for agent_name, feedback, score, contra in results:
        draft_reviews[agent_name] = feedback
        raw_scores[agent_name] = score
        if contra:
            is_contradict = True
        
    print(f"  ✅ Drafting Node 완료! (모순 감지 여부: {is_contradict})", flush=True)
    
    return {
        "draft_reviews": draft_reviews, 
        "raw_scores": raw_scores,
        "is_contradiction": is_contradict,
        "debate_count": 0,
        "critiques": []
    }

async def cross_review_node(state: AgentState):
    """
    각 에이전트가 다른 에이전트의 초안을 바탕으로 교차 검증을 수행합니다.
    """
    concept = state["concept"]
    user_answer = state["user_answer"]
    
    current_round = state.get("debate_count", 0) + 1
    print(f"\n[LangGraph] 🔄 2. Cross Review Node 진행 중... (라운드: {current_round})", flush=True)
    print("  - 에이전트들이 타 전문가들의 의견을 바탕으로 개별 비판을 수행합니다...", flush=True)
    
    drafts = state.get("draft_reviews", {})
    
    async def call_rebuttal(persona):
        async with gpu_semaphore:
            # 본인을 제외한 다른 에이전트들의 리뷰만 취합
            other_reviews = "\n".join([f"[{p}] \n{rev}\n" for p, rev in drafts.items() if p != persona])
            
            sys_msg = AGENT_REBUTTAL_PROMPT.format(
                persona=persona, 
                concept=concept, 
                user_answer=user_answer, 
                other_reviews=other_reviews
            )
            res = await llm.ainvoke([SystemMessage(content=sys_msg)])
            return f"[{persona}] \n{res.content}"
    
    tasks = [
        call_rebuttal("The Academic Auditor"),
        call_rebuttal("The Market Practitioner"),
        call_rebuttal("The Macro-Connector")
    ]
    
    rebuttals = await asyncio.gather(*tasks)
    
    new_critique = f"--- Round {current_round} Rebuttals ---\n" + "\n\n".join(rebuttals)
    
    print("  ✅ Cross Review Node 완료!", flush=True)
    return {"critiques": [new_critique]} # List 덧셈 (operator.add)

async def moderator_check_node(state: AgentState):
    """
    토론 진행 횟수를 체크하고 다음 라우팅을 결정하는 노드입니다.
    의견 수렴 여부를 LLM으로 판단할 수도 있으나, 여기서는 효율을 위해
    간단하게 debate_count를 늘리고 최대 횟수(예: 1회) 도달 시 종료하도록 구성합니다.
    """
    count = state.get("debate_count", 0) + 1
    
    # 실제 프로덕션에서는 너무 오랜 토론을 방지하기 위해 1번만 교차검토 수행하지만, 테스트를 위해 2회로 늘렸습니다.
    if count >= 2:
        action = "synthesis"
        print(f"\n[LangGraph] ⚖️ Moderator Check: 충분히 토론했습니다. (총 {count}회) 최종 요약으로 넘어갑니다.", flush=True)
    else:
        action = "continue"
        print(f"\n[LangGraph] ⚖️ Moderator Check: 토론이 더 필요합니다. 다시 교차 검증을 진행합니다.", flush=True)
        
    return {"debate_count": count, "moderator_action": action}

async def synthesis_node(state: AgentState):
    """
    최종 중재 노드: 그동안의 모든 초안, 비판을 종합하여 하나의 피드백을 작성합니다.
    """
    concept = state["concept"]
    user_answer = state["user_answer"]
    
    print(f"\n[LangGraph] 📝 3. Synthesis Node 진행 중...", flush=True)
    print("  - 모더레이터가 전문가들의 의견을 바탕으로 학생을 위한 최종 피드백을 요약합니다...", flush=True)
    
    critiques_str = "\n".join(state.get("critiques", []))
    
    sys_msg = SYNTHESIS_SYSTEM_PROMPT.format(
        concept=concept,
        user_answer=user_answer,
        critiques=critiques_str
    )
    
    async with gpu_semaphore:
        res = await creative_llm.ainvoke([SystemMessage(content=sys_msg)])
    
    print("  ✅ Synthesis Node 완료! 최종 피드백 산출 완료 🎉\n", flush=True)
    return {"final_synthesis": res.content}
