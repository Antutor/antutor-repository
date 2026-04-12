import os
import sys
import asyncio

# 상위 폴더(back) 경로를 sys.path에 추가하여 config.py를 불러올 수 있게 함
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_ollama import ChatOllama
from config import LOCAL_LLM_MODEL, LOCAL_LLM_ENDPOINT, DRAFT_LLM_MODEL, DEBATE_LLM_MODEL

# 포트 제외한 base_url 추출 (ex: http://localhost:11434)
# LOCAL_LLM_ENDPOINT 는 обычно "http://localhost:11434/api/chat"
base_url = LOCAL_LLM_ENDPOINT.split("/api")[0]

# 1. 초안 생성용 기초 모델 (qwen2.5:7b, low temperature)
draft_llm = ChatOllama(
    model=DRAFT_LLM_MODEL,
    base_url=base_url,
    temperature=0.0,
    num_predict=2048,
    num_ctx=8192
)

# 2. 토론 및 반론용 모델 (qwen3:8b, low temperature)
debate_llm = ChatOllama(
    model=DEBATE_LLM_MODEL,
    base_url=base_url,
    temperature=0.0,
    num_predict=2048,
    num_ctx=8192
)

# 3. 최종 요약 및 중재용 모델 (qwen3:8b, consistent temperature)
synthesis_llm = ChatOllama(
    model=DEBATE_LLM_MODEL,
    base_url=base_url,
    temperature=0.0,
    num_predict=2048,
    num_ctx=8192
)

# Legacy compatibility (optional, but keep for safety if used elsewhere)
llm = draft_llm
creative_llm = synthesis_llm

# GPU VRAM 보호를 위한 세마포어 (vLLM 또는 다수 에이전트 병렬 처리 시 상향)
gpu_semaphore = asyncio.Semaphore(3)
