@echo off
REM RasswetGifts - Quick Start Script for Windows

echo.
echo ========================================
echo   🎮 RasswetGifts - Crash Game Server
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH!
    echo Please install Python from https://www.python.org/
    pause
    exit /b 1
)

echo ✅ Python найден
echo.

REM Install requirements
echo 📦 Установка зависимостей...
python -m pip install -q -r requirements.txt
if errorlevel 1 (
    echo ⚠️ Some dependencies may not have installed correctly
) else (
    echo ✅ Зависимости установлены!
)
echo.

REM Run the app
echo 🚀 Запуск приложения на http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo.

python run.py

pause
