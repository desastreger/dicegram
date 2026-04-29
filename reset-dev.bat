@echo off
REM Dicegram - hard reset dev servers.
REM Kills anything on backend :8000 and the vite range :5173-:5180,
REM nukes orphan uvicorn / vite-node processes, then restarts both.

setlocal enabledelayedexpansion
cd /d "%~dp0"

set "VENV_DIR=%LOCALAPPDATA%\dicegram-venv"
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"

echo [reset] Closing existing dev servers...

REM --- kill by listening port ---
for %%P in (8000 5173 5174 5175 5176 5177 5178 5179 5180) do (
    for /f "tokens=5" %%A in ('netstat -ano ^| findstr /R /C:":%%P *.*LISTENING"') do (
        taskkill /PID %%A /F >nul 2>&1
    )
)

REM --- kill orphan uvicorn + vite workers (esbuild etc.) ---
wmic process where "commandline like '%%uvicorn app.main:app%%'" call terminate >nul 2>&1
wmic process where "commandline like '%%vite dev%%'" call terminate >nul 2>&1
wmic process where "commandline like '%%node_modules\\vite%%'" call terminate >nul 2>&1
wmic process where "commandline like '%%node_modules\\@esbuild%%'" call terminate >nul 2>&1

REM small settle so Windows releases sockets
timeout /t 2 /nobreak >nul

if not exist "%VENV_PY%" (
    echo [reset] Backend venv missing at %VENV_DIR% -- run start-dev.bat once to bootstrap it.
    exit /b 1
)

if not exist "backend\.env" (
    copy backend\.env.example backend\.env >nul
    echo [reset] Wrote backend\.env from example.
)

if not exist "frontend\node_modules" (
    echo [reset] frontend\node_modules missing -- running npm install...
    pushd frontend
    call npm install || goto :err
    popd
)

echo [run] Backend  -^> http://localhost:8000
start "Dicegram API (:8000)" cmd /k "cd /d %~dp0backend && %VENV_PY% -m uvicorn app.main:app --reload --port 8000"

echo [run] Frontend -^> http://localhost:5173
start "Dicegram UI (:5173)" cmd /k "cd /d %~dp0frontend && npm run dev -- --host 127.0.0.1 --port 5173 --strictPort"

timeout /t 4 /nobreak >nul
start http://localhost:5173
exit /b 0

:err
echo [error] Reset failed. See messages above.
exit /b 1
