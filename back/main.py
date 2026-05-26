import sys
if sys.platform != "win32":
    try:
        import uvloop
        uvloop.install()
    except ImportError:
        pass

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import standard routers
from routers import users, dictionary, chat, sandbox, benchmark, attendance, quiz

app = FastAPI(title="Antutor Metric AI Backend", description="Sejong University Capstone Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:8080",
        # --- Production (Vercel) ---
        # Vercel 배포 완료 후 아래에 실제 URL 추가
        # "https://antutor.vercel.app",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",  # 모든 Vercel 프리뷰 URL 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# Application API Endpoints (Routers)
# ---------------------------------------------------------
from database import supabase

app.include_router(users.router)
app.include_router(dictionary.router)
app.include_router(chat.router)
app.include_router(sandbox.router)
app.include_router(benchmark.router)
app.include_router(attendance.router)
app.include_router(quiz.router)

@app.get("/debug-concepts")
def debug_concepts():
    return supabase.table("concepts").select("name").execute().data
