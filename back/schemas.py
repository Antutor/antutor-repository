from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class UserCreate(BaseModel):
    username: str = Field(..., pattern=r"^[A-Za-z0-9]{4,}$")
    password: str = Field(..., pattern=r"^[A-Za-z0-9]{4,}$")

class ChatRequest(BaseModel):
    session_id: str
    concept: str
    user_answer: str
    language: Optional[str] = "ko"

class EndSessionRequest(BaseModel):
    session_id: str
    language: Optional[str] = "ko"

class PromptTuningSandboxRequest(BaseModel):
    system_prompt: str
    user_prompt: str
    model: Optional[str] = None
    temperature: Optional[float] = 0.0
    is_json: Optional[bool] = False

class AgentSandboxRequest(BaseModel):
    persona: str
    concept: str
    user_answer: str
    ground_truth: Optional[str] = None
    definition: Optional[str] = None
    acceptable_extensions: Optional[str] = None
    context: Optional[str] = None
    use_real_context: Optional[bool] = False
    custom_prompt: Optional[str] = None
    language: Optional[str] = "ko"
    model: Optional[str] = None
    temperature: Optional[float] = None

class ModeratorSandboxRequest(BaseModel):
    user_answer: str
    lowest_persona: str
    expert_results: List[Dict[str, Any]]
    custom_prompt: Optional[str] = None
    language: Optional[str] = "ko"
    model: Optional[str] = None
    temperature: Optional[float] = None

class GraphSandboxRequest(BaseModel):
    concept: str
    user_answer: str
    definition: str
    acceptable_extensions: Optional[str] = ""
    use_real_context: Optional[bool] = False
    language: Optional[str] = "ko"
    session_context: Optional[Dict[str, Any]] = None
    model: Optional[str] = None
    temperature: Optional[float] = None

class ScaffoldingSandboxRequest(BaseModel):
    concept_name: str
    definition: str
    acceptable_extensions: Optional[str] = ""
    last_question: Optional[str] = ""    # 빈 문자열 = 첫 또는 정의 기반 힌트
    kg_context: Optional[str] = ""
    use_real_kg: Optional[bool] = False
    idk_count: Optional[int] = 1           # 1=Nudge, 2=Concept, 3=Fill-blank, 4+=Reveal
    student_answer: Optional[str] = ""     # 학생의 현재 턴 답변
    session_context: Optional[str] = ""   # 이전 턴 히스토리 (JSON string)
    custom_prompt: Optional[str] = None
    language: Optional[str] = "ko"
    model: Optional[str] = None
    temperature: Optional[float] = None

class ScaffoldEvalSandboxRequest(BaseModel):
    concept: str
    definition: str
    acceptable_extensions: Optional[str] = ""
    scaffold_step: str
    user_answer: str
    last_hint: str
    language: Optional[str] = "ko"

class ResumeDecisionRequest(BaseModel):
    concept: str
    decision: str  # "resume" or "fresh"
    language: Optional[str] = "ko"

class QuizQuestionOut(BaseModel):
    id: Any
    concept: str
    question: str
    choices: List[str]

class QuizAnswerSubmit(BaseModel):
    question_id: Any
    selected_choice: int
    confidence_level: int # 1(low), 2(mid), 3(high), 0(No Reply)

class QuizSubmission(BaseModel):
    session_id: str
    user_id: str
    concept: str
    is_pre_test: bool
    answers: List[QuizAnswerSubmit]

class QuizAnswerDetailOut(BaseModel):
    question_id: Any
    correct_option: Optional[int] = 0
    commentary: Optional[str] = None
    earned_score: Optional[int] = 0

class QuizResultOut(BaseModel):
    session_id: str
    score: int
    max_score: int
    skill_improvement: Optional[float] = None
    details: Optional[List[QuizAnswerDetailOut]] = None
