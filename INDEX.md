# 📚 RasswetGifts - Центр документации

Добро пожаловать! Здесь вы найдете всё необходимое для работы с приложением.

## 🚀 Начало работы

### Для нетерпеливых (3 минуты)

👉 **[QUICK_START.md](QUICK_START.md)** - Самый быстрый способ запустить

### Для внимательных (15 минут)

👉 **[SETUP_INSTRUCTIONS.md](SETUP_INSTRUCTIONS.md)** - Пошаговая инструкция

### Для любопытных (30 минут)

👉 **[README.md](README.md)** - Полная документация проекта

---

## 📋 Что было сделано?

👉 **[CHANGELOG.md](CHANGELOG.md)** - Полный отчет об исправлениях

Короче:

- ✅ Исправлено 7 ошибок в JavaScript
- ✅ Переконфигурировано приложение для локального запуска
- ✅ Установлены расширения VS Code
- ✅ Созданы удобные скрипты запуска
- ✅ Подготовлена вся документация

---

## 🎮 Как запустить?

### Вариант 1: Windows (самый простой)

```cmd
run.bat
```

### Вариант 2: Python (любая ОС)

```bash
python start.py
```

### Вариант 3: VS Code (F5)

1. Нажми `F5`
2. Выбери конфигурацию
3. Нажми зеленую кнопку ▶️

---

## 📁 Файлы проекта

```
RasswetGifts/
├── 📄 README.md ..................... Полная документация
├── 📄 QUICK_START.md ............... Быстрый старт
├── 📄 SETUP_INSTRUCTIONS.md ........ Подробная инструкция
├── 📄 CHANGELOG.md ................. Отчет об исправлениях
├── 📄 INFO.txt ..................... Краткая справка
│
├── 🎮 ЗАПУСК
├── 📄 run.py ....................... Основной скрипт
├── 📄 start.py ..................... Альтернативный скрипт
├── 📄 run.bat ...................... Батник для Windows
├── 📄 run.ps1 ...................... PowerShell скрипт
├── 📄 check_config.py .............. Проверка конфигурации
│
├── ⚙️ КОНФИГУРАЦИЯ
├── 📄 app.py ....................... Flask приложение ✅
├── 📄 bot.py ....................... Telegram бот
├── 📄 requirements.txt ............. Зависимости
├── 📄 .vscode/launch.json .......... Отладчик VS Code
├── 📄 .vscode/settings.json ........ Настройки VS Code
├── 📄 .gitignore ................... Git игнорирование
│
├── 🎨 ШАБЛОНЫ
├── 📁 templates/
│   ├── crash.html ✅ ИСПРАВЛЕНО!
│   ├── base.html
│   └── ...
│
├── 📊 ДАННЫЕ
├── 📁 data/
│   ├── cases.json
│   ├── crash_status.json
│   └── raswet_gifts.db (создается автоматически)
│
└── 🖼️ СТАТИКА
    └── 📁 static/
        └── gifs/
            └── crash.gif
```

---

## ✨ Главные исправления

### 1. Ошибка в JavaScript (crash.html)

```javascript
// ❌ БЫЛО
let amount = parseInt(amountInput.value);

// ✅ СТАЛО
let amount = parseInt(document.getElementById("amount").value);
```

### 2. Неправильный API

```javascript
// ❌ БЫЛО
await fetch("/api/telegram/user?user_id=" + user.id);

// ✅ СТАЛО
await fetch("/api/crash/status");
```

### 3. Отсутствие обработки ошибок

```javascript
// ✅ ДОБАВЛЕНО
try {
  // код
} catch (e) {
  alert("Ошибка: " + e.message);
}
```

### 4. Конфигурация для локального запуска

```python
# ❌ БЫЛО
BASE_PATH = '/home/rasswetik52/mysite'

# ✅ СТАЛО
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
```

---

## 🔍 Быстрая проверка

Хочешь убедиться что всё готово? Запусти:

```bash
python check_config.py
```

Это проверит:

- ✅ Версию Python
- ✅ Наличие всех файлов
- ✅ Права доступа
- ✅ Необходимые модули

---

## 🎯 После запуска

Когда сервер запущен, открой в браузере:

| URL                             | Описание                  |
| ------------------------------- | ------------------------- |
| http://localhost:5000/          | Главная страница          |
| http://localhost:5000/crash     | CRASH режим ✅ ИСПРАВЛЕНО |
| http://localhost:5000/cases     | Кейсы                     |
| http://localhost:5000/inventory | Инвентарь                 |

---

## 🐛 Если что-то не работает

### Python не установлен?

Скачай с https://www.python.org/

### Ошибка "No module named 'flask'"?

```bash
pip install flask flask-cors
```

### Порт 5000 занят?

Измени в `app.py`:

```python
app.run(host='127.0.0.1', port=5001)
```

### БД заблокирована?

```bash
# Удали старую БД
del data\raswet_gifts.db

# Запусти заново
python start.py
```

### Ещё что-то сломалось?

1. Посмотри в консоль Flask - там описание ошибки
2. Откройте DevTools браузера (F12) - на вкладке Console
3. Прочитай README.md и SETUP_INSTRUCTIONS.md
4. Если всё еще не работает - удали всё и начни заново 😄

---

## 📞 Полезные ссылки

- **Python docs**: https://docs.python.org/3/
- **Flask docs**: https://flask.palletsprojects.com/
- **SQLite docs**: https://www.sqlite.org/docs.html
- **VS Code docs**: https://code.visualstudio.com/docs

---

## 🎉 Готово!

Приложение полностью готово к работе!

```
┌─────────────────────────────────────┐
│  🚀 Запусти скрипт и наслаждайся!  │
└─────────────────────────────────────┘
```

---

**Последнее обновление**: 3 февраля 2026  
**Версия**: 1.0 (Fully Fixed & Optimized)  
**Статус**: ✅ Ready for Development
