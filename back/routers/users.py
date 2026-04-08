from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
import re

from schemas import UserCreate
from auth import get_password_hash, create_access_token, verify_password
from database import users_db
from config import ACCESS_TOKEN_EXPIRE_MINUTES
from services.translator import translate_en_to_ko

router = APIRouter()

@router.get("/check-username")
async def check_username(username: str):
    """지정된 아이디(username)가 이미 데이터베이스에 존재하는지 실시간으로 확인합니다."""
    if not re.match(r"^[A-Za-z0-9]{4,}$", username):
        raise HTTPException(status_code=400, detail="아이디는 영어 또는 숫자로만 4자리 이상 입력해야 합니다.")
        
    if username in users_db:
        return {"available": False, "message": await translate_en_to_ko("Username already exists.")}
    return {"available": True, "message": await translate_en_to_ko("Username is available.")}

@router.post("/register")
async def register(user: UserCreate):
    if user.username in users_db:
        detail = await translate_en_to_ko("Username already registered")
        raise HTTPException(status_code=400, detail=detail)
    
    users_db[user.username] = {
        "hashed_password": get_password_hash(user.password),
        "history": {},
        "completed_concepts": []
    }
    msg = await translate_en_to_ko("User successfully registered")
    return {"message": msg}

@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = users_db.get(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        detail = await translate_en_to_ko("Incorrect username or password")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": form_data.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
