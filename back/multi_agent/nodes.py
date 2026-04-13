import json
import asyncio
import re

from langchain_core.messages import SystemMessage, HumanMessage
from multi_agent.state import AgentState
from multi_agent.prompts import (
    NEW_ACADEMIC_DRAFT_PROMPT,
    NEW_MARKET_DRAFT_PROMPT,
    NEW_MACRO_DRAFT_PROMPT,
    NEW_MODERATOR_AGENT_PROMPT,
    AGENT_REBUTTAL_PROMPT
)
from multi_agent.llm_config import draft_llm, debate_llm, synthesis_llm, gpu_semaphore

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

async def call_academic(concept, ground_truth, user_answer):
    async with gpu_semaphore:
        sys_msg = NEW_ACADEMIC_DRAFT_PROMPT.format(concept=concept, ground_truth=ground_truth, user_answer=user_answer)
        res = await draft_llm.ainvoke([SystemMessage(content=sys_msg)])
        data = extract_json(res.content)
        return "The Academic Auditor", data

async def call_market(concept, news_context, user_answer):
    async with gpu_semaphore:
        sys_msg = NEW_MARKET_DRAFT_PROMPT.format(concept=concept, news_context=news_context, user_answer=user_answer)
        res = await draft_llm.ainvoke([SystemMessage(content=sys_msg)])
        data = extract_json(res.content)
        return "The Market Practitioner", data

async def call_macro(concept, kg_context, user_answer):
    async with gpu_semaphore:
        sys_msg = NEW_MACRO_DRAFT_PROMPT.format(concept=concept, kg_context=kg_context, user_answer=user_answer)
        res = await draft_llm.ainvoke([SystemMessage(content=sys_msg)])
        data = extract_json(res.content)
        return "The Macro-Connector", data

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
    
    results = await asyncio.gather(
        call_academic(concept, ground_truth, user_answer), 
        call_market(concept, news_context, user_answer), 
        call_macro(concept, kg_context, user_answer)
    )
    
    draft_reviews = {}
    raw_scores = {}
    is_contradict = False
    
    for agent_name, data in results:
        draft_reviews[agent_name] = data
        raw_scores[agent_name] = data.get("score", 0.0)
        # Academic Agent 가 모순을 감지했는지 확인
        if agent_name == "The Academic Auditor":
            if data.get("type") == "contradiction" or data.get("retry_needed"):
                is_contradict = True
        
    print(f"  ✅ Drafting Node 완료! (모순 감지 여부: {is_contradict})", flush=True)
    
    return {
        "draft_reviews": draft_reviews, 
        "raw_scores": raw_scores,
        "is_contradiction": is_contradict,
        "debate_count": 0,
        "critiques": []
    }

async def call_rebuttal(persona, concept, user_answer, drafts):
    async with gpu_semaphore:
        # 본인을 제외한 다른 에이전트들의 리뷰만 취합
        other_reviews = "\n".join([f"[{p}] \n{rev}\n" for p, rev in drafts.items() if p != persona])
        
        sys_msg = AGENT_REBUTTAL_PROMPT.format(
            persona=persona, 
            concept=concept, 
            user_answer=user_answer, 
            other_reviews=other_reviews
        )
        res = await debate_llm.ainvoke([SystemMessage(content=sys_msg)])
        
        # JSON 기반 파싱: 필드 추출 후 dict로 반환
        data = extract_json(res.content)
        return {
            "persona": persona,
            "agreement_level": data.get("agreement_level", "N/A"),
            "agreement_reason": data.get("agreement_reason", "N/A"),
            "unique_insight": data.get("unique_insight", "N/A"),
            "rebuttal_point": data.get("rebuttal_point", "N/A"),
            "rebuttal_question": data.get("rebuttal_question", "N/A")
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
    
    tasks = [
        call_rebuttal("The Academic Auditor", concept, user_answer, drafts),
        call_rebuttal("The Market Practitioner", concept, user_answer, drafts),
        call_rebuttal("The Macro-Connector", concept, user_answer, drafts)
    ]
    
    rebuttals = await asyncio.gather(*tasks)
    rebuttal_list = list(rebuttals)  # tuple → list 변환
    
    # 기존 formatted string critiques 유지 (하위 호환)
    new_critique = f"--- Round {current_round} Rebuttals ---\n" + "\n\n".join(
        [f"[{r['persona']}]\n- Level: {r['agreement_level']}\n- Reason: {r['agreement_reason']}\n- Insight: {r['unique_insight']}\n- Rebuttal: {r['rebuttal_point']}\n- Question: {r['rebuttal_question']}" for r in rebuttal_list]
    )
    
    print("  ✅ Cross Review Node 완료!", flush=True)
    return {
        "critiques": [new_critique],        # List 덧셈 (operator.add)
        "rebuttal_results": rebuttal_list   # Moderator에 전달될 구조화된 데이터
    }

async def moderator_check_node(state: AgentState):
    """
    토론 진행 횟수를 체크하고 다음 라우팅을 결정하는 노드입니다.
    의견 수렴 여부를 LLM으로 판단할 수도 있으나, 여기서는 효율을 위해
    간단하게 debate_count를 늘리고 최대 횟수(예: 1회) 도달 시 종료하도록 구성합니다.
    """
    count = state.get("debate_count", 0) + 1
    
    # 1회만 교차검토를 수행하도록 제한합니다.
    if count >= 1:
        action = "synthesis"
        print(f"\n[LangGraph] ⚖️ Moderator Check: 충분히 토론했습니다. (총 {count}회) 최종 요약으로 넘어갑니다.", flush=True)
    else:
        action = "continue"
        print(f"\n[LangGraph] ⚖️ Moderator Check: 토론이 더 필요합니다. 다시 교차 검증을 진행합니다.", flush=True)
        
    return {"debate_count": count, "moderator_action": action}

async def synthesis_node(state: AgentState):
    """
    최종 중재 노드: 에이전트들의 JSON 결과를 종합하여 모더레이터가 최종 피드백을 작성합니다.
    """
    concept = state["concept"]
    user_answer = state["user_answer"]
    drafts = state.get("draft_reviews", {})
    
    print(f"\n[LangGraph] ⚖️ 3. Synthesis (Moderator) Node 진행 중...", flush=True)
    
    # 각 에이전트의 결과를 JSON 문자열로 변환하여 프롬프트에 주입
    academic_res = json.dumps(drafts.get("The Academic Auditor", {}), ensure_ascii=False, indent=2)
    market_res = json.dumps(drafts.get("The Market Practitioner", {}), ensure_ascii=False, indent=2)
    macro_res = json.dumps(drafts.get("The Macro-Connector", {}), ensure_ascii=False, indent=2)
    
    # 각 에이전트의 rebuttal 결과를 JSON 배열 문자열로 변환
    rebuttal_results = state.get("rebuttal_results", [])
    rebuttal_results_str = json.dumps(rebuttal_results, ensure_ascii=False, indent=2)
    
    sys_msg = NEW_MODERATOR_AGENT_PROMPT.format(
        concept=concept,
        user_answer=user_answer,
        academic_result=academic_res,
        market_result=market_res,
        macro_result=macro_res,
        rebuttal_results=rebuttal_results_str
    )
    
    async with gpu_semaphore:
        res = await synthesis_llm.ainvoke([SystemMessage(content=sys_msg)])
    
    moderator_data = extract_json(res.content)
    final_message = moderator_data.get("message", res.content)
    
    print("  ✅ Synthesis Node 완료! 최종 피드백 산출 완료 🎉\n", flush=True)
    return {"final_synthesis": final_message}
