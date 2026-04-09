import os
import sys

# 현재 디렉토리를 경로에 추가하여 database, config 모듈을 정확히 불러오도록 설정
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import supabase
from config import SUPABASE_URL, SUPABASE_KEY

def test_connection():
    print("=== Supabase Connection Test ===")
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ 실패: .env 파일에 SUPABASE_URL 과 SUPABASE_KEY 를 입력하지 않으셨습니다.")
        print("현재 입력된 URL:", SUPABASE_URL)
        return

    if supabase is None:
        print("❌ 실패: Supabase Client 객체가 초기화되지 않았습니다.")
        return
        
    try:
        # 간단히 Users 테이블을 1개만 조회해봅니다 (테이블이 비어있어도 []를 반환하며 연결은 성공함)
        response = supabase.table("users").select("*").limit(1).execute()
        print("✅ 성공! Supabase 데이터베이스에 정상적으로 연결되었습니다.")
        print("조회된 Users 테이블 데이터 샘플:", response.data)
    except Exception as e:
        print("❌ 예약 실패: 데이터베이스 접근 중 에러가 발생했습니다.")
        print("원인(Error):", str(e))
        print("-> 프로젝트 URL, KEY가 올바른지 다시 확인해주세요.")

if __name__ == "__main__":
    test_connection()
