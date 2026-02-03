# RasswetGifts - Quick Start Script for PowerShell

Write-Host ""
Write-Host "========================================"
Write-Host "   🎮 RasswetGifts - Crash Game Server"
Write-Host "========================================"
Write-Host ""

# Check if Python is installed
$pythonCheck = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Python не установлен или не в PATH!"
    Write-Host "Установите Python с https://www.python.org/"
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

Write-Host "✅ Python найден: $pythonCheck"
Write-Host ""

# Install requirements
Write-Host "📦 Установка зависимостей..." -ForegroundColor Yellow
python -m pip install -q -r requirements.txt
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Зависимости установлены!" -ForegroundColor Green
} else {
    Write-Host "⚠️ Некоторые зависимости могут быть установлены неправильно" -ForegroundColor Yellow
}
Write-Host ""

# Run the app
Write-Host "🚀 Запуск приложения на http://localhost:5000" -ForegroundColor Green
Write-Host ""
Write-Host "Нажмите Ctrl+C для остановки сервера" -ForegroundColor Cyan
Write-Host ""

python run.py

Read-Host "Нажмите Enter для выхода"
