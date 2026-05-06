from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState
import jwt
import asyncio

from schemas import ChatRequest, EndSessionRequest, ResumeDecisionRequest
from database import supabase
from dependencies import get_current_user
from config import GIVE_UP_KEYWORDS, SECRET_KEY, ALGORITHM
from services.llm_agent import (
    retrieve_news_rag,
    retrieve_knowledge_graph
)
from multi_agent.graph import debate_graph
from services.translator import translate_en_to_ko, translate_ko_to_en
from datetime import datetime
import json
import os
from multi_agent.llm_config import draft_llm
from multi_agent.prompts import RECOVERY_NUDGE_PROMPT, RECOVERY_FILL_BLANK_PROMPT
from langchain_core.messages import SystemMessage
import json

def get_recovery_prompt(concept_name, ground_truth, kg_context, idk_count):
    if idk_count == 1:
        return RECOVERY_NUDGE_PROMPT.format(concept_name=concept_name, ground_truth=ground_truth, kg_context=kg_context)
    else:
        return RECOVERY_FILL_BLANK_PROMPT.format(concept_name=concept_name, ground_truth=ground_truth)

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
    response = supabase.table("concepts").select("*").execute()
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
async def start_session(concept: str, current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    
    # 1. 지원하는 개념 DB 확인
    target_concept = await get_concept_by_term(concept)
    if not target_concept:
        raise HTTPException(status_code=404, detail="Target Concept is not supported.")
        
    db_concept_id = target_concept["concept_id"]
    actual_concept_name = target_concept["name"]
    initial_question_korean = await translate_en_to_ko(f"How would you explain {actual_concept_name}?")
        
    # 2. 동일 개념 과거 완료/학습 이력 확인
    resume_available = False
    last_ai_response = ""
    
    prev_sessions = supabase.table("sessions").select("session_id").eq("user_id", user_id).eq("concept_id", db_concept_id).execute()
    if prev_sessions.data:
        session_ids = [s["session_id"] for s in prev_sessions.data]
        logs_res = supabase.table("chat_logs").select("ai_response").in_("session_id", session_ids).order("created_at", desc=True).limit(1).execute()
        if logs_res.data and logs_res.data[0].get("ai_response"):
            resume_available = True
            last_ai_response = await translate_en_to_ko(logs_res.data[0]["ai_response"])

    # 3. 만약 이력이 있다면, 세션을 미리 생성하지 않고 "재개 여부" 정보만 반환
    if resume_available:
        resume_prompt = await translate_en_to_ko("이전 학습의 마지막 질문부터 이어서 학습하시겠습니까, 아니면 처음부터 다시 학습하시겠습니까?")
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
        "status": "IN_PROGRESS"
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
    user_id = current_user["user_id"]
    concept = request.concept
    decision = request.decision # "resume" or "fresh"
    
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
        "status": "IN_PROGRESS"
    }
    insert_res = supabase.table("sessions").insert(new_session).execute()
    session_id = str(insert_res.data[0]["session_id"])
    
    # 3. 결정에 따른 첫 질문 결정
    if decision == "resume":
        prev_sessions = supabase.table("sessions").select("session_id").eq("user_id", user_id).eq("concept_id", db_concept_id).execute()
        # 현재 생성한 세션 제외
        other_session_ids = [s["session_id"] for s in prev_sessions.data if str(s["session_id"]) != session_id]
        
        logs_res = supabase.table("chat_logs").select("ai_response").in_("session_id", other_session_ids).order("created_at", desc=True).limit(1).execute()
        
        if logs_res.data and logs_res.data[0].get("ai_response"):
            question = await translate_en_to_ko(logs_res.data[0]["ai_response"])
        else:
            question = await translate_en_to_ko(f"How would you explain {actual_concept_name}?")
    else:
        question = await translate_en_to_ko(f"How would you explain {actual_concept_name}?")
        
    return {
        "session_id": session_id,
        "question": question
    }

@router.post("/chat")
async def chat(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    print(f"\n[DEBUG] 📩 유저로부터 /chat 요청 도착! (답변: {request.user_answer[:30]}...)", flush=True)
    user_id = current_user["user_id"]
    
    sess_res = supabase.table("sessions").select("*").eq("session_id", int(request.session_id)).execute()
    if not sess_res.data:
        raise HTTPException(status_code=404, detail="Invalid Session ID.")
    session = sess_res.data[0]
    
    if session["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this session.")
        
    db_concept_id = session["concept_id"]
    concept_res = supabase.table("concepts").select("*").eq("concept_id", db_concept_id).execute()
    if not concept_res.data:
        raise HTTPException(status_code=404, detail="Target Concept is not supported.")
    concept_data = concept_res.data[0]
    concept_name = concept_data["name"]
    ground_truth = concept_data["definition"]
    
    eval_user_answer = await translate_ko_to_en(request.user_answer)
    # Check both original (Korean) and translated (English) for keywords
    is_give_up = any(kw in request.user_answer.lower() or kw in eval_user_answer.lower() for kw in GIVE_UP_KEYWORDS)
    is_contradiction = False
    
    any_fallback = False
    if is_give_up:
        antutor_score = 0.0
        expert_scores = {"The Market Practitioner": 0.0, "The Macro-Connector": 0.0, "The Academic Auditor": 0.0}
        propositions = []
        expert_results = [{"persona": "System", "score": 0.0, "feedback": "User requested help."}]
        lowest_persona = "System"
    else:
        propositions = ["(Evaluated by Multi-Agent Debate Graph)"]
        
        news_context, kg_context = await asyncio.gather(
            retrieve_news_rag(concept_name),
            retrieve_knowledge_graph(concept_name.lower())
        )

        initial_state = {
            "concept": concept_name,
            "user_answer": eval_user_answer,
            "ground_truth": ground_truth,
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
            "hint_provided": False
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
            supabase.table("sessions").update({"scaffolding_counter": current_scaffold_count + 1}).eq("session_id", session["session_id"]).execute()
        
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
        save_debate_log(
            session_id=session["session_id"],
            concept=concept_name,
            user_answer=eval_user_answer,
            draft_reviews=final_state["draft_reviews"],
            critiques=final_state.get("critiques", []),
            final_synthesis=final_state.get("final_synthesis", "")
        )
        
        if is_contradiction:
            antutor_score = 0.0
            propositions = ["Local LLM Blocked: Explicit contradiction found."]
            expert_results = [{"persona": "System", "score": 0.0, "feedback": "Answer contradicts the ground truth."}]
            expert_scores = {"System": 0.0, "The Market Practitioner": 0.0, "The Macro-Connector": 0.0, "The Academic Auditor": 0.0}
            lowest_persona = "System"
        else:
            lowest_persona = min(expert_scores.keys(), key=lambda k: expert_scores[k])
        
    raw_avg_score = (
        expert_scores.get("The Academic Auditor", 0) * 100 +
        expert_scores.get("The Market Practitioner", 0) * 100 +
        expert_scores.get("The Macro-Connector", 0) * 100
    ) / 3.0

    moderator_action = "proceed"
    scaffold_plan = None
    
    current_idk_count = session["idk_count"]
    
    guidance_message = "" # DB 저장을 위해 기본값 설정
    
    if is_give_up:
        current_idk_count += 1
        supabase.table("sessions").update({"idk_count": current_idk_count}).eq("session_id", session["session_id"]).execute()
        moderator_action = "scaffold"
        if current_idk_count == 1:
            scaffold_step = "Sub-concept Nudge"
        else:
            scaffold_step = "Fill-in-the-Blank"
            
        sys_prompt = get_recovery_prompt(concept_name, ground_truth, kg_context, current_idk_count)
        
        # 동기 블록 내에서 ainvoke를 호출해야 하므로 asyncio 이벤트 루프 또는 await 사용 필요
        # wait! 이 함수는 POST /chat (async def) 내부입니다. await 가능.
        res = await draft_llm.ainvoke([SystemMessage(content=sys_prompt)])
        
        try:
            parsed = json.loads(res.content)
            guidance_message = parsed.get("message", res.content)
        except Exception:
            guidance_message = res.content
            
        scaffold_plan = {
            "step": scaffold_step,
            "message": guidance_message
        }
    else:
        if raw_avg_score >= 85:
            moderator_action = "suggest_termination"
            guidance_message = "You have achieved a high level of mastery. Would you like to terminate the session? (Yes/No)"
            scaffold_plan = {
                "step": "Termination Suggestion",
                "message": guidance_message
            }
        elif is_contradiction:
            moderator_action = "retry"
            guidance_message = "Your answer seems to contradict the core facts. Please review the concept once more or ask for a 'hint'!"
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

    # 현재 턴 수 계산
    logs_count_res = supabase.table("chat_logs").select("log_id", count="exact").eq("session_id", session["session_id"]).execute()
    turn_number = logs_count_res.count + 1 if logs_count_res.count is not None else 1

    chat_log_payload = {
        "session_id": session["session_id"],
        "turn_number": turn_number,
        "user_message": request.user_answer,
        "score_academic": antutor_score,
        "score_market": expert_scores.get("The Market Practitioner", 0),
        "score_macro": expert_scores.get("The Macro-Connector", 0),
        "selected_agent": lowest_persona,
        "ai_response": guidance_message
    }
    
    # DB 제약조건 회피 처리를 위해 ai_response 번역이 일어나기 전 원문 저장 (ai_response is the english generation generated by llms)
    supabase.table("chat_logs").insert(chat_log_payload).execute()
    
    translated_propositions = [await translate_en_to_ko(p) for p in propositions]
    
    for expert in expert_results:
        raw_feedback = expert.get("feedback")
        if isinstance(raw_feedback, dict):
            # JSON 객체인 경우 실제 텍스트 피드백만 추출
            actual_text = raw_feedback.get("feedback", "")
            if actual_text:
                expert["feedback"] = await translate_en_to_ko(actual_text)
            else:
                expert["feedback"] = ""
        elif isinstance(raw_feedback, str):
            # 이미 문자열인 경우 그대로 번역
            expert["feedback"] = await translate_en_to_ko(raw_feedback)
            
    if scaffold_plan:
        if scaffold_plan.get("message"):
            scaffold_plan["message"] = await translate_en_to_ko(scaffold_plan["message"])
        if scaffold_plan.get("definition"):
            scaffold_plan["definition"] = await translate_en_to_ko(scaffold_plan["definition"])

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
    user_id = current_user["user_id"]
    
    sess_res = supabase.table("sessions").select("*").eq("session_id", int(request.session_id)).execute()
    if not sess_res.data:
        raise HTTPException(status_code=404, detail="Invalid Session ID.")
    session = sess_res.data[0]
    
    if session["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this session.")
        
    supabase.table("sessions").update({"status": "ENDED"}).eq("session_id", session["session_id"]).execute()
        
    nudge_count = session["idk_count"]
    logs_res = supabase.table("chat_logs").select("*").eq("session_id", session["session_id"]).order("turn_number").execute()
    
    academic_scores = []
    market_scores = []
    macro_scores = []
    
    for log in logs_res.data:
        academic_scores.append(float(log["score_academic"] or 0) * 100)
        market_scores.append(float(log["score_market"] or 0) * 100)
        macro_scores.append(float(log["score_macro"] or 0) * 100)
        
    last_academic = academic_scores[-1] if academic_scores else 0
    last_market = market_scores[-1] if market_scores else 0
    last_macro = macro_scores[-1] if macro_scores else 0
    
    latest_avg = (last_academic + last_market + last_macro) / 3.0
    
    if nudge_count == 0:
        final_score = latest_avg * 1.5
        educational_insights = f"Excellent! Your base average was {latest_avg:.1f}. You earned a 1.5x bonus for completing without help, making your final score {final_score:.1f}!"
    else:
        final_score = latest_avg
        educational_insights = f"Your score is {latest_avg:.1f}. You received help from the agent {nudge_count} times. Try harder next time for a bonus score!"
        
    # 과거 ENDED 된 동종 concept 이력이 있는지 검사
    past_sessions_res = supabase.table("sessions").select("session_id").eq("user_id", user_id).eq("concept_id", session["concept_id"]).eq("status", "ENDED").execute()
    is_first_time = len(past_sessions_res.data) <= 1 # 현재 방금 ENDED 시킨 세션이 포함되어 있으므로 <= 1
    
    radar_payload = {"Academic": academic_scores, "Market": market_scores, "Macro": macro_scores}
    
    translated_insights = await translate_en_to_ko(educational_insights)
    translated_message = await translate_en_to_ko("Session terminated successfully.")
    
    return {
        "message": translated_message,
        "educational_insights": translated_insights,
        "is_first_time": is_first_time,
        "growth_visualization": radar_payload
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
            
        user_res = supabase.table("users").select("*").eq("username", username).execute()
        if not user_res.data:
            await websocket.send_json({"type": "error", "message": "User not found."})
            await websocket.close(code=1008)
            return
            
        current_user = user_res.data[0]
        user_id = current_user["user_id"]
        
        # 2. 세션 및 개념 데이터 조회
        await websocket.send_json({"type": "status", "message": "🔍 Checking session data..."})
        
        sess_res = supabase.table("sessions").select("*").eq("session_id", int(session_id)).execute()
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
        concept_res = supabase.table("concepts").select("*").eq("concept_id", db_concept_id).execute()
        if not concept_res.data:
            await websocket.send_json({"type": "error", "message": "Target Concept is not supported."})
            await websocket.close()
            return
            
        concept_data = concept_res.data[0]
        concept_name = concept_data["name"]
        ground_truth = concept_data["definition"]
        
        eval_user_answer = await translate_ko_to_en(user_answer)
        is_give_up = any(kw in user_answer.lower() or kw in eval_user_answer.lower() for kw in GIVE_UP_KEYWORDS)
        
        await websocket.send_json({"type": "status", "message": "🌐 Searching Knowledge Graph & News..."})
        
        news_context, kg_context = await asyncio.gather(
            retrieve_news_rag(concept_name),
            retrieve_knowledge_graph(concept_name.lower())
        )
        
        initial_state = {
            "concept": concept_name,
            "user_answer": eval_user_answer,
            "ground_truth": ground_truth,
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
            "hint_provided": False
        }
        
        await websocket.send_json({"type": "status", "message": "🤖 AI Agents are drafting & debating..."})
        
        final_state = None
        
        if is_give_up:
            current_idk_count = session["idk_count"] + 1
            supabase.table("sessions").update({"idk_count": current_idk_count}).eq("session_id", session["session_id"]).execute()
            
            sys_prompt = get_recovery_prompt(concept_name, ground_truth, kg_context, current_idk_count)
            
            recovery_text = ""
            async for chunk in draft_llm.astream([SystemMessage(content=sys_prompt)]):
                if chunk.content:
                    recovery_text += chunk.content
                    await websocket.send_json({"type": "stream", "chunk": chunk.content})
            
            try:
                parsed = json.loads(recovery_text)
                guidance_message = parsed.get("message", recovery_text)
            except Exception:
                guidance_message = recovery_text
                
            final_state = initial_state
            final_state["raw_scores"] = {"The Market Practitioner": 0.0, "The Macro-Connector": 0.0, "The Academic Auditor": 0.0}
            final_state["is_contradiction"] = False
            final_state["final_synthesis"] = guidance_message
            
            if current_idk_count == 1:
                scaffold_step = "Sub-concept Nudge"
            else:
                scaffold_step = "Fill-in-the-Blank"
                
            final_state["scaffold_plan"] = {
                "step": scaffold_step,
                "message": guidance_message
            }
        else:
            async for event in debate_graph.astream_events(initial_state, version="v1"):
                kind = event["event"]
                
                if kind == "on_chat_model_stream":
                    tags = event.get("tags", [])
                    if "synthesis_llm" in tags:
                        chunk = event["data"]["chunk"]
                        if chunk.content:
                            await websocket.send_json({"type": "stream", "chunk": chunk.content})
                
                elif kind == "on_chain_end":
                    if event["name"] == "LangGraph":
                        final_state = event["data"]["output"]
        
        await websocket.send_json({"type": "status", "message": "✅ Finalizing response..."})
        
        expert_scores_raw = final_state.get("raw_scores", {})
        antutor_score = expert_scores_raw.get("The Academic Auditor", 0.0)
        is_contradiction = final_state.get("is_contradiction", False)
        hint_provided = final_state.get("hint_provided", False)
        
        if hint_provided:
            current_scaffold_count = session.get("scaffolding_counter", 0)
            supabase.table("sessions").update({"scaffolding_counter": current_scaffold_count + 1}).eq("session_id", session["session_id"]).execute()
            
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
        
        save_debate_log(
            session_id=session["session_id"],
            concept=concept_name,
            user_answer=eval_user_answer,
            draft_reviews=final_state.get("draft_reviews", {}),
            critiques=final_state.get("critiques", []),
            final_synthesis=final_state.get("final_synthesis", "")
        )
        
        if is_contradiction:
            antutor_score = 0.0
            propositions = ["Local LLM Blocked: Explicit contradiction found."]
            expert_results = [{"persona": "System", "score": 0.0, "feedback": "Answer contradicts the ground truth."}]
            expert_scores = {"System": 0.0, "The Market Practitioner": 0.0, "The Macro-Connector": 0.0, "The Academic Auditor": 0.0}
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

        moderator_action = "proceed"
        scaffold_plan = None
        current_idk_count = session["idk_count"]
        guidance_message = ""
        
        if is_give_up:
            moderator_action = "scaffold"
            scaffold_plan = final_state.get("scaffold_plan")
            guidance_message = final_state.get("final_synthesis", "")
        else:
            if raw_avg_score >= 85:
                moderator_action = "suggest_termination"
                guidance_message = "You have achieved a high level of mastery. Would you like to terminate the session? (Yes/No)"
                scaffold_plan = {"step": "Termination Suggestion", "message": guidance_message}
            elif is_contradiction:
                moderator_action = "retry"
                guidance_message = "Your answer seems to contradict the core facts. Please review the concept once more or ask for a 'hint'!"
                scaffold_plan = {"step": "Retry Prompt", "message": guidance_message}
            else:
                moderator_action = "proceed"
                guidance_message = final_state.get("final_synthesis", "Good job, but let's explore more deeply.")
                scaffold_plan = {"step": "Guidance Prompt", "message": guidance_message}

        logs_count_res = supabase.table("chat_logs").select("log_id", count="exact").eq("session_id", session["session_id"]).execute()
        turn_number = logs_count_res.count + 1 if logs_count_res.count is not None else 1

        chat_log_payload = {
            "session_id": session["session_id"],
            "turn_number": turn_number,
            "user_message": user_answer,
            "score_academic": antutor_score,
            "score_market": expert_scores.get("The Market Practitioner", 0),
            "score_macro": expert_scores.get("The Macro-Connector", 0),
            "selected_agent": lowest_persona,
            "ai_response": guidance_message
        }
        
        supabase.table("chat_logs").insert(chat_log_payload).execute()
        
        translated_propositions = [await translate_en_to_ko(p) for p in propositions]
        for expert in expert_results:
            raw_feedback = expert.get("feedback")
            if isinstance(raw_feedback, dict):
                actual_text = raw_feedback.get("feedback", "")
                expert["feedback"] = await translate_en_to_ko(actual_text) if actual_text else ""
            elif isinstance(raw_feedback, str):
                expert["feedback"] = await translate_en_to_ko(raw_feedback)
                
        if scaffold_plan:
            if scaffold_plan.get("message"):
                scaffold_plan["message"] = await translate_en_to_ko(scaffold_plan["message"])
            if scaffold_plan.get("definition"):
                scaffold_plan["definition"] = await translate_en_to_ko(scaffold_plan["definition"])

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
