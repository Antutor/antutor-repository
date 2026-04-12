# Neo4j 지식그래프 연동 서비스
# EconomicConcept 노드 간의 관계를 양방향으로 조회하여
# LLM 프롬프트에 사용할 수 있는 텍스트 형태로 반환합니다.

import ssl
import certifi
from neo4j import AsyncGraphDatabase
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, NEO4J_DATABASE

# ─────────────────────────────────────────────────────────────────────────────
# Windows 환경에서 neo4j+s:// (라우팅+TLS) URI 는 자체 SSL 처리를 하므로
# certifi CA 번들을 직접 주입할 수 없습니다.
# 대신 bolt:// URI + encrypted=True + certifi ssl_context 조합으로
# 동일하게 TLS 연결을 수립합니다.
# .env 의 NEO4J_URI 는 "neo4j+s://..." 형태로 유지하고,
# 여기서 호스트만 파싱하여 bolt:// URI 를 재조립합니다.
# ─────────────────────────────────────────────────────────────────────────────
def _make_neo4j_uri(uri: str) -> str:
    """neo4j+s:// URI에서 호스트를 추출해 neo4j:// URI로 변환.
    neo4j:// = 라우팅 프로토콜 (홈 DB 자동 선택) + certifi SSL 주입 가능.
    """
    for prefix in ("neo4j+s://", "neo4j+ssc://", "bolt+s://", "bolt+ssc://", "bolt://"):
        if uri.startswith(prefix):
            return "neo4j://" + uri[len(prefix):]
    if uri.startswith("neo4j://"):
        return uri  # 이미 올바른 형태
    return uri


_NEO4J_URI   = _make_neo4j_uri(NEO4J_URI)
_SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())

# 관계 타입 → 한글 설명 매핑
ACTION_KR_MAP = {
    "INCREASES": "상승시킨다(증가시킨다)",
    "DECREASES": "하락시킨다(감소시킨다)",
    "CONTROLS": "통제한다(억제한다)",
    "INDICATES": "나타내는 지표이다",
    "AFFECTS": "영향을 미친다",
}

_CYPHER_QUERY = """
MATCH (a:EconomicConcept {name_kr: $keyword})-[r]-(b:EconomicConcept)
RETURN startNode(r).name_kr AS Subject,
       type(r)              AS Action,
       endNode(r).name_kr  AS Object
"""


async def get_economic_facts(keyword: str) -> str:
    """
    keyword: 한글 경제 개념명 (예: '기준금리')
    Returns: 팩트 문장들을 개행으로 이어붙인 문자열.
             매칭 결과가 없으면 안내 문자열 반환.
    """
    facts: list[str] = []

    async with AsyncGraphDatabase.driver(
        _NEO4J_URI,
        auth=(NEO4J_USER, NEO4J_PASSWORD),
        encrypted=True,
        ssl_context=_SSL_CONTEXT,
    ) as driver:
        async with driver.session() as session:
            result = await session.run(_CYPHER_QUERY, keyword=keyword)
            records = await result.data()

    for record in records:
        subject = record["Subject"]
        action  = record["Action"]
        obj     = record["Object"]
        action_kr = ACTION_KR_MAP.get(action, "관계가 있다")
        facts.append(f"- {subject}는(은) {obj}을(를) {action_kr}.")

    if not facts:
        return f"지식그래프에서 '{keyword}'에 대한 관계 데이터를 찾을 수 없습니다."

    return "\n".join(facts)


async def retrieve_knowledge_graph(concept: str) -> str:
    """
    llm_agent.py 의 retrieve_knowledge_graph 와 동일한 시그니처로
    기존 코드를 그대로 교체할 수 있는 어댑터 함수입니다.

    concept: 영문 또는 한글 개념명
    Returns: LLM 프롬프트에 삽입용 문자열
    """
    try:
        facts_text = await get_economic_facts(concept)
        return (
            f"[지식그래프 컨텍스트 — '{concept}']\n"
            f"{facts_text}"
        )
    except Exception as e:
        # Neo4j 연결 실패 시 빈 컨텍스트로 graceful fallback
        print(f"[KnowledgeGraph] ⚠️  Neo4j 조회 실패 (keyword={concept}): {e}", flush=True)
        return f"지식그래프 조회 중 오류가 발생했습니다: {str(e)}"
