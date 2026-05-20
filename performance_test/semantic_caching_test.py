import requests
import time
import matplotlib.pyplot as plt
import sys
import os

# 백엔드 DB 연동을 위해 path 추가
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'back'))
from database import supabase

API_URL = "http://localhost:8080/chat"
# 테스트용 세션 정보 (DB에 있는 유효한 세션 ID와 각각의 유저 토큰으로 교체하세요)
HEADERS_USER_A = {"Authorization": "Bearer YOUR_JWT_TOKEN"}
HEADERS_USER_B = {"Authorization": "Bearer YOUR_JWT_TOKEN"}

# PAYLOAD_1: 유저 A의 세션 (캐시 미스 유도 - LLM 풀가동)
PAYLOAD_1 = {
    "session_id": "146", 
    "concept": "inflation",
    "user_answer": "인플레이션은 물가가 지속적으로 오르는 현상이야."
}

# PAYLOAD_2: 유저 B의 세션 (의미는 같지만 완전히 다른 형태의 문장 - 시맨틱 캐시 히트 검증)
PAYLOAD_2 = {
    "session_id": "147", 
    "concept": "inflation",
    "user_answer": "물건 가격이 전반적으로 꾸준히 상승하는 것을 의미해."
}

print("🧹 [Cleanup] 테스트 재현성을 위해 기존 데이터 정리를 수행합니다...")
try:
    # 1. 두 세션의 chat_logs 제거 (turn_number를 1로 초기화하기 위함)
    supabase.table("chat_logs").delete().in_("session_id", [146, 147]).execute()
    print("  - chat_logs 테이블에서 세션 146, 147의 기존 로그를 삭제했습니다.")
    
    # 2. semantic_cache 테이블의 기존 캐시 항목 제거
    supabase.table("semantic_cache").delete().eq("concept", "inflation").execute()
    print("  - semantic_cache 테이블에서 'inflation' 관련 캐시를 초기화했습니다.")
except Exception as e:
    print(f"  ⚠️ 정리에 실패했습니다 (테스트는 계속 진행됩니다): {e}")

def measure_latency(payload, headers):
    start = time.time()
    res = requests.post(API_URL, json=payload, headers=headers)
    end = time.time()
    
    # 🚨 서버가 에러를 뱉었는지(403, 404, 500 등) 확인하기 위해 결과 출력
    if res.status_code != 200:
        print(f"⚠️ [Error {res.status_code}] {res.text}")
    else:
        # LLM 응답인지 캐시 응답인지 일부 출력
        data = res.json()
        from_cache = data.get("from_cache", False)
        print(f"✅ [Success 200] 캐시 히트 여부: {from_cache} | 응답 데이터 일부: {str(data)[:100]}...")
        
    return (end - start) * 1000  # ms 단위 변환

print("\n1. 유저 A 캐시 미스(LLM 작동) 테스트 중 (원본 문장)...")
time_llm = measure_latency(PAYLOAD_1, HEADERS_USER_A)

print("\n2. 유저 B 시맨틱 캐시 히트 테스트 중 (의미가 같은 다른 문장)...")
# 조금의 딜레이를 주어 DB 저장이 반영될 틈을 줍니다.
time.sleep(1.5)
time_cache = measure_latency(PAYLOAD_2, HEADERS_USER_B)

# 📈 차트 그리기
labels = ['Cache Miss (LLM Graph)', 'Cache Hit (Semantic)']
times = [time_llm, time_cache]

plt.figure(figsize=(8, 5))
bars = plt.bar(labels, times, color=['#ff9999', '#66b3ff'])
plt.ylabel('Response Time (ms)')
plt.title('Semantic Caching Performance Optimization')

# 막대 위에 정확한 수치 텍스트 표시
for bar in bars:
    yval = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2, yval + 10, f'{int(yval)} ms', ha='center', va='bottom', fontweight='bold')

plt.savefig('cache_optimization_result.png')
print("\n✅ 차트가 cache_optimization_result.png 로 저장되었습니다!")
