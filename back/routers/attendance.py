from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, date, timedelta
from dependencies import get_current_user
from database import supabase

router = APIRouter(prefix="/api/attendance", tags=["Attendance"])

@router.get("")
async def get_attendance(current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    
    # 현재 달의 1일 날짜 문자열
    today = date.today()
    first_day_of_month = today.replace(day=1).isoformat()
    
    # 1. 이번 달 출석한 날짜 목록 가져오기
    response = supabase.table("user_attendance").select("attendance_date").eq("user_id", user_id).gte("attendance_date", first_day_of_month).execute()
    attended_dates = [row["attendance_date"] for row in response.data]
    
    # 2. 연속 출석일 수(streak) 계산
    all_attendance_response = supabase.table("user_attendance").select("attendance_date").eq("user_id", user_id).order("attendance_date", desc=True).execute()
    all_dates = set([row["attendance_date"] for row in all_attendance_response.data])
    
    streak = 0
    current_date = today
    
    # 오늘 출석 여부 확인
    if today.isoformat() in all_dates:
        streak += 1
        current_date -= timedelta(days=1)
        
    # 어제부터 역순으로 연속 출석 확인
    while current_date.isoformat() in all_dates:
        streak += 1
        current_date -= timedelta(days=1)
        
    return {
        "attended_dates": attended_dates,
        "streak": streak
    }

@router.post("")
async def mark_attendance(current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    today = date.today().isoformat()
    
    # 이미 출석했는지 확인
    response = supabase.table("user_attendance").select("attendance_date").eq("user_id", user_id).eq("attendance_date", today).execute()
    
    if response.data:
        return {"message": "Already attended today.", "attended_date": today}
        
    # 출석 기록 추가
    new_record = {
        "user_id": user_id,
        "attendance_date": today
    }
    
    try:
        supabase.table("user_attendance").insert(new_record).execute()
        return {"message": "Attendance marked successfully.", "attended_date": today}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
