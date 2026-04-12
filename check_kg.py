"""
Neo4j 지식그래프 연결 및 데이터 확인 디버깅 스크립트
실행: python check_kg.py
"""

import asyncio
import ssl
import os
import certifi
from dotenv import load_dotenv
from neo4j import AsyncGraphDatabase

load_dotenv()

URI  = os.getenv("NEO4J_URI", "")
USER = os.getenv("NEO4J_USER", "neo4j")
PWD  = os.getenv("NEO4J_PASSWORD", "")

# Windows SSL 체인 문제 우회: certifi CA 번들 사용
def _make_neo4j_uri(uri: str) -> str:
    for prefix in ("neo4j+s://", "neo4j+ssc://", "bolt+s://", "bolt+ssc://", "bolt://"):
        if uri.startswith(prefix):
            return "neo4j://" + uri[len(prefix):]
    return uri

BOLT_URI    = _make_neo4j_uri(URI)
SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())

def driver():
    return AsyncGraphDatabase.driver(
        BOLT_URI,
        auth=(USER, PWD),
        encrypted=True,
        ssl_context=SSL_CONTEXT,
    )

# ─────────────────────────────────────────────────────────────────────────────
# 테스트 1: 연결 확인
# ─────────────────────────────────────────────────────────────────────────────
async def test_connection():
    print("\n" + "="*55)
    print("  [1] Neo4j Aura 연결 테스트")
    print("="*55)
    print(f"  URI  : {URI}")
    print(f"  USER : {USER}")
    print(f"  PWD  : {'*' * len(PWD)}")
    print(f"  → 변환된 NEO4J URI: {BOLT_URI}")
    try:
        async with driver() as d:
            await d.verify_connectivity()
        print("  ✅ 연결 성공!")
        return True
    except Exception as e:
        print(f"  ❌ 연결 실패: {e}")
        print("\n  💡 해결 방법:")
        print("     1. console.neo4j.io 에서 인스턴스가 Running 상태인지 확인")
        print("     2. Free 플랜은 3일 비사용 후 자동 중지 → Resume 버튼 클릭")
        return False

# ─────────────────────────────────────────────────────────────────────────────
# 테스트 2: EconomicConcept 노드 전체 목록 조회
# ─────────────────────────────────────────────────────────────────────────────
async def test_list_concepts():
    print("\n" + "="*55)
    print("  [2] 저장된 EconomicConcept 노드 목록 (최대 20개)")
    print("="*55)
    query = "MATCH (n:EconomicConcept) RETURN n.name_kr AS name ORDER BY name LIMIT 20"
    async with driver() as d:
        async with d.session() as s:
            result = await s.run(query)
            records = await result.data()
    if not records:
        print("  ⚠️  EconomicConcept 노드가 없습니다. DB에 데이터를 먼저 삽입하세요.")
    else:
        print(f"  총 {len(records)}개 노드 확인:")
        for r in records:
            print(f"    - {r['name']}")

# ─────────────────────────────────────────────────────────────────────────────
# 테스트 3: 특정 키워드로 팩트 조회 (핵심 로직 테스트)
# ─────────────────────────────────────────────────────────────────────────────
async def test_keyword_facts(keyword: str):
    print("\n" + "="*55)
    print(f"  [3] 키워드 '{keyword}' 관계 팩트 조회")
    print("="*55)
    ACTION_KR_MAP = {
        "INCREASES":  "상승시킨다(증가시킨다)",
        "DECREASES":  "하락시킨다(감소시킨다)",
        "CONTROLS":   "통제한다(억제한다)",
        "INDICATES":  "나타내는 지표이다",
        "AFFECTS":    "영향을 미친다",
    }
    query = """
    MATCH (a:EconomicConcept {name_kr: $keyword})-[r]-(b:EconomicConcept)
    RETURN startNode(r).name_kr AS Subject,
           type(r)              AS Action,
           endNode(r).name_kr  AS Object
    """
    async with driver() as d:
        async with d.session() as s:
            result = await s.run(query, keyword=keyword)
            records = await result.data()

    if not records:
        print(f"  ⚠️  '{keyword}'에 연결된 관계가 없습니다.")
        print(f"     → name_kr 값이 정확한지 확인하세요. (위 [2]번 목록 참고)")
    else:
        print(f"  ✅ {len(records)}개 관계 발견:")
        for r in records:
            action_kr = ACTION_KR_MAP.get(r["Action"], "관계가 있다")
            print(f"    {r['Subject']}는(은)  [{r['Action']}]  {r['Object']}을(를) {action_kr}.")

# ─────────────────────────────────────────────────────────────────────────────
# 테스트 4: 전체 관계(엣지) 수 확인
# ─────────────────────────────────────────────────────────────────────────────
async def test_graph_stats():
    print("\n" + "="*55)
    print("  [4] 지식그래프 통계")
    print("="*55)
    async with driver() as d:
        async with d.session() as s:
            n_result = await s.run("MATCH (n:EconomicConcept) RETURN count(n) AS cnt")
            e_result = await s.run("MATCH ()-[r]-() RETURN count(r) AS cnt")
            n_records = await n_result.data()
            e_records = await e_result.data()
    print(f"  노드(EconomicConcept) 수: {n_records[0]['cnt']}")
    print(f"  엣지(관계) 수           : {e_records[0]['cnt']}")

# ─────────────────────────────────────────────────────────────────────────────
# 메인
# ─────────────────────────────────────────────────────────────────────────────
async def main():
    print("\n🔍 Neo4j 지식그래프 디버깅 시작")

    connected = await test_connection()
    if not connected:
        print("\n연결에 실패했습니다. 아래 이슈를 해결 후 다시 실행하세요.")
        return

    await test_graph_stats()
    await test_list_concepts()

    # 여기서 확인하고 싶은 키워드를 바꿔가며 테스트하세요
    test_keywords = ["기준금리", "물가지수", "환율"]
    for kw in test_keywords:
        await test_keyword_facts(kw)

    print("\n✅ 디버깅 완료\n")

if __name__ == "__main__":
    asyncio.run(main())
