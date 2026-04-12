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
LOCAL_LLM_MODEL = os.getenv("LOCAL_LLM_MODEL", "qwen2.5:7b")
DRAFT_LLM_MODEL = os.getenv("DRAFT_LLM_MODEL", "qwen2.5:7b")
DEBATE_LLM_MODEL = os.getenv("DEBATE_LLM_MODEL", "qwen3:8b")
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
DEEPL_API_KEY = os.getenv("DEEPL_API_KEY", "")
ENABLE_KOREAN_TRANSLATION = os.getenv("ENABLE_KOREAN_TRANSLATION", "true").lower() == "true"

# --- Supabase Database Configuration ---
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# --- Neo4j Knowledge Graph Configuration ---
NEO4J_URI      = os.getenv("NEO4J_URI", "")
NEO4J_USER     = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

# --- Keyword Detection for Give-Up (Supports English & Korean) ---
GIVE_UP_KEYWORDS = [
    # English
    "don't know", "give up", "not sure", "no idea", "hint", 
    "can't explain", "too hard", "stuck", "confused", "help",
    # Korean
    "모르겠", "잘 몰라", "포기", "힌트", "모름", "알려줘", "도와줘",
    "너무 어렵", "막혔", "설명 못하", "도움"
]

