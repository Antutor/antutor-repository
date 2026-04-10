from langgraph.graph import StateGraph, START, END
from multi_agent.state import AgentState
from multi_agent.nodes import (
    drafting_node,
    cross_review_node,
    moderator_check_node,
    synthesis_node
)

def router(state: AgentState):
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
    workflow.add_node("cross_review_node", cross_review_node)
    workflow.add_node("moderator_check_node", moderator_check_node)
    workflow.add_node("synthesis_node", synthesis_node)
    
    # 3. Define Edges
    workflow.add_edge(START, "drafting_node")
    workflow.add_edge("drafting_node", "cross_review_node")
    workflow.add_edge("cross_review_node", "moderator_check_node")
    
    # 4. Conditional Edges
    workflow.add_conditional_edges(
        "moderator_check_node",
        router,
        {
            "cross_review_node": "cross_review_node",
            "synthesis_node": "synthesis_node"
        }
    )
    
    workflow.add_edge("synthesis_node", END)
    
    # 5. Compile the graph
    app = workflow.compile()
    return app

# 싱글톤처럼 재사용 가능하도록 앱 객체 할당
debate_graph = build_graph()
