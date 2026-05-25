from fastapi import APIRouter, HTTPException
from typing import List
from schemas import QuizQuestionOut, QuizSubmission, QuizResultOut
from services.quiz_service import QuizService

router = APIRouter(
    prefix="/quiz",
    tags=["Quiz"]
)

@router.get("/{concept}", response_model=List[QuizQuestionOut])
def get_quiz_questions(concept: str):
    """
    특정 개념(예: '인플레이션')에 대한 퀴즈 문항들을 반환합니다.
    """
    # if concept != "인플레이션":
    #     raise HTTPException(status_code=404, detail="현재 '인플레이션' 주제의 퀴즈만 제공됩니다.")
    
    return QuizService.get_inflation_questions()

@router.post("/submit", response_model=QuizResultOut)
def submit_quiz(submission: QuizSubmission):
    """
    퀴즈 답변을 제출하고, 확신도 기반 채점(CBM) 방식의 점수를 계산합니다.
    사후 테스트인 경우, 사전 테스트 점수와 비교하여 Hake's Gain(실력 향상도)를 함께 반환합니다.
    """
    return QuizService.evaluate_submission(submission)
