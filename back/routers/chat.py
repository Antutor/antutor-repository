from fastapi import APIRouter, Depends, HTTPException
import asyncio
import uuid

from schemas import ChatRequest, EndSessionRequest
from database import session_memory, users_db
from dependencies import get_current_user
from config import TARGET_CONCEPTS, CONCEPT_DICTIONARY, GIVE_UP_KEYWORDS
from services.llm_agent import (
    evaluate_academic_auditor,
    retrieve_news_rag,
    retrieve_knowledge_graph,
    call_expert_agent,
    generate_moderator_guidance_message
)
from services.translator import translate_en_to_ko, translate_ko_to_en

router = APIRouter()

@router.get("/start/{concept}")
async def start_session(concept: str, current_user: str = Depends(get_current_user)):
    if concept not in TARGET_CONCEPTS:
        raise HTTPException(status_code=404, detail="Target Concept is not supported.")
    
    session_id = str(uuid.uuid4())
    
    session_memory[session_id] = {
        "user_id": current_user,
        "concept": concept,
        "scaffold_level": 0,  
        "scaffold_count": 0,
        "history": [],
        "radar_data": {"Academic": [], "Market": [], "Macro": []}
    }
    
    return {
        "session_id": session_id,
        "concept": concept,
        "initial_question": await translate_en_to_ko(TARGET_CONCEPTS[concept]["initial_question"])
    }

@router.post("/chat")
async def chat(request: ChatRequest, current_user: str = Depends(get_current_user)):
    if request.session_id not in session_memory:
        raise HTTPException(status_code=404, detail="Invalid Session ID.")
        
    session = session_memory[request.session_id]
    if session["user_id"] != current_user:
        raise HTTPException(status_code=403, detail="Not authorized to access this session.")
        
    concept = request.concept
    ground_truth = TARGET_CONCEPTS[concept]["definition"]
    
    # === 사용자 입력값을 AI 처리를 위해 영어로 번역 ===
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
        academic_result = await evaluate_academic_auditor(concept, eval_user_answer, ground_truth)
        is_contradiction = academic_result.get("is_contradiction", False)
        antutor_score = academic_result.get("score", 0.0)
        
        if is_contradiction:
            antutor_score = 0.0
            propositions = ["Local LLM Blocked: Explicit contradiction found."]
            expert_results = [{"persona": "System", "score": 0.0, "feedback": "Answer contradicts the ground truth."}]
            expert_scores = {"System": 0.0, "The Market Practitioner": 0.0, "The Macro-Connector": 0.0, "The Academic Auditor": 0.0}
        else:
            propositions = ["(Atomic extraction skipped: Evaluated by LLM-as-a-judge in one go)"]
            
            news_context, kg_context = await asyncio.gather(
                retrieve_news_rag(concept),
                retrieve_knowledge_graph(concept)
            )

            tasks = [
                call_expert_agent("The Market Practitioner", concept, eval_user_answer, context=news_context),
                call_expert_agent("The Macro-Connector", concept, eval_user_answer, context=kg_context)
            ]
            
            other_expert_results = list(await asyncio.gather(*tasks))

            expert_results = [
                {"persona": "The Academic Auditor", "score": antutor_score, "feedback": academic_result.get("feedback", "")}
            ] + other_expert_results

            expert_scores_raw = {"The Academic Auditor": antutor_score}
            for res in other_expert_results:
                res["score"] = res.get("score") if res.get("score") is not None else 0.75
                expert_scores_raw[res["persona"]] = res["score"]
                    
            expert_scores = expert_scores_raw
            
        lowest_persona = min(expert_scores.keys(), key=lambda k: expert_scores[k])
        
    raw_avg_score = (
        expert_scores.get("The Academic Auditor", 0) * 100 +
        expert_scores.get("The Market Practitioner", 0) * 100 +
        expert_scores.get("The Macro-Connector", 0) * 100
    ) / 3.0

    moderator_action = "proceed"
    scaffold_plan = None
    current_scaffold_level = session["scaffold_level"]

    if is_give_up:
        session["scaffold_count"] += 1
        moderator_action = "scaffold"
        if current_scaffold_level == 0:
            session["scaffold_level"] = 1
            scaffold_plan = {
                "step": "Sub-concept Nudge",
                "message": TARGET_CONCEPTS[concept]["sub_concept_question"]
            }
        elif current_scaffold_level >= 1:
            session["scaffold_level"] = 2
            term_key = TARGET_CONCEPTS[concept]["dictionary_link"].split("/")[-1]
            dict_info = CONCEPT_DICTIONARY.get(term_key, {})
            scaffold_plan = {
                "step": "Concept Dictionary Link",
                "message": "It looks like you need help. Here is the concept dictionary link.",
                "dictionary_link": TARGET_CONCEPTS[concept]["dictionary_link"],
                "definition": dict_info.get("simple_definition", "")
            }
    else:
        if raw_avg_score >= 85:
            moderator_action = "suggest_termination"
            scaffold_plan = {
                "step": "Termination Suggestion",
                "message": "You have achieved a high level of mastery. Would you like to terminate the session? (Yes/No)"
            }
        elif is_contradiction:
            moderator_action = "retry"
            scaffold_plan = {
                "step": "Retry Prompt",
                "message": "Your answer seems to contradict the core facts. Please review the concept once more or ask for a 'hint'!"
            }
        else:
            moderator_action = "proceed"
            guidance_message = await generate_moderator_guidance_message(eval_user_answer, lowest_persona, expert_results)
            
            scaffold_plan = {
                "step": "Guidance Prompt",
                "message": guidance_message
            }

    session["radar_data"]["Academic"].append(antutor_score * 100)
    session["radar_data"]["Market"].append(expert_scores.get("The Market Practitioner", 0) * 100)
    session["radar_data"]["Macro"].append(expert_scores.get("The Macro-Connector", 0) * 100)
    
    session["history"].append({
        "user_answer": request.user_answer,
        "nli_score": antutor_score,
        "action": moderator_action
    })

    # === 통신 최말단 탈부착식 번역 계층 통과 ===
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
async def end_session(request: EndSessionRequest, current_user: str = Depends(get_current_user)):
    """
    Terminates the learning session, calculates final score including bonuses,
    and returns educational insights and growth visualization.
    """
    if request.session_id not in session_memory:
        raise HTTPException(status_code=404, detail="Invalid Session ID.")
        
    session = session_memory[request.session_id]
    if session["user_id"] != current_user:
        raise HTTPException(status_code=403, detail="Not authorized to access this session.")
        
    nudge_count = session.get("scaffold_count", 0)
    academic_scores = session["radar_data"]["Academic"]
    market_scores = session["radar_data"]["Market"]
    macro_scores = session["radar_data"]["Macro"]
    
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
        
    user_data = users_db[current_user]
    concept = session["concept"]
    completed = user_data.get("completed_concepts", [])
    
    is_first_time = concept not in completed
    if is_first_time:
        user_data["completed_concepts"].append(concept)
        
    radar_payload = session["radar_data"]
    
    # 번역 계층 통과
    translated_insights = await translate_en_to_ko(educational_insights)
    translated_message = await translate_en_to_ko("Session terminated successfully.")
    
    return {
        "message": translated_message,
        "educational_insights": translated_insights,
        "is_first_time": is_first_time,
        "growth_visualization": radar_payload
    }
