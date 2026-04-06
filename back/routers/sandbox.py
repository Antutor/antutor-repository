from fastapi import APIRouter, Depends
import httpx
import json
from datetime import datetime

from schemas import PromptTuningSandboxRequest
from config import LOCAL_LLM_MODEL, LOCAL_LLM_ENDPOINT
from dependencies import get_current_user

router = APIRouter()

def save_sandbox_log(request_data: dict, response_content: str):
    import os
    
    file_path = "sandbox_logs.jsonl"
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "request": request_data,
        "response": response_content
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
            
            save_sandbox_log(req_data, result_content)

            return {
                "status": "success",
                "request_settings": req_data,
                "response": result_content
            }
            
    except Exception as e:
        return {"status": "error", "detail": f"Sandbox LLM Call Error: {str(e)}"}
