@echo off

cd /d "%~dp0backend"

start "CLUE Server" cmd /k "call .venv\Scripts\activate && python -m uvicorn app.main:app --reload"

timeout /t 3 /nobreak >nul

start "" http://127.0.0.1:8000