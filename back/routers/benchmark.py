from fastapi import APIRouter, HTTPException
import asyncio
import time
from schemas import ChatRequest
from services.llm_agent import (
    retrieve_news_rag,
    retrieve_knowledge_graph
)
from multi_agent.nodes import (
    drafting_node,
    cross_review_node,
    synthesis_node,
    call_academic, # I might need to export these or replicate them
    call_market,
    call_macro,
    call_rebuttal
)
from multi_agent.graph import debate_graph
from multi_agent.state import AgentState

router = APIRouter(prefix="/benchmark", tags=["performance"])

# For sync simulation, we need the individual agent calls which are currently inside nodes.py
# I'll replicate the core logic here to ensure true sequential execution for the sync benchmark.

@router.post("/sync")
async def benchmark_sync(request: ChatRequest):
    """
    [SERIAL EXECUTION] 
    Everything runs one after another. 
    Simulates a traditional sync architecture.
    """
    concept = request.concept
    user_answer = request.user_answer
    ground_truth = "Definition of " + concept # Mock GT
    
    print(f"\n[BENCHMARK] 🟢 Sync Mode Start (Concept: {concept})")
    start_time = time.time()
    
    # 1. RAG (Sequential)
    news_context = await retrieve_news_rag(concept)
    kg_context = await retrieve_knowledge_graph(concept)
    
    # 2. Drafting (Sequential)
    # Replicating drafting_node's logic but without asyncio.gather
    # Since they are exported in nodes.py (I'll need to check if they are exported or just local)
    # Actually, drafting_node defines them locally. I'll modify nodes.py to export them or just replicate.
    # For now, I'll simulate by calling the drafting node logic sequentially.
    
    # Simulating 3 agent drafting calls sequentially
    from multi_agent.nodes import call_academic, call_market, call_macro
    
    res1 = await call_academic(concept, ground_truth, user_answer)
    res2 = await call_market(concept, news_context, user_answer)
    res3 = await call_macro(concept, kg_context, user_answer)
    
    draft_reviews = {res1[0]: res1[1], res2[0]: res2[1], res3[0]: res3[1]}
    
    # 3. Cross Review Round 1 (Sequential)
    from multi_agent.nodes import call_rebuttal
    reb1 = await call_rebuttal("The Academic Auditor", concept, user_answer, draft_reviews)
    reb2 = await call_rebuttal("The Market Practitioner", concept, user_answer, draft_reviews)
    reb3 = await call_rebuttal("The Macro-Connector", concept, user_answer, draft_reviews)
    
    critiques = [f"Round 1: {reb1}\n{reb2}\n{reb3}"]
    
    # 4. Synthesis
    print(f"[BENCHMARK] ⌛ Sync Mode Synthesis Step...")
    final_feedback = await synthesis_node({
        "concept": concept, 
        "user_answer": user_answer, 
        "critiques": critiques,
        "draft_reviews": draft_reviews
    })
    
    end_time = time.time()
    print(f"[BENCHMARK] ✅ Sync Mode Complete! (Elapsed: {end_time - start_time:.2f}s)")
    
    return {
        "mode": "sync",
        "elapsed_time": end_time - start_time,
        "result": final_feedback["final_synthesis"]
    }

@router.post("/async")
async def benchmark_async(request: ChatRequest):
    """
    [PARALLEL EXECUTION]
    Uses the production LangGraph and asyncio.gather logic.
    """
    concept = request.concept
    user_answer = request.user_answer
    ground_truth = "Definition of " + concept
    
    print(f"\n[BENCHMARK] 🚀 Async Mode Start (Concept: {concept})")
    start_time = time.time()
    
    # 1. RAG (Parallel)
    news_context, kg_context = await asyncio.gather(
        retrieve_news_rag(concept),
        retrieve_knowledge_graph(concept)
    )
    
    # 2. End-to-End Graph (Internal node parallelism)
    initial_state = {
        "concept": concept,
        "user_answer": user_answer,
        "ground_truth": ground_truth,
        "news_context": news_context,
        "kg_context": kg_context,
        "draft_reviews": {},
        "critiques": [],
        "raw_scores": {},
        "is_contradiction": False,
        "final_synthesis": "",
        "debate_count": 0,
        "moderator_action": ""
    }
    
    final_state = await debate_graph.ainvoke(initial_state)
    
    end_time = time.time()
    print(f"[BENCHMARK] ✅ Async Mode Complete! (Elapsed: {end_time - start_time:.2f}s)")
    
    return {
        "mode": "async",
        "elapsed_time": end_time - start_time,
        "result": final_state["final_synthesis"]
    }
