from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    username: str
    password: str

class ChatRequest(BaseModel):
    session_id: str
    concept: str
    user_answer: str

class EndSessionRequest(BaseModel):
    session_id: str

class PromptTuningSandboxRequest(BaseModel):
    system_prompt: str
    user_prompt: str
    model: Optional[str] = None
    temperature: Optional[float] = 0.0
    is_json: Optional[bool] = False
