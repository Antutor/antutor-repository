import os
import sys
import asyncio

# 상위 폴더(back) 경로를 sys.path에 추가하여 config.py를 불러올 수 있게 함
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    LOCAL_LLM_MODEL, 
    LOCAL_LLM_ENDPOINT, 
    DRAFT_LLM_MODEL, 
    DEBATE_LLM_MODEL,
    DRAFT_LLM_ENDPOINT,
    DEBATE_LLM_ENDPOINT,
    LLM_BACKEND_TYPE,
    VLLM_API_KEY
)

if LLM_BACKEND_TYPE.lower() == "vllm":
    from langchain_openai import ChatOpenAI
    # 1. vLLM 기반 OpenAI 호환 API (RunPod 등)
    # vLLM endpoint usually ends with /v1
    draft_base_url = DRAFT_LLM_ENDPOINT if DRAFT_LLM_ENDPOINT.endswith("/v1") else DRAFT_LLM_ENDPOINT + "/v1"
    debate_base_url = DEBATE_LLM_ENDPOINT if DEBATE_LLM_ENDPOINT.endswith("/v1") else DEBATE_LLM_ENDPOINT + "/v1"
    
    draft_llm = ChatOpenAI(
        model=DRAFT_LLM_MODEL,
        base_url=draft_base_url,
        api_key=VLLM_API_KEY or "empty",
        temperature=0.0,
        max_tokens=2048,
        timeout=300,
        default_headers={"ngrok-skip-browser-warning": "true"}
    ).with_config({"tags": ["draft_llm"]})
    
    debate_llm = ChatOpenAI(
        model=DEBATE_LLM_MODEL,
        base_url=debate_base_url,
        api_key=VLLM_API_KEY or "empty",
        temperature=0.0,
        max_tokens=2048,
        timeout=300,
        default_headers={"ngrok-skip-browser-warning": "true"}
    ).with_config({"tags": ["debate_llm"]})
    
    synthesis_llm = ChatOpenAI(
        model=DEBATE_LLM_MODEL,
        base_url=debate_base_url,
        api_key=VLLM_API_KEY or "empty",
        temperature=0.0,
        max_tokens=2048,
        timeout=300,
        default_headers={"ngrok-skip-browser-warning": "true"}
    ).with_config({"tags": ["synthesis_llm"]})
else:
    from langchain_ollama import ChatOllama
    # 2. 로컬 Ollama 구동 (기존)
    # 포트 제외한 base_url 추출 (ex: http://localhost:11434)
    base_url = LOCAL_LLM_ENDPOINT.split("/api")[0]
    
    draft_llm = ChatOllama(
        model=DRAFT_LLM_MODEL,
        base_url=base_url,
        temperature=0.0,
        num_predict=2048,
        num_ctx=8192
    ).with_config({"tags": ["draft_llm"]})

    debate_llm = ChatOllama(
        model=DEBATE_LLM_MODEL,
        base_url=base_url,
        temperature=0.0,
        num_predict=2048,
        num_ctx=8192
    ).with_config({"tags": ["debate_llm"]})

    synthesis_llm = ChatOllama(
        model=DEBATE_LLM_MODEL,
        base_url=base_url,
        temperature=0.0,
        num_predict=2048,
        num_ctx=8192
    ).with_config({"tags": ["synthesis_llm"]})

# Legacy compatibility (optional, but keep for safety if used elsewhere)
llm = draft_llm
creative_llm = synthesis_llm

# GPU/RAM 보호를 위한 세마포어
# - 모델 크기(4.5 GiB)가 가용 메모리보다 클 경우 1로 설정하여 동시 LLM 호출을 제한
# - 메모리가 충분할 경우 2~3으로 높이면 gather 병렬처리 이점 회복 가능
gpu_semaphore = asyncio.Semaphore(3)
