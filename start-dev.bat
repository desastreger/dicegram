@echo off
REM Diagram Editor — local dev launcher
REM Opens two terminal windows (backend + frontend) and the browser.

cd /d "%~dp0"

if not exist "backend\.venv\Scripts\python.exe" (
    echo [setup] Creating Python venv and installing backend dependencies...
    python -m venv backend\.venv || goto :err
    backend\.venv\Scripts\python.exe -m pip install --upgrade pip --quiet || goto :err
    backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt || goto :err
)

if not exist "backend\.env" (
    copy backend\.env.example backend\.env >nul
    echo [setup] Wrote backend\.env — edit SECRET_KEY for production.
)

if not exist "frontend\node_modules" (
    echo [setup] Installing frontend dependencies...
    pushd frontend
    call npm install || goto :err
    popd
)

echo [run] Starting backend on http://localhost:8000 ...
start "Diagram API (backend :8000)" cmd /k "cd /d %~dp0backend && .venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000"

echo [run] Starting frontend on http://localhost:5173 ...
start "Diagram UI (frontend :5173)" cmd /k "cd /d %~dp0frontend && npm run dev -- --port 5173"

timeout /t 4 >nul
start http://localhost:5173
exit /b 0

:err
echo [error] Setup failed. See messages above.
exit /b 1
