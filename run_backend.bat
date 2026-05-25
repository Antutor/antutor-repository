@echo off
title Antutor Backend Server

:: 1. back 폴더로 이동 (여기에 main.py가 있으니까요!)
cd /d "%~dp0back"

:: 2. 가상환경 확인 및 생성
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

:: 3. 가상환경 활성화 및 패키지 설치
echo Setting up environment...
call venv\Scripts\activate.bat
python -m pip install -U pip

:: 상위 폴더(..)에 있는 requirements.txt 설치
if exist "..\requirements.txt" (
    pip install -r "..\requirements.txt"
)

:: 4. 서버 실행
echo Starting Backend Server on http://localhost:8000...
uvicorn main:app --reload --port 8000

pause