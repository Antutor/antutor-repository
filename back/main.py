from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import standard routers
from routers import users, dictionary, chat, sandbox, benchmark

app = FastAPI(title="Antutor Metric AI Backend", description="Sejong University Capstone Backend")

# 이 코드가 있어야 프론트엔드에서 백엔드 데이터를 읽을 수 있음
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], # 리액트 주소
    allow_credentials=True,
    allow_methods=["*"], # 모든 방식(GET, POST 등) 허용
    allow_headers=["*"], # 모든 헤더 허용
)

# ---------------------------------------------------------
# Application API Endpoints (Routers)
# ---------------------------------------------------------

app.include_router(users.router)
app.include_router(dictionary.router)
app.include_router(chat.router)
app.include_router(sandbox.router)
app.include_router(benchmark.router)
