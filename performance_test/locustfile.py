"""
Antutor Multi-Agent Performance Benchmark — Advanced Locust Script
==================================================================

[테스트 목적]
  에이전트를 "동기 직렬로 호출했을 때"와 "현재 백엔드 로직대로(asyncio.gather 병렬) 실행할 때"
  성능 차이를 동시접속자 수를 단계적으로 늘려가며 비교합니다.

  ┌──────────────┬──────────────────────────────────────────────────────────┐
  │  /benchmark/sync  │ 동기 직렬: RAG → Draft 3개 순차 → Rebuttal 3개 순차 → Synthesis │
  │  /benchmark/async │ 현재 로직: RAG 병렬 + asyncio.gather(Draft 3개) + gather(Rebuttal 3개) │
  └──────────────┴──────────────────────────────────────────────────────────┘

[실행 방법]

  방법 A — StepLoadShape 자동 단계 (권장, 한 번에 전체 구간 측정)
    cd performance_test
    locust -f locustfile.py --host http://localhost:8000 --csv results/bench --headless

  방법 B — 특정 동시접속자 수 수동 지정
    locust -f locustfile.py --headless -u 10 -r 2 --run-time 3m \\
           --host http://localhost:8000 --csv results/bench_u10

  방법 C — SyncUser 또는 AsyncUser 단독 실행
    locust -f locustfile.py --headless -u 10 -r 2 --run-time 3m \\
           --host http://localhost:8000 --csv results/sync_only \\
           --class-picker   ← Web UI에서 선택, 또는 아래처럼 클래스 직접 지정
    locust -f locustfile.py SyncUser --headless ...

[결과 시각화]
  python visualize.py --prefix results/bench

[부하 단계 (StepLoadShape)]
  Step 0 — Baseline   : 동시접속자  1명,  60초 유지
  Step 1 — Low        :             5명, 120초 유지
  Step 2 — Medium     :            10명, 120초 유지
  Step 3 — High       :            20명, 120초 유지
  ─ 전체 약 7분 20초 소요
"""

from locust import HttpUser, task, between, events, LoadTestShape
from locust.exception import StopUser
import random
import time


# ---------------------------------------------------------------
# 테스트 시나리오 데이터 (개념 다양성 확보)
# ---------------------------------------------------------------
SCENARIOS = [
    # 쉬운 답변 (partial 예상)
    {"concept": "Inflation",
     "user_answer": "Inflation means prices keep going up, so money buys less over time."},
    {"concept": "Inflation",
     "user_answer": "물가가 전반적으로 오르면서 구매력이 떨어지는 현상이다."},
    # 틀린 답변 (contradiction 예상 → retry 경로)
    {"concept": "Inflation",
     "user_answer": "Inflation means prices go down and people can buy more with the same money."},
    # 정확한 답변 (correct 예상)
    {"concept": "Opportunity Cost",
     "user_answer": "Opportunity cost is the value of the best alternative you give up when making a choice."},
    {"concept": "Interest Rates",
     "user_answer": "When the central bank raises interest rates, borrowing costs rise and consumer spending typically falls."},
    {"concept": "GDP",
     "user_answer": "GDP is the total market value of all final goods and services produced in a country in a given period."},
    {"concept": "Supply and Demand",
     "user_answer": "If supply increases while demand stays constant, prices tend to fall."},
    {"concept": "Monetary Policy",
     "user_answer": "Monetary policy refers to central bank actions that control money supply and interest rates to stabilize inflation and growth."},
    {"concept": "Exchange Rate",
     "user_answer": "A weaker exchange rate makes exports cheaper and imports more expensive."},
    {"concept": "GDP",
     "user_answer": "GDP growth means the economy is expanding, usually leading to more employment and higher incomes."},
]

# Baseline / 일관성 검증용 고정 시나리오 (동시접속자 1명 구간에서 주로 사용)
FIXED_SCENARIO = {
    "concept": "Inflation",
    "user_answer": "Inflation is a sustained rise in the general price level, which reduces the purchasing power of money.",
}


# ---------------------------------------------------------------
# 공통 헬퍼 — 요청 전송
# ---------------------------------------------------------------
def post_benchmark(client, endpoint: str, scenario: dict, name: str):
    """
    주어진 엔드포인트에 벤치마크 요청을 보냅니다.
    - timeout=300 : LLM 추론 딜레이를 감안한 넉넉한 타임아웃
    - catch_response : 응답 내용을 검사하여 성공/실패를 Locust에 명시적으로 알림
    """
    payload = {
        "session_id": f"bench_{int(time.time() * 1000)}",
        "concept": scenario["concept"],
        "user_answer": scenario["user_answer"],
    }
    with client.post(
        endpoint,
        json=payload,
        name=name,
        catch_response=True,
        timeout=900,
    ) as resp:
        if resp.status_code == 200:
            try:
                body = resp.json()
                # 서버 내부 처리 시간이 응답에 포함되어 있으면 검증
                if "elapsed_time" not in body:
                    resp.failure("응답에 elapsed_time 필드가 없습니다.")
                else:
                    resp.success()
            except Exception as e:
                resp.failure(f"JSON 파싱 오류: {e}")
        elif resp.status_code == 422:
            resp.failure(f"요청 형식 오류 (422): {resp.text[:200]}")
        elif resp.status_code >= 500:
            resp.failure(f"서버 오류 ({resp.status_code}): {resp.text[:200]}")
        else:
            resp.failure(f"HTTP {resp.status_code}")


# ---------------------------------------------------------------
# SyncUser — 직렬 방식 (기준선)
# ---------------------------------------------------------------
class SyncUser(HttpUser):
    """
    /benchmark/sync 를 호출하는 가상 사용자.

    내부 동작:
      RAG 조회(순차) → Draft 3 에이전트(순차) → Rebuttal 3 에이전트(순차) → Synthesis

    목적: 동기 직렬 처리 방식의 지연시간/처리량을 기준값으로 수집
    """
    wait_time = between(5, 10)   # 실제 학생이 답변 입력하는 시간 모방
    weight = 1                   # AsyncUser와 동일 비율

    @task(3)
    def evaluate_random(self):
        """랜덤 시나리오 — 다양한 개념/답변 조합으로 현실적인 부하 생성"""
        scenario = random.choice(SCENARIOS)
        post_benchmark(self.client, "/benchmark/sync", scenario, "/benchmark/sync")

    @task(1)
    def evaluate_fixed(self):
        """고정 시나리오 — 결과 일관성 및 캐시 효과 검증용"""
        post_benchmark(self.client, "/benchmark/sync", FIXED_SCENARIO, "/benchmark/sync [fixed]")


# ---------------------------------------------------------------
# AsyncUser — 현재 백엔드 로직 (asyncio.gather 병렬 실행)
# ---------------------------------------------------------------
class AsyncUser(HttpUser):
    """
    /benchmark/async 를 호출하는 가상 사용자.

    내부 동작 (현재 백엔드 로직 그대로):
      RAG 조회(asyncio.gather 병렬)
      → LangGraph debate_graph.ainvoke()
          ├─ drafting_node   : asyncio.gather(Academic, Market, Macro) 병렬
          ├─ cross_review_node: asyncio.gather(3× Rebuttal) 병렬
          └─ synthesis_node  : Moderator 단일 실행

    목적: 현재 비동기 병렬 처리의 실제 처리량/지연시간 측정
    """
    wait_time = between(5, 10)
    weight = 1

    @task(3)
    def evaluate_random(self):
        """랜덤 시나리오"""
        scenario = random.choice(SCENARIOS)
        post_benchmark(self.client, "/benchmark/async", scenario, "/benchmark/async")

    @task(1)
    def evaluate_fixed(self):
        """고정 시나리오 — 일관성 검증용"""
        post_benchmark(self.client, "/benchmark/async", FIXED_SCENARIO, "/benchmark/async [fixed]")


# ---------------------------------------------------------------
# StepLoadShape — 동시접속자 수를 단계적으로 증가
# ---------------------------------------------------------------
class StepLoadShape(LoadTestShape):
    """
    동시접속자 수를 아래 단계로 자동 조절합니다.

    단계       │ 동시접속자 │ spawn_rate │ 유지 시간
    ───────────┼───────────┼────────────┼──────────
    Baseline   │     1     │     1      │  60 초
    Low        │     5     │     2      │ 120 초
    Medium     │    10     │     2      │ 120 초
    High       │    20     │     4      │ 120 초

    ※ StepLoadShape를 사용하면 -u / -r 옵션은 무시됩니다.
    ※ --headless 없이 실행하면 Web UI(localhost:8089)에서 실시간 모니터링 가능.
    """

    stages = [
        {"duration":  300, "users":  1, "spawn_rate": 1},   # Baseline (300s)
        {"duration": 1200, "users":  5, "spawn_rate": 2},   # Low (900s 추가)
        {"duration": 2100, "users": 10, "spawn_rate": 2},   # Medium (900s 추가)
        {"duration": 3000, "users": 20, "spawn_rate": 4},   # High (900s 추가)
    ]

    def tick(self):
        run_time = self.get_run_time()
        for stage in self.stages:
            if run_time < stage["duration"]:
                return stage["users"], stage["spawn_rate"]
        return None  # 모든 단계 완료 → 테스트 종료


# ---------------------------------------------------------------
# 테스트 시작/종료 콘솔 요약
# ---------------------------------------------------------------
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print(f"\n{'='*65}")
    print("  🚀 Antutor Benchmark 시작")
    print("  ┌ Sync  : /benchmark/sync  (직렬 처리 — 기준선)")
    print("  └ Async : /benchmark/async (현재 로직 — asyncio.gather 병렬)")
    print()
    print("  부하 단계:")
    print("    Baseline (  1 users, 60s) → Low  (  5 users, 120s)")
    print("          → Medium ( 10 users, 120s) → High ( 20 users, 120s)")
    print(f"{'='*65}\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    stats = environment.stats
    print(f"\n{'='*65}")
    print("  📊 벤치마크 최종 요약")
    print(f"  {'엔드포인트':<35} {'Avg(ms)':>8} {'p90(ms)':>8} {'RPS':>7} {'Fail':>5}")
    print(f"  {'-'*63}")
    for key, entry in stats.entries.items():
        req_type, name = key
        if req_type == "INTERNAL" or not name.startswith("/benchmark"):
            continue
        p90 = entry.get_response_time_percentile(0.90)
        print(
            f"  {name:<35} "
            f"{entry.avg_response_time:>8.0f} "
            f"{p90:>8.0f} "
            f"{entry.current_rps:>7.2f} "
            f"{entry.num_failures:>5}"
        )
    print(f"{'='*65}\n")
