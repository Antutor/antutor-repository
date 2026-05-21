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
    model: Optional[str] = None
    temperature: Optional[float] = None

class ModeratorSandboxRequest(BaseModel):
    user_answer: str
    lowest_persona: str
    expert_results: List[Dict[str, Any]]
    custom_prompt: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None

class GraphSandboxRequest(BaseModel):
    concept: str
    user_answer: str
    definition: str
    acceptable_extensions: Optional[str] = ""
    use_real_context: Optional[bool] = False
    model: Optional[str] = None
    temperature: Optional[float] = None

class ScaffoldingSandboxRequest(BaseModel):
    concept_name: str
    ground_truth: str
    kg_context: Optional[str] = ""
    use_real_kg: Optional[bool] = False
    idk_count: Optional[int] = 1           # 1=Nudge, 2=Concept, 3=Fill-blank, 4+=Reveal
    custom_prompt: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None

class ResumeDecisionRequest(BaseModel):
    concept: str
    decision: str  # "resume" or "fresh"
    language: Optional[str] = "ko"
