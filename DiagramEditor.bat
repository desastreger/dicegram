@echo off
:: Diagram Editor - Windows Launcher
:: Double-click this file to launch the application.
:: If Python is not in your PATH, edit the line below to point to your python.exe.

setlocal

:: Try to find python
where python >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON=python
) else (
    where python3 >nul 2>&1
    if %errorlevel% equ 0 (
        set PYTHON=python3
    ) else (
        :: Common install locations
        if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
            set PYTHON="%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
        ) else if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
            set PYTHON="%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
        ) else if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" (
            set PYTHON="%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
        ) else (
            echo.
            echo  ERROR: Python not found.
            echo  Please install Python 3.10+ from https://python.org
            echo  and make sure "Add Python to PATH" is checked during install.
            echo.
            pause
            exit /b 1
        )
    )
)

cd /d "%~dp0"

:: Check dependencies on first run
%PYTHON% -c "import PySide6" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing dependencies...
    %PYTHON% -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo.
        echo  ERROR: Failed to install dependencies.
        echo  Try running manually: pip install -r requirements.txt
        echo.
        pause
        exit /b 1
    )
)

:: Launch the application
%PYTHON% run.py %*
