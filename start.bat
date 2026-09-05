@echo off
setlocal enabledelayedexpansion

echo ========================================================
echo         Starting Project Mentor AI (Jarvis Core)
echo ========================================================
echo.

rem Auto-initialize environment configuration files if missing
if not exist "%~dp0.env" (
    if exist "%~dp0.env.example" (
        echo [*] Initializing root .env from .env.example...
        copy "%~dp0.env.example" "%~dp0.env" >nul
    )
)

if not exist "%~dp0backend\.env" (
    if exist "%~dp0backend\.env.example" (
        echo [*] Initializing backend\.env from backend\.env.example...
        copy "%~dp0backend\.env.example" "%~dp0backend\.env" >nul
    )
)

if not exist "%~dp0frontend\.env.local" (
    if exist "%~dp0frontend\.env.local.example" (
        echo [*] Initializing frontend\.env.local from .env.local.example...
        copy "%~dp0frontend\.env.local.example" "%~dp0frontend\.env.local" >nul
    )
)

echo [*] Launching FastAPI Backend (Port 8000)...
start "Mentor Backend (FastAPI)" cmd /k "cd /d %~dp0backend && call venv\Scripts\activate.bat && uvicorn app.main:app --reload --port 8000"

timeout /t 3 /nobreak >nul

echo [*] Launching Next.js 14 Frontend (Port 3000)...
start "Mentor Frontend (Next.js)" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ========================================================
echo  All systems initializing:
echo    - Web UI:      http://localhost:3000
echo    - API Docs:    http://localhost:8000/docs
echo    - Telemetry:   http://localhost:8000/api/devices/telemetry
echo    - Analytics:   http://localhost:8000/api/analytics/usage
echo ========================================================
echo.
pause

