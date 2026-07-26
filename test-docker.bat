@echo off
setlocal

echo [dicegram] Checking Docker is available...
docker info >nul 2>&1
if errorlevel 1 (
    echo [dicegram] ERROR: Docker is not running. Start Docker Desktop and try again.
    exit /b 1
)

if not exist ".env" (
    echo [dicegram] Creating .env from .env.example with a generated SECRET_KEY...
    copy .env.example .env >nul
    powershell -NoProfile -Command "$b=([guid]::NewGuid().ToString('N') + [guid]::NewGuid().ToString('N')); (Get-Content .env) -replace '^SECRET_KEY=.*', ('SECRET_KEY=' + $b) | Set-Content .env"
    if errorlevel 1 (
        echo [dicegram] ERROR: could not generate SECRET_KEY via PowerShell.
        echo [dicegram] Edit .env by hand: set SECRET_KEY to a long, 32+ char random string, then re-run.
        exit /b 1
    )
    echo [dicegram] .env created. Review it before going live.
)

echo [dicegram] Building and starting the container (first run takes a few minutes)...
docker compose up --build -d
if errorlevel 1 (
    echo [dicegram] ERROR: docker compose failed to start. See output above.
    exit /b 1
)

echo [dicegram] Waiting for the app to come up...
timeout /t 6 /nobreak >nul

echo [dicegram] App is at http://localhost:8000
start "" http://localhost:8000

echo [dicegram] Tailing logs. Ctrl+C stops following (container keeps running -- run "docker compose down" to stop it).
docker compose logs -f
