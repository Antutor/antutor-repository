from langgraph.graph import StateGraph, START, END
from multi_agent.state import AgentState
from multi_agent.nodes import (
    drafting_node,
    retry_router,
    retry_node,
    cross_review_node,
    moderator_check_node,
    synthesis_node
)

def debate_router(state: AgentState):
    """
    moderator_check_node가 뱉은 결과(moderator_action)를 바탕으로 분기합니다.
    """
    action = state.get("moderator_action", "synthesis")
    if action == "continue":
        return "cross_review_node"
    return "synthesis_node"

def build_graph():
    # 1. Initialize StateGraph with our TypedDict
    workflow = StateGraph(AgentState)

    # 2. Add Nodes
    workflow.add_node("drafting_node", drafting_node)
    workflow.add_node("retry_node", retry_node)          # NEW: retry 경량 노드
    workflow.add_node("cross_review_node", cross_review_node)
    workflow.add_node("moderator_check_node", moderator_check_node)
    workflow.add_node("synthesis_node", synthesis_node)

    # 3. Start → drafting
    workflow.add_edge(START, "drafting_node")

    # 4. drafting 직후: retry_needed 여부에 따라 분기 (NEW)
    #    retry_needed=true  → retry_node → END  (cross_review·synthesis 완전 스킵)
    #    retry_needed=false → cross_review_node → 기존 토론 흐름
    workflow.add_conditional_edges(
        "drafting_node",
        retry_router,
        {
            "retry_node": "retry_node",
            "cross_review_node": "cross_review_node",
        }
    )

    # 5. retry_node는 바로 END
    workflow.add_edge("retry_node", END)

    # 6. 기존 토론 흐름
    workflow.add_edge("cross_review_node", "moderator_check_node")
    workflow.add_conditional_edges(
        "moderator_check_node",
        debate_router,
        {
            "cross_review_node": "cross_review_node",
            "synthesis_node": "synthesis_node"
        }
    )
    workflow.add_edge("synthesis_node", END)

    # 7. Compile
    app = workflow.compile()
    return app

# 싱글톤처럼 재사용 가능하도록 앱 객체 할당
debate_graph = build_graph()
