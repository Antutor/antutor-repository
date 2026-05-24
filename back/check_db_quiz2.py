import sys
import os

# 현재 디렉토리가 back이므로 모듈 검색 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import supabase

print("Testing Supabase Connection for Quiz Tables...")

try:
    print("\n[1] Fetching questions:")
    res = supabase.table("questions").select("*").limit(2).execute()
    print(res.data)
    
    print("\n[2] Fetching quiz_attempts:")
    res2 = supabase.table("quiz_attempts").select("*").limit(2).execute()
    print(res2.data)
    
    print("\n[3] Fetching quiz_answers:")
    res3 = supabase.table("quiz_answers").select("*").limit(2).execute()
    print(res3.data)
    
    print("\n[4] Fetching sessions (hakes_gain check):")
    res4 = supabase.table("sessions").select("session_id, hakes_gain").limit(2).execute()
    print(res4.data)
    
    print("\n✅ Connection and queries successful!")
except Exception as e:
    print("\n❌ Error:", e)
