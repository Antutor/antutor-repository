import asyncio
import json
import httpx
import re
from typing import Optional, Dict, Any, List
from fastapi import HTTPException

from config import (
    LOCAL_LLM_ENDPOINT, LOCAL_LLM_MODEL, 
    PROMPTS, NEWS_API_KEY
)

async def call_local_llm(prompt: str, is_json: bool = False, model: Optional[str] = None) -> str:
    """Helper to call local LLM API (e.g., Ollama)"""
    model_name = model or LOCAL_LLM_MODEL
    
    payload = {
        "model": model_name,
        "messages": [
            {"role": "user", "content": prompt}
        ],
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

async def evaluate_academic_auditor(concept: str, user_answer: str, ground_truth: str) -> dict:
    prompt = PROMPTS["experts"]["The Academic Auditor"].format(
        concept=concept, ground_truth=ground_truth, user_answer=user_answer
    )
    
    raw_response = await call_local_llm(prompt, is_json=True)
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

async def retrieve_knowledge_graph(concept: str) -> str:
    # Simulating a Knowledge Graph retrieval
    await asyncio.sleep(0.5)
    return f"Knowledge Graph Node [{concept}] -> Connected to [Global Trade, Employment Rates, Inflation]. Policy changes directly impact these connected nodes."

async def call_expert_agent(persona: str, concept: str, user_answer: str, context: Optional[str] = None) -> Dict[str, Any]:
    prompt = PROMPTS["experts"][persona].format(concept=concept, user_answer=user_answer, context=context)
    
    try:
        feedback = await call_local_llm(prompt, is_json=False)
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

async def generate_moderator_guidance_message(user_answer: str, lowest_persona: str, expert_results: List[Dict]) -> str:
    lowest_feedback = next((res["feedback"] for res in expert_results if res["persona"] == lowest_persona), "")
    
    prompt = f"""
You are the friendly Lead Tutor guiding a student. 
The student provided this answer: "{user_answer}"
The expert '{lowest_persona}' evaluated the answer and gave this feedback: "{lowest_feedback}"

Write a short, encouraging message in English (1-3 sentences) directly replying to the student. 
1. Point out exactly what they missed based ONLY on the {lowest_persona}'s feedback.
2. End with a follow-up question to help them think about that missing aspect.
Do NOT give them the direct answer.
"""
    return await call_local_llm(prompt, is_json=False)
