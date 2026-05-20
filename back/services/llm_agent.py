import asyncio
import json
import httpx
import re
from typing import Optional, Dict, Any, List
from fastapi import HTTPException

from config import (
    LOCAL_LLM_ENDPOINT, LOCAL_LLM_MODEL,
    TAVILY_API_KEY, LLM_BACKEND_TYPE, VLLM_API_KEY
)
from services.knowledge_graph import retrieve_knowledge_graph  # noqa: F401 — re-exported
from multi_agent.prompts import (
    NEW_ACADEMIC_DRAFT_PROMPT,
    NEW_MARKET_DRAFT_PROMPT,
    NEW_MACRO_DRAFT_PROMPT
)

def strip_think_tags(text: str) -> str:
    """Qwen3 등의 모델이 출력하는 <think>...</think> 블록을 제거합니다."""
    return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()

class ThinkTagStreamFilter:
    """
    스트리밍 청크에서 <think>...</think> 블록을 실시간으로 제거합니다.
    청크 경계에서 태그가 잘리는 경우를 처리하기 위해 상태를 유지합니다.
    """
    def __init__(self):
        self._buffer = ""
        self._in_think = False

    def feed(self, chunk: str) -> str:
        """청크를 받아 <think> 블록이 제거된 출력 문자열을 반환합니다."""
        self._buffer += chunk
        result = ""
        while True:
            if self._in_think:
                end = self._buffer.find("</think>")
                if end == -1:
                    # </think> 아직 도착 안 함 — 버퍼 유지
                    self._buffer = ""
                    break
                else:
                    # </think> 발견 — think 블록 종료
                    self._buffer = self._buffer[end + len("</think>"):]
                    self._in_think = False
            else:
                start = self._buffer.find("<think>")
                if start == -1:
                    # think 블록 없음 — 버퍼 전체 출력
                    result += self._buffer
                    self._buffer = ""
                    break
                else:
                    # <think> 발견 — 그 이전 내용만 출력
                    result += self._buffer[:start]
                    self._buffer = self._buffer[start + len("<think>"):]
                    self._in_think = True
        return result

async def call_local_llm(prompt: str, is_json: bool = False, model: Optional[str] = None, temperature: Optional[float] = None) -> str:
    """Helper to call local LLM API (Ollama or vLLM)"""
    model_name = model or LOCAL_LLM_MODEL
    
    headers = {"ngrok-skip-browser-warning": "true"}
    
    if LLM_BACKEND_TYPE.lower() == "vllm":
        # vLLM (OpenAI Format)
        endpoint = LOCAL_LLM_ENDPOINT if LOCAL_LLM_ENDPOINT.endswith("/v1") else LOCAL_LLM_ENDPOINT + "/v1"
        endpoint += "/chat/completions"
        if VLLM_API_KEY:
            headers["Authorization"] = f"Bearer {VLLM_API_KEY}"
            
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature if temperature is not None else 0.0,
            "max_tokens": 512
        }
        if is_json:
            payload["response_format"] = {"type": "json_object"}
    else:
        # Ollama Format
        endpoint = LOCAL_LLM_ENDPOINT
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "options": {
                "temperature": temperature if temperature is not None else 0.0
            },
            "stream": False
        }
        if is_json:
            payload["format"] = "json"
            
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(endpoint, json=payload, headers=headers, timeout=300.0)
            response.raise_for_status()
            data = response.json()
            
            if "choices" in data: # OpenAI / vLLM
                return strip_think_tags(data["choices"][0]["message"]["content"])
            elif "message" in data: # Ollama
                return strip_think_tags(data["message"]["content"])
            return str(data)
    except Exception as e:
        print(f"LLM Call Error ({LLM_BACKEND_TYPE}): {str(e)}")
        if is_json:
            return '{"is_contradiction": false, "score": 0.5, "feedback": "API error."}'
    
    return "LLM Error."

async def evaluate_academic_auditor(
    concept: str, 
    user_answer: str, 
    definition: Optional[str] = None, 
    acceptable_extensions: str = "", 
    custom_prompt: Optional[str] = None, 
    model: Optional[str] = None, 
    temperature: Optional[float] = None,
    ground_truth: Optional[str] = None
) -> dict:
    actual_definition = definition or ground_truth or ""
    template = custom_prompt or NEW_ACADEMIC_DRAFT_PROMPT
    
    format_kwargs = {
        "concept": concept,
        "user_answer": user_answer,
    }
    
    if "{definition}" in template or "{acceptable_extensions}" in template:
        format_kwargs["definition"] = actual_definition
        format_kwargs["acceptable_extensions"] = acceptable_extensions
    else:
        format_kwargs["ground_truth"] = actual_definition
        
    prompt = "/no_think\n" + template.format(**format_kwargs)
    
    raw_response = await call_local_llm(prompt, is_json=True, model=model, temperature=temperature)
    try:
        return json.loads(raw_response)
    except Exception:
        return {
            "is_contradiction": False,
            "score": 0.5,
            "feedback": "Failed to parse local LLM assessment."
        }

# 웹페이지 네비게이션/면책 문구 패턴 — AI 컨텍스트에 불필요
_BOILERPLATE_PATTERNS = [
    "official website", ".gov website", "government organization",
    "united states government", "federal reserve",   # 기관 소개 보일러플레이트
    "javascript", "cookies", "cookie policy",         # 브라우저/쿠키 안내
    "subscribe", "newsletter", "sign up", "log in",  # 마케팅/로그인 유도
    "all rights reserved", "privacy policy",          # 법적 고지
    "click here", "read more", "learn more",          # 네비게이션 링크
]

def _is_boilerplate(sentence: str) -> bool:
    """웹페이지 면책/네비게이션 문구인지 확인합니다."""
    lower = sentence.lower()
    return any(pat in lower for pat in _BOILERPLATE_PATTERNS)

def _trim_to_sentences(text: str, max_chars: int = 300) -> str:
    """
    max_chars 미만에서 완성된 문장만 포함하도록 자릅니다.
    - 짧거나(< 25자) 물음표로 끝나는 소제목 형태 문장은 건너뜁니다.
    - 보일러플레이트(정부 면책, 쿠키 안내 등) 문장을 제거합니다.
    """
    import re as _re

    def _keep(s: str) -> bool:
        return len(s) >= 25 and not s.strip().endswith('?') and not _is_boilerplate(s)

    if len(text) <= max_chars:
        sentences = _re.split(r'(?<=[.!?])\s+', text)
        kept = [s for s in sentences if _keep(s)]
        return ' '.join(kept).strip() or text

    sentences = _re.split(r'(?<=[.!?])\s+', text)
    result = ""
    for s in sentences:
        if not _keep(s):
            continue
        candidate = (result + " " + s).strip()
        if len(candidate) > max_chars:
            break
        result = candidate
    return result if result else text[:max_chars]

def _clean_content(text: str) -> str:
    """
    Tavily 검색 결과의 불필요한 노이즈를 제거합니다.
    - 마크다운 헤더 줄 전체 제거 (# 텍스트 → 줄 삭제)
    - 볼드(**), 이탤릭(*) 제거
    - ': 579This' 같은 콜론+공백+숫자 아티팩트 제거
    - 연속 공백·개행 정리
    """
    import re as _re
    text = _re.sub(r'(?m)^#+.*$', '', text)               # ## 헤더 줄 전체 제거
    text = _re.sub(r'\*{1,3}(.*?)\*{1,3}', r'\1', text)  # **bold**, *italic* 제거
    text = _re.sub(r':\s*\d+\s*', ' ', text)             # ': 579' 또는 ':579' 아티팩트 제거
    text = _re.sub(r'\s+', ' ', text).strip()             # 공백 정리
    return text

# ---------------------------------------------------------------------------
# Tavily Search (langchain-tavily) — Market Practitioner 뉴스 컨텍스트 확보
# ---------------------------------------------------------------------------
try:
    from langchain_tavily import TavilySearch
    import os as _os
    # setdefault 대신 직접 할당: 빈 문자열로 이미 설정된 경우에도 덮어씁니다.
    if TAVILY_API_KEY:
        _os.environ["TAVILY_API_KEY"] = TAVILY_API_KEY
    _tavily_tool = TavilySearch(max_results=3)
    print(f"✅ [Tavily] 초기화 완료 (key={'설정됨' if TAVILY_API_KEY else '없음'})", flush=True)
except Exception as _e:
    print(f"⚠️ [Tavily] 초기화 오류: {_e}")
    _tavily_tool = None

async def retrieve_tavily_news(concept: str) -> str:
    """
    TavilySearch(langchain-tavily) 를 사용하여 개념 관련 최신 뉴스를 검색합니다.
    Market Practitioner 에이전트의 news_context 로 연결됩니다.
    """
    if not TAVILY_API_KEY or TAVILY_API_KEY == "your-tavily-api-key-here":
        print("⚠️ [Tavily] API 키가 설정되지 않았습니다. 빈 컨텍스트 반환.", flush=True)
        return f"No recent news found for {concept}. (Tavily API key not configured)"

    if _tavily_tool is None:
        return f"No recent news found for {concept}. (Tavily tool initialization failed)"

    try:
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None, lambda: _tavily_tool.invoke(f"{concept} economics market")
        )
        # 디버그: 실제 반환값 타입과 내용 확인
        print(f"🔍 [Tavily] type={type(results).__name__}, preview={str(results)[:300]}", flush=True)

        if not results:
            return f"No recent news found for {concept}."

        # TavilySearch 버전에 따라 반환값 형식이 다를 수 있음:
        #   - {"results": [...]}  : dict 래퍼 (신버전)
        #   - list[dict]          : 리스트 직접 반환
        #   - str                 : 포맷된 문자열 직접 반환
        items = []
        if isinstance(results, dict):
            items = results.get("results", [])
        elif isinstance(results, list):
            items = results
        elif isinstance(results, str):
            return f"Recent news context for {concept}:\n{_clean_content(results)[:600]}"

        snippets = []
        for r in items:
            if isinstance(r, dict):
                content = _trim_to_sentences(
                    _clean_content(r.get("content", r.get("snippet", ""))),
                    max_chars=600
                )
                if content:
                    # 제목·URL은 AI 컨텍스트에 불필요하므로 내용만 포함
                    snippets.append(f"- {content}")

        if snippets:
            news_text = "\n".join(snippets)
            return f"Recent news context for {concept}:\n{news_text}"
        else:
            return f"No relevant news found for {concept}."
    except Exception as e:
        print(f"⚠️ [Tavily] 검색 오류: {e}", flush=True)
        return f"Error fetching news for {concept}: {str(e)}"

# 기존 직접 호출자(채팅.py, sandbox.py, benchmark.py)와의 호환성을 위한 별칭
# 실제 구현체는 Tavily로 전환되었습니다.
retrieve_news_rag = retrieve_tavily_news

# --- Deprecated: 기존 News API 구현 (주석 처리) ---
# async def retrieve_news_rag(concept: str) -> str:
#     if not NEWS_API_KEY:
#         raise HTTPException(status_code=500, detail="NEWS_API_KEY is not configured.")
#     url = f"https://newsapi.org/v2/everything?q={concept}&sortBy=relevancy&pageSize=3&apiKey={NEWS_API_KEY}"
#     async with httpx.AsyncClient() as client:
#         try:
#             response = await client.get(url, timeout=5.0)
#             data = response.json()
#             if data.get("status") == "ok" and data.get("articles"):
#                 articles = data["articles"]
#                 news_summary = " ".join([f"Headline: {art['title']}." for art in articles])
#                 return f"Recent news context for {concept}: {news_summary}"
#             else:
#                 return f"No recent news found for {concept}."
#         except Exception as e:
#             raise HTTPException(status_code=500, detail=f"Error fetching news for {concept}: {str(e)}")
#     raise HTTPException(status_code=500, detail=f"Failed to retrieve news context for {concept}.")


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
    prompt = "/no_think\n" + template.format(concept=concept, user_answer=user_answer, context=context)
    
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
