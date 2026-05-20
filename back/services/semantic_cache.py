"""
back/services/semantic_cache.py
================================
시맨틱 캐싱 — 임베딩 기반 유사 질문 캐시

DB 미구축 상태:
  - get_cached_response() : 항상 None 반환 (캐시 미스)
  - save_to_cache()        : print()로 임시 처리

실제 운영 시 TODO 주석 위치에 pgvector 조회/저장 로직을 추가합니다.
임베딩 모델은 sentence-transformers(all-MiniLM-L6-v2)를 사용하며,
패키지가 없으면 경고만 출력하고 캐시 기능은 조용히 비활성화됩니다.
"""

from __future__ import annotations

import asyncio
from typing import Optional

# ---------------------------------------------------------------------------
# 임베딩 모델 — Lazy 초기화 (서버 시작 속도 보호)
# ---------------------------------------------------------------------------
from datetime import datetime
from database import supabase

# ---------------------------------------------------------------------------
# 임베딩 모델 — Lazy 초기화 (서버 시작 속도 보호)
# ---------------------------------------------------------------------------
_encoder = None
_encoder_ready = False

def _load_encoder():
    """sentence-transformers 모델을 최초 호출 시 한 번만 로드합니다."""
    global _encoder, _encoder_ready
    if _encoder_ready:
        return
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore
        _encoder = SentenceTransformer("all-MiniLM-L6-v2")
        _encoder_ready = True
        print("✅ [SemanticCache] 임베딩 모델 로드 완료 (all-MiniLM-L6-v2)", flush=True)
    except ImportError:
        print(
            "⚠️ [SemanticCache] sentence-transformers 미설치 — 캐시 비활성화.\n"
            "   활성화하려면: pip install sentence-transformers",
            flush=True,
        )
        _encoder_ready = True   # 재시도 방지


# ---------------------------------------------------------------------------
# 임베딩 생성
# ---------------------------------------------------------------------------

async def get_embedding(text: str) -> Optional[list[float]]:
    """
    텍스트를 벡터로 변환합니다.
    모델 미설치 시 None을 반환합니다.

    Args:
        text: 임베딩할 텍스트 (영어 권장)

    Returns:
        float 리스트 (384차원) 또는 None
    """
    _load_encoder()
    if _encoder is None:
        return None

    loop = asyncio.get_event_loop()
    vector = await loop.run_in_executor(
        None, lambda: _encoder.encode(text, normalize_embeddings=True).tolist()
    )
    return vector


# ---------------------------------------------------------------------------
# 캐시 조회
# ---------------------------------------------------------------------------

async def get_cached_response(concept: str, user_answer: str) -> Optional[str]:
    """
    해당 개념(concept)에 대해 유사한 사용자 답변(user_answer)이 있었는지 벡터 DB에서 조회합니다.

    Args:
        concept: 대상 개념 이름 (예: "inflation")
        user_answer: 사용자의 답변 텍스트 (영어)

    Returns:
        캐시 히트 시 cached_response 문자열, 미스 시 None
    """
    embedding = await get_embedding(user_answer)
    if embedding is None:
        return None
    try:
        result = supabase.rpc("match_semantic_cache", {
            "p_concept": concept,
            "p_embedding": embedding,
            "p_match_threshold": 0.65,
            "p_match_count": 1
        }).execute()
        if result.data:
            print(f"✅ [SemanticCache] 캐시 히트! similarity={result.data[0]['similarity']:.4f}", flush=True)
            return result.data[0]["cached_response"]
    except Exception as e:
        print(f"⚠️ [SemanticCache] 캐시 조회 오류: {e}", flush=True)

    print(
        f"🔍 [SemanticCache] DB 유사도 검색 (캐시 미스 반환) "
        f"| concept='{concept}' | answer_preview='{user_answer[:50]}'",
        flush=True,
    )
    return None


# ---------------------------------------------------------------------------
# 캐시 저장
# ---------------------------------------------------------------------------

async def save_to_cache(concept: str, user_answer: str, response: str) -> None:
    """
    새로운 사용자 답변과 튜터의 피드백 쌍을 벡터 DB에 저장합니다.

    Args:
        concept: 대상 개념 이름 (예: "inflation")
        user_answer: 사용자의 답변 텍스트 (영어)
        response: LLM(튜터)이 생성한 최종 피드백 텍스트
    """
    embedding = await get_embedding(user_answer)

    if embedding is not None:
        try:
            supabase.table("semantic_cache").insert({
                "concept": concept,
                "user_answer": user_answer,
                "cached_response": response,
                "embedding": embedding,
                "created_at": datetime.utcnow().isoformat()
            }).execute()
            print(
                f"💾 [SemanticCache] 캐시 DB 저장 완료 "
                f"| concept='{concept}' | vector_dim={len(embedding)}",
                flush=True,
            )
        except Exception as e:
            print(f"⚠️ [SemanticCache] 캐시 저장 실패: {e}", flush=True)

