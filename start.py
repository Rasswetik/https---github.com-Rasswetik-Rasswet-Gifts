#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple app initialization and runner
"""
import os
import sys

# Add the project directory to the path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

if __name__ == '__main__':
    from app import app, init_db
    
    print("\n" + "="*60)
    print("🎮 RasswetGifts - Инициализация приложения")
    print("="*60 + "\n")
    
    # Initialize database
    print("🔧 Инициализация базы данных...")
    try:
        with app.app_context():
            init_db()
        print("✅ База данных готова!\n")
    except Exception as e:
        print(f"⚠️ Ошибка инициализации БД: {e}\n")
    
    # Start the server
    print("🚀 Запуск Flask сервера...")
    print("📍 Адрес: http://127.0.0.1:5000")
    print("📍 Crash режим: http://127.0.0.1:5000/crash")
    print("\n⚡ Нажмите Ctrl+C для остановки\n")
    
    try:
        app.run(
            host='127.0.0.1',
            port=5000,
            debug=True,
            use_reloader=False  # Set to False to avoid reload issues
        )
    except KeyboardInterrupt:
        print("\n\n🛑 Сервер остановлен")
        sys.exit(0)
