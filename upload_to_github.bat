@echo off
REM RasswetGifts - Quick GitHub Upload Script for Windows

color 0B
cls

echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║  🚀 RASWET GIFTS - QUICK GITHUB UPLOAD                ║
echo ╚════════════════════════════════════════════════════════╝
echo.

echo Step 1️⃣  Инициализируем Git репозиторий...
git init
git config user.name "Igor"
git config user.email "igor@example.com"
echo.
echo ✅ Git инициализирован
echo.

echo Step 2️⃣  Добавляем все файлы...
git add .
echo.
echo ✅ Файлы добавлены
echo.

echo Step 3️⃣  Создаем первый коммит...
git commit -m "Initial commit: RasswetGifts Crash Game Mode - Fully functional Flask web app"
echo.
echo ✅ Коммит создан
echo.

echo ╔════════════════════════════════════════════════════════╗
echo ║  ГОТОВО К ЗАГРУЗКЕ НА GITHUB!                         ║
echo ╚════════════════════════════════════════════════════════╝
echo.

echo Теперь следуй инструкциям:
echo.

echo 1️⃣  СОЗДАЙ РЕПОЗИТОРИЙ НА GITHUB:
echo    → https://github.com/new
echo    → Repository name: raswet-gifts
echo    → Выбираешь Public
echo    → Создаешь БЕЗ README
echo.

echo 2️⃣  ЗАПУСТИ ЭТИ 3 КОМАНДЫ (замени ТВО_НИК на свой никнейм):
echo.
echo    git remote add origin https://github.com/ТВО_НИК/raswet-gifts.git
echo    git branch -M main
echo    git push -u origin main
echo.

echo ⚠️  Замени 'ТВО_НИК' на свой GitHub никнейм!
echo.

echo 3️⃣  ЕСЛИ ПОПРОСИТ ПАРОЛЬ:
echo    → Используй GitHub Personal Access Token
echo    → Создай тут: https://github.com/settings/tokens
echo.

pause
