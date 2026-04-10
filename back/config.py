import os
from dotenv import load_dotenv

# .env 파일의 환경 변수를 불러옵니다. (override=True로 핫리로드 시 즉각 반영)
load_dotenv(override=True)
# --- Authentication Configuration ---
SECRET_KEY = os.getenv("SECRET_KEY", "your-very-secure-secret-key-capstone-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 1 week expiration

# --- Constants are now managed in DB ---

LOCAL_LLM_ENDPOINT = os.getenv("LOCAL_LLM_ENDPOINT", "http://localhost:11434/api/chat")
LOCAL_LLM_MODEL = os.getenv("LOCAL_LLM_MODEL", "gemma3:12b")
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
DEEPL_API_KEY = os.getenv("DEEPL_API_KEY", "")
ENABLE_KOREAN_TRANSLATION = os.getenv("ENABLE_KOREAN_TRANSLATION", "true").lower() == "true"

# --- Supabase Database Configuration ---
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

PROMPTS = {
    "experts": {
        "The Academic Auditor": """You are 'The Academic Auditor'. You act as an impartial evaluator to assess a student's answer against the formal ground truth.
Concept: {concept}
Ground Truth: {ground_truth}
User Answer: {user_answer}

You MUST return a valid JSON object with exactly three keys:
1. "is_contradiction": boolean (true if the user's answer explicitly contradicts the fundamental meaning of the ground truth, false otherwise)
2. "score": float from 0.0 to 1.0 representing accuracy.
3. "feedback": string containing a brief, encouraging assessment.

Return ONLY the JSON object, with no markdown tags (e.g., no ```json).""",
        "The Market Practitioner": "You are 'The Market Practitioner'. Evaluate the concept explanation based on real-world market impacts. Incorporate the following News API RAG context into your assessment.\nNews Context: {context}\nConcept: {concept}\nUser Answer: {user_answer}\nProvide a brief assessment. Finally, on a new line, provide a numerical score from 0.00 to 1.00 enclosed in brackets, e.g., [0.85].",
        "The Macro-Connector": "You are 'The Macro-Connector'. Evaluate how well the explanation connects the concept to broader macroeconomic trends. Incorporate the following Knowledge Graph context into your assessment.\nKnowledge Graph Context: {context}\nConcept: {concept}\nUser Answer: {user_answer}\nProvide a brief assessment. Finally, on a new line, provide a numerical score from 0.00 to 1.00 enclosed in brackets, e.g., [0.85]."
    }
}

# --- Keyword Detection for Give-Up ---
GIVE_UP_KEYWORDS = [
    "don't know", "give up", "not sure", "no idea", "hint", 
    "can't explain", "too hard", "stuck", "confused", "help"
]

