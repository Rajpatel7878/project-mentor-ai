@echo off
echo Starting Project Mentor AI...

start "Mentor Backend" cmd /k "cd /d %~dp0backend && python -m venv venv 2>nul && call venv\Scripts\activate.bat && pip install -r requirements.txt -q && uvicorn app.main:app --reload --port 8000"

timeout /t 5 /nobreak >nul

start "Mentor Frontend" cmd /k "cd /d %~dp0frontend && npm install && npm run dev"

echo.
echo Project Mentor AI is starting...
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo.
pause
