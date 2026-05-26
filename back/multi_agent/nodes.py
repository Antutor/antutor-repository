import json
import asyncio
import re
from functools import wraps

from langchain_core.messages import SystemMessage, HumanMessage
from multi_agent.state import AgentState
from multi_agent.prompts import (
    NEW_ACADEMIC_DRAFT_PROMPT,
    NEW_ACADEMIC_ADVANCED_PROMPT,
    NEW_MARKET_DRAFT_PROMPT,
    NEW_MACRO_DRAFT_PROMPT,
    NEW_MODERATOR_AGENT_PROMPT,
    AGENT_REBUTTAL_PROMPT_ACADEMIC,
    AGENT_REBUTTAL_PROMPT_ACADEMIC_ADVANCED,
    AGENT_REBUTTAL_PROMPT_MARKET,
    AGENT_REBUTTAL_PROMPT_MACRO,
    SCAFFOLD_EVAL_PROMPT
)
from multi_agent.llm_config import draft_llm, debate_llm, synthesis_llm, gpu_semaphore
from services.llm_agent import strip_think_tags

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

def with_retry_and_fallback(max_retries=3, fallback_value=None):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    print(f"⚠️ [Retry] {func.__name__} failed (attempt {attempt + 1}/{max_retries}): {str(e)}", flush=True)
                    if attempt == max_retries - 1:
                        if fallback_value is not None:
                            print(f"🛡️ [Fallback] {func.__name__} returning safe fallback.", flush=True)
                            return fallback_value
                        raise e
                    await asyncio.sleep(1.0)
        return wrapper
    return decorator

@with_retry_and_fallback(max_retries=3, fallback_value=("The Academic Auditor", {"score": 0.5, "feedback": "System fallback due to timeout or error.", "is_contradiction": False, "is_fallback": True}))
async def call_academic(concept, definition, acceptable_extensions, user_answer, session_context="", last_question="", consecutive_high_score_count=0):
    async with gpu_semaphore:
        if consecutive_high_score_count >= 1:
            sys_msg = "/no_think\n" + NEW_ACADEMIC_ADVANCED_PROMPT.format(
                concept=concept,
                acceptable_extensions=acceptable_extensions,
                last_question=last_question,
                session_context=session_context,
                user_answer=user_answer
            )
        else:
            sys_msg = "/no_think\n" + NEW_ACADEMIC_DRAFT_PROMPT.format(
                concept=concept, 
                definition=definition, 
                acceptable_extensions=acceptable_extensions, 
                user_answer=user_answer,
                session_context=session_context,
                last_question=last_question,
                consecutive_high_score_count=consecutive_high_score_count
            )
        res = await draft_llm.ainvoke([SystemMessage(content=sys_msg)])
        data = extract_json(strip_think_tags(res.content))
        return "The Academic Auditor", data



@with_retry_and_fallback(max_retries=3, fallback_value=("The Market Practitioner", {"score": 0.5, "feedback": "System fallback due to timeout or error.", "is_contradiction": False, "is_fallback": True}))
async def call_market(concept, news_context, user_answer):
    async with gpu_semaphore:
        sys_msg = "/no_think\n" + NEW_MARKET_DRAFT_PROMPT.format(concept=concept, news_context=news_context, user_answer=user_answer)
        res = await draft_llm.ainvoke([SystemMessage(content=sys_msg)])
        data = extract_json(strip_think_tags(res.content))
        return "The Market Practitioner", data

@with_retry_and_fallback(max_retries=3, fallback_value=("The Macro-Connector", {"score": 0.5, "feedback": "System fallback due to timeout or error.", "is_contradiction": False, "is_fallback": True}))
async def call_macro(concept, kg_context, user_answer):
    async with gpu_semaphore:
        sys_msg = "/no_think\n" + NEW_MACRO_DRAFT_PROMPT.format(concept=concept, kg_context=kg_context, user_answer=user_answer)
        res = await draft_llm.ainvoke([SystemMessage(content=sys_msg)])
        data = extract_json(strip_think_tags(res.content))
        return "The Macro-Connector", data

async def drafting_node(state: AgentState):
    """
    1회차 초안 노드: 각 전문가(Academic, Market, Macro)가 독립적으로 평가를 수행합니다.
    (노드 안에서 asyncio.gather 로 병렬 수행하여 대기시간 최적화)
    """
    concept = state["concept"]
    user_answer = state["user_answer"]
    definition = state.get("definition") or ""
    acceptable_extensions = state.get("acceptable_extensions") or ""
    news_context = state.get("news_context", "")
    kg_context = state.get("kg_context", "")
    session_context = state.get("session_context", "")
    last_question = state.get("last_question", "")
    consecutive_high_score_count = state.get("consecutive_high_score_count", 0)
    
    print(f"\n[LangGraph] 🚀 1. Drafting Node 진행 중... (개념: {concept})", flush=True)
    print(f"  - 3명의 에이전트(Academic, Market, Macro)가 초안을 작성 중입니다...", flush=True)
    
    results = await asyncio.gather(
        call_academic(
            concept, definition, acceptable_extensions, user_answer, 
            session_context=session_context, last_question=last_question, 
            consecutive_high_score_count=consecutive_high_score_count
        ), 
        call_market(concept, news_context, user_answer), 
        call_macro(concept, kg_context, user_answer)
    )
    
    draft_reviews = {}
    raw_scores = {}
    is_contradict = False
    
    for agent_name, data in results:
        draft_reviews[agent_name] = data
        raw_scores[agent_name] = data.get("score", 0.0)
        # Academic Agent 가 모순/오답을 감지했는지 확인
        # - "contradiction": 사실과 반대되는 내용 포함
        # - "incorrect": 틀린 답변 (AI팀 요청: incorrect도 is_contradiction=True로 처리)
        if agent_name == "The Academic Auditor":
            if data.get("type") in ("contradiction", "incorrect"):
                is_contradict = True
        
    print(f"  ✅ Drafting Node 완료! (모순 감지 여부: {is_contradict})", flush=True)
    
    return {
        "draft_reviews": draft_reviews, 
        "raw_scores": raw_scores,
        "is_contradiction": is_contradict,
        "debate_count": 0,
        "critiques": []
    }


def retry_router(state: AgentState) -> str:
    """
    drafting_node 직후 라우터.

    Academic Agent의 retry_needed=true 판정이 나오면
    cross_review + synthesis_node 를 완전히 건너뜁니다.
    → Moderator LLM 추론 비용(cross_review 1회 + synthesis 1회) 절약.

    retry_needed=false(일반 평가)이면 기존 토론 흐름을 그대로 실행합니다.
    """
    academic = state.get("draft_reviews", {}).get("The Academic Auditor", {})
    retry_needed = academic.get("retry_needed", False)
    if retry_needed is True or str(retry_needed).lower() == "true":
        print(
            "\n[LangGraph] ⏩ retry_needed=true 감지 — "
            "cross_review·synthesis 스킵, retry_node로 직행합니다.",
            flush=True,
        )
        return "retry_node"
    return "cross_review_node"


async def retry_node(state: AgentState):
    """
    retry_needed=true 전용 경량 노드.

    NEW_MODERATOR_AGENT_PROMPT의 P1(Retry) 로직을 통해 LLM 1회 호출하여
    news_context / KG context가 반영된 자연스러운 retry 메시지를 생성합니다.

    LLM 호출 실패 시 Academic Agent의 hint + weakest_point 문자열 조합으로 fallback합니다.

    반환값은 synthesis_node와 동일한 키셋을 사용하여
    chat.py·WS 핸들러가 동일하게 처리할 수 있도록 합니다.
    """
    concept   = state["concept"]
    user_answer = state["user_answer"]
    academic  = state.get("draft_reviews", {}).get("The Academic Auditor", {})
    drafts    = state.get("draft_reviews", {})
    language  = state.get("language", "ko")
    # LLM은 항상 영어로 생성 → chat.py의 translate_en_to_ko()가 번역을 담당
    output_language = "English"

    print(
        "\n[LangGraph] 🔁 Retry Node 진행 중... "
        "(Moderator LLM P1 로직으로 retry 메시지 생성)",
        flush=True,
    )

    # ── LLM 호출 (NEW_MODERATOR_AGENT_PROMPT P1 경로) ──────────────────────
    academic_res = json.dumps(academic, ensure_ascii=False, indent=2)
    # retry 경로에서는 Market/Macro 초안과 rebuttal이 없으므로 빈값 전달
    empty_json   = json.dumps({}, ensure_ascii=False)
    empty_list   = json.dumps([], ensure_ascii=False)
    # state에 session_context가 있으면 사용, 없으면 fallback
    session_context_str = state.get("session_context") or f"consecutive_high_score_count: {state.get('consecutive_high_score_count', 0)}"

    sys_msg = "/no_think\n" + NEW_MODERATOR_AGENT_PROMPT.format(
        concept=concept,
        user_answer=user_answer,
        session_context=session_context_str,
        academic_result=academic_res,
        market_result=empty_json,
        macro_result=empty_json,
        rebuttal_results=empty_list,
        news_context=state.get("news_context", ""),
        output_language=output_language,
        turn_count=state.get("turn_count", 0),
        source_turn_count=state.get("source_turn_count", 0),
        mode="retry",
        focus_agent="The Academic Auditor",
        consecutive_high_score_count=state.get("consecutive_high_score_count", 0)
    )

    llm_result = await call_synthesis(sys_msg)

    if llm_result is not None:
        # LLM 응답에서 message 추출
        moderator_data = extract_json(llm_result)
        message = moderator_data.get("message", "").strip()
        if message:
            print(
                f"  ✅ Retry Node 완료! LLM P1 메시지 생성 성공\n",
                flush=True,
            )
            return {
                "final_synthesis": message,
                "moderator_action": "retry",
                "hint_provided": True,
            }

    # ── Fallback: LLM 실패 또는 빈 message → 문자열 조합 ──────────────────
    hint_text = academic.get("hint", "")
    weakest   = academic.get("weakest_point", "")

    print(
        f"  ⚠️ Retry Node fallback: LLM 호출 실패 또는 빈 응답. "
        f"문자열 조합으로 retry 메시지 생성 (hint_present={bool(hint_text)})\n",
        flush=True,
    )

    if hint_text:
        if language == "ko":
            message = f"{weakest} {hint_text} 다시 설명해볼 수 있을까요?"
        else:
            message = f"{weakest} {hint_text} Could you try explaining it again?"
    else:
        if language == "ko":
            message = (
                f"답변에 핵심 개념이 빠져있거나 잘못 서술된 부분이 있습니다. "
                f"({weakest}) 다시 한번 설명해볼 수 있을까요?"
            )
        else:
            message = (
                f"Your answer contains a key conceptual error or missing element. "
                f"({weakest}) Could you try again?"
            )

    return {
        "final_synthesis": message,
        "moderator_action": "retry",
        "hint_provided": True,
    }

@with_retry_and_fallback(
    max_retries=3, 
    fallback_value={
        "persona": "Fallback Agent",
        "agreement_level": "N/A",
        "agreement_reason": "System fallback due to timeout or error.",
        "unique_insight": "N/A",
        "rebuttal_point": "N/A",
        "rebuttal_question": "N/A"
    }
)
async def call_rebuttal(persona, state):
    async with gpu_semaphore:
        concept = state["concept"]
        user_answer = state["user_answer"]
        drafts = state.get("draft_reviews", {})
        session_context = state.get("session_context") or f"consecutive_high_score_count: {state.get('consecutive_high_score_count', 0)}"

        # 본인을 제외한 다른 에이전트들의 리뷰만 취합
        other_reviews = "\n".join([f"[{p}] \n{rev}\n" for p, rev in drafts.items() if p != persona])
        
        if persona == "The Academic Auditor":
            consecutive_count = state.get("consecutive_high_score_count", 0)
            if consecutive_count >= 1:
                prompt_template = AGENT_REBUTTAL_PROMPT_ACADEMIC_ADVANCED
            else:
                prompt_template = AGENT_REBUTTAL_PROMPT_ACADEMIC
            acceptable_extensions = state.get("acceptable_extensions", "")
            sys_msg = "/no_think\n" + prompt_template.format(
                concept=concept, 
                user_answer=user_answer, 
                acceptable_extensions=acceptable_extensions,
                session_context=session_context,
                other_reviews=other_reviews,
                turn_count=state.get("turn_count", 0)
            )
        elif persona == "The Market Practitioner":
            prompt_template = AGENT_REBUTTAL_PROMPT_MARKET
            news_context = state.get("news_context", "")
            sys_msg = "/no_think\n" + prompt_template.format(
                concept=concept, 
                user_answer=user_answer, 
                news_context=news_context,
                session_context=session_context,
                other_reviews=other_reviews,
                turn_count=state.get("turn_count", 0),
                source_turn_count=state.get("source_turn_count", 0)
            )
        else:
            prompt_template = AGENT_REBUTTAL_PROMPT_MACRO
            kg_context = state.get("kg_context", "")
            sys_msg = "/no_think\n" + prompt_template.format(
                concept=concept, 
                user_answer=user_answer, 
                kg_context=kg_context,
                session_context=session_context,
                other_reviews=other_reviews,
                turn_count=state.get("turn_count", 0),
                source_turn_count=state.get("source_turn_count", 0)
            )
            
        res = await debate_llm.ainvoke([SystemMessage(content=sys_msg)])
        
        # JSON 기반 파싱: 필드 추출 후 dict로 반환
        data = extract_json(strip_think_tags(res.content))
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
        call_rebuttal("The Academic Auditor", state),
        call_rebuttal("The Market Practitioner", state),
        call_rebuttal("The Macro-Connector", state)
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

@with_retry_and_fallback(max_retries=3, fallback_value=None)
async def call_synthesis(sys_msg):
    async with gpu_semaphore:
        res = await synthesis_llm.ainvoke([SystemMessage(content=sys_msg)])
    return strip_think_tags(res.content)

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
    rebuttals_str = json.dumps(rebuttal_results, ensure_ascii=False, indent=2)
    
    # state에 session_context가 있으면 사용, 없으면 fallback
    session_context_str = state.get("session_context") or f"consecutive_high_score_count: {state.get('consecutive_high_score_count', 0)}"
    language = state.get("language", "ko")
    output_language = "English"  # LLM은 항상 영어로 생성 → chat.py의 translate_en_to_ko()가 번역 담당
    
    # Calculate mode for mastery check
    current_count = state.get("consecutive_high_score_count", 0)
    raw_scores = state.get("raw_scores", {})
    academic_score = raw_scores.get("The Academic Auditor", 0)
    
    avg_score = (
        raw_scores.get("The Academic Auditor", 0) * 100 +
        raw_scores.get("The Market Practitioner", 0) * 100 +
        raw_scores.get("The Macro-Connector", 0) * 100
    ) / 300.0

    if current_count == 0:
        new_count = 1 if academic_score >= 0.5 else 0
    else:
        new_count = current_count + 1 if avg_score >= 0.6 else 1

    mode = "mastery" if new_count >= 3 and avg_score >= 0.6 else ""
    
    # focus_agent calculation
    focus_agent = "The Academic Auditor"
    if raw_scores:
        # Find all agents sorted by score (ascending)
        sorted_agents = sorted(raw_scores.keys(), key=lambda k: raw_scores[k])
        current_lowest = sorted_agents[0]
        previous_lowest = state.get("previous_lowest_agent")
        
        # If the same agent is lowest again, rotate to the second lowest
        if current_lowest == previous_lowest and len(sorted_agents) > 1:
            focus_agent = sorted_agents[1]
        else:
            focus_agent = current_lowest

    # Map agent name to dimension guide format
    agent_to_dimension = {
        "The Academic Auditor": "academic",
        "The Market Practitioner": "market",
        "The Macro-Connector": "macro"
    }
    focus_dimension = agent_to_dimension.get(focus_agent, "academic")

    sys_msg = "/no_think\n" + NEW_MODERATOR_AGENT_PROMPT.format(
        concept=concept,
        user_answer=user_answer,
        session_context=session_context_str,
        academic_result=academic_res,
        market_result=market_res,
        macro_result=macro_res,
        rebuttal_results=rebuttals_str,
        news_context=state.get("news_context", ""),
        output_language=output_language,
        turn_count=state.get("turn_count", 0),
        source_turn_count=state.get("source_turn_count", 0),
        mode=mode,
        focus_agent=focus_dimension,
        consecutive_high_score_count=state.get("consecutive_high_score_count", 0)
    )
    
    res_content = await call_synthesis(sys_msg)
    
    if res_content is None:
        # 타임아웃 발생 시 fallback 처리: 각 에이전트의 부분 결과를 조합하여 반환
        print("\n[Fallback] Moderator timeout. 부분 결과를 조합하여 반환합니다.", flush=True)
        academic_data = drafts.get("The Academic Auditor", {})
        weakest_point = academic_data.get("weakest_point", "")
        hint = academic_data.get("hint", "")
        
        if language == "ko":
            fallback_msg = f"응답 생성 시간이 초과되어 학술적 피드백만 전달합니다.\n발견된 핵심 약점: {weakest_point}"
            if hint:
                fallback_msg += f"\n힌트: {hint}"
        else:
            fallback_msg = f"Response generation timed out. Delivering academic feedback only.\nWeakest point: {weakest_point}"
            if hint:
                fallback_msg += f"\nHint: {hint}"
                
        moderator_data = {"message": fallback_msg, "hint_provided": bool(hint), "mode": "retry" if academic_data.get("retry_needed") else "normal"}
        final_message = fallback_msg
    else:
        moderator_data = extract_json(res_content)
        final_message = moderator_data.get("message", res_content)
    
    # 안정적인 파싱을 위한 처리
    raw_hint_provided = moderator_data.get("hint_provided", False)
    if isinstance(raw_hint_provided, str):
        hint_provided = raw_hint_provided.lower() == "true"
    else:
        hint_provided = bool(raw_hint_provided)
        
    mode = moderator_data.get("mode", "")
    
    # Priority 1: retry_needed 연동 강제화
    academic_data = drafts.get("The Academic Auditor", {})
    retry_needed = academic_data.get("retry_needed", False)
    if retry_needed is True or str(retry_needed).lower() == "true":
        mode = "retry"
        hint_provided = True
    else:
        hint_provided = False
    
    print("  ✅ Synthesis Node 완료! 최종 피드백 산출 완료 🎉\n", flush=True)
    return {"final_synthesis": final_message, "hint_provided": hint_provided, "moderator_action": mode}
