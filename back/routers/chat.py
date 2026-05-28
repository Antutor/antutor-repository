from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from starlette.websockets import WebSocketState
import jwt
import asyncio
import re

from schemas import ChatRequest, EndSessionRequest, ResumeDecisionRequest
from database import supabase
from dependencies import get_current_user
from config import GIVE_UP_KEYWORDS, SECRET_KEY, ALGORITHM
from services.llm_agent import (
    retrieve_news_rag,
    retrieve_knowledge_graph,
    ThinkTagStreamFilter,
    strip_think_tags,
    call_scaffold_eval
)
from multi_agent.graph import debate_graph
from multi_agent.nodes import call_academic
from services.translator import translate_en_to_ko, translate_ko_to_en
from datetime import datetime, timezone, timedelta
import json
import ast
import os
from multi_agent.llm_config import draft_llm
from multi_agent.prompts import RECOVERY_NUDGE_PROMPT, RECOVERY_CONCEPT_PROMPT, RECOVERY_FILL_BLANK_PROMPT, RECOVERY_REVEAL_PROMPT
from langchain_core.messages import SystemMessage
# --- 보안 가드레일 & 시맨틱 캐시 ---
from services.guardrail import run_guardrail, run_guardrail_ws
from services.semantic_cache import get_cached_response, save_to_cache

def get_recovery_prompt(concept_name, definition, acceptable_extensions, last_question, kg_context, idk_count, student_answer="", session_context=""):
    fmt = dict(concept_name=concept_name, definition=definition, acceptable_extensions=acceptable_extensions,
               last_question=last_question, kg_context=kg_context, student_answer=student_answer, session_context=session_context)
    if idk_count == 1:
        template = RECOVERY_NUDGE_PROMPT.format(**fmt)
    elif idk_count == 2:
        template = RECOVERY_CONCEPT_PROMPT.format(**fmt)
    elif idk_count == 3:
        template = RECOVERY_FILL_BLANK_PROMPT.format(**fmt)
    else:
        template = RECOVERY_REVEAL_PROMPT.format(**fmt)
    return "/no_think\n" + template

def save_chat_log_db(chat_log_payload):
    try:
        supabase.table("chat_logs").insert(chat_log_payload).execute()
    except Exception as e:
        if 'turn_summary' in str(e) or 'PGRST204' in str(e):
            print(f"[Warning] 'turn_summary' 컬럼이 없어 제외하고 저장 시도: {e}", flush=True)
            chat_log_payload.pop("turn_summary", None)
            try:
                supabase.table("chat_logs").insert(chat_log_payload).execute()
                return
            except Exception as e2:
                error_msg = f"Failed to save chat log to DB after fallback: {e2}"
                print(error_msg, flush=True)
        else:
            error_msg = f"Failed to save chat log to DB: {e}"
            print(error_msg, flush=True)
            try:
                with open("db_error.log", "a", encoding="utf-8") as f:
                    f.write(f"[{datetime.now().isoformat()}] {error_msg} | Payload: {json.dumps(chat_log_payload, ensure_ascii=False)}\n")
            except:
                pass

async def db(fn):
    """
    Supabase 동기 클라이언트 호출을 스레드 풀에서 실행합니다.
    - 이벤트 루프 비블로킹 → 동시접속 안전
    - await으로 완료 보장 → end_session race condition 방지
    Usage: result = await db(lambda: supabase.table("X").select("*").execute())
    """
    return await asyncio.to_thread(fn)


_SHORT_ANSWER_STOPWORDS = {
    "this", "that", "there", "their", "what", "which", "when", "where",
    "because", "would", "should", "could", "about", "with", "from",
}

def is_short_answer(text: str) -> bool:
    """
    사용자 입력이 '네', 'yes', 'ok' 등 서술형이 아닌 단답형인지 판별합니다.
    공백 기준 단어 수 ≤ 2이면 단답형으로 간주합니다.
    is_give_up=True인 경우에는 호출하지 않습니다.
    """
    stripped = text.strip()
    if not stripped:
        return False
    # 구두점 제거 후 단어 수 계산
    clean = re.sub(r'[!?.。、,，~ㅋㅎ]+', '', stripped).strip()
    words = clean.split()
    return len(words) <= 2


_SHORT_ANSWER_REPROMPT_EN = (
    "A brief response isn't enough for a proper evaluation. "
    "Please explain the concept in your own words — include WHY it happens, "
    "HOW it works, and WHAT effects it has. Give it another try!"
)


def save_debate_log(session_id, concept, user_answer, draft_reviews, critiques, final_synthesis):
    try:
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, "debate_logs.jsonl")
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "concept": concept,
            "user_answer": user_answer,
            "draft_reviews": draft_reviews,
            "critiques": critiques,
            "final_synthesis": final_synthesis
        }
        
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"Failed to save debate log: {e}")

router = APIRouter()

async def get_concept_by_term(term: str):
    response = await db(lambda: supabase.table("concepts").select("*").execute())
    concepts = response.data
    
    target_concept = None
    
    for row in concepts:
        if row["name"].lower() == term.lower():
            target_concept = row
            break
            
    if not target_concept:
        for row in concepts:
            translated_k = await translate_en_to_ko(row["name"])
            if term == translated_k or term == translated_k.replace(" ", ""):
                target_concept = row
                break
    return target_concept

@router.get("/start/{concept}")
async def start_session(concept: str, language: str = "ko", current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("user_id", current_user.get("id"))
    
    # 1. 지원하는 개념 DB 확인
    target_concept = await get_concept_by_term(concept)
    if not target_concept:
        raise HTTPException(status_code=404, detail="Target Concept is not supported.")
        
    db_concept_id = target_concept["concept_id"]
    actual_concept_name = target_concept["name"]
    initial_question_korean = await translate_en_to_ko(f"How would you explain {actual_concept_name}?", language)
        
    # 2. 동일 개념 과거 완료/학습 이력 확인
    resume_available = False
    last_ai_response = ""
    
    prev_sessions = await db(lambda: supabase.table("sessions").select("session_id").eq("user_id", user_id).eq("concept_id", db_concept_id).execute())
    if prev_sessions.data:
        session_ids = [s["session_id"] for s in prev_sessions.data]
        logs_res = await db(lambda: supabase.table("chat_logs").select("ai_response").in_("session_id", session_ids).order("created_at", desc=True).limit(1).execute())
        if logs_res.data and logs_res.data[0].get("ai_response"):
            resume_available = True
            last_ai_response = await translate_en_to_ko(logs_res.data[0]["ai_response"], language)

    # 3. 만약 이력이 있다면, 세션을 미리 생성하지 않고 "재개 여부" 정보만 반환
    if resume_available:
        if language == "en":
            resume_prompt = "Would you like to resume from the last session, or start fresh?"
        else:
            resume_prompt = "이전 학습의 마지막 질문부터 이어서 학습하시겠습니까, 아니면 처음부터 다시 학습하시겠습니까?"
        return {
            "session_id": None, # 아직 생성 안됨
            "concept": actual_concept_name,
            "resume_available": True,
            "resume_prompt": resume_prompt,
            "last_ai_response": last_ai_response,
            "initial_question": initial_question_korean
        }
    
    # 4. 이력이 없다면 즉시 신규 세션 생성
    new_session = {
        "user_id": user_id,
        "concept_id": db_concept_id,
        "status": "IN_PROGRESS",
        "created_at": datetime.now(timezone(timedelta(hours=9))).isoformat()
    }
    insert_res = supabase.table("sessions").insert(new_session).execute()
    session_id = str(insert_res.data[0]["session_id"])
    
    return {
        "session_id": session_id,
        "concept": actual_concept_name,
        "initial_question": initial_question_korean,
        "resume_available": False,
        "resume_prompt": "",
        "last_ai_response": ""
    }


@router.post("/resolve_resume")
async def resolve_resume(request: ResumeDecisionRequest, current_user: dict = Depends(get_current_user)):
    """
    사용자의 재개 여부 결정(resume/fresh)에 따라 세션을 생성하고 첫 질문을 반환합니다.
    """
    user_id = current_user.get("user_id", current_user.get("id"))
    concept = request.concept
    decision = request.decision # "resume" or "fresh"
    language = request.language or "ko"
    
    # 1. 개념 정보 조회
    target_concept = await get_concept_by_term(concept)
    if not target_concept:
        raise HTTPException(status_code=404, detail="Concept not found.")
    db_concept_id = target_concept["concept_id"]
    actual_concept_name = target_concept["name"]
    
    # 2. 신규 세션 생성
    new_session = {
        "user_id": user_id,
        "concept_id": db_concept_id,
        "status": "IN_PROGRESS",
        "created_at": datetime.now(timezone(timedelta(hours=9))).isoformat()
    }
    insert_res = supabase.table("sessions").insert(new_session).execute()
    session_id = str(insert_res.data[0]["session_id"])
    
    # 3. 결정에 따른 첫 질문 결정
    if decision == "resume":
        prev_sessions = await db(lambda: supabase.table("sessions").select("session_id").eq("user_id", user_id).eq("concept_id", db_concept_id).execute())
        # 현재 생성한 세션 제외
        other_session_ids = [s["session_id"] for s in prev_sessions.data if str(s["session_id"]) != session_id]
        
        logs_res = await db(lambda: supabase.table("chat_logs").select("ai_response").in_("session_id", other_session_ids).order("created_at", desc=True).limit(1).execute())
        
        if logs_res.data and logs_res.data[0].get("ai_response"):
            question = await translate_en_to_ko(logs_res.data[0]["ai_response"], language)
        else:
            question = await translate_en_to_ko(f"How would you explain {actual_concept_name}?", language)
    else:
        question = await translate_en_to_ko(f"How would you explain {actual_concept_name}?", language)
        
    return {
        "session_id": session_id,
        "question": question
    }

@router.post("/chat")
async def chat(request: ChatRequest, background_tasks: BackgroundTasks, current_user: dict = Depends(get_current_user)):
    print(f"\n[DEBUG] 📩 유저로부터 /chat 요청 도착! (답변: {request.user_answer[:30]}...)", flush=True)
    user_id = current_user.get("user_id", current_user.get("id"))
    language = request.language or "ko"
    
    sess_res = await db(lambda: supabase.table("sessions").select("*").eq("session_id", int(request.session_id)).execute())
    if not sess_res.data:
        raise HTTPException(status_code=404, detail="Invalid Session ID.")
    session = sess_res.data[0]
    
    if session["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this session.")
        
    db_concept_id = session["concept_id"]
    concept_res = await db(lambda: supabase.table("concepts").select("*").eq("concept_id", db_concept_id).execute())
    if not concept_res.data:
        raise HTTPException(status_code=404, detail="Target Concept is not supported.")
    concept_data = concept_res.data[0]
    concept_name = concept_data["name"]
    definition = concept_data["definition"]
    acceptable_extensions = concept_data.get("acceptable_extensions", "")
    
    eval_user_answer = await translate_ko_to_en(request.user_answer, language)
    # Check only original (Korean or English) input for keywords to prevent translation false positives
    is_give_up = any(kw in request.user_answer.lower() for kw in GIVE_UP_KEYWORDS)
    is_contradiction = False

    # ── 1. 보안 가드레일 ──────────────────────────────────────────────
    await run_guardrail(eval_user_answer, user_id=str(user_id))

    # ── 1-1. 단답형 감지 — 서술형 재유도 (3단계 빈칸채우기 시에는 단답형 허용) ─────────
    if not is_give_up and session.get("idk_count", 0) != 3 and is_short_answer(request.user_answer):
        reprompt_msg = await translate_en_to_ko(_SHORT_ANSWER_REPROMPT_EN, language)
        return {
            "atomic_propositions": [],
            "expert_average_score": 0.0,
            "is_contradiction_override": False,
            "expert_feedback": [],
            "is_fallback": False,
            "is_short_answer": True,
            "moderator_decision": {
                "status": "short_answer",
                "lowest_performing_area": "N/A",
                "scaffold_plan": {
                    "step": "Short Answer Reprompt",
                    "message": reprompt_msg
                }
            }
        }

    # 현재 턴 수 계산 (캐싱 로직 및 DB 저장에 활용)
    logs_count_res = await db(lambda: supabase.table("chat_logs").select("log_id", count="exact").eq("session_id", session["session_id"]).execute())
    turn_number = logs_count_res.count + 1 if logs_count_res.count is not None else 1

    # ── 2. 시맨틱 캐시 조회 ──────────────────────────────────────────
    # 첫 번째 답변(Draft)일 때만 캐시를 조회합니다. 꼬리 질문(turn_number > 1)에 대한 답변은 캐시를 우회해야 문맥에 맞는 평가가 가능합니다.
    if not is_give_up and turn_number == 1:
        cached_response = await get_cached_response(concept_name, eval_user_answer)
        if cached_response:
            print(f"✅ [Chat] 시맨틱 캐시 히트! 캐시된 응답 반환", flush=True)
            translated_cached = await translate_en_to_ko(cached_response, language)
            return {
                "atomic_propositions": ["(Served from semantic cache)"],
                "expert_average_score": 0.0,
                "is_contradiction_override": False,
                "expert_feedback": [],
                "is_fallback": False,
                "from_cache": True,
                "moderator_decision": {
                    "status": "proceed",
                    "lowest_performing_area": "N/A",
                    "scaffold_plan": {
                        "step": "Guidance Prompt",
                        "message": translated_cached
                    }
                }
            }
    
    any_fallback = False
    is_scaffold_success = False

    # kg_context: give_up 시 스캐폴딩 프롬프트에도 필요하므로 is_give_up 여부와 무관하게 항상 조회합니다.
    # (첫 턴에서 바로 give_up 시 NameError 방지)
    kg_context = await retrieve_knowledge_graph(concept_name.lower())

    # ── Scaffolding 답변 평가 ─────────────────────────────────────────
    # idk_count > 0 이고 give_up이 아닌 실제 답변이 들어온 경우:
    # Academic Agent로 평가 후 correct이면 정상 흐름 복귀, 아니면 다음 scaffolding 레벨로 진입
    if not is_give_up and session["idk_count"] > 0:
        print(f"\n[ChatRouter] 📋 Scaffolding 답변 평가 중... (idk_count={session['idk_count']})", flush=True)
        
        # 직전 턴의 힌트 텍스트 가져오기 (가장 마지막 ai_response)
        hint_log = await db(lambda: supabase.table("chat_logs") \
            .select("ai_response, scaffold_step") \
            .eq("session_id", session["session_id"]) \
            .not_.is_("scaffold_step", "null") \
            .order("turn_number", desc=True) \
            .limit(1).execute())
        last_hint = hint_log.data[0]["ai_response"] if hint_log.data else ""
        scaffold_step = hint_log.data[0]["scaffold_step"] if hint_log.data else ""

        scaffold_eval = await call_scaffold_eval(
            concept_name, definition, acceptable_extensions or "", scaffold_step, last_hint, eval_user_answer
        )
        if scaffold_eval.get("type") == "correct":
            # 정답 → idk_count 초기화 후 정상 debate 흐름으로
            print(f"  ✅ Scaffolding 답변 정답 인정 — idk_count 초기화, 정상 흐름으로 복귀", flush=True)
            await db(lambda: supabase.table("sessions").update({"idk_count": 0}).eq("session_id", session["session_id"]).execute())
            is_scaffold_success = True
            
            if scaffold_step in ["Fill-in-the-Blank", "3단계 힌트", "Level 3"]:
                import re
                pattern = r'_{2,}|\[\s*_*\s*\]|\(\s*_*\s*\)'
                if re.search(pattern, last_hint):
                    eval_user_answer = re.sub(pattern, eval_user_answer, last_hint, count=1)
                else:
                    eval_user_answer = f"{last_hint} {eval_user_answer}"
        else:
            # 오답 → is_give_up=True로 전환해 다음 scaffolding 레벨 힌트 생성
            print(f"  ⚠️ Scaffolding 답변 오답 — 다음 scaffolding 레벨로 진입", flush=True)
            is_give_up = True

    # ── session_context 히스토리 빌드 ────────────────────────────────
    # give_up 경로(scaffolding)와 정상 경로 모두에서 사용하므로 분기 전에 빌드합니다.
    try:
        history_res = await db(lambda: supabase.table("chat_logs") \
            .select("turn_number, user_message, ai_response, scaffold_step, news_urls, selected_agent, turn_summary") \
            .eq("session_id", session["session_id"]) \
            .order("turn_number", desc=False) \
            .execute())
    except Exception as e:
        print(f"[Warning] 'turn_summary' 컬럼 조회 실패. 일반 조회로 폴백합니다: {e}")
        history_res = await db(lambda: supabase.table("chat_logs") \
            .select("turn_number, user_message, ai_response, scaffold_step, news_urls, selected_agent") \
            .eq("session_id", session["session_id"]) \
            .order("turn_number", desc=False) \
            .execute())

    full_history = history_res.data
    turn_summaries = []
    for log in full_history:
        summary = log.get("turn_summary")
        if summary:
            turn_summaries.append(f"[Turn {log['turn_number']}] {summary}")
        else:
            turn_summaries.append(f"[Turn {log['turn_number']}] (No summary available)")

    RECENT_N = 3

    def format_full(logs):
        formatted = {}
        for log in logs:
            formatted[f"turn_{log['turn_number']}"] = {
                "user_answer": log.get("user_message") or "",
                "final_synthesis": log.get("ai_response") or "",
                "scaffold_step": log.get("scaffold_step") or None
            }
        return json.dumps(formatted, ensure_ascii=False, indent=2)

    if len(full_history) <= RECENT_N:
        session_context_str = format_full(full_history)
    else:
        older = turn_summaries[:-RECENT_N]
        recent = full_history[-RECENT_N:]
        session_context_str = (
            "[Past turns summary]\n" + "\n".join(older) +
            "\n\n[Recent turns]\n" + format_full(recent)
        )
    
    session_context_str = f"consecutive_high_score_count: {session.get('consecutive_high_score_count', 0)}\n\n" + session_context_str
    
    last_question_from_history = ""
    for log in reversed(history_res.data):
        if log.get("scaffold_step") is None:
            last_question_from_history = log.get("ai_response") or ""
            break
            
    last_selected_agent = None
    if history_res.data:
        last_selected_agent = history_res.data[-1].get("selected_agent")

    # 이전 턴에서 사용한 뉴스 URL 수집 (중복 제외)
    used_news_urls: set = set()
    for log in history_res.data:
        urls = log.get("news_urls")
        if not urls:
            continue
        if isinstance(urls, str):
            try:
                # Some DBs return string representations of lists like "['url1', 'url2']"
                urls = json.loads(urls.replace("'", '"'))
            except Exception:
                try:
                    urls = ast.literal_eval(urls)
                except Exception:
                    urls = [urls]
        if isinstance(urls, list):
            used_news_urls.update(urls)

    if is_give_up:
        antutor_score = 0.0
        expert_scores = {"The Market Practitioner": 0.0, "The Macro-Connector": 0.0, "The Academic Auditor": 0.0}
        propositions = []
        expert_results = [{"persona": "System", "score": 0.0, "feedback": "User requested help."}]
        lowest_persona = "System"
        news_urls: set = set()
    else:
        propositions = ["(Evaluated by Multi-Agent Debate Graph)"]

        # news_context: last_question 키워드 + 이전 턴 URL dedup 적용
        from services.llm_agent import retrieve_tavily_news_v2
        news_context, news_urls = await retrieve_tavily_news_v2(
            concept_name, eval_user_answer,
            last_question=last_question_from_history,
            used_urls=used_news_urls
        )

        turn_count = len(session_history)

        initial_state = {
            "concept": concept_name,
            "user_answer": eval_user_answer,
            "definition": definition,
            "acceptable_extensions": acceptable_extensions,
            "news_context": news_context,
            "kg_context": kg_context,
            "draft_reviews": {},
            "critiques": [],
            "raw_scores": {},
            "is_contradiction": False,
            "final_synthesis": "",
            "debate_count": 0,
            "moderator_action": "",
            "consecutive_high_score_count": session.get("consecutive_high_score_count", 0),
            "source_turn_count": session.get("source_turn_count", 0),
            "hint_provided": False,
            "session_context": session_context_str,
            "last_question": last_question_from_history,
            "turn_count": turn_count,
            "previous_lowest_agent": last_selected_agent,
            "is_scaffold_success": is_scaffold_success,
            "scaffold_step": scaffold_step
        }
        
        print(f"👉 [ChatRouter] 랭그래프 호출 진입 전... (RAG 완료, State 준비 완료)", flush=True)
        final_state = await debate_graph.ainvoke(initial_state)

        expert_results = []
        expert_scores_raw = final_state["raw_scores"]
        
        antutor_score = expert_scores_raw.get("The Academic Auditor", 0.0)
        is_contradiction = final_state.get("is_contradiction", False)
        hint_provided = final_state.get("hint_provided", False)
        
        if hint_provided:
            current_scaffold_count = session.get("scaffolding_counter", 0)
            await db(lambda: supabase.table("sessions").update({"scaffolding_counter": current_scaffold_count + 1}).eq("session_id", session["session_id"]).execute())
        
        for persona, review in final_state["draft_reviews"].items():
            fallback_flag = review.get("is_fallback", False) if isinstance(review, dict) else False
            if fallback_flag:
                any_fallback = True
                
            expert_results.append({
                "persona": persona,
                "score": expert_scores_raw.get(persona, 0.75),
                "feedback": review,
                "is_fallback": fallback_flag
            })
            
        expert_scores = expert_scores_raw
        
        # 교차 검증 로그를 파일로 저장
        background_tasks.add_task(
            save_debate_log,
            session_id=session["session_id"],
            concept=concept_name,
            user_answer=eval_user_answer,
            draft_reviews=final_state["draft_reviews"],
            critiques=final_state.get("critiques", []),
            final_synthesis=final_state.get("final_synthesis", "")
        )
        
        final_synthesis = final_state.get("final_synthesis", "")
        if is_scaffold_success:
            if language == "en":
                success_step_name = {
                    "Sub-concept Nudge": "Level 1 Hint",
                    "Concept Explanation": "Level 2 Hint",
                    "Fill-in-the-Blank": "Level 3 Hint"
                }.get(scaffold_step, scaffold_step)
                success_msg = f"That is correct! You have successfully completed the {success_step_name}. "
            else:
                success_step_name = {
                    "Sub-concept Nudge": "1단계 힌트",
                    "Concept Explanation": "2단계 힌트",
                    "Fill-in-the-Blank": "3단계 힌트"
                }.get(scaffold_step, scaffold_step)
                success_msg = f"정답입니다! 훌륭하게 맞추셨어요. {success_step_name}를 벗어났습니다. "
                
            final_synthesis = success_msg + final_synthesis
            final_state["final_synthesis"] = final_synthesis
        
        turn_summary_to_save = final_state.get("turn_summary", "")
        
        if is_contradiction:
            antutor_score = 0.0
            propositions = ["Local LLM Blocked: Explicit contradiction found."]
            lowest_persona = "System"
        else:
            lowest_persona = min(expert_scores.keys(), key=lambda k: expert_scores[k])
        
    raw_avg_score = (
        expert_scores.get("The Academic Auditor", 0) * 100 +
        expert_scores.get("The Market Practitioner", 0) * 100 +
        expert_scores.get("The Macro-Connector", 0) * 100
    ) / 3.0

    avg_score = raw_avg_score / 100

    # 1. consecutive_high_score_count 로직
    academic_score = expert_scores.get("The Academic Auditor", 0)
    current_count = session.get("consecutive_high_score_count", 0)

    if current_count == 0:
        new_count = 1 if academic_score >= 0.5 else 0
    else:
        new_count = current_count + 1 if avg_score >= 0.6 else 1

    # 2. source_turn_count 로직
    current_source_turn = session.get("source_turn_count", 0)
    if avg_score >= 0.5:
        new_source_turn = current_source_turn + 1
    else:
        new_source_turn = current_source_turn

    await db(lambda: supabase.table("sessions").update({
        "consecutive_high_score_count": new_count,
        "source_turn_count": new_source_turn
    }).eq("session_id", session["session_id"]).execute())

    moderator_action = "proceed"
    scaffold_plan = None
    
    current_idk_count = session["idk_count"]
    
    guidance_message = "" # DB 저장을 위해 기본값 설정
    
    if is_give_up:
        current_idk_count += 1
        moderator_action = "scaffold"
        if current_idk_count == 1:
            await db(lambda: supabase.table("sessions").update({"idk_count": current_idk_count}).eq("session_id", session["session_id"]).execute())
            scaffold_step = "Sub-concept Nudge"
            scaffolding_level = 3
        elif current_idk_count == 2:
            await db(lambda: supabase.table("sessions").update({"idk_count": current_idk_count}).eq("session_id", session["session_id"]).execute())
            scaffold_step = "Concept Explanation"
            scaffolding_level = 2
        elif current_idk_count == 3:
            await db(lambda: supabase.table("sessions").update({"idk_count": current_idk_count}).eq("session_id", session["session_id"]).execute())
            scaffold_step = "Fill-in-the-Blank"
            scaffolding_level = 1
        else:
            await db(lambda: supabase.table("sessions").update({"idk_count": 0}).eq("session_id", session["session_id"]).execute())
            scaffold_step = "Solution Reveal"
            scaffolding_level = 0
            
        # 마지막 AI 질문 조회 (이전 턴에 Moderator가 던진 질문 — 힌트 맥락 기준)
        last_log = await db(lambda: supabase.table("chat_logs") \
            .select("ai_response") \
            .eq("session_id", session["session_id"]) \
            .is_("scaffold_step", "null") \
            .order("turn_number", desc=True) \
            .limit(1).execute())
        last_question = last_log.data[0]["ai_response"] if last_log.data else ""

        sys_prompt = get_recovery_prompt(concept_name, definition, acceptable_extensions, last_question, kg_context, current_idk_count,
                                          student_answer=eval_user_answer, session_context=session_context_str)

        # 동기 블록 내에서 ainvoke를 호출해야 하므로 asyncio 이벤트 루프 또는 await 사용 필요
        # wait! 이 함수는 POST /chat (async def) 내부입니다. await 가능.
        res = await draft_llm.ainvoke([SystemMessage(content=sys_prompt)])
        
        clean_content = strip_think_tags(res.content)
        try:
            parsed = json.loads(clean_content)
            guidance_message = parsed.get("message", clean_content)
        except Exception:
            guidance_message = clean_content
            
        scaffold_prefixes = {
            "Sub-concept Nudge": "💡 1단계 힌트: ",
            "Concept Explanation": "💡 2단계 힌트: ",
            "Fill-in-the-Blank": "💡 3단계 힌트: ",
            "Solution Reveal": "💡 정답 공개: "
        }
        prefix = scaffold_prefixes.get(scaffold_step, "")
        if prefix:
            guidance_message = f"{prefix}{guidance_message}"
            
        scaffold_plan = {
            "step": scaffold_step,
            "scaffolding_level": scaffolding_level,
            "message": guidance_message
        }
    else:
        if session["idk_count"] > 0:
            await db(lambda: supabase.table("sessions").update({"idk_count": 0}).eq("session_id", session["session_id"]).execute())

        # graph 내 retry_router가 retry_needed=true를 감지했으면
        # retry_node가 final_synthesis와 moderator_action="retry"를 이미 설정합니다.
        # 그 외의 경우 synthesis_node가 moderate_action을 설정합니다.
        synth_mode = final_state.get("moderator_action", "proceed")

        if new_count >= 3 and avg_score >= 0.6:
            moderator_action = "suggest_termination"
            guidance_message = final_state.get("final_synthesis", "Excellent job! You have fully understood this concept.")
            scaffold_plan = {
                "step": "Termination Suggestion",
                "message": guidance_message
            }
        elif is_contradiction or synth_mode == "retry":
            # retry_node 또는 is_contradiction → final_synthesis는 이미 올바른 retry 메시지
            moderator_action = "retry"
            guidance_message = final_state.get("final_synthesis") or "Your answer seems to contradict the core facts. Please review the concept once more or ask for a 'hint'!"
            scaffold_plan = {
                "step": "Retry Prompt",
                "message": guidance_message
            }
        else:
            moderator_action = "proceed"
            guidance_message = final_state.get("final_synthesis", "Good job, but let's explore more deeply.")
            scaffold_plan = {
                "step": "Guidance Prompt",
                "message": guidance_message
            }

    # ── 3. 시맨틱 캐시 저장 ──────────────────────────────────────────
    # 첫 번째 턴에서 생성된 피드백만 캐시에 저장합니다.
    if not is_give_up and guidance_message and turn_number == 1:
        await save_to_cache(concept_name, eval_user_answer, guidance_message)

    chat_log_payload = {
        "session_id": session["session_id"],
        "turn_number": turn_number,
        "user_message": request.user_answer,
        "score_academic": antutor_score,
        "score_market": expert_scores.get("The Market Practitioner", 0),
        "score_macro": expert_scores.get("The Macro-Connector", 0),
        "selected_agent": lowest_persona[:20] if lowest_persona else None,
        "ai_response": guidance_message,
        "scaffold_step": scaffold_plan.get("step") if is_give_up and scaffold_plan else None,
        "news_urls": list(news_urls) if news_urls else [],
        "turn_summary": turn_summary_to_save if not is_give_up else "",
        "created_at": datetime.now(timezone(timedelta(hours=9))).isoformat()
    }
    
    # DB 제약조건 회피 처리를 위해 ai_response 번역이 일어나기 전 원문 저장 (ai_response is the english generation generated by llms)
    # await asyncio.to_thread: 스레드 풀에서 실행(이벤트 루프 비블로킹) + await으로 완료 보장(end_session race condition 방지)
    await asyncio.to_thread(save_chat_log_db, chat_log_payload)
    
    translated_propositions = [await translate_en_to_ko(p, language) for p in propositions]
    
    for expert in expert_results:
        raw_feedback = expert.get("feedback")
        if isinstance(raw_feedback, dict):
            # JSON 객체인 경우 실제 텍스트 피드백만 추출
            actual_text = raw_feedback.get("feedback", raw_feedback.get("weakest_point", ""))
            if actual_text:
                expert["feedback"] = await translate_en_to_ko(actual_text, language)
            else:
                expert["feedback"] = ""
        elif isinstance(raw_feedback, str):
            # 이미 문자열인 경우 그대로 번역
            expert["feedback"] = await translate_en_to_ko(raw_feedback, language)
            
    if scaffold_plan:
        if scaffold_plan.get("message"):
            scaffold_plan["message"] = await translate_en_to_ko(scaffold_plan["message"], language)
        if scaffold_plan.get("definition"):
            scaffold_plan["definition"] = await translate_en_to_ko(scaffold_plan["definition"], language)

    return {
        "atomic_propositions": translated_propositions,
        "expert_average_score": raw_avg_score,
        "is_contradiction_override": is_contradiction,
        "expert_feedback": expert_results,
        "is_fallback": any_fallback,
        "moderator_decision": {
            "status": moderator_action,
            "lowest_performing_area": lowest_persona,
            "scaffold_plan": scaffold_plan
        }
    }

@router.post("/end_session")
async def end_session(request: EndSessionRequest, current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("user_id", current_user.get("id"))
    language = request.language or "ko"
    
    sess_res = await db(lambda: supabase.table("sessions").select("*").eq("session_id", int(request.session_id)).execute())
    if not sess_res.data:
        raise HTTPException(status_code=404, detail="Invalid Session ID.")
    session = sess_res.data[0]
    
    if session["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this session.")
        
    await db(lambda: supabase.table("sessions").update({"status": "ENDED"}).eq("session_id", session["session_id"]).execute())
        
    nudge_count = session["idk_count"]
    logs_res = await db(lambda: supabase.table("chat_logs").select("*").eq("session_id", session["session_id"]).order("turn_number").execute())
    
    academic_scores = []
    market_scores = []
    macro_scores = []
    
    for log in logs_res.data:
        academic_scores.append(float(log["score_academic"] or 0) * 100)
        market_scores.append(float(log["score_market"] or 0) * 100)
        macro_scores.append(float(log["score_macro"] or 0) * 100)
    last_academic = 0.0
    last_market = 0.0
    last_macro = 0.0
    
    # Iterate backwards to find the last non-zero score (ignore 0.0 from scaffolding/contradiction)
    for acad, mkt, mac in reversed(list(zip(academic_scores, market_scores, macro_scores))):
        if acad > 0 or mkt > 0 or mac > 0:
            last_academic = acad
            last_market = mkt
            last_macro = mac
            break
            
    latest_avg = (last_academic + last_market + last_macro) / 3.0
    
    # ── 스캐폴딩 단계별 사용 횟수 집계 ─────────────────────────────────
    scaffold_step_labels = {
        "Sub-concept Nudge": "nudge",
        "Concept Explanation": "concept",
        "Fill-in-the-Blank": "fill_blank",
        "Solution Reveal": "reveal",
        "Counterfactual Probe": "nudge"
    }
    scaffolding_summary = {"nudge": 0, "concept": 0, "fill_blank": 0, "reveal": 0, "total": 0}
    try:
        scaffold_logs = await db(lambda: supabase.table("chat_logs") \
            .select("scaffold_step") \
            .eq("session_id", session["session_id"]) \
            .not_.is_("scaffold_step", "null") \
            .execute())
        for log in scaffold_logs.data:
            step = log.get("scaffold_step")
            key = scaffold_step_labels.get(step)
            if key:
                scaffolding_summary[key] += 1
                scaffolding_summary["total"] += 1
    except Exception:
        # scaffold_step 컬럼이 DB에 아직 없는 경우 graceful fallback
        scaffolding_summary["total"] = nudge_count
        
    if scaffolding_summary["total"] == 0:
        final_score = latest_avg + 50
        educational_insights = f"Excellent! Your base average was {latest_avg:.1f}. You earned a 50-point bonus for completing without help, making your final score {final_score:.1f}!"
    else:
        final_score = latest_avg
        educational_insights = f"Your score is {latest_avg:.1f}. You received help from the agent {scaffolding_summary['total']} times. Try harder next time for a bonus score!"
        
    # 과거 ENDED 된 동종 concept 이력이 있는지 검사
    past_sessions_res = await db(lambda: supabase.table("sessions").select("session_id").eq("user_id", user_id).eq("concept_id", session["concept_id"]).eq("status", "ENDED").execute())
    is_first_time = len(past_sessions_res.data) <= 1  # 현재 방금 ENDED 시킨 세션이 포함되어 있으므로 <= 1

    # Exclude scaffolding turns (score=0) from the radar chart to avoid dragging down the cumulative total
    valid_logs = [log for log in logs_res.data if (float(log["score_academic"] or 0) + float(log["score_market"] or 0) + float(log["score_macro"] or 0)) > 0]
    radar_academic = [float(log["score_academic"] or 0) * 100 for log in valid_logs]
    radar_market = [float(log["score_market"] or 0) * 100 for log in valid_logs]
    radar_macro = [float(log["score_macro"] or 0) * 100 for log in valid_logs]
    radar_payload = {"Academic": radar_academic, "Market": radar_market, "Macro": radar_macro}

    translated_insights = await translate_en_to_ko(educational_insights, language)
    translated_message = await translate_en_to_ko("Session terminated successfully.", language)

    # ── 최종 리포트 반환 ─────────────────────────────────────────────
    return {
        "message": translated_message,
        "educational_insights": translated_insights,
        "is_first_time": is_first_time,
        "growth_visualization": radar_payload,
        "scaffolding_summary": scaffolding_summary,
        "base_score": latest_avg,
        "final_score": final_score
    }

@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    
    try:
        # 1. 초기 인증 및 데이터 수신
        data = await websocket.receive_json()
        token = data.get("token")
        session_id = data.get("session_id")
        user_answer = data.get("user_answer")
        language = data.get("language", "ko")
        
        if not token or not session_id or not user_answer:
            await websocket.send_json({"type": "error", "message": "Missing required fields (token, session_id, user_answer)."})
            await websocket.close(code=1008)
            return
            
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username = payload.get("sub")
            if not username:
                raise ValueError("Invalid token")
        except Exception as e:
            await websocket.send_json({"type": "error", "message": "Authentication failed."})
            await websocket.close(code=1008)
            return
            
        user_res = await db(lambda: supabase.table("users").select("*").eq("username", username).execute())
        if not user_res.data:
            await websocket.send_json({"type": "error", "message": "User not found."})
            await websocket.close(code=1008)
            return
            
        current_user = user_res.data[0]
        user_id = current_user.get("user_id", current_user.get("id"))
        
        # 2. 세션 및 개념 데이터 조회
        await websocket.send_json({"type": "status", "message": await translate_en_to_ko("🔍 Checking session data...", language)})
        
        sess_res = await db(lambda: supabase.table("sessions").select("*").eq("session_id", int(session_id)).execute())
        if not sess_res.data:
            await websocket.send_json({"type": "error", "message": "Invalid Session ID."})
            await websocket.close()
            return
        session = sess_res.data[0]
        
        if session["user_id"] != user_id:
            await websocket.send_json({"type": "error", "message": "Not authorized to access this session."})
            await websocket.close()
            return
            
        db_concept_id = session["concept_id"]
        concept_res = await db(lambda: supabase.table("concepts").select("*").eq("concept_id", db_concept_id).execute())
        if not concept_res.data:
            await websocket.send_json({"type": "error", "message": "Target Concept is not supported."})
            await websocket.close()
            return
            
        concept_data = concept_res.data[0]
        concept_name = concept_data["name"]
        definition = concept_data["definition"]
        acceptable_extensions = concept_data.get("acceptable_extensions", "")
        
        eval_user_answer = await translate_ko_to_en(user_answer, language)
        # Check only original input for keywords to prevent translation false positives
        is_give_up = any(kw in user_answer.lower() for kw in GIVE_UP_KEYWORDS)

        # ── 1. 보안 가드레일 ──────────────────────────────────────────
        blocked_msg = await run_guardrail_ws(eval_user_answer, user_id=str(user_id))
        if blocked_msg:
            await websocket.send_json({"type": "error", "message": blocked_msg})
            await websocket.close(code=1008)
            return

        # ── 1-1. 단답형 감지 — 서술형 재유도 (3단계 빈칸채우기 시에는 단답형 허용) ─────────
        if not is_give_up and session.get("idk_count", 0) != 3 and is_short_answer(user_answer):
            reprompt_msg = await translate_en_to_ko(_SHORT_ANSWER_REPROMPT_EN, language)
            await websocket.send_json({
                "type": "final_result",
                "data": {
                    "atomic_propositions": [],
                    "expert_average_score": 0.0,
                    "is_contradiction_override": False,
                    "expert_feedback": [],
                    "is_fallback": False,
                    "is_short_answer": True,
                    "moderator_decision": {
                        "status": "short_answer",
                        "lowest_performing_area": "N/A",
                        "scaffold_plan": {
                            "step": "Short Answer Reprompt",
                            "message": reprompt_msg
                        }
                    }
                }
            })
            await asyncio.sleep(1)
            await websocket.close()
            return

        # 턴 수 계산
        logs_count_res = await db(lambda: supabase.table("chat_logs").select("log_id", count="exact").eq("session_id", session["session_id"]).execute())
        turn_number = logs_count_res.count + 1 if logs_count_res.count is not None else 1

        # ── 2. 시맨틱 캐시 조회 ──────────────────────────────────────────
        if not is_give_up and turn_number == 1:
            cached_response = await get_cached_response(concept_name, eval_user_answer)
            if cached_response:
                print(f"✅ [WS Chat] 시맨틱 캐시 히트! 캐시된 응답 반환", flush=True)
                translated_cached = await translate_en_to_ko(cached_response, language)
                await websocket.send_json({
                    "type": "final_result",
                    "data": {
                        "atomic_propositions": ["(Served from semantic cache)"],
                        "expert_average_score": 0.0,
                        "is_contradiction_override": False,
                        "expert_feedback": [],
                        "is_fallback": False,
                        "from_cache": True,
                        "moderator_decision": {
                            "status": "proceed",
                            "lowest_performing_area": "N/A",
                            "scaffold_plan": {
                                "step": "Guidance Prompt",
                                "message": translated_cached
                            }
                        }
                    }
                })
                await asyncio.sleep(1)
                await websocket.close()
                return

        await websocket.send_json({"type": "status", "message": await translate_en_to_ko("🌐 Searching Knowledge Graph & News...", language)})
        
        # ── 히스토리를 gather 전에 먼저 조회 — last_question + used_urls를 gather에 전달 ─────────────
        try:
            history_res = await db(lambda: supabase.table("chat_logs") \
                .select("turn_number, user_message, ai_response, scaffold_step, news_urls, selected_agent, turn_summary") \
                .eq("session_id", session["session_id"]) \
                .order("turn_number", desc=False) \
                .execute())
        except Exception as e:
            print(f"[Warning] 'turn_summary' 컬럼 조회 실패. 일반 조회로 폴백합니다: {e}")
            history_res = await db(lambda: supabase.table("chat_logs") \
                .select("turn_number, user_message, ai_response, scaffold_step, news_urls, selected_agent") \
                .eq("session_id", session["session_id"]) \
                .order("turn_number", desc=False) \
                .execute())

        full_history = history_res.data
        turn_summaries = []
        for log in full_history:
            summary = log.get("turn_summary")
            if summary:
                turn_summaries.append(f"[Turn {log['turn_number']}] {summary}")
            else:
                turn_summaries.append(f"[Turn {log['turn_number']}] (No summary available)")

        RECENT_N = 3

        def format_full(logs):
            formatted = {}
            for log in logs:
                formatted[f"turn_{log['turn_number']}"] = {
                    "user_answer": log.get("user_message") or "",
                    "final_synthesis": log.get("ai_response") or "",
                    "scaffold_step": log.get("scaffold_step") or None
                }
            return json.dumps(formatted, ensure_ascii=False, indent=2)

        if len(full_history) <= RECENT_N:
            session_context_str = format_full(full_history)
        else:
            older = turn_summaries[:-RECENT_N]
            recent = full_history[-RECENT_N:]
            session_context_str = (
                "[Past turns summary]\n" + "\n".join(older) +
                "\n\n[Recent turns]\n" + format_full(recent)
            )
        
        session_context_str = f"consecutive_high_score_count: {session.get('consecutive_high_score_count', 0)}\n\n" + session_context_str

        last_question_from_history = ""
        for log in reversed(history_res.data):
            if log.get("scaffold_step") is None:
                last_question_from_history = log.get("ai_response") or ""
                break
                
        last_selected_agent = None
        if history_res.data:
            last_selected_agent = history_res.data[-1].get("selected_agent")

        used_news_urls: set = set()
        for log in history_res.data:
            urls = log.get("news_urls")
            if not urls:
                continue
            if isinstance(urls, str):
                try:
                    urls = json.loads(urls.replace("'", '"'))
                except Exception:
                    try:
                        urls = ast.literal_eval(urls)
                    except Exception:
                        urls = [urls]
            if isinstance(urls, list):
                used_news_urls.update(urls)

        # 뉴스 + KG 병렬 gather (다음 turn 다른 기사 + last_question 키워드 적용)
        from services.llm_agent import retrieve_tavily_news_v2
        (news_context, news_urls), kg_context = await asyncio.gather(
            retrieve_tavily_news_v2(concept_name, eval_user_answer,
                                    last_question=last_question_from_history,
                                    used_urls=used_news_urls),
            retrieve_knowledge_graph(concept_name.lower())
        )

        # ── Scaffolding 답변 평가 ─────────────────────────────────────────
        # idk_count > 0 이고 give_up이 아닌 실제 답변이 들어온 경우:
        # Academic Agent로 평가 후 correct이면 정상 흐름 복귀, 아니면 다음 scaffolding 레벨로 진입
        is_scaffold_success = False
        if not is_give_up and session["idk_count"] > 0:
            print(f"\n[WS ChatRouter] 📋 Scaffolding 답변 평가 중... (idk_count={session['idk_count']})", flush=True)
            await websocket.send_json({"type": "status", "message": await translate_en_to_ko("📋 Evaluating your answer...", language)})
            
            # 직전 턴의 힌트 텍스트 가져오기
            hint_log = supabase.table("chat_logs") \
                .select("ai_response, scaffold_step") \
                .eq("session_id", session["session_id"]) \
                .not_.is_("scaffold_step", "null") \
                .order("turn_number", desc=True) \
                .limit(1).execute()
            last_hint = hint_log.data[0]["ai_response"] if hint_log.data else ""
            scaffold_step = hint_log.data[0]["scaffold_step"] if hint_log.data else ""
            
            scaffold_eval = await call_scaffold_eval(
                concept_name, definition, acceptable_extensions or "", scaffold_step, last_hint, eval_user_answer
            )
            if scaffold_eval.get("type") == "correct":
                print(f"  ✅ Scaffolding 답변 정답 인정 — idk_count 초기화, 정상 흐름으로 복귀", flush=True)
                supabase.table("sessions").update({"idk_count": 0}).eq("session_id", session["session_id"]).execute()
                is_scaffold_success = True
                
                if scaffold_step in ["Fill-in-the-Blank", "3단계 힌트", "Level 3"]:
                    import re
                    pattern = r'_{2,}|\[\s*_*\s*\]|\(\s*_*\s*\)'
                    if re.search(pattern, last_hint):
                        eval_user_answer = re.sub(pattern, eval_user_answer, last_hint, count=1)
                    else:
                        eval_user_answer = f"{last_hint} {eval_user_answer}"
            else:
                print(f"  ⚠️ Scaffolding 답변 오답 — 다음 scaffolding 레벨로 진입", flush=True)
                is_give_up = True


        initial_state = {
            "concept": concept_name,
            "user_answer": eval_user_answer,
            "definition": definition,
            "acceptable_extensions": acceptable_extensions,
            "news_context": news_context,
            "kg_context": kg_context,
            "draft_reviews": {},
            "critiques": [],
            "raw_scores": {},
            "is_contradiction": False,
            "final_synthesis": "",
            "debate_count": 0,
            "moderator_action": "",
            "consecutive_high_score_count": session.get("consecutive_high_score_count", 0),
            "hint_provided": False,
            "language": language,
            "session_context": session_context_str,
            "last_question": last_question_from_history,
            "previous_lowest_agent": last_selected_agent,
            "is_scaffold_success": is_scaffold_success,
            "scaffold_step": scaffold_step
        }
        
        await websocket.send_json({"type": "status", "message": await translate_en_to_ko("🤖 AI Agents are drafting & debating...", language)})
        
        final_state = initial_state.copy()
        
        if is_give_up:
            current_idk_count = session["idk_count"] + 1
            if current_idk_count >= 4:
                await db(lambda: supabase.table("sessions").update({"idk_count": 0}).eq("session_id", session["session_id"]).execute())
            else:
                await db(lambda: supabase.table("sessions").update({"idk_count": current_idk_count}).eq("session_id", session["session_id"]).execute())
            
            # 마지막 AI 질문 조회
            last_log = await db(lambda: supabase.table("chat_logs") \
                .select("ai_response") \
                .eq("session_id", session["session_id"]) \
                .is_("scaffold_step", "null") \
                .order("turn_number", desc=True) \
                .limit(1).execute())
            last_question = last_log.data[0]["ai_response"] if last_log.data else ""

            sys_prompt = get_recovery_prompt(concept_name, definition, acceptable_extensions, last_question, kg_context, current_idk_count,
                                              student_answer=eval_user_answer, session_context=session_context_str)

            if current_idk_count == 1:
                scaffold_step = "Sub-concept Nudge"
                scaffolding_level = 3
            elif current_idk_count == 2:
                scaffold_step = "Concept Explanation"
                scaffolding_level = 2
            elif current_idk_count == 3:
                scaffold_step = "Fill-in-the-Blank"
                scaffolding_level = 1
            else:
                scaffold_step = "Solution Reveal"
                scaffolding_level = 0
                
            scaffold_prefixes = {
                "Sub-concept Nudge": "💡 1단계 힌트: ",
                "Concept Explanation": "💡 2단계 힌트: ",
                "Fill-in-the-Blank": "💡 3단계 힌트: ",
                "Solution Reveal": "💡 정답 공개: "
            }
            prefix = scaffold_prefixes.get(scaffold_step, "")

            recovery_text = ""
            think_filter = ThinkTagStreamFilter()
            async for chunk in draft_llm.astream([SystemMessage(content=sys_prompt)]):
                if chunk.content:
                    recovery_text += chunk.content
                    filtered = think_filter.feed(chunk.content)
                    if filtered:
                        # 프론트엔드에서 레이블을 렌더링할 수 있도록 prefix 정보를 함께 전달
                        await websocket.send_json({"type": "stream", "chunk": filtered, "prefix": prefix})
            
            recovery_text = strip_think_tags(recovery_text)
            try:
                parsed = json.loads(recovery_text)
                guidance_message = parsed.get("message", recovery_text)
            except Exception:
                guidance_message = recovery_text
                
            # Prefix calculation was moved above to pass to websocket stream
            # prefix = scaffold_prefixes.get(scaffold_step, "")
            if prefix:
                guidance_message = f"{prefix}{guidance_message}"
                
            final_state["raw_scores"] = {"The Market Practitioner": 0.0, "The Macro-Connector": 0.0, "The Academic Auditor": 0.0}
            final_state["is_contradiction"] = False
            final_state["final_synthesis"] = guidance_message
            
            final_state["scaffold_plan"] = {
                "step": scaffold_step,
                "scaffolding_level": scaffolding_level,
                "message": guidance_message
            }

        else:
            if session["idk_count"] > 0:
                await db(lambda: supabase.table("sessions").update({"idk_count": 0}).eq("session_id", session["session_id"]).execute())
                
            if is_scaffold_success:
                if language == "en":
                    success_step_name = {
                        "Sub-concept Nudge": "Level 1 Hint",
                        "Concept Explanation": "Level 2 Hint",
                        "Fill-in-the-Blank": "Level 3 Hint"
                    }.get(scaffold_step, scaffold_step)
                    success_msg = f"That is correct! You have successfully completed the {success_step_name}. "
                else:
                    success_step_name = {
                        "Sub-concept Nudge": "1단계 힌트",
                        "Concept Explanation": "2단계 힌트",
                        "Fill-in-the-Blank": "3단계 힌트"
                    }.get(scaffold_step, scaffold_step)
                    success_msg = f"정답입니다! 훌륭하게 맞추셨어요. {success_step_name}를 벗어났습니다. "
                await websocket.send_json({"type": "stream", "chunk": success_msg})
                
            think_filter = ThinkTagStreamFilter()
            async for event in debate_graph.astream_events(initial_state, version="v1"):
                kind = event["event"]
                
                if kind == "on_chat_model_stream":
                    tags = event.get("tags", [])
                    if "synthesis_llm" in tags:
                        chunk = event["data"]["chunk"]
                        if chunk.content:
                            filtered = think_filter.feed(chunk.content)
                            if filtered:
                                await websocket.send_json({"type": "stream", "chunk": filtered})
                
                elif kind == "on_chain_end":
                    out = event["data"].get("output")
                    if isinstance(out, dict):
                        valid_keys = {"draft_reviews", "raw_scores", "is_contradiction", "critiques", "rebuttal_results", "final_synthesis", "debate_count", "moderator_action", "hint_provided"}
                        updates = {k: v for k, v in out.items() if k in valid_keys}
                        if updates:
                            final_state.update(updates)
                            
            if is_scaffold_success:
                if language == "en":
                    success_step_name = {
                        "Sub-concept Nudge": "Level 1 Hint",
                        "Concept Explanation": "Level 2 Hint",
                        "Fill-in-the-Blank": "Level 3 Hint"
                    }.get(scaffold_step, scaffold_step)
                    success_msg = f"That is correct! You have successfully completed the {success_step_name}. "
                else:
                    success_step_name = {
                        "Sub-concept Nudge": "1단계 힌트",
                        "Concept Explanation": "2단계 힌트",
                        "Fill-in-the-Blank": "3단계 힌트"
                    }.get(scaffold_step, scaffold_step)
                    success_msg = f"정답입니다! 훌륭하게 맞추셨어요. {success_step_name}를 벗어났습니다. "
                    
                if "final_synthesis" in final_state:
                    final_state["final_synthesis"] = success_msg + final_state["final_synthesis"]
        
        await websocket.send_json({"type": "status", "message": await translate_en_to_ko("✅ Finalizing response...", language)})
        
        expert_scores_raw = final_state.get("raw_scores", {})
        antutor_score = expert_scores_raw.get("The Academic Auditor", 0.0)
        is_contradiction = final_state.get("is_contradiction", False)
        hint_provided = final_state.get("hint_provided", False)
        
        if hint_provided:
            current_scaffold_count = session.get("scaffolding_counter", 0)
            await db(lambda: supabase.table("sessions").update({"scaffolding_counter": current_scaffold_count + 1}).eq("session_id", session["session_id"]).execute())
            
        expert_results = []
        any_fallback = False
        for persona, review in final_state.get("draft_reviews", {}).items():
            fallback_flag = review.get("is_fallback", False) if isinstance(review, dict) else False
            if fallback_flag:
                any_fallback = True
            expert_results.append({
                "persona": persona,
                "score": expert_scores_raw.get(persona, 0.75),
                "feedback": review,
                "is_fallback": fallback_flag
            })
            
        expert_scores = expert_scores_raw
        
        # save_debate_log: 로컬 파일 I/O라 치명적이진 않으나 통일성을 위해 to_thread 사용
        asyncio.create_task(asyncio.to_thread(save_debate_log,
            session_id=session["session_id"],
            concept=concept_name,
            user_answer=eval_user_answer,
            draft_reviews=final_state.get("draft_reviews", {}),
            critiques=final_state.get("critiques", []),
            final_synthesis=final_state.get("final_synthesis", "")
        ))
        
        if is_contradiction:
            antutor_score = 0.0
            propositions = ["Local LLM Blocked: Explicit contradiction found."]
            lowest_persona = "System"
        elif is_give_up:
            propositions = []
            lowest_persona = "System"
        else:
            propositions = ["(Evaluated by Multi-Agent Debate Graph)"]
            lowest_persona = min(expert_scores.keys(), key=lambda k: expert_scores[k]) if expert_scores else "System"
            
        raw_avg_score = (
            expert_scores.get("The Academic Auditor", 0) * 100 +
            expert_scores.get("The Market Practitioner", 0) * 100 +
            expert_scores.get("The Macro-Connector", 0) * 100
        ) / 3.0 if expert_scores else 0.0

        avg_score = raw_avg_score / 100

        # 1. consecutive_high_score_count 로직
        academic_score = expert_scores.get("The Academic Auditor", 0) if expert_scores else 0
        current_count = session.get("consecutive_high_score_count", 0)

        if current_count == 0:
            new_count = 1 if academic_score >= 0.5 else 0
        else:
            new_count = current_count + 1 if avg_score >= 0.6 else 1

        # 2. source_turn_count 로직
        current_source_turn = session.get("source_turn_count", 0)
        if avg_score >= 0.5:
            new_source_turn = current_source_turn + 1
        else:
            new_source_turn = current_source_turn

        await db(lambda: supabase.table("sessions").update({
            "consecutive_high_score_count": new_count,
            "source_turn_count": new_source_turn
        }).eq("session_id", session["session_id"]).execute())

        moderator_action = "proceed"
        scaffold_plan = None
        current_idk_count = session["idk_count"]
        guidance_message = ""
        
        if is_give_up:
            moderator_action = "scaffold"
            scaffold_plan = final_state.get("scaffold_plan")
            guidance_message = final_state.get("final_synthesis", "")
        else:
            # graph 내 retry_router가 retry_needed=true를 감지했으면
            # retry_node가 final_synthesis와 moderator_action="retry"를 이미 설정합니다.
            synth_mode = final_state.get("moderator_action", "proceed")

            if new_count >= 3 and avg_score >= 0.6:
                moderator_action = "suggest_termination"
                base_msg = final_state.get("final_synthesis", "Excellent job! You have fully understood this concept.")
                guidance_message = base_msg
                scaffold_plan = {"step": "Termination Suggestion", "message": guidance_message}
            elif is_contradiction or synth_mode == "retry":
                # retry_node 또는 is_contradiction → final_synthesis는 이미 올바른 retry 메시지
                moderator_action = "retry"
                guidance_message = final_state.get("final_synthesis") or "Your answer seems to contradict the core facts. Please review the concept once more or ask for a 'hint'!"
                scaffold_plan = {"step": "Retry Prompt", "message": guidance_message}
            else:
                moderator_action = "proceed"
                guidance_message = final_state.get("final_synthesis", "Good job, but let's explore more deeply.")
                scaffold_plan = {"step": "Guidance Prompt", "message": guidance_message}

        # ── 3. 시맨틱 캐시 저장 ──────────────────────────────────────────
        if not is_give_up and guidance_message and turn_number == 1:
            await save_to_cache(concept_name, eval_user_answer, guidance_message)

        chat_log_payload = {
            "session_id": session["session_id"],
            "turn_number": turn_number,
            "user_message": user_answer,
            "score_academic": antutor_score,
            "score_market": expert_scores.get("The Market Practitioner", 0),
            "score_macro": expert_scores.get("The Macro-Connector", 0),
            "selected_agent": lowest_persona,
            "ai_response": guidance_message,
            "scaffold_step": scaffold_plan.get("step") if is_give_up and scaffold_plan else None,
            "news_urls": list(news_urls) if news_urls else [],
            "turn_summary": final_state.get("turn_summary", "") if not is_give_up else "",
            "created_at": datetime.now(timezone(timedelta(hours=9))).isoformat()
        }
        
        # await asyncio.to_thread: 이벤트 루프 비블로킹 + 완료 보장 (end_session race condition 방지)
        await asyncio.to_thread(save_chat_log_db, chat_log_payload)

        
        translated_propositions = [await translate_en_to_ko(p, language) for p in propositions]
        for expert in expert_results:
            raw_feedback = expert.get("feedback")
            if isinstance(raw_feedback, dict):
                actual_text = raw_feedback.get("feedback", raw_feedback.get("weakest_point", ""))
                expert["feedback"] = await translate_en_to_ko(actual_text, language) if actual_text else ""
            elif isinstance(raw_feedback, str):
                expert["feedback"] = await translate_en_to_ko(raw_feedback, language)
                
        if scaffold_plan:
            if scaffold_plan.get("message"):
                scaffold_plan["message"] = await translate_en_to_ko(scaffold_plan["message"], language)
            if scaffold_plan.get("definition"):
                scaffold_plan["definition"] = await translate_en_to_ko(scaffold_plan["definition"], language)

        await websocket.send_json({
            "type": "final_result",
            "data": {
                "atomic_propositions": translated_propositions,
                "expert_average_score": raw_avg_score,
                "is_contradiction_override": is_contradiction,
                "expert_feedback": expert_results,
                "is_fallback": any_fallback,
                "moderator_decision": {
                    "status": moderator_action,
                    "lowest_performing_area": lowest_persona,
                    "scaffold_plan": scaffold_plan
                }
            }
        })
        
        await asyncio.sleep(1)
        await websocket.close()
        
    except WebSocketDisconnect:
        print("WebSocket client disconnected")
    except Exception as e:
        print(f"WebSocket Error: {e}")
        try:
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.send_json({"type": "error", "message": str(e)})
                await websocket.close(code=1011)
        except Exception:
            pass
