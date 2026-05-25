from fastapi import APIRouter, Depends, HTTPException
from typing import List
from schemas import QuizQuestionOut, QuizSubmission, QuizResultOut
from services.quiz_service import QuizService
from dependencies import get_current_user

router = APIRouter(
    prefix="/quiz",
    tags=["Quiz"]
)

@router.get("/{concept}", response_model=List[QuizQuestionOut])
def get_quiz_questions(concept: str):
    """
    특정 개념(예: '인플레이션')에 대한 퀴즈 문항들을 반환합니다.
    """
    return QuizService.get_inflation_questions()

@router.post("/submit", response_model=QuizResultOut)
def submit_quiz(submission: QuizSubmission, current_user: dict = Depends(get_current_user)):
    """
    퀴즈 답변을 제출하고, 확신도 기반 채점(CBM) 방식의 점수를 계산합니다.
    사후 테스트인 경우, 사전 테스트 점수와 비교하여 Hake's Gain(실력 향상도)를 함께 반환합니다.
    """
    # 프론트엔드에서 넘어온 userName (TestUser) 대신, 토큰에서 추출한 진짜 UUID를 매핑
    real_user_id = current_user.get("user_id", current_user.get("id"))
    submission.user_id = real_user_id
    
    return QuizService.evaluate_submission(submission)
