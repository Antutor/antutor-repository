from fastapi import APIRouter, Depends, HTTPException
import asyncio

from schemas import ChatRequest, EndSessionRequest
from database import supabase
from dependencies import get_current_user
from config import GIVE_UP_KEYWORDS
from services.llm_agent import (
    retrieve_news_rag,
    retrieve_knowledge_graph
)
from multi_agent.graph import debate_graph
from services.translator import translate_en_to_ko, translate_ko_to_en
from datetime import datetime
import json
import os

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

@router.get("/start/{concept}")
async def start_session(concept: str, current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    
    # 1. 지원하는 개념 DB 확인
    concept_res = supabase.table("concepts").select("*").eq("name", concept).execute()
    if not concept_res.data:
        raise HTTPException(status_code=404, detail="Target Concept is not supported.")
        
    db_concept_id = concept_res.data[0]["concept_id"]
        
    # 2. 동일 개념 과거 완료/학습 이력 확인
    resume_available = False
    last_ai_response = ""
    
    prev_sessions = supabase.table("sessions").select("session_id").eq("user_id", user_id).eq("concept_id", db_concept_id).execute()
    if prev_sessions.data:
        session_ids = [s["session_id"] for s in prev_sessions.data]
        logs_res = supabase.table("chat_logs").select("ai_response").in_("session_id", session_ids).order("created_at", desc=True).limit(1).execute()
        if logs_res.data and logs_res.data[0].get("ai_response"):
            resume_available = True
            last_ai_response = logs_res.data[0]["ai_response"]

    # 3. 신규 세션 DB 생성
    new_session = {
        "user_id": user_id,
        "concept_id": db_concept_id,
        "status": "IN_PROGRESS"
    }
    insert_res = supabase.table("sessions").insert(new_session).execute()
    session_id = str(insert_res.data[0]["session_id"]) # string formatting
    
    initial_question_korean = await translate_en_to_ko(f"How would you explain {concept}?")
    resume_prompt = await translate_en_to_ko("이전 학습의 마지막 질문부터 이어서 학습하시겠습니까, 아니면 처음부터 다시 학습하시겠습니까?") if resume_available else ""
    
    return {
        "session_id": session_id,
        "concept": concept,
        "initial_question": initial_question_korean,
        "resume_available": resume_available,
        "resume_prompt": resume_prompt,
        "last_ai_response": last_ai_response
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
    is_give_up = any(kw in eval_user_answer.lower() for kw in GIVE_UP_KEYWORDS)
    is_contradiction = False
    
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
            retrieve_knowledge_graph(concept_name)
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
            "moderator_action": ""
        }
        
        print(f"👉 [ChatRouter] 랭그래프 호출 진입 전... (RAG 완료, State 준비 완료)", flush=True)
        final_state = await debate_graph.ainvoke(initial_state)

        expert_results = []
        expert_scores_raw = final_state["raw_scores"]
        
        antutor_score = expert_scores_raw.get("The Academic Auditor", 0.0)
        is_contradiction = final_state.get("is_contradiction", False)
        
        for persona, review in final_state["draft_reviews"].items():
            expert_results.append({
                "persona": persona,
                "score": expert_scores_raw.get(persona, 0.75),
                "feedback": review
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
        
        backtrack_id = concept_data.get("backtrack_id")
        
        # backtrack_id로 실제 단어 이름(name) 조회 (만약 backtrack_id가 실제 name과 같다면 최적화 가능)
        backtrack_res = supabase.table("concepts").select("*").eq("name", backtrack_id).execute()
        if not backtrack_res.data:
            backtrack_res = supabase.table("concepts").select("*").eq("concept_id", backtrack_id).execute()
            
        backtrack_name = backtrack_res.data[0]["name"] if backtrack_res.data else backtrack_id
        
        if current_idk_count == 1:
            backtrack_question = f"Before we proceed, can you explain what {backtrack_name} is?"
            guidance_message = backtrack_question
            scaffold_plan = {
                "step": "Sub-concept Nudge",
                "message": backtrack_question
            }
        else:
            # 2번 연속 idk 시 (기본 개념 사전 보여줌)
            dict_content = backtrack_res.data[0].get("dict_content", "") if backtrack_res.data else ""
            
            guidance_message = "It looks like you need help. Here is the concept dictionary link."
            scaffold_plan = {
                "step": "Concept Dictionary Link",
                "message": guidance_message,
                "dictionary_link": f"/dictionary/{backtrack_name}",
                "definition": dict_content
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
        if expert.get("feedback"):
            expert["feedback"] = await translate_en_to_ko(expert["feedback"])
            
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
