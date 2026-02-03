#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration checker для RasswetGifts
Проверяет что всё готово к запуску
"""

import os
import sys

def check_python():
    """Проверка версии Python"""
    print("🐍 Python версия:", end=" ")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ {version.major}.{version.minor} (Нужна 3.8+)")
        return False
    print(f"✅ {version.major}.{version.minor}.{version.micro}")
    return True

def check_files():
    """Проверка наличия необходимых файлов"""
    print("\n📁 Проверка файлов:")
    required_files = [
        'app.py',
        'bot.py',
        'requirements.txt',
        'templates/crash.html',
        'templates/base.html',
        'data/cases.json',
    ]
    
    all_exist = True
    for file in required_files:
        if os.path.exists(file):
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} (НЕ НАЙДЕН)")
            all_exist = False
    
    return all_exist

def check_directories():
    """Проверка наличия необходимых директорий"""
    print("\n📂 Проверка директорий:")
    required_dirs = [
        'templates',
        'static',
        'data',
    ]
    
    all_exist = True
    for dir in required_dirs:
        if os.path.isdir(dir):
            print(f"   ✅ {dir}/")
        else:
            print(f"   ❌ {dir}/ (ОТСУТСТВУЕТ)")
            all_exist = False
    
    return all_exist

def check_imports():
    """Проверка импортов"""
    print("\n📦 Проверка импортов:")
    
    required_modules = [
        ('flask', 'Flask'),
        ('sqlite3', 'SQLite3'),
    ]
    
    all_ok = True
    for module, name in required_modules:
        try:
            __import__(module)
            print(f"   ✅ {name}")
        except ImportError:
            print(f"   ❌ {name} (НЕ УСТАНОВЛЕН)")
            all_ok = False
    
    return all_ok

def check_permissions():
    """Проверка прав доступа"""
    print("\n🔐 Проверка прав:")
    
    try:
        # Пытаемся создать файл в data
        test_file = 'data/.test'
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        print("   ✅ Права доступа в порядке")
        return True
    except Exception as e:
        print(f"   ❌ Проблема с правами: {e}")
        return False

def main():
    """Главная функция проверки"""
    print("\n" + "="*60)
    print("🎮 RasswetGifts - Проверка конфигурации")
    print("="*60)
    
    results = {
        'Python': check_python(),
        'Файлы': check_files(),
        'Директории': check_directories(),
        'Импорты': check_imports(),
        'Права доступа': check_permissions(),
    }
    
    print("\n" + "="*60)
    print("📊 РЕЗУЛЬТАТ ПРОВЕРКИ:")
    print("="*60)
    
    all_ok = True
    for check, result in results.items():
        status = "✅" if result else "❌"
        print(f"{status} {check}")
        if not result:
            all_ok = False
    
    print("="*60)
    
    if all_ok:
        print("\n✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!")
        print("\n🚀 Вы можете запустить приложение:")
        print("   python run.py")
        print("   или")
        print("   python start.py")
        print("\n📍 Потом откройте: http://localhost:5000/crash")
        return 0
    else:
        print("\n❌ БЫЛИ ОБНАРУЖЕНЫ ПРОБЛЕМЫ")
        print("\n💡 Решения:")
        print("   1. Убедитесь что Python 3.8+")
        print("   2. Все файлы на месте")
        print("   3. Установите зависимости: pip install -r requirements.txt")
        return 1

if __name__ == '__main__':
    sys.exit(main())
