# AI Hallucination Mitigation System Launcher for PowerShell
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "  Starting AI Hallucination Mitigation System" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan

$rootDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "`n[1/2] Starting FastAPI Backend on http://0.0.0.0:8000 ..." -ForegroundColor Yellow
Start-Process -FilePath "cmd.exe" -ArgumentList "/k title Backend API && cd /d `"$rootDir`" && .venv\Scripts\python.exe -m uvicorn api.app:app --app-dir backend --host 0.0.0.0 --port 8000 --reload"

Write-Host "[2/2] Starting Frontend on http://localhost:8080 ..." -ForegroundColor Yellow
Start-Process -FilePath "cmd.exe" -ArgumentList "/k title Frontend UI && cd /d `"$rootDir\frontend`" && npm run dev"

Write-Host "`n===================================================" -ForegroundColor Green
Write-Host "  Both services are running!" -ForegroundColor Green
Write-Host "  - Backend API: http://127.0.0.1:8000" -ForegroundColor White
Write-Host "  - API Docs:    http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host "  - Frontend UI: http://localhost:8080" -ForegroundColor White
Write-Host "===================================================" -ForegroundColor Green
