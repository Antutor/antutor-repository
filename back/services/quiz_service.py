from schemas import QuizQuestionOut, QuizSubmission, QuizResultOut, QuizAnswerDetailOut
from typing import List
from database import supabase
import math

class QuizService:
    @staticmethod
    def get_inflation_questions() -> List[QuizQuestionOut]:
        # '인플레이션' 관련 문제를 5개 가져옵니다.
        # 난이도나 카테고리 필터가 필요하다면 추후 .eq() 조건을 추가할 수 있습니다.
        res = supabase.table("questions").select("*").limit(5).execute()
        questions_data = res.data
        
        result = []
        for q in questions_data:
            result.append(QuizQuestionOut(
                id=q.get("question_id"),
                concept="인플레이션",
                question=q.get("question_text", ""),
                choices=[
                    q.get("option_1", ""),
                    q.get("option_2", ""),
                    q.get("option_3", ""),
                    q.get("option_4", ""),
                    q.get("option_5", "")
                ]
            ))
        return result

    @staticmethod
    def _calculate_cbm_score(is_correct: bool, confidence_level: int) -> int:
        if confidence_level not in [1, 2, 3]:
            return 0
        
        if is_correct:
            if confidence_level == 1: return 1
            if confidence_level == 2: return 2
            if confidence_level == 3: return 3
        else:
            if confidence_level == 1: return 0
            if confidence_level == 2: return -2
            if confidence_level == 3: return -6
        return 0

    @staticmethod
    def _calculate_hakes_gain(pre_score: float, post_score: float, perfect_score: float) -> float:
        # 만점인 경우 공식의 분모가 0이 되어 계산이 불가능하므로, 향상 여지가 없었다고 가정하고 0.0을 반환
        if perfect_score == pre_score:
            return 0.0
        return (post_score - pre_score) / (perfect_score - pre_score)

    @staticmethod
    def evaluate_submission(submission: QuizSubmission) -> QuizResultOut:
        question_ids = [ans.question_id for ans in submission.answers]
        if not question_ids:
            return QuizResultOut(session_id=submission.session_id, score=0, max_score=0)

        # DB에서 제출된 문제들의 정답과 해설 가져오기
        questions_res = supabase.table("questions").select("question_id, correct_option, commentary").in_("question_id", question_ids).execute()
        questions_map = {q["question_id"]: {"correct_option": q["correct_option"], "commentary": q.get("commentary", "")} for q in questions_res.data}
        
        total_score = 0
        max_possible_score = len(submission.answers) * 3 # 문항당 최대 3점
        
        evaluated_answers = []
        
        # 제출된 답안을 순회하며 CBM 방식 채점
        for answer_sub in submission.answers:
            q_info = questions_map.get(answer_sub.question_id)
            correct_option = q_info["correct_option"] if q_info else None
            is_correct = False
            earned_score = 0
            
            if correct_option is not None:
                # 선택지 번호(1~5)와 정답 번호(1~5) 비교
                is_correct = (correct_option == answer_sub.selected_choice)
                earned_score = QuizService._calculate_cbm_score(is_correct, answer_sub.confidence_level)
                total_score += earned_score
                
            evaluated_answers.append({
                "question_id": answer_sub.question_id,
                "selected_option": answer_sub.selected_choice,
                "confidence_level": answer_sub.confidence_level,
                "is_correct": is_correct,
                "earned_score": earned_score
            })
                
        session_id = submission.session_id
        user_id = submission.user_id
        quiz_type = "PRE" if submission.is_pre_test else "POST"
        
        # 1. quiz_attempts 테이블에 기록 저장
        attempt_res = supabase.table("quiz_attempts").insert({
            "session_id": session_id,
            "user_id": user_id,
            "quiz_type": quiz_type,
            "total_score": total_score
        }).execute()
        
        # 새로 생성된 시도(attempt)의 ID 가져오기
        attempt_id = attempt_res.data[0]["attempt_id"]
        
        # 2. quiz_answers 테이블에 각 문항별 상세 응답 내역 저장
        answers_insert_data = []
        for ea in evaluated_answers:
            answers_insert_data.append({
                "attempt_id": attempt_id,
                "question_id": ea["question_id"],
                "selected_option": ea["selected_option"],
                "confidence_level": ea["confidence_level"],
                "is_correct": ea["is_correct"],
                "earned_score": ea["earned_score"]
            })
            
        if answers_insert_data:
            supabase.table("quiz_answers").insert(answers_insert_data).execute()
            
        skill_improvement = None
        details = None
            
        # 3. 사후 퀴즈인 경우 사전 퀴즈 점수 조회 및 Hake's Gain 계산, 그리고 세션 테이블 업데이트
        if quiz_type == "POST":
            # 사후 퀴즈인 경우에만 정답과 해설 상세 내역 제공
            details = [
                QuizAnswerDetailOut(
                    question_id=ans.question_id,
                    correct_option=questions_map.get(ans.question_id, {}).get("correct_option", 0),
                    commentary=questions_map.get(ans.question_id, {}).get("commentary", "")
                )
                for ans in submission.answers
            ]
            
            # 동일 세션의 가장 최근 PRE 퀴즈 결과 조회
            pre_test_res = supabase.table("quiz_attempts") \
                .select("total_score") \
                .eq("session_id", session_id) \
                .eq("quiz_type", "PRE") \
                .order("created_at", desc=True) \
                .limit(1) \
                .execute()
            
            if pre_test_res.data:
                pre_test_score = pre_test_res.data[0]["total_score"]
                skill_improvement = QuizService._calculate_hakes_gain(
                    pre_score=float(pre_test_score),
                    post_score=float(total_score),
                    perfect_score=float(max_possible_score)
                )
                
                # sessions 테이블에 hakes_gain 수치 업데이트
                supabase.table("sessions").update({
                    "hakes_gain": skill_improvement
                }).eq("session_id", session_id).execute()
                
        return QuizResultOut(
            session_id=session_id,
            score=total_score,
            max_score=max_possible_score,
            skill_improvement=skill_improvement,
            details=details
        )
