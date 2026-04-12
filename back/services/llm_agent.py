import asyncio
import json
import httpx
import re
from typing import Optional, Dict, Any, List
from fastapi import HTTPException

from config import (
    LOCAL_LLM_ENDPOINT, LOCAL_LLM_MODEL,
    NEWS_API_KEY
)
from services.knowledge_graph import retrieve_knowledge_graph  # noqa: F401 — re-exported
from multi_agent.prompts import (
    NEW_ACADEMIC_DRAFT_PROMPT,
    NEW_MARKET_DRAFT_PROMPT,
    NEW_MACRO_DRAFT_PROMPT
)

async def call_local_llm(prompt: str, is_json: bool = False, model: Optional[str] = None, temperature: Optional[float] = None) -> str:
    """Helper to call local LLM API (e.g., Ollama)"""
    model_name = model or LOCAL_LLM_MODEL
    
    payload = {
        "model": model_name,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "options": {
            "temperature": temperature if temperature is not None else 0.0
        },
        "stream": False
    }
    
    if is_json:
        payload["format"] = "json"
        
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(LOCAL_LLM_ENDPOINT, json=payload, timeout=120.0)
            response.raise_for_status()
            data = response.json()
            
            if "message" in data:
                return data["message"]["content"]
            elif "choices" in data:
                return data["choices"][0]["message"]["content"]
            return str(data)
    except Exception as e:
        print(f"Local LLM Call Error: {str(e)}")
        if is_json:
            return '{"is_contradiction": false, "score": 0.5, "feedback": "API error."}'
    
    return "Local LLM Error."

async def evaluate_academic_auditor(concept: str, user_answer: str, ground_truth: str, custom_prompt: Optional[str] = None, model: Optional[str] = None, temperature: Optional[float] = None) -> dict:
    template = custom_prompt or NEW_ACADEMIC_DRAFT_PROMPT
    prompt = template.format(
        concept=concept, ground_truth=ground_truth, user_answer=user_answer
    )
    
    raw_response = await call_local_llm(prompt, is_json=True, model=model, temperature=temperature)
    try:
        return json.loads(raw_response)
    except Exception:
        return {
            "is_contradiction": False,
            "score": 0.5,
            "feedback": "Failed to parse local LLM assessment."
        }

async def retrieve_news_rag(concept: str) -> str:
    if not NEWS_API_KEY:
        raise HTTPException(status_code=500, detail="NEWS_API_KEY is not configured.")
    
    url = f"https://newsapi.org/v2/everything?q={concept}&sortBy=relevancy&pageSize=3&apiKey={NEWS_API_KEY}"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=5.0)
            data = response.json()
            if data.get("status") == "ok" and data.get("articles"):
                articles = data["articles"]
                news_summary = " ".join([f"Headline: {art['title']}." for art in articles])
                return f"Recent news context for {concept}: {news_summary}"
            else:
                return f"No recent news found for {concept}."
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching news for {concept}: {str(e)}")
    
    raise HTTPException(status_code=500, detail=f"Failed to retrieve news context for {concept}.")

# retrieve_knowledge_graph 는 services/knowledge_graph.py 에서 import 되어
# 이 모듈의 네임스페이스로 re-export 됩니다.
# benchmark.py 등 기존 import 경로(from services.llm_agent import retrieve_knowledge_graph)는
# 그대로 동작합니다.

async def call_expert_agent(persona: str, concept: str, user_answer: str, context: Optional[str] = None, custom_prompt: Optional[str] = None, model: Optional[str] = None, temperature: Optional[float] = None) -> Dict[str, Any]:
    # Persona mapping to constants
    prompt_map = {
        "The Academic Auditor": NEW_ACADEMIC_DRAFT_PROMPT,
        "The Market Practitioner": NEW_MARKET_DRAFT_PROMPT,
        "The Macro-Connector": NEW_MACRO_DRAFT_PROMPT
    }
    template = custom_prompt or prompt_map.get(persona, NEW_ACADEMIC_DRAFT_PROMPT)
    prompt = template.format(concept=concept, user_answer=user_answer, context=context)
    
    try:
        feedback = await call_local_llm(prompt, is_json=False, model=model, temperature=temperature)
        score = None
        match = re.search(r'\[\s*(0\.\d+|1\.00?)\s*\]', feedback)
        if match:
            try:
                score = float(match.group(1))
                feedback = re.sub(r'\[\s*(0\.\d+|1\.00?)\s*\]', '', feedback).strip()
            except ValueError:
                pass
                
        return {"persona": persona, "feedback": feedback, "score": score}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"[{persona} Connection Error] Failed to generate feedback: {str(e)}")

async def generate_moderator_guidance_message(user_answer: str, lowest_persona: str, expert_results: List[Dict], custom_prompt: Optional[str] = None, model: Optional[str] = None, temperature: Optional[float] = None) -> str:
    lowest_feedback = next((res["feedback"] for res in expert_results if res["persona"] == lowest_persona), "")
    
    if custom_prompt:
        try:
            prompt = custom_prompt.format(
                user_answer=user_answer,
                lowest_persona=lowest_persona,
                lowest_feedback=lowest_feedback
            )
        except KeyError:
            # Fallback if formatting fails due to missing keys in custom prompt
            prompt = custom_prompt 
    else:
        prompt = f"""
You are the friendly Lead Tutor guiding a student. 
The student provided this answer: "{user_answer}"
The expert '{lowest_persona}' evaluated the answer and gave this feedback: "{lowest_feedback}"

Write a short, encouraging message in English (1-3 sentences) directly replying to the student. 
1. Point out exactly what they missed based ONLY on the {lowest_persona}'s feedback.
2. End with a follow-up question to help them think about that missing aspect.
Do NOT give them the direct answer.
"""
    return await call_local_llm(prompt, is_json=False, model=model, temperature=temperature)
