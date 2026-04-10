from typing import TypedDict, List, Dict, Annotated
import operator

class AgentState(TypedDict):
    concept: str
    user_answer: str
    ground_truth: str
    news_context: str
    kg_context: str
    
    # 1회차 초안: 각 에이전트의 피드백 (딕셔너리 형태 {"The Academic Auditor": "...", ...})
    draft_reviews: Dict[str, str]
    
    # 교차 검증 내용 누적: 리스트에 추가 (add 연산자로 합쳐짐)
    critiques: Annotated[List[str], operator.add]
    
    # 점수 저장: DB 저장을 위해 파싱된 numeric 점수를 따로 가지고 있음
    raw_scores: Dict[str, float]
    
    # Ground Truth 위배 여부
    is_contradiction: bool
    
    # 모더레이터 최종 종합 내용
    final_synthesis: str
    
    # 토론 라운드 횟수 (무한 루프 방지)
    debate_count: int
    
    # 모더레이터의 결정 (proceed, scaffold, retry 등)
    moderator_action: str
