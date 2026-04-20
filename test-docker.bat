@echo off
setlocal

echo [dicegram] Checking Docker is available...
docker info >nul 2>&1
if errorlevel 1 (
    echo [dicegram] ERROR: Docker is not running. Start Docker Desktop and try again.
    exit /b 1
)

echo [dicegram] Building and starting container...
echo [dicegram] App will be at http://localhost:8000
echo [dicegram] Press Ctrl+C to stop.
echo.

start "" http://localhost:8000

docker compose up --build
