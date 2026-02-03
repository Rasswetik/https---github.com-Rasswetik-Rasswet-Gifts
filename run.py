#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для инициализации и запуска RasswetGifts приложения локально
"""

import os
import sys
import subprocess

def install_requirements():
    """Установка зависимостей из requirements.txt"""
    print("\n📦 Установка зависимостей...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "-r", "requirements.txt"])
        print("✅ Зависимости установлены успешно!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка при установке зависимостей: {e}")
        return False

def check_data_files():
    """Проверка наличия необходимых файлов данных"""
    print("\n📁 Проверка файлов данных...")
    required_files = [
        'data/cases.json',
        'data/crash_status.json'
    ]
    
    for file_path in required_files:
        if not os.path.exists(file_path):
            print(f"⚠️ Файл не найден: {file_path}")
        else:
            print(f"✅ {file_path} найден")

def main():
    """Основная функция"""
    print("🎮 RasswetGifts - Инициализация приложения")
    print("=" * 50)
    
    # Установка зависимостей
    if not install_requirements():
        print("⚠️ Продолжаем несмотря на ошибку установки зависимостей...")
    
    # Проверка файлов
    check_data_files()
    
    # Запуск приложения
    print("\n🚀 Запуск Flask приложения на http://localhost:5000")
    print("=" * 50)
    print("Нажмите Ctrl+C для остановки сервера\n")
    
    try:
        from app import app, init_db
        
        # Инициализируем БД
        with app.app_context():
            print("🔧 Инициализация базы данных...")
            init_db()
            print("✅ База данных готова!")
        
        # Запускаем приложение
        app.run(host='127.0.0.1', port=5000, debug=True, use_reloader=True)
        
    except KeyboardInterrupt:
        print("\n\n🛑 Сервер остановлен пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Ошибка при запуске: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
