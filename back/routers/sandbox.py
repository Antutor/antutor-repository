from fastapi import APIRouter, Depends
import httpx
import json
import time
from datetime import datetime

from schemas import (
    PromptTuningSandboxRequest,
    AgentSandboxRequest,
    ModeratorSandboxRequest,
    GraphSandboxRequest,
    ScaffoldingSandboxRequest
)
from multi_agent.graph import debate_graph
from services.llm_agent import (
    retrieve_news_rag,
    retrieve_knowledge_graph,
    call_expert_agent,
    evaluate_academic_auditor,
    generate_moderator_guidance_message,
    call_scaffolding_agent
)
from services.translator import translate_ko_to_en
from config import LOCAL_LLM_MODEL, LOCAL_LLM_ENDPOINT
from dependencies import get_current_user

router = APIRouter()

def save_sandbox_log(request_data: dict, response_data: any, test_type: str = "generic"):
    import os
    
    file_path = "sandbox_logs.jsonl"
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "test_type": test_type,
        "request": request_data,
        "response": response_data
    }
    try:
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"Failed to save sandbox log: {e}")

@router.post("/ai/test/sandbox", tags=["Sandbox"])
async def ai_test_sandbox(request: PromptTuningSandboxRequest, current_user: str = Depends(get_current_user)):
    """
    프롬프트 튜닝 및 다양한 LLM 하이퍼파라미터 실험을 위한 샌드박스 API입니다.
    """
    model_name = request.model or LOCAL_LLM_MODEL
    
    messages = []
    if request.system_prompt:
        messages.append({"role": "system", "content": request.system_prompt})
    messages.append({"role": "user", "content": request.user_prompt})
    
    payload = {
        "model": model_name,
        "messages": messages,
        "options": {
            "temperature": request.temperature
        },
        "stream": False
    }
    
    if request.is_json:
        payload["format"] = "json"
        
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(LOCAL_LLM_ENDPOINT, json=payload, timeout=120.0)
            response.raise_for_status()
            data = response.json()
            
            result_content = ""
            if "message" in data:
                result_content = data["message"]["content"]
            elif "choices" in data:
                result_content = data["choices"][0]["message"]["content"]
            else:
                result_content = str(data)

            req_data = request.dict() if hasattr(request, 'dict') else request.model_dump()
            
            save_sandbox_log(req_data, result_content, "prompt_test")

            return {
                "status": "success",
                "request_settings": req_data,
                "response": result_content
            }
            
    except Exception as e:
        return {"status": "error", "detail": f"Sandbox LLM Call Error: {str(e)}"}

@router.get("/ai/test/rag/{concept}", tags=["Sandbox"])
async def test_rag_sandbox(concept: str, current_user: str = Depends(get_current_user)):
    """
    RAG(Tavily Search) 기능만 단독으로 테스트합니다.
    """
    try:
        news_context = await retrieve_news_rag(concept)
        response_data = {"status": "success", "concept": concept, "news_context": news_context}
        save_sandbox_log({"concept": concept}, response_data, "rag_test")
        return response_data
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@router.get("/ai/test/kg/{concept}", tags=["Sandbox"])
async def test_kg_sandbox(concept: str, current_user: str = Depends(get_current_user)):
    """
    지식 그래프 추출 기능만 단독으로 테스트합니다.
    """
    try:
        kg_context = await retrieve_knowledge_graph(concept)
        response_data = {"status": "success", "concept": concept, "kg_context": kg_context}
        save_sandbox_log({"concept": concept}, response_data, "kg_test")
        return response_data
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@router.post("/ai/test/agent", tags=["Sandbox"])
async def test_agent_sandbox(request: AgentSandboxRequest, current_user: str = Depends(get_current_user)):
    """
    특정 페르소나(에이전트)의 프롬프트와 평가 로직을 단독으로 테스트합니다.
    """
    try:
        persona = request.persona
        eval_user_answer = await translate_ko_to_en(request.user_answer)
        
        req_data = request.dict() if hasattr(request, 'dict') else request.model_dump()
        if persona == "The Academic Auditor":
            actual_def = request.definition or request.ground_truth
            if not actual_def:
                return {"status": "error", "detail": "definition or ground_truth is required for The Academic Auditor"}
            result = await evaluate_academic_auditor(
                concept=request.concept, 
                user_answer=eval_user_answer, 
                definition=actual_def, 
                acceptable_extensions=request.acceptable_extensions or "",
                custom_prompt=request.custom_prompt,
                model=request.model,
                temperature=request.temperature
            )
            response_data = {"status": "success", "persona": persona, "result": result}
            save_sandbox_log(req_data, response_data, "agent_test")
            return response_data
        else:
            context = request.context
            
            # 실제 RAG 파이프라인을 연동할 것인지 여부
            if request.use_real_context:
                if persona == "The Market Practitioner":
                    context = await retrieve_news_rag(request.concept)
                elif persona == "The Macro-Connector":
                    context = await retrieve_knowledge_graph(request.concept)
            
            
            result = await call_expert_agent(
                persona, 
                request.concept, 
                eval_user_answer, 
                context=context, 
                custom_prompt=request.custom_prompt,
                model=request.model,
                temperature=request.temperature
            )
            response_data = {"status": "success", "persona": persona, "context_used": context, "result": result}
            save_sandbox_log(req_data, response_data, "agent_test")
            return response_data
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@router.post("/ai/test/moderator", tags=["Sandbox"])
async def test_moderator_sandbox(request: ModeratorSandboxRequest, current_user: str = Depends(get_current_user)):
    """
    여러 에이전트의 피드백 결과를 종합하여 제공하는 모더레이터 메시지를 테스트합니다.
    """
    try:
        eval_user_answer = await translate_ko_to_en(request.user_answer)
        guidance = await generate_moderator_guidance_message(
            eval_user_answer, 
            request.lowest_persona, 
            request.expert_results,
            custom_prompt=request.custom_prompt,
            model=request.model,
            temperature=request.temperature
        )
        response_data = {"status": "success", "guidance_message": guidance}
        req_data = request.dict() if hasattr(request, 'dict') else request.model_dump()
        save_sandbox_log(req_data, response_data, "moderator_test")
        return response_data
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@router.post("/ai/test/graph", tags=["Sandbox"])
async def test_graph_sandbox(request: GraphSandboxRequest, current_user: str = Depends(get_current_user)):
    """
    전체 랭그래프(debate_graph) 파이프라인(초안 -> 교차검증 -> 최종요약)을 테스트합니다.
    """
    import asyncio
    try:
        eval_user_answer = await translate_ko_to_en(request.user_answer)
        
        # 실제 RAG/KG 컨텍스트 연동 여부
        news_context = ""
        kg_context = ""
        if request.use_real_context:
            news_context, kg_context = await asyncio.gather(
                retrieve_news_rag(request.concept),
                retrieve_knowledge_graph(request.concept)
            )
            
        initial_state = {
            "concept": request.concept,
            "user_answer": eval_user_answer,
            "definition": request.definition,
            "acceptable_extensions": request.acceptable_extensions or "",
            "ground_truth": request.definition,  # Backward compatibility
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
        
        start_time = time.time()
        final_state = await debate_graph.ainvoke(initial_state)
        end_time = time.time()
        execution_time = round(end_time - start_time, 2)
        
        req_data = request.dict() if hasattr(request, 'dict') else request.model_dump()
        save_sandbox_log(req_data, final_state, "graph_test")
        
        return {
            "status": "success",
            "execution_time_seconds": execution_time,
            "final_state": final_state
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@router.post("/ai/test/scaffolding", tags=["Sandbox"])
async def test_scaffolding_sandbox(
    request: ScaffoldingSandboxRequest,
    current_user: str = Depends(get_current_user)
):
    """
    ZPD 기반 스캐폴딩 4단계 프롬프트를 독립적으로 테스트합니다.

    idk_count 값에 따라 아래 프롬프트가 선택됩니다:
      1 → Level 3 (Nudge)           — RECOVERY_NUDGE_PROMPT
      2 → Level 2 (Concept Hint)    — RECOVERY_CONCEPT_PROMPT
      3 → Level 1 (Fill-in-blank)   — RECOVERY_FILL_BLANK_PROMPT
      4 → Level 0 (Solution Reveal) — RECOVERY_REVEAL_PROMPT

    use_real_kg=true 이면 Neo4j에서 실제 KG 컨텍스트를 조회하여 주입합니다.
    custom_prompt 를 제공하면 기본 프롬프트를 완전히 대체합니다.
    """
    try:
        kg_context = request.kg_context or ""

        # 실제 KG 연동 요청 시 Neo4j 조회
        if request.use_real_kg:
            kg_context = await retrieve_knowledge_graph(request.concept_name.lower())

        result = await call_scaffolding_agent(
            concept_name=request.concept_name,
            definition=request.definition,
            acceptable_extensions=request.acceptable_extensions or "",
            last_question=request.last_question or "",
            kg_context=kg_context,
            idk_count=request.idk_count,
            custom_prompt=request.custom_prompt,
            model=request.model,
            temperature=request.temperature,
        )

        response_data = {
            "status": "success",
            **result,
            "kg_context_used": kg_context or "(none)",
        }

        req_data = request.dict() if hasattr(request, "dict") else request.model_dump()
        save_sandbox_log(req_data, response_data, "scaffolding_test")
        return response_data

    except Exception as e:
        return {"status": "error", "detail": str(e)}
