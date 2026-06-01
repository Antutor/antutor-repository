"""
back/services/semantic_cache.py
================================
시맨틱 캐싱 — 임베딩 기반 유사 질문 캐시

임베딩 모델: sentence-transformers (all-MiniLM-L6-v2, 384차원 코사인 유사도)

임계값 두 개 정리 (역할과 근거)
-----------------------------------------------------------------------
[1] 캐시 조회 임계값  p_match_threshold = 0.65  (get_cached_response)
  · 목적: 새 답변이 "의미적으로 유사한" 과거 답변과 매치되는지 판단
  · 근거: all-MiniLM-L6-v2 벤치마크 기준, 0.65는 다른 표현·철자가 달라도
          같은 개념을 설명하면 히트되는 범위
          (예: "prices rise" vs "cost increases" ≈ 0.72 → 같은 피드백 재사용 OK)
  · 0.65 미만 = 의미상 실질적 차이 존재 → LLM 교사가 직접 평가해야 한다 판단

[2] 중복 저장 방지 임계값  p_match_threshold = 0.98  (save_to_cache)
  · 목적: DB에 거의 동일한 항목이 반복 INSERT되는 것을 차단
  · 근거: 0.98 이상은 대소문자·조사 정도의 차이만 있는 사실상 동일 답변을 의미
          (완전히 새로운 학습자 답변은 0.97 이하로 유지됨)
  · 0.65(조회 임계값)보다 높게 설정한 이유:
          캐시 히트 범위(0.65~0.97)에서는 다양한 새 답변이 유입될 수 있고
          그것들은 서로 다른 맥락 → 별도 항목으로 저장해야 캐시 품질 유지
-----------------------------------------------------------------------
"""

from __future__ import annotations

import asyncio
import concurrent.futures
from typing import Optional

# ---------------------------------------------------------------------------
# 임베딩 모델 — Lazy 초기화 (서버 시작 속도 보호)
# ---------------------------------------------------------------------------
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))
from database import supabase

# ---------------------------------------------------------------------------
# 임베딩 전용 스레드 풀 — CPU-bound 연산이 기본 asyncio 스레드 풀을 점유하지 않도록 분리
# ---------------------------------------------------------------------------
_embedding_executor = concurrent.futures.ThreadPoolExecutor(
    max_workers=4, thread_name_prefix="embedding"
)

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
        from sentence_transformers import SentenceTransformer
        _encoder = SentenceTransformer("all-MiniLM-L6-v2")
        print("✅ [SemanticCache] 임베딩 모델(all-MiniLM-L6-v2) 로드 완료.", flush=True)
        _encoder_ready = True
    except Exception as e:
        print(f"⚠️ [SemanticCache] 오류: {e}", flush=True)
        _encoder_ready = True


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
        _embedding_executor, lambda: _encoder.encode(text, normalize_embeddings=True).tolist()
    )
    return vector


# ---------------------------------------------------------------------------
# 캐시 조회
# ---------------------------------------------------------------------------

async def get_cached_response(concept: str, user_answer: str, last_question: str = "") -> Optional[str]:
    """
    해당 개념(concept)에 대해 유사한 사용자 답변(user_answer)이 있었는지 벡터 DB에서 조회합니다.

    Args:
        concept: 대상 개념 이름 (예: "inflation")
        user_answer: 사용자의 답변 텍스트 (영어)
        last_question: 튜터의 직전 질문 텍스트

    Returns:
        캐시 히트 시 cached_response 문자열, 미스 시 None
    """
    embedding = await get_embedding(user_answer)
    if embedding is None:
        return None
    try:
        result = supabase.rpc("match_semantic_cache", {
            "p_concept": concept,
            "p_last_question": last_question,
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

async def save_to_cache(concept: str, user_answer: str, response: str, last_question: str = "") -> None:
    """
    새로운 사용자 답변과 튜터의 피드백 쌍을 벡터 DB에 저장합니다.
    저장 전에 동일·유사(similarity >= 0.98) 항목이 이미 존재하면 건너뜁니다.

    Args:
        concept: 대상 개념 이름 (예: "inflation")
        user_answer: 사용자의 답변 텍스트 (영어)
        response: LLM(튜터)이 생성한 최종 피드백 텍스트
        last_question: 튜터의 직전 질문 텍스트
    """
    embedding = await get_embedding(user_answer)

    if embedding is not None:
        # ── 중복 저장 방지 ────────────────────────────────────────────
        # 0.98 이상의 고유사도 항목이 이미 있으면 INSERT를 건너뜁니다.
        try:
            dup_check = await asyncio.to_thread(
                lambda: supabase.rpc("match_semantic_cache", {
                    "p_concept": concept,
                    "p_last_question": last_question,
                    "p_embedding": embedding,
                    "p_match_threshold": 0.98,
                    "p_match_count": 1
                }).execute()
            )
            if dup_check.data:
                print(
                    f"⏭️  [SemanticCache] 중복 항목 감지 — 저장 건너뜀 "
                    f"(similarity={dup_check.data[0]['similarity']:.4f}) "
                    f"| concept='{concept}'",
                    flush=True,
                )
                return
        except Exception as e:
            # 중복 체크 실패 시 저장은 계속 진행 (안전한 폴백)
            print(f"⚠️ [SemanticCache] 중복 체크 오류 (저장 계속 진행): {e}", flush=True)

        try:
            await asyncio.to_thread(
                lambda: supabase.table("semantic_cache").insert({
                    "concept": concept,
                    "last_question": last_question,
                    "user_answer": user_answer,
                    "cached_response": response,
                    "embedding": embedding,
                    "created_at": datetime.now(KST).isoformat()
                }).execute()
            )
            print(
                f"💾 [SemanticCache] 캐시 DB 저장 완료 "
                f"| concept='{concept}' | vector_dim={len(embedding)}",
                flush=True,
            )
        except Exception as e:
            print(f"⚠️ [SemanticCache] 캐시 저장 실패: {e}", flush=True)

