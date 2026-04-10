import os
import sys
import asyncio

# 상위 폴더(back) 경로를 sys.path에 추가하여 config.py를 불러올 수 있게 함
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_ollama import ChatOllama
from config import LOCAL_LLM_MODEL, LOCAL_LLM_ENDPOINT

# 포트 제외한 base_url 추출 (ex: http://localhost:11434)
# LOCAL_LLM_ENDPOINT 는 обычно "http://localhost:11434/api/chat"
base_url = LOCAL_LLM_ENDPOINT.split("/api")[0]

llm = ChatOllama(
    model=LOCAL_LLM_MODEL,
    base_url=base_url,
    temperature=0.0
)

# 토론 등의 다양성을 원하면 temperature=0.7로 세팅한 별도 모델 사용도 가능
creative_llm = ChatOllama(
    model=LOCAL_LLM_MODEL,
    base_url=base_url,
    temperature=0.5
)

# GPU VRAM 보호를 위한 세마포어 (로컬 테스트용 1, vLLM 도입 시 상향)
gpu_semaphore = asyncio.Semaphore(1)
