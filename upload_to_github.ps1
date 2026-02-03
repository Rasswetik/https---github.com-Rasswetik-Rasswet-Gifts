#!/usr/bin/env powershell
# RasswetGifts - Quick GitHub Upload Script

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  🚀 RASWET GIFTS - QUICK GITHUB UPLOAD                ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Step 1: Initialize Git
Write-Host "Step 1️⃣  Инициализируем Git репозиторий..." -ForegroundColor Yellow
git init
git config user.name "Igor"
git config user.email "igor@example.com"
Write-Host "✅ Git инициализирован`n"

# Step 2: Add all files
Write-Host "Step 2️⃣  Добавляем все файлы..." -ForegroundColor Yellow
git add .
Write-Host "✅ Файлы добавлены`n"

# Step 3: Create initial commit
Write-Host "Step 3️⃣  Создаем первый коммит..." -ForegroundColor Yellow
git commit -m "Initial commit: RasswetGifts Crash Game Mode - Fully functional Flask web app with Telegram integration"
Write-Host "✅ Коммит создан`n"

# Step 4: Instructions for GitHub
Write-Host "╔════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  ГОТОВО К ЗАГРУЗКЕ НА GITHUB!                         ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════╝`n" -ForegroundColor Green

Write-Host "Теперь следуй инструкциям:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1️⃣  СОЗДАЙ ПУСТОЙ РЕПОЗИТОРИЙ НА GITHUB:" -ForegroundColor Yellow
Write-Host "   → Переходишь на https://github.com/new" -ForegroundColor White
Write-Host "   → Repository name: raswet-gifts" -ForegroundColor White
Write-Host "   → Выбираешь Public" -ForegroundColor White
Write-Host "   → Создаешь БЕЗ README, .gitignore, license" -ForegroundColor White
Write-Host ""

Write-Host "2️⃣  ЗАМЕНИ НИЖЕ СВОЙ НИКНЕЙМ И ЗАПУСТИ КОМАНДЫ:" -ForegroundColor Yellow
Write-Host ""
Write-Host "   git remote add origin https://github.com/ТВО_НИК/raswet-gifts.git" -ForegroundColor Cyan
Write-Host "   git branch -M main" -ForegroundColor Cyan
Write-Host "   git push -u origin main" -ForegroundColor Cyan
Write-Host ""
Write-Host "   ⚠️  Замени 'ТВО_НИК' на свой GitHub никнейм!" -ForegroundColor Red
Write-Host ""

Write-Host "3️⃣  ЕСЛИ ВСЕ ПРОШЛО УСПЕШНО:" -ForegroundColor Yellow
Write-Host "   → Твой код загружен на GitHub!" -ForegroundColor Green
Write-Host "   → Переходишь на https://github.com/ТВО_НИК/raswet-gifts" -ForegroundColor Green
Write-Host "   → Видишь все файлы в репозитории" -ForegroundColor Green
Write-Host ""

Write-Host "📍 КОПИРУЙ И ЗАПУСТИ ЭТИ 3 КОМАНДЫ:" -ForegroundColor Magenta
Write-Host ""
Write-Host "git remote add origin https://github.com/ТВО_НИК/raswet-gifts.git`ngit branch -M main`ngit push -u origin main" -ForegroundColor Cyan
Write-Host ""

Write-Host "Когда запросит пароль - используй GitHub Personal Access Token" -ForegroundColor Yellow
Write-Host "(Создай тут: https://github.com/settings/tokens)" -ForegroundColor Yellow
Write-Host ""
