from fastapi import APIRouter, HTTPException
import asyncio
import time
import json
from schemas import ChatRequest
from services.llm_agent import (
    retrieve_news_rag,
    retrieve_knowledge_graph
)
from multi_agent.nodes import (
    call_academic,
    call_market,
    call_macro,
    call_rebuttal,
    synthesis_node,
)
from multi_agent.graph import debate_graph

router = APIRouter(prefix="/benchmark", tags=["performance"])


@router.post("/sync")
async def benchmark_sync(request: ChatRequest):
    """
    [직렬 실행 모드]
    RAG 조회 → 에이전트 초안 → Rebuttal → Synthesis 를 모두 순차적으로 실행.
    전통적인 동기 아키텍처를 시뮬레이션합니다.
    """
    concept = request.concept
    user_answer = request.user_answer
    ground_truth = "Definition of " + concept  # Mock GT

    print(f"\n[BENCHMARK] 🟢 Sync Mode Start (Concept: {concept})")
    start_time = time.time()

    # 1. RAG — Sequential (직렬)
    news_context = await retrieve_news_rag(concept)
    kg_context = await retrieve_knowledge_graph(concept)

    # 2. Drafting — Sequential (직렬, 3 에이전트 순차 호출)
    res1 = await call_academic(concept, ground_truth, user_answer)
    res2 = await call_market(concept, news_context, user_answer)
    res3 = await call_macro(concept, kg_context, user_answer)

    draft_reviews = {
        res1[0]: res1[1],
        res2[0]: res2[1],
        res3[0]: res3[1],
    }

    # 3. Rebuttal — Sequential (직렬, 3 에이전트 순차 호출)
    reb1 = await call_rebuttal("The Academic Auditor", concept, user_answer, draft_reviews)
    reb2 = await call_rebuttal("The Market Practitioner", concept, user_answer, draft_reviews)
    reb3 = await call_rebuttal("The Macro-Connector", concept, user_answer, draft_reviews)

    rebuttal_results = [reb1, reb2, reb3]

    # 4. Synthesis
    print(f"[BENCHMARK] ⌛ Sync Mode Synthesis Step...")
    final_feedback = await synthesis_node({
        "concept": concept,
        "user_answer": user_answer,
        "draft_reviews": draft_reviews,
        "rebuttal_results": rebuttal_results,
        "critiques": [],
        "raw_scores": {},
        "is_contradiction": False,
        "final_synthesis": "",
        "debate_count": 1,
        "moderator_action": "synthesis",
    })

    end_time = time.time()
    elapsed = round(end_time - start_time, 3)
    print(f"[BENCHMARK] ✅ Sync Mode Complete! (Elapsed: {elapsed}s)")

    return {
        "mode": "sync",
        "elapsed_time": elapsed,
        "result": final_feedback["final_synthesis"],
    }


@router.post("/async")
async def benchmark_async(request: ChatRequest):
    """
    [병렬 실행 모드]
    RAG 조회를 asyncio.gather로 병렬화, LangGraph 내부 노드도 gather로 병렬 실행.
    프로덕션 비동기 아키텍처와 동일합니다.
    """
    concept = request.concept
    user_answer = request.user_answer
    ground_truth = "Definition of " + concept

    print(f"\n[BENCHMARK] 🚀 Async Mode Start (Concept: {concept})")
    start_time = time.time()

    # 1. RAG — Parallel (병렬)
    news_context, kg_context = await asyncio.gather(
        retrieve_news_rag(concept),
        retrieve_knowledge_graph(concept)
    )

    # 2. End-to-End LangGraph (내부 노드 병렬 실행)
    initial_state = {
        "concept": concept,
        "user_answer": user_answer,
        "ground_truth": ground_truth,
        "news_context": news_context,
        "kg_context": kg_context,
        "draft_reviews": {},
        "critiques": [],
        "rebuttal_results": [],
        "raw_scores": {},
        "is_contradiction": False,
        "final_synthesis": "",
        "debate_count": 0,
        "moderator_action": "",
    }

    final_state = await debate_graph.ainvoke(initial_state)

    end_time = time.time()
    elapsed = round(end_time - start_time, 3)
    print(f"[BENCHMARK] ✅ Async Mode Complete! (Elapsed: {elapsed}s)")

    return {
        "mode": "async",
        "elapsed_time": elapsed,
        "result": final_state["final_synthesis"],
    }
