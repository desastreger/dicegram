@echo off
REM Dicegram — local dev launcher
REM Opens two terminal windows (backend + frontend) and the browser.

cd /d "%~dp0"

REM Venv lives outside OneDrive — Files-On-Demand corrupts platform binaries.
set "VENV_DIR=%LOCALAPPDATA%\dicegram-venv"
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"

if not exist "%VENV_PY%" (
    echo [setup] Creating Python venv at %VENV_DIR% ...
    python -m venv "%VENV_DIR%" || goto :err
    "%VENV_PY%" -m pip install --upgrade pip --quiet || goto :err
    "%VENV_PY%" -m pip install -r backend\requirements.txt || goto :err
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
start "Dicegram API (backend :8000)" cmd /k "cd /d %~dp0backend && "%VENV_PY%" -m uvicorn app.main:app --reload --port 8000"

echo [run] Starting frontend on http://localhost:5173 ...
start "Dicegram UI (frontend :5173)" cmd /k "cd /d %~dp0frontend && npm run dev -- --port 5173"

timeout /t 4 >nul
start http://localhost:5173
exit /b 0

:err
echo [error] Setup failed. See messages above.
exit /b 1
