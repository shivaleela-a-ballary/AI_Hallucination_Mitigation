@echo off
title AI Hallucination Mitigation System Launcher
echo ===================================================
echo   Starting AI Hallucination Mitigation System
echo ===================================================

cd /d "%~dp0"

echo [1/2] Launching FastAPI Backend on http://0.0.0.0:8000 ...
start "Backend - FastAPI" cmd /k "title Backend API && .venv\Scripts\python.exe -m uvicorn api.app:app --app-dir backend --host 0.0.0.0 --port 8000 --reload"

echo [2/2] Launching Frontend on http://localhost:8080 ...
start "Frontend - Vite" cmd /k "title Frontend UI && cd frontend && npm run dev"

echo.
echo ===================================================
echo   Both services have been launched in separate windows!
echo   - Backend API: http://127.0.0.1:8000
echo   - API Docs:    http://127.0.0.1:8000/docs
echo   - Frontend UI: http://localhost:8080
echo ===================================================
timeout /t 5 >nul
