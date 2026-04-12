from fastapi import APIRouter, Depends
import httpx
import json
from datetime import datetime

from schemas import (
    PromptTuningSandboxRequest,
    AgentSandboxRequest,
    ModeratorSandboxRequest,
    GraphSandboxRequest
)
from multi_agent.graph import debate_graph
from services.llm_agent import (
    retrieve_news_rag,
    retrieve_knowledge_graph,
    call_expert_agent,
    evaluate_academic_auditor,
    generate_moderator_guidance_message
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
    RAG(News API) 기능만 단독으로 테스트합니다.
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
            if not request.ground_truth:
                return {"status": "error", "detail": "ground_truth is required for The Academic Auditor"}
            result = await evaluate_academic_auditor(
                request.concept, 
                eval_user_answer, 
                request.ground_truth, 
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
            "ground_truth": request.ground_truth,
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
        
        final_state = await debate_graph.ainvoke(initial_state)
        
        req_data = request.dict() if hasattr(request, 'dict') else request.model_dump()
        save_sandbox_log(req_data, final_state, "graph_test")
        
        return {
            "status": "success",
            "final_state": final_state
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}

