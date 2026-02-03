# app.py - основной файл приложения
from flask import Flask, render_template, request, jsonify, send_from_directory
import sqlite3
import json
import os
import logging
import random
import traceback
import string
from datetime import datetime, timedelta
import math
import shutil
import time
import threading
import pytz
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Создаем приложение Flask
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'raswet-secret-key-2024')

# Конфигурация
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
ADMIN_ID = int(os.getenv('ADMIN_ID', '5257227756'))
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8224991617:AAF2F7ub0XF9N6wsWyn3PmhdZnYt62KmpRE')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 16 * 1024 * 1024

# Глобальные переменные для кэширования
gifts_cache = None
gifts_cache_time = None
CACHE_DURATION = 300

# Система уровней
LEVEL_SYSTEM = [
    {"level": 1, "exp_required": 0, "reward_stars": 0, "reward_tickets": 0},
    {"level": 2, "exp_required": 100, "reward_stars": 10, "reward_tickets": 1},
    {"level": 3, "exp_required": 300, "reward_stars": 25, "reward_tickets": 2},
    {"level": 4, "exp_required": 600, "reward_stars": 50, "reward_tickets": 3},
    {"level": 5, "exp_required": 1000, "reward_stars": 100, "reward_tickets": 5},
    {"level": 6, "exp_required": 1500, "reward_stars": 150, "reward_tickets": 7},
    {"level": 7, "exp_required": 2100, "reward_stars": 200, "reward_tickets": 10},
    {"level": 8, "exp_required": 2800, "reward_stars": 250, "reward_tickets": 12},
    {"level": 9, "exp_required": 3600, "reward_stars": 300, "reward_tickets": 15},
    {"level": 10, "exp_required": 4500, "reward_stars": 400, "reward_tickets": 20},
    {"level": 11, "exp_required": 5500, "reward_stars": 500, "reward_tickets": 25},
    {"level": 12, "exp_required": 6600, "reward_stars": 600, "reward_tickets": 30},
    {"level": 13, "exp_required": 7800, "reward_stars": 700, "reward_tickets": 35},
    {"level": 14, "exp_required": 9100, "reward_stars": 800, "reward_tickets": 40},
    {"level": 15, "exp_required": 10500, "reward_stars": 900, "reward_tickets": 45},
    {"level": 16, "exp_required": 12000, "reward_stars": 1000, "reward_tickets": 50},
    {"level": 17, "exp_required": 13600, "reward_stars": 1100, "reward_tickets": 55},
    {"level": 18, "exp_required": 15300, "reward_stars": 1200, "reward_tickets": 60},
    {"level": 19, "exp_required": 17100, "reward_stars": 1300, "reward_tickets": 65},
    {"level": 20, "exp_required": 19000, "reward_stars": 1500, "reward_tickets": 70},
    {"level": 21, "exp_required": 25000, "reward_stars": 2000, "reward_tickets": 75}
]

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_gifts_cached():
    """Загружает подарки с кэшированием"""
    global gifts_cache, gifts_cache_time

    current_time = time.time()

    if gifts_cache is not None and gifts_cache_time is not None:
        if current_time - gifts_cache_time < CACHE_DURATION:
            logger.info("🎁 Используются кэшированные подарки")
            return gifts_cache

    logger.info("🎁 Загрузка подарков из файла...")
    gifts_cache = load_gifts()
    gifts_cache_time = current_time

    if gifts_cache:
        logger.info(f"🎁 Загружено {len(gifts_cache)} подарков в кэш")
    else:
        logger.error("❌ Не удалось загрузить подарки в кэш")

    return gifts_cache

def load_gifts():
    """Загружает подарки из JSON файла"""
    try:
        data_path = os.path.join(BASE_PATH, 'data')
        file_path = os.path.join(data_path, 'gifts.json')

        logger.info(f"📁 Загрузка подарков из: {file_path}")

        if not os.path.exists(file_path):
            logger.error(f"❌ Файл gifts.json не найден по пути: {file_path}")
            demo_gifts = [
                {"id": 1, "name": "Демо подарок 1", "value": 100, "image": "/static/img/default_gift.png"},
                {"id": 2, "name": "Демо подарок 2", "value": 500, "image": "/static/img/default_gift.png"}
            ]
            logger.info(f"✅ Создано {len(demo_gifts)} демо-подарков")
            return demo_gifts

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            gifts = data.get('gifts', [])

        logger.info(f"✅ Загружено {len(gifts)} подарков")
        return gifts

    except json.JSONDecodeError as e:
        logger.error(f"❌ Ошибка парсинга JSON: {e}")
        return []
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки подарков: {e}")
        logger.error(f"❌ Трассировка: {traceback.format_exc()}")
        return []

def save_gifts(gifts):
    """Сохраняет подарки в JSON файл"""
    try:
        file_path = os.path.join(BASE_PATH, 'data', 'gifts.json')

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump({'gifts': gifts}, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ Сохранено {len(gifts)} подарков")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения подарков: {e}")
        return False

def load_cases():
    """Загружает кейсы из JSON файла"""
    try:
        file_path = os.path.join(BASE_PATH, 'data', 'cases.json')

        if not os.path.exists(file_path):
            logger.error(f"❌ Файл cases.json не найден!")
            return []

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            cases = data.get('cases', [])
            logger.info(f"✅ Загружено {len(cases)} кейсов")
            return cases

    except Exception as e:
        logger.error(f"❌ Ошибка загрузки кейсов: {e}")
        return []

def save_cases(cases):
    """Сохраняет кейсы в JSON файл"""
    try:
        file_path = os.path.join(BASE_PATH, 'data', 'cases.json')

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump({'cases': cases}, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ Сохранено {len(cases)} кейсов")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения кейсов: {e}")
        return False

def get_db_connection():
    """Получает соединение с базой данных (FIXED)"""
    db_path = os.path.join(BASE_PATH, 'data', 'raswet_gifts.db')

    # ВАЖНО: добавляем check_same_thread=False для Flask
    conn = sqlite3.connect(db_path, timeout=30, check_same_thread=False)

    # Оптимизированные настройки
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA busy_timeout = 30000")  # Уменьшаем до 30 секунд
    conn.execute("PRAGMA cache_size = -10000")   # 10MB кэша
    conn.execute("PRAGMA temp_store = MEMORY")
    conn.execute("PRAGMA foreign_keys = ON")

    return conn

def init_db():
    """Инициализация базы данных"""
    try:
        data_path = os.path.join(BASE_PATH, 'data')
        os.makedirs(data_path, exist_ok=True)

        static_path = os.path.join(BASE_PATH, 'static')
        os.makedirs(static_path, exist_ok=True)

        gifs_path = os.path.join(static_path, 'gifs')
        os.makedirs(gifs_path, exist_ok=True)

        gifts_path = os.path.join(gifs_path, 'gifts')
        os.makedirs(gifts_path, exist_ok=True)

        cases_path = os.path.join(gifs_path, 'cases')
        os.makedirs(cases_path, exist_ok=True)

        uploads_path = os.path.join(static_path, 'uploads', 'notifications')
        os.makedirs(uploads_path, exist_ok=True)

        db_path = os.path.join(data_path, 'raswet_gifts.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        table_exists = cursor.fetchone()

        if not table_exists:
            logger.info("📊 Создаем таблицы базы данных...")

            # Таблица пользователей
            cursor.execute('''
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY,
                    first_name TEXT,
                    last_name TEXT,
                    username TEXT,
                    photo_url TEXT,
                    balance_stars INTEGER DEFAULT 0,
                    balance_tickets INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    referral_code TEXT UNIQUE,
                    referred_by INTEGER,
                    referral_count INTEGER DEFAULT 0,
                    total_earned_stars INTEGER DEFAULT 0,
                    total_earned_tickets INTEGER DEFAULT 0,
                    referral_bonus_claimed BOOLEAN DEFAULT FALSE,
                    experience INTEGER DEFAULT 0,
                    current_level INTEGER DEFAULT 1,
                    total_cases_opened INTEGER DEFAULT 0,
                    last_daily_bonus TIMESTAMP,
                    consecutive_days INTEGER DEFAULT 0
                )
            ''')

            # Таблица инвентаря
            cursor.execute('''
                CREATE TABLE inventory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    gift_id INTEGER,
                    gift_name TEXT,
                    gift_image TEXT,
                    gift_value INTEGER,
                    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_withdrawing BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')

            # Таблица истории операций
            cursor.execute('''
                CREATE TABLE user_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    operation_type TEXT NOT NULL,
                    amount INTEGER NOT NULL,
                    description TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')

            # Таблица для отслеживания лимитов кейсов
            cursor.execute('''
                CREATE TABLE case_limits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    case_id INTEGER NOT NULL,
                    current_amount INTEGER DEFAULT 0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(case_id)
                )
            ''')

            # Таблица рефералов
            cursor.execute('''
                CREATE TABLE referrals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    referrer_id INTEGER,
                    referred_id INTEGER,
                    reward_claimed BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (referrer_id) REFERENCES users (id),
                    FOREIGN KEY (referred_id) REFERENCES users (id),
                    UNIQUE(referred_id)
                )
            ''')

            # Таблица реферальных наград
            cursor.execute('''
                CREATE TABLE referral_rewards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    referrer_id INTEGER,
                    reward_type TEXT NOT NULL,
                    reward_amount INTEGER NOT NULL,
                    description TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (referrer_id) REFERENCES users (id)
                )
            ''')

            # Таблица выводов
            cursor.execute('''
                CREATE TABLE withdrawals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    inventory_id INTEGER NOT NULL,
                    gift_name TEXT NOT NULL,
                    gift_image TEXT NOT NULL,
                    gift_value INTEGER NOT NULL,
                    status TEXT DEFAULT 'pending',
                    telegram_username TEXT,
                    user_photo_url TEXT,
                    user_first_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP,
                    admin_notes TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (inventory_id) REFERENCES inventory (id)
                )
            ''')

            # Таблица пополнений баланса
            cursor.execute('''
                CREATE TABLE deposits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    amount INTEGER NOT NULL,
                    currency TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    payment_method TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    telegram_payment_charge_id TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')

            # Таблица промокодов
            cursor.execute('''
                CREATE TABLE promo_codes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE NOT NULL,
                    reward_stars INTEGER DEFAULT 0,
                    reward_tickets INTEGER DEFAULT 0,
                    max_uses INTEGER DEFAULT 1,
                    used_count INTEGER DEFAULT 0,
                    created_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
            ''')

            # Таблица использованных промокодов
            cursor.execute('''
                CREATE TABLE used_promo_codes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    promo_code_id INTEGER NOT NULL,
                    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (promo_code_id) REFERENCES promo_codes (id),
                    UNIQUE(user_id, promo_code_id)
                )
            ''')

            # Таблица уровней пользователей
            cursor.execute('''
                CREATE TABLE user_levels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    level INTEGER DEFAULT 1,
                    experience INTEGER DEFAULT 0,
                    total_experience INTEGER DEFAULT 0,
                    last_level_up TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    UNIQUE(user_id)
                )
            ''')

            # Таблица истории уровней
            cursor.execute('''
                CREATE TABLE level_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    old_level INTEGER,
                    new_level INTEGER,
                    experience_gained INTEGER,
                    reason TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')

            # Таблица истории побед
            cursor.execute('''
                CREATE TABLE win_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    user_name TEXT,
                    gift_name TEXT,
                    gift_image TEXT,
                    gift_value INTEGER,
                    case_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')

            # Таблица истории открытий кейсов
            cursor.execute('''
                CREATE TABLE case_open_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    case_id INTEGER NOT NULL,
                    case_name TEXT,
                    gift_id INTEGER,
                    gift_name TEXT,
                    gift_image TEXT,
                    gift_value INTEGER,
                    cost INTEGER DEFAULT 0,
                    cost_type TEXT DEFAULT 'stars',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')

            # Таблицы для Ultimate Crash
            cursor.execute('''
                CREATE TABLE ultimate_crash_games (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    status TEXT DEFAULT 'waiting',
                    current_multiplier DECIMAL(10,2) DEFAULT 1.00,
                    target_multiplier DECIMAL(10,2) DEFAULT 5.00,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE ultimate_crash_bets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_id INTEGER,
                    user_id INTEGER,
                    bet_amount INTEGER DEFAULT 0,
                    gift_value INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'active',
                    cashout_multiplier DECIMAL(10,2),
                    win_amount INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (game_id) REFERENCES ultimate_crash_games (id)
                )
            ''')

            cursor.execute('''
                CREATE TABLE ultimate_crash_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_id INTEGER,
                    final_multiplier DECIMAL(10,2),
                    total_bets INTEGER DEFAULT 0,
                    total_amount INTEGER DEFAULT 0,
                    finished_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Таблицы для Crash Game
            cursor.execute('''
                CREATE TABLE crash_games (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    multiplier DECIMAL(10,2) DEFAULT 1.00,
                    status TEXT DEFAULT 'waiting',
                    current_multiplier DECIMAL(10,2) DEFAULT 1.00,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE crash_bets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_id INTEGER,
                    user_id INTEGER,
                    bet_amount INTEGER DEFAULT 0,
                    bet_type TEXT DEFAULT 'stars',
                    gift_id INTEGER,
                    gift_name TEXT,
                    gift_image TEXT,
                    gift_value INTEGER,
                    multiplier DECIMAL(10,2) DEFAULT 1.00,
                    status TEXT DEFAULT 'active',
                    cashout_multiplier DECIMAL(10,2),
                    win_amount INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (game_id) REFERENCES crash_games (id),
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')

            cursor.execute('''
                CREATE TABLE crash_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_id INTEGER,
                    multiplier DECIMAL(10,2),
                    total_bets INTEGER DEFAULT 0,
                    total_amount INTEGER DEFAULT 0,
                    finished_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (game_id) REFERENCES crash_games (id)
                )
            ''')

            # Таблицы для уведомлений
            cursor.execute('''
                CREATE TABLE notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    width INTEGER DEFAULT 80,
                    pages JSON NOT NULL,
                    is_active BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    admin_id INTEGER NOT NULL
                )
            ''')

            cursor.execute('''
                CREATE TABLE user_notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    notification_id INTEGER NOT NULL,
                    shown BOOLEAN DEFAULT FALSE,
                    shown_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (notification_id) REFERENCES notifications (id),
                    UNIQUE(user_id, notification_id)
                )
            ''')

            logger.info("✅ Все таблицы созданы успешно!")
        else:
            logger.info("✅ Таблицы уже существуют, пропускаем создание")

        # Инициализируем лимиты для существующих кейсов
        cases = load_cases()
        for case in cases:
            if case.get('limited'):
                cursor.execute('SELECT id FROM case_limits WHERE case_id = ?', (case['id'],))
                existing = cursor.fetchone()

                if not existing:
                    cursor.execute('''
                        INSERT INTO case_limits (case_id, current_amount)
                        VALUES (?, ?)
                    ''', (case['id'], case['amount']))
                    logger.info(f"✅ Инициализирован лимит для кейса {case['id']}: {case['amount']}")

        # Создаем начальную игру Ultimate Crash
        cursor.execute('SELECT COUNT(*) FROM ultimate_crash_games WHERE status IN ("waiting", "counting", "flying")')
        active_games = cursor.fetchone()[0]

        if active_games == 0:
            target_multiplier = round(random.uniform(3.0, 10.0), 2)
            cursor.execute('''
                INSERT INTO ultimate_crash_games (status, target_multiplier, start_time)
                VALUES ('waiting', ?, CURRENT_TIMESTAMP)
            ''', (target_multiplier,))
            logger.info(f"✅ Создана начальная игра Ultimate Crash, множитель: {target_multiplier}x")

        conn.commit()
        conn.close()
        logger.info("✅ База данных инициализирована успешно!")

    except Exception as e:
        logger.error(f"❌ Ошибка инициализации базы данных: {e}")
        logger.error(f"❌ Трассировка: {traceback.format_exc()}")

def add_history_record(user_id, operation_type, amount, description):
    """Добавляет запись в историю операций"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO user_history (user_id, operation_type, amount, description)
            VALUES (?, ?, ?, ?)
        ''', (user_id, operation_type, amount, description))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Ошибка добавления в историю: {e}")
        return False

def add_win_history(user_id, user_name, gift_name, gift_image, gift_value, case_name):
    """Добавляет запись в историю побед"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO win_history (user_id, user_name, gift_name, gift_image, gift_value, case_name)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, user_name, gift_name, gift_image, gift_value, case_name))

        cursor.execute('''
            DELETE FROM win_history
            WHERE id NOT IN (
                SELECT id FROM win_history
                ORDER BY created_at DESC
                LIMIT 50
            )
        ''')

        conn.commit()
        conn.close()
        logger.info(f"📝 Добавлена запись в историю побед: {user_name} выиграл {gift_name}")
        return True
    except Exception as e:
        logger.error(f"Ошибка добавления в историю побед: {e}")
        return False

def add_case_open_history(user_id, case_id, case_name, gift_id, gift_name, gift_image, gift_value, cost=0, cost_type='stars'):
    """Добавляет запись в историю открытий кейсов"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO case_open_history (user_id, case_id, case_name, gift_id, gift_name, gift_image, gift_value, cost, cost_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, case_id, case_name, gift_id, gift_name, gift_image, gift_value, cost, cost_type))

        cursor.execute('''
            DELETE FROM case_open_history
            WHERE id NOT IN (
                SELECT id FROM case_open_history
                ORDER BY created_at DESC
                LIMIT 100
            )
        ''')

        conn.commit()
        conn.close()
        logger.info(f"📝 Добавлена запись в историю открытий: {user_id} открыл {case_name}")
        return True
    except Exception as e:
        logger.error(f"Ошибка добавления в историю открытий: {e}")
        return False

def add_experience(user_id, exp_amount, reason=""):
    """Добавляет опыт пользователю и проверяет повышение уровня"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT experience, current_level FROM users WHERE id = ?', (user_id,))
        result = cursor.fetchone()

        if not result:
            conn.close()
            return {'success': False, 'error': 'Пользователь не найден'}

        current_exp, current_level = result
        new_exp = current_exp + exp_amount

        new_level = current_level
        level_up_rewards = []
        level_up_info = None

        # Проверяем повышение уровня
        while new_level < len(LEVEL_SYSTEM):
            next_level_info = LEVEL_SYSTEM[new_level]
            if new_exp >= next_level_info["exp_required"]:
                new_level += 1

                # Награда за достижение нового уровня
                reward_stars = next_level_info["reward_stars"]
                reward_tickets = next_level_info["reward_tickets"]

                if reward_stars > 0:
                    cursor.execute('UPDATE users SET balance_stars = balance_stars + ?, total_earned_stars = total_earned_stars + ? WHERE id = ?',
                                 (reward_stars, reward_stars, user_id))
                    level_up_rewards.append(f"{reward_stars}⭐")

                if reward_tickets > 0:
                    cursor.execute('UPDATE users SET balance_tickets = balance_tickets + ?, total_earned_tickets = total_earned_tickets + ? WHERE id = ?',
                                 (reward_tickets, reward_tickets, user_id))
                    level_up_rewards.append(f"{reward_tickets}🎫")

                # Записываем в историю
                cursor.execute('''
                    INSERT INTO level_history (user_id, old_level, new_level, experience_gained, reason)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, new_level-1, new_level, exp_amount, reason))

                level_up_info = {
                    'old_level': new_level-1,
                    'new_level': new_level,
                    'reward_stars': reward_stars,
                    'reward_tickets': reward_tickets,
                    'rewards_text': ', '.join(level_up_rewards)
                }

                logger.info(f"🎉 Пользователь {user_id} достиг уровня {new_level}! Награда: {reward_stars}⭐, {reward_tickets}🎫")
            else:
                break

        # Обновляем пользователя
        cursor.execute('UPDATE users SET experience = ?, current_level = ? WHERE id = ?',
                     (new_exp, new_level, user_id))

        conn.commit()
        conn.close()

        return {
            'success': True,
            'old_level': current_level,
            'new_level': new_level,
            'exp_gained': exp_amount,
            'total_exp': new_exp,
            'level_up_info': level_up_info
        }

    except Exception as e:
        logger.error(f"Ошибка добавления опыта: {e}")
        return {'success': False, 'error': str(e)}

def get_user_level_info(user_id):
    """Получает информацию об уровне пользователя"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT experience, current_level FROM users WHERE id = ?', (user_id,))
        result = cursor.fetchone()

        if not result:
            conn.close()
            return None

        experience, current_level = result

        current_level_info = next((level for level in LEVEL_SYSTEM if level["level"] == current_level), None)
        next_level_info = next((level for level in LEVEL_SYSTEM if level["level"] == current_level + 1), None)

        conn.close()

        if current_level_info and next_level_info:
            exp_to_next_level = next_level_info["exp_required"] - experience
            progress_percentage = ((experience - current_level_info["exp_required"]) /
                                (next_level_info["exp_required"] - current_level_info["exp_required"])) * 100
        else:
            exp_to_next_level = 0
            progress_percentage = 100

        return {
            'current_level': current_level,
            'experience': experience,
            'exp_to_next_level': max(0, exp_to_next_level),
            'progress_percentage': min(max(progress_percentage, 0), 100),
            'current_level_info': current_level_info,
            'next_level_info': next_level_info
        }

    except Exception as e:
        logger.error(f"Ошибка получения информации об уровне: {e}")
        return None

def update_case_limit(case_id):
    """Обновляет лимит кейса (уменьшает на 1)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cases = load_cases()
        case = next((c for c in cases if c['id'] == case_id), None)

        if not case:
            conn.close()
            return None

        if not case.get('limited'):
            conn.close()
            return None

        cursor.execute('SELECT current_amount FROM case_limits WHERE case_id = ?', (case_id,))
        result = cursor.fetchone()

        if not result:
            max_amount = case.get('amount', 0)
            if max_amount > 0:
                current_amount = max_amount - 1
                cursor.execute('INSERT INTO case_limits (case_id, current_amount) VALUES (?, ?)',
                             (case_id, current_amount))
                conn.commit()
                conn.close()
                return current_amount
            else:
                conn.close()
                return 0
        else:
            current_amount = result[0]
            if current_amount > 0:
                new_amount = current_amount - 1
                cursor.execute('UPDATE case_limits SET current_amount = ? WHERE case_id = ?', (new_amount, case_id))
                conn.commit()
                logger.info(f"📊 Лимит кейса {case_id} уменьшен: {current_amount} -> {new_amount}")
                conn.close()
                return new_amount
            else:
                conn.close()
                return 0

    except Exception as e:
        logger.error(f"Ошибка обновления лимита кейса: {e}")
        return None

def get_case_limit(case_id):
    """Получает текущий лимит кейса"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT current_amount FROM case_limits WHERE case_id = ?', (case_id,))
        result = cursor.fetchone()

        if result:
            current_amount = result[0]
            conn.close()
            logger.info(f"📊 Получен лимит кейса {case_id}: {current_amount}")
            return current_amount
        else:
            cases = load_cases()
            case = next((c for c in cases if c['id'] == case_id), None)
            if case and case.get('limited'):
                max_amount = case.get('amount', 0)
                cursor.execute('INSERT INTO case_limits (case_id, current_amount) VALUES (?, ?)',
                             (case_id, max_amount))
                conn.commit()
                conn.close()
                logger.info(f"📊 Создан лимит для кейса {case_id}: {max_amount}")
                return max_amount
            else:
                conn.close()
                return None

    except Exception as e:
        logger.error(f"Ошибка получения лимита кейса: {e}")
        return None

def generate_referral_code():
    """Генерирует уникальный реферальный код"""
    characters = string.ascii_uppercase + string.digits
    while True:
        code = ''.join(random.choice(characters) for _ in range(8))

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE referral_code = ?', (code,))
        existing = cursor.fetchone()
        conn.close()

        if not existing:
            return code

def process_referral(referred_user_id, referral_code):
    """Обрабатывает реферальную ссылку"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM users WHERE referral_code = ?', (referral_code,))
        referrer = cursor.fetchone()

        if referrer:
            referrer_id = referrer[0]

            if referrer_id == referred_user_id:
                logger.warning(f"⚠️ Попытка самоприглашения: {referred_user_id}")
                return False

            cursor.execute('SELECT id FROM referrals WHERE referred_id = ?', (referred_user_id,))
            existing = cursor.fetchone()

            if not existing:
                cursor.execute('''
                    INSERT INTO referrals (referrer_id, referred_id)
                    VALUES (?, ?)
                ''', (referrer_id, referred_user_id))

                cursor.execute('UPDATE users SET referral_count = referral_count + 1 WHERE id = ?', (referrer_id,))

                cursor.execute('UPDATE users SET balance_tickets = balance_tickets + 1, total_earned_tickets = total_earned_tickets + 1 WHERE id = ?', (referrer_id,))

                add_experience(referrer_id, 50, "Приглашение друга")

                cursor.execute('SELECT first_name FROM users WHERE id = ?', (referred_user_id,))
                referred_user = cursor.fetchone()
                referred_name = referred_user[0] if referred_user else 'Новый пользователь'

                add_history_record(referrer_id, 'referral_reward', 1, f'Приглашен пользователь: {referred_name}')

                cursor.execute('''
                    INSERT INTO referral_rewards (referrer_id, reward_type, reward_amount, description)
                    VALUES (?, ?, ?, ?)
                ''', (referrer_id, 'tickets', 1, 'За приглашение друга'))

                cursor.execute('UPDATE users SET referred_by = ? WHERE id = ?', (referrer_id, referred_user_id))

                conn.commit()
                conn.close()

                logger.info(f"🎫 Пользователь {referrer_id} получил 1 билет за приглашение {referred_user_id}")
                return True

        conn.close()
        return False

    except Exception as e:
        logger.error(f"Ошибка обработки реферала: {e}")
        return False

def generate_extreme_crash_multiplier():
    """Генерация экстремального множителя для Ultimate Crash с редкими высокими множителями"""
    r = random.random()

    if r < 0.85:  # 85% шанс на множитель 1.0-2.0
        return round(1.0 + random.random() * 1.0, 2)
    elif r < 0.95:  # 10% шанс на множитель 2.0-3.0
        return round(2.0 + random.random() * 1.0, 2)
    elif r < 0.99:  # 4% шанс на множитель 3.0-4.0
        return round(3.0 + random.random() * 1.0, 2)
    else:  # 1% шанс на множитель 4.0-6.0 (очень редко)
        return round(4.0 + random.random() * 2.0, 2)

def start_crash_loop():
    def loop():
        while True:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("SELECT id,status,current_multiplier FROM crash_games ORDER BY id DESC LIMIT 1")
            game = cur.fetchone()

            if not game or game[1] == "crashed":
                cur.execute("INSERT INTO crash_games(status,current_multiplier) VALUES('flying',1.0)")
                conn.commit()
            else:
                gid,status,mult = game
                if status == "flying":
                    mult = float(mult) + random.uniform(0.05,0.25)

                    if random.random() < 0.03:
                        cur.execute("UPDATE crash_games SET status='crashed' WHERE id=?", (gid,))
                    else:
                        cur.execute("UPDATE crash_games SET current_multiplier=? WHERE id=?", (round(mult,2),gid))

                    conn.commit()

            conn.close()
            time.sleep(0.5)

    threading.Thread(target=loop, daemon=True).start()


def start_ultimate_crash_loop():

    """Запускает простой игровой цикл"""
    def game_loop():
        logger.info("🚀 Запущен простой игровой цикл Ultimate Crash")

        while True:
            try:
                # Проверяем и создаем новую игру если нужно
                conn = get_db_connection()
                cursor = conn.cursor()

                # Ищем активную игру
                cursor.execute('''
                    SELECT id, status, start_time, current_multiplier, target_multiplier
                    FROM ultimate_crash_games
                    WHERE status IN ('waiting', 'counting', 'flying')
                    ORDER BY id DESC LIMIT 1
                ''')

                game = cursor.fetchone()

                if game:
                    game_id, status, start_time, current_mult, target_mult = game

                    # Преобразуем время
                    if isinstance(start_time, str):
                        try:
                            if '.' in start_time:
                                start_time = start_time.split('.')[0]
                            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                            start_timestamp = time.mktime(start_dt.timetuple())
                        except:
                            start_timestamp = time.time() - 30
                    else:
                        start_timestamp = time.time() - 30

                    elapsed = time.time() - start_timestamp

                    # Обработка разных фаз
                    if status == 'waiting':
                        if elapsed >= 15:  # 15 секунд ожидания
                            cursor.execute('UPDATE ultimate_crash_games SET status = "counting" WHERE id = ?', (game_id,))
                            logger.info(f"⏱️ Игра #{game_id} перешла в фазу отсчета")
                    elif status == 'counting':
                        if elapsed >= 20:  # 5 секунд отсчета (15+5)
                            cursor.execute('UPDATE ultimate_crash_games SET status = "flying" WHERE id = ?', (game_id,))
                            logger.info(f"🚀 Игра #{game_id} началась!")
                    elif status == 'flying':
                        # Увеличиваем множитель
                        current_mult_float = float(current_mult) if current_mult else 1.0
                        target_mult_float = float(target_mult) if target_mult else 5.0

                        if current_mult_float < target_mult_float:
                            # Разная скорость в разных диапазонах
                            increment = 0.02
                            if current_mult_float < 1.5:
                                increment = 0.01
                            elif current_mult_float < 2.0:
                                increment = 0.015
                            elif current_mult_float < 4.0:
                                increment = 0.03
                            else:
                                increment = 0.05

                            # Случайный краш
                            crash_chance = 0.01 * (current_mult_float / 10)
                            if random.random() < crash_chance:
                                cursor.execute('UPDATE ultimate_crash_games SET status = "crashed" WHERE id = ?', (game_id,))
                                logger.info(f"💥 Случайный краш на {current_mult_float:.2f}x")
                            else:
                                new_multiplier = round(current_mult_float + increment, 2)
                                if new_multiplier >= target_mult_float:
                                    cursor.execute('UPDATE ultimate_crash_games SET status = "crashed", current_multiplier = ? WHERE id = ?',
                                                 (target_mult_float, game_id))
                                    logger.info(f"💥 Достигнут целевой множитель {target_mult_float:.2f}x")
                                else:
                                    cursor.execute('UPDATE ultimate_crash_games SET current_multiplier = ? WHERE id = ?',
                                                 (new_multiplier, game_id))
                                    logger.debug(f"📈 Множитель обновлен: {new_multiplier:.2f}x")
                        else:
                            cursor.execute('UPDATE ultimate_crash_games SET status = "crashed" WHERE id = ?', (game_id,))
                            logger.info(f"💥 Игра #{game_id} завершена на {current_mult_float:.2f}x")

                    conn.commit()

                conn.close()

                time.sleep(0.5)  # Пауза между проверками

            except Exception as e:
                logger.error(f"❌ Ошибка в игровом цикле: {e}")
                time.sleep(2)

    thread = threading.Thread(target=game_loop, daemon=True)
    thread.start()
    logger.info("✅ Простой игровой цикл запущен")

# ==================== ОСНОВНЫЕ РОУТЫ ====================

@app.route('/')
def lobby_page():
    """Страница лобби"""
    logger.info("🏠 Запрос страницы лобби")
    return render_template('lobby.html')

@app.route('/index')
def index():
    """Главная страница"""
    logger.info("📄 Запрос главной страницы")
    return render_template('index.html')

@app.route('/case/<int:case_id>')
def case_page(case_id):
    """Страница конкретного кейса"""
    logger.info(f"📄 Запрос страницы кейса {case_id}")
    return render_template('case.html', case_id=case_id)

@app.route('/inventory')
def inventory_page():
    """Страница инвентаря"""
    logger.info("🎒 Запрос страницы инвентаря")
    return render_template('inventory.html')

@app.route('/profile')
def profile_page():
    """Страница профиля"""
    logger.info("👤 Запрос страницы профиля")
    return render_template('profile.html')

@app.route('/ref')
def ref_page():
    """Страница реферальной системы"""
    logger.info("👥 Запрос страницы рефералов")
    return render_template('ref.html')

@app.route('/upgrade')
def upgrade_page():
    """Страница апгрейдов"""
    logger.info("⚡ Запрос страницы апгрейдов")
    return render_template('upgrade.html')

@app.route('/admin')
def admin_page():
    """Страница админ-панели"""
    logger.info("🛠️ Запрос страницы админ-панели")
    return render_template('admin.html')

@app.route('/cases')
def cases_page():
    """Страница кейсов"""
    logger.info("📦 Запрос страницы кейсов")
    return render_template('index.html')

@app.route('/levels')
def levels_page():
    """Страница уровней"""
    logger.info("📊 Запрос страницы уровней")
    return render_template('levels.html')

@app.route('/crash')
def crash_page():
    """Страница игры Краш"""
    logger.info("🎮 Запрос страницы игры Краш")
    return render_template('crash.html')

@app.route('/ultimate-crash')
def ultimate_crash_page():
    """Страница Ultimate Crash"""
    logger.info("🚀 Запрос страницы Ultimate Crash")
    return render_template('ultimate_crash.html')

@app.route('/static/<path:path>')
def serve_static(path):
    """Обслуживание статических файлов"""
    return send_from_directory('static', path)

# ==================== API ENDPOINTS ====================

# TELEGRAM API
@app.route('/api/telegram/user', methods=['GET'])
def get_telegram_user():
    """Получение данных пользователя Telegram"""
    try:
        user_id = request.args.get('user_id')

        if not user_id:
            return jsonify({'success': False, 'error': 'ID пользователя не указан'})

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()

        if not user:
            conn.close()
            return jsonify({'success': False, 'error': 'Пользователь не найден'})

        user_data = {
            'id': user[0],
            'first_name': user[1],
            'last_name': user[2],
            'username': user[3],
            'photo_url': user[4],
            'balance_stars': user[5],
            'balance_tickets': user[6],
            'referral_code': user[8],
            'experience': user[14] or 0,
            'current_level': user[15] or 1
        }

        conn.close()

        return jsonify({
            'success': True,
            'user': user_data
        })

    except Exception as e:
        logger.error(f"❌ Ошибка получения пользователя: {e}")
        return jsonify({'success': False, 'error': str(e)})



# ==================== ДОПОЛНИТЕЛЬНЫЕ API ДЛЯ ULTIMATE CRASH ====================

@app.route('/api/ultimate-crash/simple-status', methods=['GET'])
def ultimate_crash_simple_status():
    """Упрощенный статус игры (для минимизации блокировок)"""
    try:
        user_id = request.args.get('user_id')

        # Используем самое быстрое соединение
        conn = sqlite3.connect(os.path.join(BASE_PATH, 'data', 'raswet_gifts.db'), timeout=5)
        conn.execute("PRAGMA busy_timeout = 5000")
        cursor = conn.cursor()

        # Получаем текущую игру
        cursor.execute('''
            SELECT id, status, current_multiplier, target_multiplier
            FROM ultimate_crash_games
            WHERE status IN ('waiting', 'counting', 'flying', 'crashed')
            ORDER BY id DESC LIMIT 1
        ''')

        game = cursor.fetchone()

        if not game:
            # Создаем новую игру если нет активной
            target_multiplier = round(random.uniform(3.0, 10.0), 2)
            cursor.execute('''
                INSERT INTO ultimate_crash_games (status, target_multiplier, start_time)
                VALUES ('waiting', ?, CURRENT_TIMESTAMP)
            ''', (target_multiplier,))
            conn.commit()
            game_id = cursor.lastrowid

            cursor.execute('''
                SELECT id, status, current_multiplier, target_multiplier
                FROM ultimate_crash_games WHERE id = ?
            ''', (game_id,))
            game = cursor.fetchone()

        game_id, status, current_mult, target_mult = game
        current_mult = float(current_mult) if current_mult else 1.0

        # Вычисляем оставшееся время
        time_remaining = 15.0
        if status == 'waiting':
            time_remaining = 15.0
        elif status == 'counting':
            time_remaining = 5.0
        elif status == 'flying':
            # Расчет времени полета
            target_mult_float = float(target_mult) if target_mult else 5.0
            progress_ratio = current_mult / target_mult_float if target_mult_float > 0 else 0
            time_remaining = max(0.1, 10.0 * (1 - progress_ratio))
        else:
            time_remaining = 0

        # Получаем ставку пользователя если есть
        user_bet = None
        if user_id:
            cursor.execute('''
                SELECT id, bet_amount, status FROM ultimate_crash_bets
                WHERE game_id = ? AND user_id = ? AND status = 'active'
                ORDER BY created_at DESC LIMIT 1
            ''', (game_id, user_id))

            bet = cursor.fetchone()
            if bet:
                user_bet = {
                    'id': bet[0],
                    'bet_amount': bet[1],
                    'status': bet[2]
                }

        conn.close()

        return jsonify({
            'success': True,
            'game': {
                'id': game_id,
                'status': status,
                'current_multiplier': round(current_mult, 2),
                'target_multiplier': float(target_mult) if target_mult else 5.0,
                'time_remaining': round(time_remaining, 1)
            },
            'user_bet': user_bet
        })

    except Exception as e:
        logger.error(f"❌ Ошибка simple-status: {e}")
        return jsonify({
            'success': True,
            'game': {
                'id': 1,
                'status': 'waiting',
                'current_multiplier': 1.0,
                'target_multiplier': 5.0,
                'time_remaining': 15.0
            },
            'user_bet': None
        })

@app.route('/api/ultimate-crash/place-bet', methods=['POST'])
def ultimate_crash_place_bet():
    """Упрощенная версия размещения ставки"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        bet_amount = data.get('bet_amount', 0)

        if not user_id:
            return jsonify({'success': False, 'error': 'ID пользователя не указан'})

        if bet_amount < 25:
            return jsonify({'success': False, 'error': 'Минимальная ставка 25'})

        conn = get_db_connection()
        cursor = conn.cursor()

        # Проверяем баланс
        cursor.execute('SELECT balance_stars FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()

        if not user:
            conn.close()
            return jsonify({'success': False, 'error': 'Пользователь не найден'})

        current_balance = user[0] or 0

        if current_balance < bet_amount:
            conn.close()
            return jsonify({'success': False, 'error': f'Недостаточно средств. Баланс: {current_balance}'})

        # Получаем активную игру
        cursor.execute('''
            SELECT id, status FROM ultimate_crash_games
            WHERE status = 'waiting'
            ORDER BY id DESC LIMIT 1
        ''')

        game = cursor.fetchone()

        if not game:
            # Создаем новую игру
            target_multiplier = round(random.uniform(3.0, 10.0), 2)
            cursor.execute('''
                INSERT INTO ultimate_crash_games (status, target_multiplier, start_time)
                VALUES ('waiting', ?, CURRENT_TIMESTAMP)
            ''', (target_multiplier,))
            game_id = cursor.lastrowid
            game_status = 'waiting'
        else:
            game_id, game_status = game

        if game_status != 'waiting':
            conn.close()
            return jsonify({'success': False, 'error': 'Игра уже началась'})

        # Проверяем, есть ли уже ставка
        cursor.execute('''
            SELECT id FROM ultimate_crash_bets
            WHERE game_id = ? AND user_id = ? AND status = 'active'
        ''', (game_id, user_id))

        existing_bet = cursor.fetchone()

        if existing_bet:
            conn.close()
            return jsonify({'success': False, 'error': 'У вас уже есть активная ставка'})

        # Списываем средства
        cursor.execute('UPDATE users SET balance_stars = balance_stars - ? WHERE id = ?',
                     (bet_amount, user_id))

        # Создаем ставку
        cursor.execute('''
            INSERT INTO ultimate_crash_bets (game_id, user_id, bet_amount, gift_value, status)
            VALUES (?, ?, ?, ?, 'active')
        ''', (game_id, user_id, bet_amount, bet_amount))

        bet_id = cursor.lastrowid

        # Добавляем в историю
        cursor.execute('''
            INSERT INTO user_history (user_id, operation_type, amount, description)
            VALUES (?, 'ultimate_crash_bet', ?, ?)
        ''', (user_id, -bet_amount, f'Ставка в Ultimate Crash: {bet_amount}'))

        conn.commit()

        # Получаем новый баланс
        cursor.execute('SELECT balance_stars FROM users WHERE id = ?', (user_id,))
        new_balance = cursor.fetchone()[0]

        conn.close()

        logger.info(f"✅ Ставка размещена: {bet_amount} (ID: {bet_id})")

        return jsonify({
            'success': True,
            'bet_id': bet_id,
            'game_id': game_id,
            'new_balance': new_balance,
            'message': f'Ставка {bet_amount} принята!'
        })

    except Exception as e:
        logger.error(f"❌ Ошибка ставки: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/ultimate-crash/cashout-simple', methods=['POST'])
def ultimate_crash_cashout_simple():
    """Упрощенный кэшаут"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')

        if not user_id:
            return jsonify({'success': False, 'error': 'ID пользователя не указан'})

        conn = get_db_connection()
        cursor = conn.cursor()

        # Получаем активную игру
        cursor.execute('''
            SELECT id, current_multiplier FROM ultimate_crash_games
            WHERE status = 'flying'
            ORDER BY id DESC LIMIT 1
        ''')

        game = cursor.fetchone()

        if not game:
            conn.close()
            return jsonify({'success': False, 'error': 'Нет активной игры'})

        game_id, current_mult = game[0], float(game[1]) if game[1] else 1.0

        # Получаем ставку пользователя
        cursor.execute('''
            SELECT id, bet_amount FROM ultimate_crash_bets
            WHERE game_id = ? AND user_id = ? AND status = 'active'
            ORDER BY created_at DESC LIMIT 1
        ''', (game_id, user_id))

        bet = cursor.fetchone()

        if not bet:
            conn.close()
            return jsonify({'success': False, 'error': 'Активная ставка не найдена'})

        bet_id, bet_amount = bet

        # Расчет выигрыша
        win_amount = int(bet_amount * current_mult)

        # Обновляем ставку
        cursor.execute('''
            UPDATE ultimate_crash_bets
            SET status = 'cashed_out',
                cashout_multiplier = ?,
                win_amount = ?
            WHERE id = ?
        ''', (current_mult, win_amount, bet_id))

        # Начисляем выигрыш
        cursor.execute('''
            UPDATE users
            SET balance_stars = balance_stars + ?,
                total_earned_stars = total_earned_stars + ?
            WHERE id = ?
        ''', (win_amount, win_amount, user_id))

        # Добавляем опыт
        exp_gained = max(5, win_amount // 100)
        cursor.execute('UPDATE users SET experience = experience + ? WHERE id = ?',
                     (exp_gained, user_id))

        # Добавляем в историю
        cursor.execute('''
            INSERT INTO user_history (user_id, operation_type, amount, description)
            VALUES (?, 'ultimate_crash_win', ?, ?)
        ''', (user_id, win_amount, f'Выигрыш в Ultimate Crash: x{current_mult:.2f}'))

        # Добавляем в историю побед
        cursor.execute('SELECT first_name FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        user_name = user[0] if user else f'User_{user_id}'

        cursor.execute('''
            INSERT INTO win_history (user_id, user_name, gift_name, gift_image, gift_value, case_name)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, user_name, f'Выигрыш в Crash x{current_mult:.2f}',
              '/static/img/star.png', win_amount, 'Ultimate Crash'))

        conn.commit()

        # Получаем новый баланс
        cursor.execute('SELECT balance_stars FROM users WHERE id = ?', (user_id,))
        new_balance = cursor.fetchone()[0]

        conn.close()

        logger.info(f"✅ Кэшаут: {win_amount} (x{current_mult:.2f})")

        return jsonify({
            'success': True,
            'win_amount': win_amount,
            'multiplier': current_mult,
            'new_balance': new_balance,
            'message': f'Вы выиграли {win_amount}!'
        })

    except Exception as e:
        logger.error(f"❌ Ошибка кэшаута: {e}")
        return jsonify({'success': False, 'error': str(e)})

# ==================== АВТОМАТИЗАЦИЯ ИГРОВОГО ЦИКЛА ====================

def start_simple_game_loop():
    """Запускает упрощенный игровой цикл"""
    def game_loop():
        logger.info("🚀 Запущен упрощенный игровой цикл")

        while True:
            try:
                # Пауза между играми
                time.sleep(3)

                conn = get_db_connection()
                cursor = conn.cursor()

                # Создаем новую игру если нет активной
                cursor.execute('''
                    SELECT COUNT(*) FROM ultimate_crash_games
                    WHERE status IN ('waiting', 'counting', 'flying')
                ''')
                active_games = cursor.fetchone()[0]

                if active_games == 0:
                    target_multiplier = round(random.uniform(3.0, 10.0), 2)
                    cursor.execute('''
                        INSERT INTO ultimate_crash_games (status, target_multiplier, start_time)
                        VALUES ('waiting', ?, CURRENT_TIMESTAMP)
                    ''', (target_multiplier,))
                    game_id = cursor.lastrowid
                    conn.commit()
                    logger.info(f"🆕 Создана новая игра #{game_id}")

                conn.close()

            except Exception as e:
                logger.error(f"❌ Ошибка игрового цикла: {e}")
                time.sleep(5)

    thread = threading.Thread(target=game_loop, daemon=True)
    thread.start()
    logger.info("✅ Простой игровой цикл запущен")



@app.route('/api/telegram-auth', methods=['POST'])
def telegram_auth():
    """Аутентификация пользователя через Telegram"""
    try:
        data = request.get_json()
        user_id = data['id']
        referral_code = data.get('referral_code')

        logger.info(f"🔐 Авторизация пользователя: {data.get('first_name')} (ID: {user_id})")

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()

        if not user:
            new_referral_code = generate_referral_code()

            cursor.execute('''
                INSERT INTO users (id, first_name, last_name, username, photo_url, balance_stars, balance_tickets, referral_code)
                VALUES (?, ?, ?, ?, ?, 100, 0, ?)
            ''', (
                user_id,
                data['first_name'],
                data.get('last_name', ''),
                data.get('username', ''),
                data.get('photo_url', ''),
                new_referral_code
            ))
            conn.commit()
            stars = 100
            tickets = 0

            if referral_code:
                process_referral(user_id, referral_code)

            add_history_record(user_id, 'registration', 0, 'Регистрация в системе')
            logger.info(f"✅ Зарегистрирован новый пользователь: {data['first_name']}")
        else:
            cursor.execute('''
                UPDATE users
                SET first_name = ?, last_name = ?, username = ?, photo_url = ?
                WHERE id = ?
            ''', (
                data['first_name'],
                data.get('last_name', ''),
                data.get('username', ''),
                data.get('photo_url', ''),
                user_id
            ))
            conn.commit()
            stars = user[5]
            tickets = user[6]
            logger.info(f"✅ Пользователь уже существует: {data['first_name']}")

        conn.close()

        return jsonify({
            'success': True,
            'user': {
                'id': user_id,
                'first_name': data['first_name'],
                'last_name': data.get('last_name', ''),
                'username': data.get('username', ''),
                'photo_url': data.get('photo_url', ''),
                'balance_stars': stars,
                'balance_tickets': tickets
            }
        })

    except Exception as e:
        logger.error(f"❌ Ошибка авторизации: {e}")
        return jsonify({'success': False, 'error': str(e)})

# USER API
@app.route('/api/user/<int:user_id>', methods=['GET'])
def get_user_data(user_id):
    """Получение данных пользователя"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()

        if not user:
            logger.warning(f"⚠️ Пользователь {user_id} не найден")
            return jsonify({'success': False, 'error': 'Пользователь не найден'})

        cursor.execute('SELECT * FROM inventory WHERE user_id = ? ORDER BY received_at DESC', (user_id,))
        inventory = cursor.fetchall()

        level_info = get_user_level_info(user_id)

        user_dict = {
            'id': user[0],
            'first_name': user[1],
            'last_name': user[2],
            'username': user[3],
            'photo_url': user[4],
            'balance_stars': user[5],
            'balance_tickets': user[6],
            'referral_code': user[8],
            'referral_count': user[10] or 0,
            'total_earned_stars': user[11] or 0,
            'total_earned_tickets': user[12] or 0,
            'referral_bonus_claimed': bool(user[13]) if user[13] is not None else False,
            'experience': user[14] or 0,
            'current_level': user[15] or 1,
            'total_cases_opened': user[16] or 0,
            'level_info': level_info
        }

        inventory_list = []
        for item in inventory:
            inventory_list.append({
                'id': item[0],
                'user_id': item[1],
                'gift_id': item[2],
                'gift_name': item[3],
                'gift_image': item[4],
                'gift_value': item[5],
                'received_at': item[6],
                'is_withdrawing': bool(item[7])
            })

        conn.close()
        return jsonify({
            'success': True,
            'user': user_dict,
            'inventory': inventory_list
        })

    except Exception as e:
        logger.error(f"❌ Ошибка получения данных пользователя: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/inventory/<int:user_id>', methods=['GET'])
def get_user_inventory(user_id):
    """Получение инвентаря пользователя"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM inventory WHERE user_id = ? ORDER BY received_at DESC', (user_id,))
        inventory = cursor.fetchall()
        conn.close()

        inventory_list = []
        for item in inventory:
            inventory_list.append({
                'id': item[0],
                'user_id': item[1],
                'gift_id': item[2],
                'gift_name': item[3],
                'gift_image': item[4],
                'gift_value': item[5],
                'received_at': item[6],
                'is_withdrawing': bool(item[7])
            })

        logger.info(f"🎒 Отправлен инвентарь пользователя {user_id}")
        return jsonify({'success': True, 'inventory': inventory_list})

    except Exception as e:
        logger.error(f"❌ Ошибка получения инвентаря: {e}")
        return jsonify({'success': False, 'error': str(e)})

# CASES API
@app.route('/api/cases')
def api_cases():
    """Получение всех кейсов с актуальными лимитами"""
    try:
        logger.info("📦 Загрузка кейсов из файла...")

        data_path = os.path.join(BASE_PATH, 'data')
        file_path = os.path.join(data_path, 'cases.json')

        logger.info(f"📁 Путь к файлу: {file_path}")

        if not os.path.exists(file_path):
            logger.error(f"❌ Файл cases.json не найден")
            demo_cases = [
                {
                    'id': 1,
                    'name': 'Бесплатный кейс',
                    'image': '/static/img/default_case.png',
                    'cost': 0,
                    'cost_type': 'stars',
                    'description': 'Открывай каждые 24 часа',
                    'limited': False,
                    'display_order': 1
                }
            ]
            return jsonify({'success': True, 'cases': demo_cases})

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            cases = data.get('cases', [])

        logger.info(f"✅ Загружено {len(cases)} кейсов")
        return jsonify({'success': True, 'cases': cases})

    except Exception as e:
        logger.error(f"❌ Критическая ошибка получения кейсов: {e}")
        logger.error(f"❌ Трассировка: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'cases': [],
            'error': 'Внутренняя ошибка сервера'
        })

@app.route('/api/cases/<int:case_id>')
def api_case_detail(case_id):
    """Получение деталей конкретного кейса"""
    try:
        cases = load_cases()
        gifts = load_gifts()

        case = next((c for c in cases if c['id'] == case_id), None)
        if not case:
            logger.error(f"❌ Кейс с ID {case_id} не найден!")
            return jsonify({'success': False, 'error': 'Кейс не найден'})

        if case.get('limited'):
            current_limit = get_case_limit(case_id)
            logger.info(f"📊 Детали кейса {case_id} - лимит: {current_limit}")
            if current_limit is not None:
                case['current_amount'] = current_limit
            else:
                case['current_amount'] = case['amount']
        else:
            case['current_amount'] = None

        case_gifts = []
        for gift_info in case['gifts']:
            gift = next((g for g in gifts if g['id'] == gift_info['id']), None)
            if gift:
                case_gifts.append({
                    **gift,
                    'chance': gift_info['chance']
                })
            else:
                logger.warning(f"⚠️ Подарок с ID {gift_info['id']} не найден для кейса {case_id}")

        case_with_gifts = {**case, 'gifts_details': case_gifts}

        logger.info(f"📦 Отправлены детали кейса {case_id}")
        return jsonify({'success': True, 'case': case_with_gifts})

    except Exception as e:
        logger.error(f"❌ Ошибка получения деталей кейса: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/cases/open', methods=['POST'])
def open_case():
    """Открытие кейса"""
    try:
        data = request.get_json()
        user_id = data['user_id']
        case_id = data['case_id']
        quantity = data.get('quantity', 1)

        cases = load_cases()
        case = next((c for c in cases if c['id'] == case_id), None)

        if not case:
            return jsonify({'success': False, 'error': 'Кейс не найден'})

        if case.get('limited'):
            current_limit = get_case_limit(case_id)
            if current_limit is not None and current_limit <= 0:
                return jsonify({'success': False, 'error': 'Лимит кейса исчерпан'})

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT balance_stars, balance_tickets, current_level FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()

        if not user:
            conn.close()
            return jsonify({'success': False, 'error': 'Пользователь не найден'})

        balance_stars, balance_tickets, user_level = user

        required_level = case.get('required_level', 1)
        if user_level < required_level:
            conn.close()
            return jsonify({'success': False, 'error': f'Требуется {required_level} уровень'})

        total_cost = case['cost'] * quantity
        if case['cost'] > 0:
            if case['cost_type'] == 'stars' and balance_stars < total_cost:
                conn.close()
                return jsonify({'success': False, 'error': 'Недостаточно звезд'})
            elif case['cost_type'] == 'tickets' and balance_tickets < total_cost:
                conn.close()
                return jsonify({'success': False, 'error': 'Недостаточно билетов'})

        if case['cost'] > 0:
            if case['cost_type'] == 'stars':
                cursor.execute('UPDATE users SET balance_stars = balance_stars - ? WHERE id = ?',
                             (total_cost, user_id))
            else:
                cursor.execute('UPDATE users SET balance_tickets = balance_tickets - ? WHERE id = ?',
                             (total_cost, user_id))

        won_gifts = []
        gifts = load_gifts()

        for _ in range(quantity):
            if case.get('gifts'):
                total_chance = sum(gift.get('chance', 1) for gift in case['gifts'])
                random_value = random.random() * total_chance
                current_chance = 0
                selected_gift_info = None

                for gift_info in case['gifts']:
                    current_chance += gift_info.get('chance', 1)
                    if random_value <= current_chance:
                        selected_gift_info = gift_info
                        break

                if selected_gift_info:
                    gift = next((g for g in gifts if g['id'] == selected_gift_info['id']), None)
                    if gift:
                        won_gifts.append(gift)

                        cursor.execute('''
                            INSERT INTO inventory (user_id, gift_id, gift_name, gift_image, gift_value)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (user_id, gift['id'], gift['name'], gift['image'], gift.get('value', 0)))

                        cursor.execute('''
                            INSERT INTO win_history (user_id, user_name, gift_name, gift_image, gift_value, case_name)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (user_id, f"User_{user_id}", gift['name'], gift['image'], gift.get('value', 0), case['name']))
            else:
                if gifts:
                    gift = random.choice(gifts)
                    won_gifts.append(gift)

                    cursor.execute('''
                        INSERT INTO inventory (user_id, gift_id, gift_name, gift_image, gift_value)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (user_id, gift['id'], gift['name'], gift['image'], gift.get('value', 0)))

        if case.get('limited'):
            update_case_limit(case_id)

        exp_gained = max(5, case['cost'] // 10 * quantity)
        cursor.execute('UPDATE users SET experience = experience + ? WHERE id = ?',
                     (exp_gained, user_id))

        cursor.execute('UPDATE users SET total_cases_opened = total_cases_opened + ? WHERE id = ?',
                     (quantity, user_id))

        for gift in won_gifts:
            cursor.execute('''
                INSERT INTO case_open_history (user_id, case_id, case_name, gift_id, gift_name, gift_image, gift_value, cost, cost_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, case_id, case['name'], gift['id'], gift['name'], gift['image'], gift.get('value', 0), case['cost'], case['cost_type']))

        conn.commit()

        cursor.execute('SELECT balance_stars, balance_tickets FROM users WHERE id = ?', (user_id,))
        new_balance = cursor.fetchone()

        conn.close()

        return jsonify({
            'success': True,
            'won_gifts': won_gifts,
            'new_balance': {
                'stars': new_balance[0],
                'tickets': new_balance[1]
            },
            'exp_gained': exp_gained
        })

    except Exception as e:
        logger.error(f"❌ Ошибка открытия кейса: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/debug-cases', methods=['GET'])
def debug_cases():
    """Отладочная информация о кейсах"""
    try:
        logger.info("🔍 Отладочная информация о кейсах")

        file_path = os.path.join(BASE_PATH, 'data', 'cases.json')
        logger.info(f"📁 Путь к файлу cases.json: {file_path}")

        exists = os.path.exists(file_path)
        logger.info(f"📁 Файл существует: {exists}")

        cases_info = []
        if exists:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    logger.info(f"📁 Размер файла: {len(content)} байт")

                    data = json.loads(content)
                    cases = data.get('cases', [])
                    logger.info(f"📁 Найдено кейсов: {len(cases)}")

                    for i, case in enumerate(cases[:5]):
                        cases_info.append({
                            'id': case.get('id'),
                            'name': case.get('name'),
                            'cost': case.get('cost'),
                            'limited': case.get('limited')
                        })
            except Exception as e:
                logger.error(f"❌ Ошибка чтения файла: {e}")

        return jsonify({
            'success': True,
            'file_path': file_path,
            'exists': exists,
            'base_path': BASE_PATH,
            'cases_sample': cases_info,
            'current_dir': os.getcwd(),
            'data_dir_exists': os.path.exists(os.path.join(BASE_PATH, 'data'))
        })

    except Exception as e:
        logger.error(f"❌ Ошибка отладки: {e}")
        return jsonify({'success': False, 'error': str(e)})

# HISTORY API
@app.route('/api/recent-wins', methods=['GET'])
def get_recent_wins():
    """Получение последних побед для главной страницы"""
    try:
        limit = request.args.get('limit', 10, type=int)

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT user_name, gift_name, gift_image, gift_value, created_at
            FROM win_history
            ORDER BY created_at DESC
            LIMIT ?
        ''', (limit,))

        wins = cursor.fetchall()
        conn.close()

        win_history_list = []
        for win in wins:
            user_name, gift_name, gift_image, gift_value, created_at = win

            win_history_list.append({
                'user_name': user_name,
                'gift_name': gift_name,
                'gift_image': gift_image,
                'gift_value': gift_value,
                'created_at': created_at
            })

        logger.info(f"📊 Отправлено {len(win_history_list)} записей истории побед")
        return jsonify({
            'success': True,
            'wins': win_history_list
        })

    except Exception as e:
        logger.error(f"❌ Ошибка получения истории побед: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'wins': []
        })

@app.route('/api/recent-case-opens', methods=['GET'])
def get_recent_case_opens():
    """Получение последних открытий кейсов"""
    try:
        limit = request.args.get('limit', 20, type=int)
        user_id = request.args.get('user_id')

        conn = get_db_connection()
        cursor = conn.cursor()

        if user_id:
            cursor.execute('''
                SELECT case_name, gift_name, gift_image, gift_value, cost, cost_type, created_at
                FROM case_open_history
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            ''', (user_id, limit))
        else:
            cursor.execute('''
                SELECT case_name, gift_name, gift_image, gift_value, cost, cost_type, created_at
                FROM case_open_history
                ORDER BY created_at DESC
                LIMIT ?
            ''', (limit,))

        opens = cursor.fetchall()
        conn.close()

        open_history_list = []
        for open_item in opens:
            case_name, gift_name, gift_image, gift_value, cost, cost_type, created_at = open_item

            file_extension = gift_image.lower().split('.')[-1] if '.' in gift_image else ''
            is_gif = file_extension == 'gif'
            is_image = file_extension in ['png', 'jpg', 'jpeg', 'webp']

            open_history_list.append({
                'case_name': case_name,
                'gift_name': gift_name,
                'gift_image': gift_image,
                'gift_value': gift_value,
                'cost': cost,
                'cost_type': cost_type,
                'created_at': created_at,
                'is_gif': is_gif,
                'is_image': is_image
            })

        logger.info(f"📊 Отправлено {len(open_history_list)} записей истории открытий")
        return jsonify({
            'success': True,
            'opens': open_history_list
        })

    except Exception as e:
        logger.error(f"❌ Ошибка получения истории открытий: {e}")
        return jsonify({'success': False, 'error': str(e)})

# DAILY BONUS API
@app.route('/api/claim-daily-bonus', methods=['POST'])
def claim_daily_bonus():
    """Получение ежедневного бонуса"""
    try:
        data = request.get_json()
        user_id = data['user_id']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT last_daily_bonus, consecutive_days FROM users WHERE id = ?', (user_id,))
        result = cursor.fetchone()

        if not result:
            conn.close()
            return jsonify({'success': False, 'error': 'Пользователь не найден'})

        last_bonus, consecutive_days = result
        now = datetime.now()

        if last_bonus:
            last_bonus_date = datetime.fromisoformat(last_bonus.replace('Z', '+00:00'))
            hours_diff = (now - last_bonus_date).total_seconds() / 3600

            if hours_diff < 24:
                conn.close()
                return jsonify({'success': False, 'error': 'Бонус уже получен сегодня'})

            if hours_diff < 48:
                consecutive_days = (consecutive_days or 0) + 1
            else:
                consecutive_days = 1
        else:
            consecutive_days = 1

        base_stars = 5
        bonus_stars = min(consecutive_days * 2, 20)
        total_stars = base_stars + bonus_stars

        cursor.execute('''
            UPDATE users
            SET balance_stars = balance_stars + ?,
                total_earned_stars = total_earned_stars + ?,
                last_daily_bonus = ?,
                consecutive_days = ?
            WHERE id = ?
        ''', (total_stars, total_stars, now.isoformat(), consecutive_days, user_id))

        add_experience(user_id, 10, "Ежедневный бонус")

        add_history_record(user_id, 'daily_bonus', total_stars,
                         f'Ежедневный бонус ({consecutive_days} день подряд)')

        conn.commit()
        conn.close()

        logger.info(f"🎁 Пользователь {user_id} получил ежедневный бонус: {total_stars} звезд")
        return jsonify({
            'success': True,
            'stars_rewarded': total_stars,
            'consecutive_days': consecutive_days,
            'message': f'🎉 Ежедневный бонус! Вы получили {total_stars} звезд!'
        })

    except Exception as e:
        logger.error(f"❌ Ошибка получения ежедневного бонуса: {e}")
        return jsonify({'success': False, 'error': str(e)})

# SELL GIFTS API
@app.route('/api/sell-gift', methods=['POST'])
def sell_gift():
    """Продажа подарка из инвентаря"""
    try:
        data = request.get_json()
        user_id = data['user_id']
        gift_id = data['gift_id']

        logger.info(f"💰 Пользователь {user_id} продает подарок из инвентаря {gift_id}")

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT gift_name, gift_value, is_withdrawing FROM inventory WHERE id = ? AND user_id = ?', (gift_id, user_id))
        gift = cursor.fetchone()

        if not gift:
            conn.close()
            return jsonify({'success': False, 'error': 'Подарок не найден в инвентаре'})

        gift_name, gift_value, is_withdrawing = gift

        if is_withdrawing:
            conn.close()
            return jsonify({'success': False, 'error': 'Подарок находится в процессе вывода и не может быть продан'})

        cursor.execute('DELETE FROM inventory WHERE id = ?', (gift_id,))

        if gift_value > 0:
            cursor.execute('''
                UPDATE users
                SET balance_stars = balance_stars + ?,
                    total_earned_stars = total_earned_stars + ?
                WHERE id = ?
            ''', (gift_value, gift_value, user_id))

        exp_gained = max(1, gift_value // 100)
        cursor.execute('UPDATE users SET experience = experience + ? WHERE id = ?', (exp_gained, user_id))

        cursor.execute('''
            INSERT INTO user_history (user_id, operation_type, amount, description)
            VALUES (?, 'gift_sold', ?, ?)
        ''', (user_id, gift_value, f'Продажа подарка: {gift_name}'))

        conn.commit()

        cursor.execute('SELECT balance_stars, balance_tickets FROM users WHERE id = ?', (user_id,))
        new_balance = cursor.fetchone()
        conn.close()

        logger.info(f"✅ Подарок продан за {gift_value} звезд")

        return jsonify({
            'success': True,
            'message': f'Подарок продан за {gift_value} звезд!',
            'new_balance': {
                'stars': new_balance[0],
                'tickets': new_balance[1]
            }
        })

    except Exception as e:
        logger.error(f"❌ Ошибка продажи подарка: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/sell-all-gifts', methods=['POST'])
def sell_all_gifts():
    """Продажа всех подарков из инвентаря"""
    try:
        data = request.get_json()
        user_id = data['user_id']

        logger.info(f"💰 Пользователь {user_id} продает все подарки из инвентаря")

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id, gift_name, gift_value FROM inventory WHERE user_id = ? AND is_withdrawing = FALSE', (user_id,))
        gifts = cursor.fetchall()

        if not gifts:
            conn.close()
            return jsonify({'success': False, 'error': 'В инвентаре нет предметов для продажи'})

        total_value = 0
        sold_count = len(gifts)

        for gift in gifts:
            total_value += gift[2] or 0

        cursor.execute('DELETE FROM inventory WHERE user_id = ? AND is_withdrawing = FALSE', (user_id,))

        if total_value > 0:
            cursor.execute('''
                UPDATE users
                SET balance_stars = balance_stars + ?,
                    total_earned_stars = total_earned_stars + ?
                WHERE id = ?
            ''', (total_value, total_value, user_id))

        exp_gained = max(5, total_value // 50)
        cursor.execute('UPDATE users SET experience = experience + ? WHERE id = ?', (exp_gained, user_id))

        cursor.execute('''
            INSERT INTO user_history (user_id, operation_type, amount, description)
            VALUES (?, 'mass_sell', ?, ?)
        ''', (user_id, total_value, f'Массовая продажа {sold_count} предметов'))

        conn.commit()

        cursor.execute('SELECT balance_stars, balance_tickets FROM users WHERE id = ?', (user_id,))
        new_balance = cursor.fetchone()
        conn.close()

        logger.info(f"✅ Продано {sold_count} предметов за {total_value} звезд")

        return jsonify({
            'success': True,
            'message': f'Продано {sold_count} предметов за {total_value} звезд!',
            'sold_count': sold_count,
            'total_value': total_value,
            'new_balance': {
                'stars': new_balance[0],
                'tickets': new_balance[1]
            }
        })

    except Exception as e:
        logger.error(f"❌ Ошибка массовой продажи подарков: {e}")
        return jsonify({'success': False, 'error': str(e)})

# WITHDRAWAL API
@app.route('/api/withdraw-gift', methods=['POST'])
def withdraw_gift():
    """Создание заявки на вывод подарка"""
    try:
        data = request.get_json()
        user_id = data['user_id']
        inventory_id = data['gift_id']

        logger.info(f"📤 Пользователь {user_id} создает заявку на вывод подарка {inventory_id}")

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM inventory WHERE id = ? AND user_id = ?', (inventory_id, user_id))
        gift = cursor.fetchone()

        if not gift:
            logger.error(f"❌ Подарок {inventory_id} не найден в инвентаре пользователя {user_id}")
            return jsonify({'success': False, 'error': 'Подарок не найден в инвентаре'})

        if gift[7]:
            logger.error(f"❌ Подарок {inventory_id} уже в процессе вывода")
            return jsonify({'success': False, 'error': 'Подарок уже в процессе вывода'})

        cursor.execute('SELECT first_name, username, photo_url FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()

        if not user:
            logger.error(f"❌ Пользователь {user_id} не найден")
            return jsonify({'success': False, 'error': 'Пользователь не найден'})

        user_first_name, username, photo_url = user

        cursor.execute('UPDATE inventory SET is_withdrawing = TRUE WHERE id = ?', (inventory_id,))

        cursor.execute('''
            INSERT INTO withdrawals (user_id, inventory_id, gift_name, gift_image, gift_value,
                                   telegram_username, user_photo_url, user_first_name, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending')
        ''', (user_id, inventory_id, gift[3], gift[4], gift[5], username, photo_url, user_first_name))

        withdrawal_id = cursor.lastrowid

        add_history_record(user_id, 'withdraw_request', 0, f'Запрос на вывод: {gift[3]}')

        conn.commit()
        conn.close()

        logger.info(f"✅ Создана заявка на вывод #{withdrawal_id} для пользователя {user_id}")
        return jsonify({
            'success': True,
            'message': '✅ Заявка на вывод создана! Ожидайте обработки.',
            'withdrawal_id': withdrawal_id
        })

    except Exception as e:
        logger.error(f"❌ Ошибка создания заявки на вывод: {e}")
        return jsonify({'success': False, 'error': str(e)})

# REFERRAL API
@app.route('/api/referral-info/<int:user_id>', methods=['GET'])
def get_referral_info(user_id):
    """Получение информации о рефералах"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT referral_code, referral_count, total_earned_stars, total_earned_tickets, referral_bonus_claimed FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()

        if not user:
            return jsonify({'success': False, 'error': 'Пользователь не найден'})

        referral_code, referral_count, total_stars, total_tickets, bonus_claimed = user

        cursor.execute('''
            SELECT u.id, u.first_name, u.username, u.photo_url, r.created_at
            FROM referrals r
            JOIN users u ON r.referred_id = u.id
            WHERE r.referrer_id = ?
            ORDER BY r.created_at DESC
        ''', (user_id,))

        referrals = cursor.fetchall()

        cursor.execute('''
            SELECT reward_type, reward_amount, description, created_at
            FROM referral_rewards
            WHERE referrer_id = ?
            ORDER BY created_at DESC
        ''', (user_id,))

        rewards = cursor.fetchall()

        referral_list = []
        for ref in referrals:
            referral_list.append({
                'id': ref[0],
                'name': ref[1],
                'username': ref[2],
                'photo_url': ref[3],
                'date': ref[4]
            })

        rewards_list = []
        for reward in rewards:
            rewards_list.append({
                'type': reward[0],
                'amount': reward[1],
                'description': reward[2],
                'date': reward[3]
            })

        conn.close()

        return jsonify({
            'success': True,
            'referral_code': referral_code,
            'referral_count': referral_count or 0,
            'total_earned_stars': total_stars or 0,
            'total_earned_tickets': total_tickets or 0,
            'referral_bonus_claimed': bool(bonus_claimed),
            'referrals': referral_list,
            'rewards_history': rewards_list
        })

    except Exception as e:
        logger.error(f"❌ Ошибка получения информации о рефералах: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/claim-referral-bonus', methods=['POST'])
def claim_referral_bonus():
    """Получение бонуса за рефералов"""
    try:
        data = request.get_json()
        user_id = data['user_id']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT referral_bonus_claimed, referral_count FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()

        if not user:
            conn.close()
            return jsonify({'success': False, 'error': 'Пользователь не найден'})

        bonus_claimed, referral_count = user

        if bonus_claimed:
            conn.close()
            return jsonify({'success': False, 'error': 'Бонус уже был получен'})

        if referral_count < 3:
            conn.close()
            return jsonify({'success': False, 'error': 'Необходимо пригласить минимум 3 друзей'})

        bonus_stars = 500
        cursor.execute('UPDATE users SET balance_stars = balance_stars + ?, total_earned_stars = total_earned_stars + ?, referral_bonus_claimed = TRUE WHERE id = ?',
                     (bonus_stars, bonus_stars, user_id))

        add_experience(user_id, 100, "Реферальный бонус")

        add_history_record(user_id, 'referral_bonus', bonus_stars, f'Бонус за приглашение {referral_count} друзей')

        cursor.execute('SELECT balance_stars, balance_tickets FROM users WHERE id = ?', (user_id,))
        new_balance = cursor.fetchone()

        conn.commit()
        conn.close()

        logger.info(f"🎁 Пользователь {user_id} получил реферальный бонус: {bonus_stars} звезд")
        return jsonify({
            'success': True,
            'message': f'🎉 Поздравляем! Вы получили {bonus_stars} звезд за приглашение {referral_count} друзей!',
            'bonus_stars': bonus_stars,
            'new_balance': {
                'stars': new_balance[0],
                'tickets': new_balance[1]
            }
        })

    except Exception as e:
        logger.error(f"❌ Ошибка получения реферального бонуса: {e}")
        return jsonify({'success': False, 'error': str(e)})

# UPGRADE API
@app.route('/api/user-upgrade-stats/<int:user_id>', methods=['GET'])
def get_user_upgrade_stats(user_id):
    """Получение статистики апгрейдов пользователя"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT COUNT(*) FROM user_history
            WHERE user_id = ? AND operation_type = 'upgrade_success'
            AND created_at > datetime('now', '-1 hour')
        ''', (user_id,))

        recent_success_count = cursor.fetchone()[0] or 0

        conn.close()

        return jsonify({
            'success': True,
            'recent_success_count': recent_success_count
        })

    except Exception as e:
        logger.error(f"❌ Ошибка получения статистики апгрейдов: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/upgrade-gift-fast', methods=['POST'])
def upgrade_gift_fast():
    """БЫСТРЫЙ апгрейд подарка"""
    try:
        data = request.get_json()
        user_id = data['user_id']
        current_gift_id = data['current_gift_id']
        target_gift_id = data['target_gift_id']

        logger.info(f"⚡ БЫСТРЫЙ апгрейд: пользователь {user_id}, подарок {current_gift_id} -> {target_gift_id}")

        gifts = load_gifts_cached()
        if not gifts:
            return jsonify({'success': False, 'error': 'Не удалось загрузить список подарков'})

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT gift_id, gift_name, gift_value FROM inventory WHERE id = ? AND user_id = ?',
                      (current_gift_id, user_id))
        current_gift = cursor.fetchone()

        if not current_gift:
            conn.close()
            return jsonify({'success': False, 'error': 'Подарок не найден в инвентаре'})

        current_gift_db_id, gift_name, current_value = current_gift

        target_gift = next((g for g in gifts if g['id'] == target_gift_id), None)
        if not target_gift:
            conn.close()
            return jsonify({'success': False, 'error': 'Целевой подарок не найден'})

        target_value = target_gift.get('value', 0)

        if target_value <= current_value:
            conn.close()
            return jsonify({'success': False, 'error': 'Нельзя апгрейдить на подарок такой же или меньшей стоимости'})

        chance = (current_value / target_value) * 100
        chance = max(10, min(chance, 90))

        cursor.execute('''
            SELECT COUNT(*) FROM user_history
            WHERE user_id = ? AND operation_type = 'upgrade_success'
            AND created_at > datetime('now', '-1 hour')
        ''', (user_id,))
        recent_success_count = cursor.fetchone()[0] or 0

        forced_failure = False
        if recent_success_count >= 3:
            success = False
            forced_failure = True
            logger.info(f"🎯 ПРИНУДИТЕЛЬНЫЙ ПРОВАЛ: 4-й апгрейд после {recent_success_count} успешных")
        else:
            random_value = random.random() * 100
            success = random_value <= chance
            logger.info(f"🎯 Обычный апгрейд: случайное число {random_value:.1f} vs шанс {chance:.1f}% = {'УСПЕХ' if success else 'ПРОВАЛ'}")

        try:
            if success:
                cursor.execute('''
                    UPDATE inventory
                    SET gift_id = ?, gift_name = ?, gift_image = ?, gift_value = ?
                    WHERE id = ?
                ''', (target_gift['id'], target_gift['name'], target_gift['image'], target_value, current_gift_id))

                exp_gained = max(5, (target_value - current_value) // 50)
                cursor.execute('UPDATE users SET experience = experience + ? WHERE id = ?', (exp_gained, user_id))

                cursor.execute('''
                    INSERT INTO user_history (user_id, operation_type, amount, description)
                    VALUES (?, 'upgrade_success', ?, ?)
                ''', (user_id, 0, f'Успешный апгрейд: {gift_name} -> {target_gift["name"]}'))

                logger.info(f"✅ Успешный апгрейд: {gift_name} -> {target_gift['name']}")

            else:
                cursor.execute('DELETE FROM inventory WHERE id = ?', (current_gift_id,))

                if forced_failure:
                    cursor.execute('''
                        INSERT INTO user_history (user_id, operation_type, amount, description)
                        VALUES (?, 'upgrade_forced_failure', ?, ?)
                    ''', (user_id, 0, f'Принудительный провал апгрейда: потерян {gift_name}'))
                else:
                    cursor.execute('''
                        INSERT INTO user_history (user_id, operation_type, amount, description)
                        VALUES (?, 'upgrade_failure', ?, ?)
                    ''', (user_id, 0, f'Неудачный апгрейд: потерян {gift_name}'))

                logger.info(f"❌ Неудачный апгрейд: потерян {gift_name}")

            conn.commit()
            conn.close()

            return jsonify({
                'success': True,
                'upgrade_success': success,
                'chance': round(chance, 1),
                'forced_failure': forced_failure,
                'recent_success_count': recent_success_count,
                'new_gift': target_gift if success else None,
                'message': '🎉 Успешный апгрейд!' if success else '❌ Апгрейд не удался'
            })

        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Ошибка транзакции апгрейда: {e}")
            return jsonify({'success': False, 'error': 'Ошибка обработки апгрейда'})

    except Exception as e:
        logger.error(f"❌ Ошибка быстрого апгрейда: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/upgrade-gift', methods=['POST'])
def upgrade_gift():
    """Апгрейд подарка"""
    try:
        data = request.get_json()
        user_id = data['user_id']
        current_gift_id = data['current_gift_id']
        target_gift_id = data['target_gift_id']

        logger.info(f"⚡ Апгрейд: {user_id} -> {current_gift_id} на {target_gift_id}")

        gifts = load_gifts_cached()
        target_gift = next((g for g in gifts if g['id'] == target_gift_id), None)
        if not target_gift:
            return jsonify({'success': False, 'error': 'Целевой подарок не найден'})

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('SELECT gift_name, gift_value FROM inventory WHERE id = ? AND user_id = ?',
                         (current_gift_id, user_id))
            current_gift = cursor.fetchone()

            if not current_gift:
                conn.close()
                return jsonify({'success': False, 'error': 'Подарок не найден'})

            gift_name, current_value = current_gift
            target_value = target_gift.get('value', 0)

            if target_value <= current_value:
                conn.close()
                return jsonify({'success': False, 'error': 'Нельзя апгрейдить на более дешевый подарок'})

            base_chance = max(10, min((current_value / target_value) * 100, 90))
            displayed_chance = round(base_chance, 1)

            price_ratio = target_value / current_value
            real_chance = base_chance

            if target_value > 10000:
                real_chance = base_chance * 0.3
            elif target_value > 5000:
                real_chance = base_chance * 0.4
            elif target_value > 2000:
                real_chance = base_chance * 0.6
            elif target_value > 1000:
                real_chance = base_chance * 0.8

            real_chance = max(5, real_chance)

            logger.info(f"🎯 Шансы: отображаемый {displayed_chance}%, реальный {real_chance:.1f}%, цена: {current_value} -> {target_value}")

            success = random.random() * 100 <= real_chance

            if success:
                cursor.execute('''
                    UPDATE inventory
                    SET gift_id = ?, gift_name = ?, gift_image = ?, gift_value = ?
                    WHERE id = ?
                ''', (target_gift['id'], target_gift['name'], target_gift['image'], target_value, current_gift_id))

                exp_gained = max(5, (target_value - current_value) // 50)
                cursor.execute('UPDATE users SET experience = experience + ? WHERE id = ?', (exp_gained, user_id))

                cursor.execute('''
                    INSERT INTO user_history (user_id, operation_type, amount, description)
                    VALUES (?, 'upgrade_success', 0, ?)
                ''', (user_id, f'Успешный апгрейд: {gift_name} -> {target_gift["name"]}'))

                logger.info(f"✅ Успешный апгрейд: {gift_name} -> {target_gift['name']} (шанс: {real_chance:.1f}%)")
            else:
                cursor.execute('DELETE FROM inventory WHERE id = ?', (current_gift_id,))

                cursor.execute('''
                    INSERT INTO user_history (user_id, operation_type, amount, description)
                    VALUES (?, 'upgrade_failure', 0, ?)
                ''', (user_id, f'Неудачный апгрейд: {gift_name}'))

                logger.info(f"❌ Неудачный апгрейд: {gift_name} (шанс был: {real_chance:.1f}%)")

            conn.commit()
            conn.close()

            return jsonify({
                'success': True,
                'upgrade_success': success,
                'chance': displayed_chance,
                'real_chance': round(real_chance, 1),
                'new_gift': target_gift if success else None,
                'message': '🎉 Успешный апгрейд!' if success else '❌ Апгрейд не удался'
            })

        except sqlite3.OperationalError as e:
            if "database is locked" in str(e):
                logger.warning("🔒 База заблокирована, повторяем запрос...")
                conn.close()
                time.sleep(0.1)
                return upgrade_gift()
            raise e
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Ошибка транзакции: {e}")
            return jsonify({'success': False, 'error': 'Ошибка обработки апгрейда'})
        finally:
            conn.close()

    except Exception as e:
        logger.error(f"❌ Ошибка апгрейда: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/debug-upgrade/<int:inventory_id>', methods=['GET'])
def debug_upgrade(inventory_id):
    """Отладочная информация для апгрейда"""
    try:
        user_id = request.args.get('user_id')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM inventory WHERE id = ? AND user_id = ?', (inventory_id, user_id))
        current_gift = cursor.fetchone()

        gifts = load_gifts_cached()

        conn.close()

        if not current_gift:
            return jsonify({
                'success': False,
                'error': 'Подарок не найден',
                'debug_info': {
                    'inventory_id': inventory_id,
                    'user_id': user_id,
                    'total_gifts_loaded': len(gifts) if gifts else 0
                }
            })

        return jsonify({
            'success': True,
            'debug_info': {
                'current_gift': {
                    'inventory_id': current_gift[0],
                    'user_id': current_gift[1],
                    'gift_id': current_gift[2],
                    'gift_name': current_gift[3],
                    'gift_value': current_gift[5]
                },
                'total_gifts_available': len(gifts) if gifts else 0,
                'gifts_sample': [{'id': g['id'], 'name': g['name'], 'value': g.get('value', 0)} for g in gifts[:5]] if gifts else []
            }
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/upgrade-possible-gifts', methods=['POST'])
def get_upgrade_possible_gifts():
    """Получение возможных подарков для апгрейда"""
    try:
        data = request.get_json()
        current_gift_id = data['current_gift_id']
        user_id = data['user_id']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT gift_value FROM inventory WHERE id = ? AND user_id = ?',
                     (current_gift_id, user_id))
        result = cursor.fetchone()
        conn.close()

        if not result:
            return jsonify({'success': False, 'error': 'Подарок не найден'})

        current_value = result[0]
        gifts = load_gifts_cached()

        if not gifts:
            return jsonify({'success': False, 'error': 'Не удалось загрузить подарки'})

        min_target_value = current_value * 1.2
        possible_gifts = []

        for gift in gifts:
            if gift.get('value', 0) > min_target_value:
                base_chance = (current_value / gift['value']) * 100
                displayed_chance = max(10, min(base_chance, 90))

                possible_gifts.append({
                    **gift,
                    'upgrade_chance': round(displayed_chance, 1)
                })

        possible_gifts.sort(key=lambda x: x.get('value', 0))
        possible_gifts = possible_gifts[:15]

        return jsonify({
            'success': True,
            'current_gift_value': current_value,
            'possible_gifts': possible_gifts
        })

    except Exception as e:
        logger.error(f"❌ Ошибка получения подарков: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/gifts')
def api_gifts():
    """Получение всех подарков для апгрейда"""
    try:
        gifts = load_gifts_cached()

        if not gifts:
            logger.error("❌ Не удалось загрузить подарки")
            return jsonify({
                'success': False,
                'error': 'Не удалось загрузить подарки',
                'gifts': []
            })

        logger.info(f"🎁 Отправлено {len(gifts)} подарков")
        return jsonify({
            'success': True,
            'gifts': gifts
        })
    except Exception as e:
        logger.error(f"❌ Ошибка получения подарков: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'gifts': []
        })

# LEVEL API
@app.route('/api/level-info/<int:user_id>', methods=['GET'])
def get_level_info(user_id):
    """Получение информации об уровне пользователя"""
    try:
        level_info = get_user_level_info(user_id)

        if not level_info:
            return jsonify({'success': False, 'error': 'Информация об уровне не найдена'})

        return jsonify({
            'success': True,
            'level_info': level_info,
            'level_system': LEVEL_SYSTEM
        })

    except Exception as e:
        logger.error(f"❌ Ошибка получения информации об уровне: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/level-history/<int:user_id>', methods=['GET'])
def get_level_history(user_id):
    """Получение истории повышения уровней"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT old_level, new_level, experience_gained, reason, created_at
            FROM level_history
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 20
        ''', (user_id,))

        history = cursor.fetchall()
        conn.close()

        history_list = []
        for item in history:
            history_list.append({
                'old_level': item[0],
                'new_level': item[1],
                'experience_gained': item[2],
                'reason': item[3],
                'date': item[4]
            })

        return jsonify({
            'success': True,
            'history': history_list
        })

    except Exception as e:
        logger.error(f"❌ Ошибка получения истории уровней: {e}")
        return jsonify({'success': False, 'error': str(e)})

# PAYMENT API
@app.route('/api/create-stars-payment', methods=['POST'])
def create_stars_payment():
    """Создание платежа через Telegram Stars"""
    try:
        data = request.get_json()
        user_id = data['user_id']
        amount = data['amount']

        logger.info(f"⭐ Создание платежа Telegram Stars: пользователь {user_id}, сумма {amount}")

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO deposits (user_id, amount, currency, status, payment_method)
            VALUES (?, ?, 'stars', 'pending', 'telegram_stars')
        ''', (user_id, amount))

        deposit_id = cursor.lastrowid

        add_history_record(user_id, 'stars_payment_created', 0, f'Создан платеж Telegram Stars: {amount} звезд')

        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'message': '✅ Платеж создан! Используйте кнопку ниже для оплаты через Telegram Stars.',
            'deposit_id': deposit_id,
            'payment_url': f'https://t.me/your_bot_name?start=stars_{deposit_id}'
        })

    except Exception as e:
        logger.error(f"❌ Ошибка создания платежа Stars: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/complete-stars-payment', methods=['POST'])
def complete_stars_payment():
    """Завершение платежа Telegram Stars"""
    try:
        data = request.get_json()
        admin_id = data.get('admin_id')
        deposit_id = data.get('deposit_id')

        if admin_id and int(admin_id) != ADMIN_ID:
            return jsonify({'success': False, 'error': 'Доступ запрещен'})

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT user_id, amount, status FROM deposits WHERE id = ?', (deposit_id,))
        deposit = cursor.fetchone()

        if not deposit:
            conn.close()
            return jsonify({'success': False, 'error': 'Платеж не найден'})

        user_id, amount, status = deposit

        if status == 'completed':
            conn.close()
            return jsonify({'success': False, 'error': 'Платеж уже завершен'})

        cursor.execute('UPDATE users SET balance_stars = balance_stars + ?, total_earned_stars = total_earned_stars + ? WHERE id = ?',
                     (amount, amount, user_id))

        add_experience(user_id, amount // 10, f"Пополнение баланса на {amount} звезд")

        cursor.execute('UPDATE deposits SET status = "completed", completed_at = CURRENT_TIMESTAMP WHERE id = ?', (deposit_id,))

        add_history_record(user_id, 'stars_payment_completed', amount, f'Пополнение через Telegram Stars: {amount} звезд')

        conn.commit()

        cursor.execute('SELECT balance_stars, balance_tickets FROM users WHERE id = ?', (user_id,))
        new_balance = cursor.fetchone()
        conn.close()

        logger.info(f"✅ Платеж Stars #{deposit_id} завершен, пользователь {user_id} получил {amount} звезд")
        return jsonify({
            'success': True,
            'message': f'Баланс пополнен на {amount} звезд!',
            'new_balance': {
                'stars': new_balance[0],
                'tickets': new_balance[1]
            }
        })

    except Exception as e:
        logger.error(f"❌ Ошибка завершения платежа Stars: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/check-stars-payment/<int:deposit_id>', methods=['GET'])
def check_stars_payment(deposit_id):
    """Проверка статуса платежа Telegram Stars"""
    try:
        user_id = request.args.get('user_id')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT status, amount, user_id FROM deposits WHERE id = ?', (deposit_id,))
        deposit = cursor.fetchone()

        if not deposit:
            conn.close()
            return jsonify({'success': False, 'error': 'Платеж не найден'})

        status, amount, deposit_user_id = deposit

        if str(deposit_user_id) != str(user_id):
            conn.close()
            return jsonify({'success': False, 'error': 'Доступ запрещен'})

        conn.close()

        return jsonify({
            'success': True,
            'status': status,
            'amount': amount,
            'message': f'Статус платежа: {status}'
        })

    except Exception as e:
        logger.error(f"❌ Ошибка проверки платежа: {e}")
        return jsonify({'success': False, 'error': str(e)})

# PROMO CODE API
@app.route('/api/use-promo-code', methods=['POST'])
def use_promo_code():
    """Активация промокода"""
    try:
        data = request.get_json()
        user_id = data['user_id']
        promo_code = data['promo_code'].upper().strip()

        logger.info(f"🎟️ Пользователь {user_id} активирует промокод: {promo_code}")

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, reward_stars, reward_tickets, max_uses, used_count, expires_at, is_active
            FROM promo_codes
            WHERE code = ?
        ''', (promo_code,))

        promo = cursor.fetchone()

        if not promo:
            conn.close()
            return jsonify({'success': False, 'error': 'Промокод не найден'})

        promo_id, reward_stars, reward_tickets, max_uses, used_count, expires_at, is_active = promo

        if not is_active:
            conn.close()
            return jsonify({'success': False, 'error': 'Промокод неактивен'})

        if expires_at:
            expires_date = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            if datetime.now() > expires_date:
                conn.close()
                return jsonify({'success': False, 'error': 'Срок действия промокода истек'})

        if max_uses > 0 and used_count >= max_uses:
            conn.close()
            return jsonify({'success': False, 'error': 'Лимит использований промокода исчерпан'})

        cursor.execute('SELECT id FROM used_promo_codes WHERE user_id = ? AND promo_code_id = ?', (user_id, promo_id))
        already_used = cursor.fetchone()

        if already_used:
            conn.close()
            return jsonify({'success': False, 'error': 'Вы уже использовали этот промокод'})

        if reward_stars > 0:
            cursor.execute('UPDATE users SET balance_stars = balance_stars + ?, total_earned_stars = total_earned_stars + ? WHERE id = ?',
                         (reward_stars, reward_stars, user_id))

        if reward_tickets > 0:
            cursor.execute('UPDATE users SET balance_tickets = balance_tickets + ?, total_earned_tickets = total_earned_tickets + ? WHERE id = ?',
                         (reward_tickets, reward_tickets, user_id))

        cursor.execute('UPDATE users SET experience = experience + 25 WHERE id = ?', (user_id,))

        cursor.execute('UPDATE promo_codes SET used_count = used_count + 1 WHERE id = ?', (promo_id,))

        cursor.execute('INSERT INTO used_promo_codes (user_id, promo_code_id) VALUES (?, ?)', (user_id, promo_id))

        rewards_text = []
        if reward_stars > 0:
            rewards_text.append(f'{reward_stars}⭐')
        if reward_tickets > 0:
            rewards_text.append(f'{reward_tickets}🎫')

        cursor.execute('''
            INSERT INTO user_history (user_id, operation_type, amount, description)
            VALUES (?, 'promo_code', ?, ?)
        ''', (user_id, reward_stars + reward_tickets, f'Активация промокода {promo_code}: {", ".join(rewards_text)}'))

        conn.commit()
        conn.close()

        logger.info(f"✅ Пользователь {user_id} активировал промокод {promo_code}")
        return jsonify({
            'success': True,
            'message': f'Промокод активирован! Вы получили: {reward_stars}⭐ и {reward_tickets}🎫',
            'rewards': {
                'stars': reward_stars,
                'tickets': reward_tickets
            }
        })

    except Exception as e:
        logger.error(f"❌ Ошибка активации промокода: {e}")
        return jsonify({'success': False, 'error': str(e)})

# ==================== ULTIMATE CRASH API ====================

@app.route('/api/ultimate-crash/status', methods=['GET'])
def ultimate_crash_status():
    """Получение статуса Ultimate Crash"""
    try:
        user_id = request.args.get('user_id')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, status, current_multiplier, target_multiplier,
                   start_time, created_at
            FROM ultimate_crash_games
            WHERE status IN ('waiting', 'counting', 'flying')
            ORDER BY id DESC LIMIT 1
        ''')

        game = cursor.fetchone()

        if not game:
            target_multiplier = round(random.uniform(3.0, 10.0), 2)
            cursor.execute('''
                INSERT INTO ultimate_crash_games (status, target_multiplier, start_time)
                VALUES ('waiting', ?, CURRENT_TIMESTAMP)
            ''', (target_multiplier,))
            game_id = cursor.lastrowid
            conn.commit()

            cursor.execute('''
                SELECT id, status, current_multiplier, target_multiplier,
                       start_time, created_at
                FROM ultimate_crash_games
                WHERE id = ?
            ''', (game_id,))
            game = cursor.fetchone()

        game_id, status, current_mult, target_mult, start_time, created_at = game

        cursor.execute('''
            SELECT
                ucb.id,
                ucb.user_id,
                ucb.bet_amount,
                ucb.status,
                ucb.cashout_multiplier,
                ucb.win_amount,
                ucb.created_at,
                u.first_name,
                u.username,
                u.photo_url
            FROM ultimate_crash_bets ucb
            LEFT JOIN users u ON ucb.user_id = u.id
            WHERE ucb.game_id = ? AND ucb.status = 'active'
            ORDER BY ucb.created_at DESC
        ''', (game_id,))

        bets = cursor.fetchall()

        user_bet = None
        if user_id:
            cursor.execute('''
                SELECT * FROM ultimate_crash_bets
                WHERE game_id = ? AND user_id = ? AND status = 'active'
                ORDER BY created_at DESC LIMIT 1
            ''', (game_id, user_id))
            user_bet_data = cursor.fetchone()

            if user_bet_data:
                user_bet = {
                    'id': user_bet_data[0],
                    'game_id': user_bet_data[1],
                    'user_id': user_bet_data[2],
                    'bet_amount': user_bet_data[3],
                    'gift_value': user_bet_data[4],
                    'status': user_bet_data[5],
                    'cashout_multiplier': user_bet_data[6],
                    'win_amount': user_bet_data[7],
                    'created_at': user_bet_data[8]
                }

        conn.close()

        bets_list = []
        for bet in bets:
            if len(bet) >= 10:
                bet_data = {
                    'id': bet[0],
                    'user_id': bet[1],
                    'bet_amount': bet[2],
                    'status': bet[3],
                    'cashout_multiplier': float(bet[4]) if bet[4] else None,
                    'win_amount': bet[5],
                    'created_at': bet[6],
                    'first_name': bet[7],
                    'username': bet[8],
                    'photo_url': bet[9] or '/static/img/default_avatar.png',
                    'user_name': bet[7] or f'Игрок {bet[1]}'
                }
                bets_list.append(bet_data)

        game_data = {
            'id': game_id,
            'status': status,
            'current_multiplier': float(current_mult) if current_mult else 1.0,
            'target_multiplier': float(target_mult) if target_mult else 5.0,
            'start_time': start_time,
            'created_at': created_at
        }

        return jsonify({
            'success': True,
            'game': game_data,
            'active_bets': bets_list,
            'user_bet': user_bet
        })

    except Exception as e:
        logger.error(f"❌ Ошибка получения статуса Ultimate Crash: {e}")
        logger.error(f"❌ Трассировка: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/ultimate-crash/bet', methods=['POST'])
def ultimate_crash_bet():
    """Размещение ставки в Ultimate Crash"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        bet_amount = data.get('bet_amount', 0)

        logger.info(f"🎯 Ставка Ultimate Crash: user {user_id}, сумма {bet_amount}")

        if not user_id:
            return jsonify({'success': False, 'error': 'ID пользователя не указан'})

        if bet_amount < 25:
            return jsonify({'success': False, 'error': 'Минимальная ставка 25⭐'})

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT balance_stars FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()

        if not user:
            conn.close()
            return jsonify({'success': False, 'error': 'Пользователь не найден'})

        if user[0] < bet_amount:
            conn.close()
            return jsonify({'success': False, 'error': 'Недостаточно звезд'})

        cursor.execute('''
            SELECT id, status FROM ultimate_crash_games
            WHERE status = 'waiting'
            ORDER BY id DESC LIMIT 1
        ''')

        game = cursor.fetchone()

        if not game:
            conn.close()
            return jsonify({'success': False, 'error': 'Нет активных игр для ставок'})

        game_id, game_status = game

        if game_status != 'waiting':
            conn.close()
            return jsonify({'success': False, 'error': 'Игра уже началась'})

        cursor.execute('UPDATE users SET balance_stars = balance_stars - ? WHERE id = ?',
                     (bet_amount, user_id))

        cursor.execute('''
            INSERT INTO ultimate_crash_bets (game_id, user_id, bet_amount, gift_value, status)
            VALUES (?, ?, ?, ?, 'active')
        ''', (game_id, user_id, bet_amount, bet_amount))

        bet_id = cursor.lastrowid

        add_history_record(user_id, 'ultimate_crash_bet', -bet_amount,
                         f'Ставка в Ultimate Crash: {bet_amount}⭐')

        conn.commit()
        conn.close()

        logger.info(f"✅ Ставка размещена: {bet_amount} (ID: {bet_id})")

        return jsonify({
            'success': True,
            'bet_id': bet_id,
            'game_id': game_id,
            'message': 'Ставка размещена!'
        })

    except Exception as e:
        logger.error(f"❌ Ошибка ставки Ultimate Crash: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/ultimate-crash/cashout', methods=['POST'])
def ultimate_crash_cashout():
    """Забрать выигрыш в Ultimate Crash"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        cashout_multiplier = data.get('cashout_multiplier', 1.0)

        if not user_id:
            return jsonify({'success': False, 'error': 'ID пользователя не указан'})

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, current_multiplier FROM ultimate_crash_games
            WHERE status = 'flying'
            ORDER BY id DESC LIMIT 1
        ''')

        game = cursor.fetchone()

        if not game:
            conn.close()
            return jsonify({'success': False, 'error': 'Нет активной игры'})

        game_id, current_mult = game[0], float(game[1]) if game[1] else 1.0

        cursor.execute('''
            SELECT id, bet_amount FROM ultimate_crash_bets
            WHERE game_id = ? AND user_id = ? AND status = 'active'
            ORDER BY created_at DESC LIMIT 1
        ''', (game_id, user_id))

        bet = cursor.fetchone()

        if not bet:
            conn.close()
            return jsonify({'success': False, 'error': 'Активная ставка не найдена'})

        bet_id, bet_amount = bet

        final_multiplier = min(cashout_multiplier, current_mult)
        win_amount = int(bet_amount * final_multiplier)

        cursor.execute('''
            UPDATE ultimate_crash_bets
            SET status = 'cashed_out',
                cashout_multiplier = ?,
                win_amount = ?
            WHERE id = ?
        ''', (final_multiplier, win_amount, bet_id))

        cursor.execute('''
            UPDATE users
            SET balance_stars = balance_stars + ?,
                total_earned_stars = total_earned_stars + ?
            WHERE id = ?
        ''', (win_amount, win_amount, user_id))

        exp_gained = max(5, win_amount // 100)
        cursor.execute('UPDATE users SET experience = experience + ? WHERE id = ?',
                     (exp_gained, user_id))

        add_history_record(user_id, 'ultimate_crash_win', win_amount,
                         f'Выигрыш в Ultimate Crash: x{final_multiplier:.2f}')

        conn.commit()
        conn.close()

        logger.info(f"✅ Кэшаут: {win_amount} (x{final_multiplier:.2f})")

        return jsonify({
            'success': True,
            'win_amount': win_amount,
            'multiplier': final_multiplier,
            'message': f'Вы выиграли {win_amount}⭐!'
        })

    except Exception as e:
        logger.error(f"❌ Ошибка кэшаута Ultimate Crash: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/ultimate-crash/game-state', methods=['GET'])
def ultimate_crash_game_state():
    """Полное состояние игры с учетом времени (с обработкой блокировок)"""
    max_retries = 3
    retry_delay = 0.1

    for attempt in range(max_retries):
        try:
            user_id = request.args.get('user_id')

            conn = get_db_connection()
            cursor = conn.cursor()

            # Используем транзакцию для атомарности
            cursor.execute('BEGIN IMMEDIATE')

            cursor.execute('''
                SELECT id, status, current_multiplier, target_multiplier,
                       start_time, created_at
                FROM ultimate_crash_games
                WHERE status IN ('waiting', 'counting', 'flying')
                ORDER BY id DESC LIMIT 1
            ''')

            game = cursor.fetchone()

            if not game:
                target_multiplier = generate_extreme_crash_multiplier()
                cursor.execute('''
                    INSERT INTO ultimate_crash_games (status, target_multiplier, start_time)
                    VALUES ('waiting', ?, datetime('now'))
                ''', (target_multiplier,))
                game_id = cursor.lastrowid
                conn.commit()

                cursor.execute('''
                    SELECT id, status, current_multiplier, target_multiplier,
                           start_time, created_at
                    FROM ultimate_crash_games
                    WHERE id = ?
                ''', (game_id,))
                game = cursor.fetchone()

            game_id, status, current_mult, target_mult, start_time, created_at = game

            # Упрощенная обработка времени
            import time as time_module

            if start_time:
                try:
                    # Преобразуем строку времени в timestamp
                    if isinstance(start_time, str):
                        # Убираем миллисекунды если есть
                        if '.' in start_time:
                            start_time = start_time.split('.')[0]

                        # Парсим время
                        try:
                            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                        except:
                            # Пробуем другие форматы
                            try:
                                start_dt = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
                            except:
                                start_dt = datetime.now()
                    else:
                        start_dt = datetime.now()

                    start_timestamp = time_module.mktime(start_dt.timetuple())
                except Exception as e:
                    logger.error(f"Ошибка парсинга времени: {e}")
                    start_timestamp = time_module.time() - 30
            else:
                start_timestamp = time_module.time() - 30

            current_time = time_module.time()
            elapsed = current_time - start_timestamp

            time_remaining = 0
            next_phase = status

            # Фаза 1: Ожидание (15 секунд)
            if status == 'waiting':
                time_remaining = max(0, 15 - elapsed)
                if time_remaining <= 0:
                    next_phase = 'counting'
                    cursor.execute('UPDATE ultimate_crash_games SET status = "counting" WHERE id = ?', (game_id,))
                    conn.commit()
                    time_remaining = 5
            # Фаза 2: Отсчет (5 секунд)
            elif status == 'counting':
                time_remaining = max(0, 5 - (elapsed - 15))
                if time_remaining <= 0:
                    next_phase = 'flying'
                    cursor.execute('UPDATE ultimate_crash_games SET status = "flying" WHERE id = ?', (game_id,))
                    conn.commit()
                    time_remaining = 30  # Максимальное время полета
            # Фаза 3: Полет
            elif status == 'flying':
                current_mult_float = float(current_mult) if current_mult else 1.0
                target_mult_float = float(target_mult) if target_mult else 5.0

                # Расчет оставшегося времени полета с разной скоростью
                if current_mult_float >= target_mult_float:
                    time_remaining = 0
                elif current_mult_float < 1.5:
                    # 5 секунд до 1.5x
                    progress = (current_mult_float - 1.0) / 0.5
                    time_remaining = (1.5 - current_mult_float) * (5 / 0.5)
                elif current_mult_float < 2.0:
                    # 3 секунды от 1.5 до 2.0
                    progress = 1.0 + (current_mult_float - 1.5) / 0.5
                    time_remaining = (2.0 - current_mult_float) * (3 / 0.5)
                elif current_mult_float < 4.0:
                    # 6 секунд от 2.0 до 4.0
                    progress = 2.0 + (current_mult_float - 2.0) / 2.0
                    time_remaining = (4.0 - current_mult_float) * (6 / 2.0)
                else:
                    # Быстрее после 4.0
                    progress = 3.0 + (current_mult_float - 4.0)
                    time_remaining = (target_mult_float - current_mult_float) * 1.5

                time_remaining = max(0.1, time_remaining)

                # Медленно увеличиваем множитель
                if current_mult_float < target_mult_float:
                    increment = 0.02  # Базовое увеличение

                    # Разная скорость на разных интервалах
                    if current_mult_float < 1.5:
                        increment = 0.02 * (5 / 15)  # Медленнее
                    elif current_mult_float < 2.0:
                        increment = 0.016 * (3 / 15)  # Средняя скорость
                    elif current_mult_float < 4.0:
                        increment = 0.033 * (6 / 15)  # Быстрее
                    else:
                        increment = 0.066 * (2 / 15)  # Очень быстро

                    # Учитываем время между запросами
                    time_since_last_update = min(elapsed, 2.0)  # Макс 2 секунды
                    increment = increment * time_since_last_update * 10  # Масштабируем

                    new_multiplier = round(current_mult_float + increment, 2)
                    if new_multiplier > target_mult_float:
                        new_multiplier = target_mult_float

                    cursor.execute('UPDATE ultimate_crash_games SET current_multiplier = ? WHERE id = ?',
                                 (new_multiplier, game_id))
                    conn.commit()

            user_bet = None
            if user_id:
                cursor.execute('''
                    SELECT id, bet_amount, status FROM ultimate_crash_bets
                    WHERE game_id = ? AND user_id = ? AND status = 'active'
                    ORDER BY created_at DESC LIMIT 1
                ''', (game_id, user_id))

                bet = cursor.fetchone()

                if bet:
                    user_bet = {
                        'id': bet[0],
                        'bet_amount': bet[1],
                        'status': bet[2]
                    }

            conn.close()

            game_data = {
                'id': game_id,
                'status': next_phase,
                'current_multiplier': float(current_mult) if current_mult else 1.0,
                'target_multiplier': float(target_mult) if target_mult else 5.0,
                'time_remaining': round(time_remaining, 1),
                'can_bet': next_phase == 'waiting'
            }

            return jsonify({
                'success': True,
                'game': game_data,
                'user_bet': user_bet
            })

        except sqlite3.OperationalError as e:
            if "database is locked" in str(e) and attempt < max_retries - 1:
                logger.warning(f"🔒 База заблокирована, повторная попытка {attempt + 1}/{max_retries}")
                try:
                    if 'conn' in locals():
                        conn.close()
                except:
                    pass
                time.sleep(retry_delay * (attempt + 1))  # Экспоненциальная задержка
                continue
            else:
                logger.error(f"❌ Критическая ошибка базы данных: {e}")
                return jsonify({'success': False, 'error': 'Ошибка доступа к базе данных'})

        except Exception as e:
            logger.error(f"❌ Ошибка получения состояния игры: {e}")
            logger.error(f"❌ Трассировка: {traceback.format_exc()}")
            try:
                if 'conn' in locals():
                    conn.close()
            except:
                pass
            return jsonify({'success': False, 'error': str(e)})

@app.route('/api/ultimate-crash/user-bet', methods=['GET'])
def get_user_ultimate_crash_bet():
    """Получение активной ставки пользователя"""
    try:
        user_id = request.args.get('user_id')

        if not user_id:
            return jsonify({'success': False, 'error': 'ID пользователя не указан'})

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id FROM ultimate_crash_games
            WHERE status IN ('waiting', 'counting', 'flying')
            ORDER BY id DESC LIMIT 1
        ''')
        game = cursor.fetchone()

        user_bet = None
        if game:
            game_id = game[0]

            cursor.execute('''
                SELECT * FROM ultimate_crash_bets
                WHERE game_id = ? AND user_id = ? AND status = 'active'
                ORDER BY created_at DESC LIMIT 1
            ''', (game_id, user_id))

            bet = cursor.fetchone()

            if bet:
                user_bet = {
                    'id': bet[0],
                    'game_id': bet[1],
                    'user_id': bet[2],
                    'bet_amount': bet[3],
                    'gift_value': bet[4],
                    'status': bet[5],
                    'cashout_multiplier': float(bet[6]) if bet[6] else None,
                    'win_amount': bet[7],
                    'created_at': bet[8]
                }

        conn.close()

        return jsonify({
            'success': True,
            'user_bet': user_bet
        })

    except Exception as e:
        logger.error(f"❌ Ошибка получения ставки пользователя: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/ultimate-crash/place-bet-final', methods=['POST'])
def place_bet_final():
    """Размещение ставки с проверкой баланса"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        bet_amount = data.get('bet_amount', 0)

        logger.info(f"🎯 Ставка Ultimate Crash: user {user_id}, сумма {bet_amount}")

        if not user_id:
            return jsonify({'success': False, 'error': 'ID пользователя не указан'})

        if bet_amount < 25:
            return jsonify({'success': False, 'error': 'Минимальная ставка 25'})

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT balance_stars FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()

        if not user:
            conn.close()
            return jsonify({'success': False, 'error': 'Пользователь не найден'})

        current_balance = user[0] or 0

        if current_balance < bet_amount:
            conn.close()
            return jsonify({'success': False, 'error': f'Недостаточно средств. Баланс: {current_balance}'})

        cursor.execute('''
            SELECT id, status FROM ultimate_crash_games
            WHERE status = 'waiting'
            ORDER BY id DESC LIMIT 1
        ''')

        game = cursor.fetchone()

        if not game:
            target_multiplier = round(random.uniform(3.0, 10.0), 2)
            cursor.execute('''
                INSERT INTO ultimate_crash_games (status, target_multiplier, start_time)
                VALUES ('waiting', ?, CURRENT_TIMESTAMP)
            ''', (target_multiplier,))
            game_id = cursor.lastrowid
            game_status = 'waiting'
        else:
            game_id, game_status = game

        if game_status != 'waiting':
            conn.close()
            return jsonify({'success': False, 'error': 'Игра уже началась'})

        cursor.execute('''
            SELECT id FROM ultimate_crash_bets
            WHERE game_id = ? AND user_id = ? AND status = 'active'
        ''', (game_id, user_id))

        existing_bet = cursor.fetchone()

        if existing_bet:
            conn.close()
            return jsonify({'success': False, 'error': 'У вас уже есть активная ставка'})

        cursor.execute('UPDATE users SET balance_stars = balance_stars - ? WHERE id = ?',
                     (bet_amount, user_id))

        cursor.execute('''
            INSERT INTO ultimate_crash_bets (game_id, user_id, bet_amount, gift_value, status)
            VALUES (?, ?, ?, ?, 'active')
        ''', (game_id, user_id, bet_amount, bet_amount))

        bet_id = cursor.lastrowid

        add_history_record(user_id, 'ultimate_crash_bet', -bet_amount,
                         f'Ставка в Ultimate Crash: {bet_amount}')

        conn.commit()

        cursor.execute('SELECT balance_stars FROM users WHERE id = ?', (user_id,))
        new_balance = cursor.fetchone()[0]

        conn.close()

        logger.info(f"✅ Ставка размещена: {bet_amount} (ID: {bet_id})")

        return jsonify({
            'success': True,
            'bet_id': bet_id,
            'game_id': game_id,
            'new_balance': new_balance,
            'message': f'Ставка {bet_amount} принята!'
        })

    except Exception as e:
        logger.error(f"❌ Ошибка ставки: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/ultimate-crash/cashout-final', methods=['POST'])
def cashout_final():
    """Забрать выигрыш с записью в историю"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')

        if not user_id:
            return jsonify({'success': False, 'error': 'ID пользователя не указан'})

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, current_multiplier FROM ultimate_crash_games
            WHERE status = 'flying'
            ORDER BY id DESC LIMIT 1
        ''')

        game = cursor.fetchone()

        if not game:
            conn.close()
            return jsonify({'success': False, 'error': 'Нет активной игры'})

        game_id, current_mult = game[0], float(game[1]) if game[1] else 1.0

        cursor.execute('''
            SELECT id, bet_amount FROM ultimate_crash_bets
            WHERE game_id = ? AND user_id = ? AND status = 'active'
            ORDER BY created_at DESC LIMIT 1
        ''', (game_id, user_id))

        bet = cursor.fetchone()

        if not bet:
            conn.close()
            return jsonify({'success': False, 'error': 'Активная ставка не найдена'})

        bet_id, bet_amount = bet

        win_amount = int(bet_amount * current_mult)

        cursor.execute('''
            UPDATE ultimate_crash_bets
            SET status = 'cashed_out',
                cashout_multiplier = ?,
                win_amount = ?
            WHERE id = ?
        ''', (current_mult, win_amount, bet_id))

        cursor.execute('''
            UPDATE users
            SET balance_stars = balance_stars + ?,
                total_earned_stars = total_earned_stars + ?
            WHERE id = ?
        ''', (win_amount, win_amount, user_id))

        exp_gained = max(5, win_amount // 100)
        add_experience(user_id, exp_gained, f"Выигрыш в Ultimate Crash x{current_mult:.2f}")

        add_history_record(user_id, 'ultimate_crash_win', win_amount,
                         f'Выигрыш в Ultimate Crash: x{current_mult:.2f}')

        cursor.execute('SELECT first_name FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        user_name = user[0] if user else f'User_{user_id}'

        cursor.execute('''
            INSERT INTO win_history (user_id, user_name, gift_name, gift_image, gift_value, case_name)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, user_name, f'Выигрыш в Crash x{current_mult:.2f}',
              '/static/img/star.png', win_amount, 'Ultimate Crash'))

        cursor.execute('''
            INSERT INTO case_open_history (user_id, case_id, case_name, gift_id, gift_name, gift_image, gift_value, cost, cost_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, 0, 'Ultimate Crash', 0, f'Выигрыш x{current_mult:.2f}',
              '/static/img/star.png', win_amount, bet_amount, 'stars'))

        conn.commit()

        cursor.execute('SELECT balance_stars FROM users WHERE id = ?', (user_id,))
        new_balance = cursor.fetchone()[0]

        conn.close()

        logger.info(f"✅ Кэшаут: {win_amount} (x{current_mult:.2f})")

        return jsonify({
            'success': True,
            'win_amount': win_amount,
            'multiplier': current_mult,
            'new_balance': new_balance,
            'message': f'Вы выиграли {win_amount}!'
        })

    except Exception as e:
        logger.error(f"❌ Ошибка кэшаута: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/ultimate-crash/history', methods=['GET'])
def get_ultimate_crash_history_api():
    """Получение истории множителей"""
    try:
        limit = request.args.get('limit', 10, type=int)

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, final_multiplier, finished_at
            FROM ultimate_crash_history
            ORDER BY finished_at DESC
            LIMIT ?
        ''', (limit,))

        history = cursor.fetchall()
        conn.close()

        history_list = []
        for item in history:
            history_list.append({
                'id': item[0],
                'final_multiplier': float(item[1]),
                'finished_at': item[2]
            })

        logger.info(f"📊 Отправлено {len(history_list)} записей истории")
        return jsonify({
            'success': True,
            'history': history_list
        })

    except Exception as e:
        logger.error(f"❌ Ошибка получения истории: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'history': []
        })


@app.route('/api/ultimate-crash/quick-status', methods=['GET'])
def ultimate_crash_quick_status():
    """Быстрый статус без блокировок базы данных"""
    try:
        # Используем кэширование или файловую систему для минимальной блокировки
        status_file = os.path.join(BASE_PATH, 'data', 'crash_status.json')

        # Пытаемся прочитать из файла
        if os.path.exists(status_file):
            try:
                with open(status_file, 'r', encoding='utf-8') as f:
                    cached_status = json.load(f)

                # Проверяем, не устарели ли данные (максимум 2 секунды)
                cache_time = cached_status.get('timestamp', 0)
                current_time = time.time()

                if current_time - cache_time < 2:  # 2 секунды кэш
                    return jsonify({
                        'success': True,
                        'game': cached_status.get('game', {
                            'id': 1,
                            'status': 'waiting',
                            'current_multiplier': 1.0,
                            'target_multiplier': 5.0,
                            'time_remaining': 10.0
                        }),
                        'cached': True
                    })
            except:
                pass

        # Если кэш устарел или его нет, получаем из базы с быстрым соединением
        conn = sqlite3.connect(os.path.join(BASE_PATH, 'data', 'raswet_gifts.db'), timeout=5)
        conn.execute("PRAGMA busy_timeout = 5000")
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, status, current_multiplier, target_multiplier
            FROM ultimate_crash_games
            WHERE status IN ('waiting', 'counting', 'flying')
            ORDER BY id DESC LIMIT 1
        ''')

        game = cursor.fetchone()
        conn.close()

        if game:
            game_id, status, current_mult, target_mult = game

            # Простой расчет времени
            time_remaining = 10.0
            if status == 'counting':
                time_remaining = 5.0
            elif status == 'flying':
                current_mult_float = float(current_mult) if current_mult else 1.0
                target_mult_float = float(target_mult) if target_mult else 5.0
                time_remaining = max(1.0, (target_mult_float - current_mult_float) * 2)

            game_data = {
                'id': game_id,
                'status': status,
                'current_multiplier': float(current_mult) if current_mult else 1.0,
                'target_multiplier': float(target_mult) if target_mult else 5.0,
                'time_remaining': round(time_remaining, 1)
            }
        else:
            # Демо-данные
            game_data = {
                'id': 1,
                'status': 'waiting',
                'current_multiplier': 1.0,
                'target_multiplier': 5.0,
                'time_remaining': 10.0
            }

        # Кэшируем результат
        try:
            cache_data = {
                'timestamp': time.time(),
                'game': game_data
            }
            with open(status_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f)
        except:
            pass

        return jsonify({
            'success': True,
            'game': game_data,
            'cached': False
        })

    except Exception as e:
        logger.error(f"❌ Ошибка quick-status: {e}")
        # Всегда возвращаем успех с демо-данными
        return jsonify({
            'success': True,
            'game': {
                'id': 1,
                'status': 'waiting',
                'current_multiplier': 1.0,
                'target_multiplier': 5.0,
                'time_remaining': 10.0
            },
            'error': 'Используются демо-данные'
        })

@app.route('/api/ultimate-crash/recent-bets', methods=['GET'])
def get_recent_ultimate_crash_bets():
    """Получение последних ставок"""
    try:
        limit = request.args.get('limit', 20, type=int)

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT
                ucb.id,
                ucb.user_id,
                ucb.bet_amount,
                ucb.status,
                ucb.cashout_multiplier,
                ucb.win_amount,
                ucb.created_at,
                u.first_name,
                u.username,
                u.photo_url
            FROM ultimate_crash_bets ucb
            LEFT JOIN users u ON ucb.user_id = u.id
            WHERE ucb.created_at > datetime('now', '-1 hour')
            ORDER BY ucb.created_at DESC
            LIMIT ?
        ''', (limit,))

        bets = cursor.fetchall()
        conn.close()

        bets_list = []
        for bet in bets:
            bets_list.append({
                'id': bet[0],
                'user_id': bet[1],
                'bet_amount': bet[2],
                'status': bet[3],
                'cashout_multiplier': float(bet[4]) if bet[4] else None,
                'win_amount': bet[5],
                'created_at': bet[6],
                'first_name': bet[7],
                'username': bet[8],
                'photo_url': bet[9] or '/static/img/default_avatar.png'
            })

        return jsonify({
            'success': True,
            'bets': bets_list
        })

    except Exception as e:
        logger.error(f"❌ Ошибка получения ставок: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'bets': []
        })

# ==================== ADMIN API ====================

@app.route('/api/admin/users', methods=['GET'])
def get_all_users():
    """Получение списка всех пользователей"""
    try:
        admin_id = request.args.get('admin_id')
        if not admin_id or int(admin_id) != ADMIN_ID:
            return jsonify({'success': False, 'error': 'Доступ запрещен'})

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, first_name, username, balance_stars, balance_tickets,
                   referral_count, created_at, total_earned_stars, total_earned_tickets,
                   experience, current_level, total_cases_opened
            FROM users
            ORDER BY created_at DESC
        ''')
        users = cursor.fetchall()
        conn.close()

        users_list = []
        for user in users:
            users_list.append({
                'id': user[0],
                'first_name': user[1],
                'username': user[2],
                'balance_stars': user[3],
                'balance_tickets': user[4],
                'referral_count': user[5],
                'created_at': user[6],
                'total_earned_stars': user[7] or 0,
                'total_earned_tickets': user[8] or 0,
                'experience': user[9] or 0,
                'current_level': user[10] or 1,
                'total_cases_opened': user[11] or 0
            })

        return jsonify({'success': True, 'users': users_list})

    except Exception as e:
        logger.error(f"❌ Ошибка получения списка пользователей: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/admin/stats', methods=['GET'])
def get_admin_stats():
    """Получение статистики для админ-панели"""
    try:
        admin_id = request.args.get('admin_id')
        if not admin_id or int(admin_id) != ADMIN_ID:
            return jsonify({'success': False, 'error': 'Доступ запрещен'})

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]

        cursor.execute('SELECT SUM(balance_stars) FROM users')
        total_stars = cursor.fetchone()[0] or 0

        cursor.execute('SELECT SUM(balance_tickets) FROM users')
        total_tickets = cursor.fetchone()[0] or 0

        cursor.execute('SELECT COUNT(*) FROM inventory')
        total_inventory = cursor.fetchone()[0]

        cursor.execute('SELECT status, COUNT(*) FROM withdrawals GROUP BY status')
        withdrawal_stats = cursor.fetchall()

        withdrawal_counts = {}
        for status, count in withdrawal_stats:
            withdrawal_counts[status] = count

        cursor.execute('SELECT COUNT(*) FROM referrals')
        total_referrals = cursor.fetchone()[0]

        cursor.execute('SELECT status, COUNT(*) FROM deposits GROUP BY status')
        deposit_stats = cursor.fetchall()

        deposit_counts = {}
        for status, count in deposit_stats:
            deposit_counts[status] = count

        cursor.execute('SELECT COUNT(*) FROM promo_codes')
        total_promos = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM used_promo_codes')
        total_promo_uses = cursor.fetchone()[0]

        cursor.execute('SELECT AVG(current_level), MAX(current_level) FROM users')
        level_stats = cursor.fetchone()
        avg_level = level_stats[0] or 1
        max_level = level_stats[1] or 1

        cursor.execute('SELECT SUM(total_cases_opened) FROM users')
        total_cases_opened = cursor.fetchone()[0] or 0

        conn.close()

        return jsonify({
            'success': True,
            'stats': {
                'total_users': total_users,
                'total_stars': total_stars,
                'total_tickets': total_tickets,
                'total_inventory': total_inventory,
                'total_referrals': total_referrals,
                'total_promos': total_promos,
                'total_promo_uses': total_promo_uses,
                'total_cases_opened': total_cases_opened,
                'average_level': round(avg_level, 2),
                'max_level': max_level,
                'withdrawals': withdrawal_counts,
                'deposits': deposit_counts
            }
        })

    except Exception as e:
        logger.error(f"❌ Ошибка получения статистики: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/admin/stats-optimized', methods=['GET'])
def get_admin_stats_optimized():
    """Оптимизированная статистика для админ-панели"""
    try:
        admin_id = request.args.get('admin_id')
        if not admin_id or int(admin_id) != ADMIN_ID:
            return jsonify({'success': False, 'error': 'Доступ запрещен'})

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]

        cursor.execute('SELECT SUM(balance_stars), SUM(balance_tickets) FROM users')
        stars_tickets = cursor.fetchone()
        total_stars, total_tickets = stars_tickets[0] or 0, stars_tickets[1] or 0

        cursor.execute('SELECT COUNT(*) FROM inventory')
        total_inventory = cursor.fetchone()[0]

        cursor.execute('''
            SELECT
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved,
                SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejected
            FROM withdrawals
        ''')
        withdrawal_stats = cursor.fetchone()

        cursor.execute('SELECT AVG(current_level), MAX(current_level) FROM users')
        level_stats = cursor.fetchone()

        conn.close()

        return jsonify({
            'success': True,
            'stats': {
                'total_users': total_users,
                'total_stars': total_stars,
                'total_tickets': total_tickets,
                'total_inventory': total_inventory,
                'withdrawals': {
                    'pending': withdrawal_stats[0] or 0,
                    'approved': withdrawal_stats[1] or 0,
                    'rejected': withdrawal_stats[2] or 0
                },
                'average_level': round(level_stats[0] or 1, 2),
                'max_level': level_stats[1] or 1
            }
        })

    except Exception as e:
        logger.error(f"❌ Ошибка получения оптимизированной статистики: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/admin/set-balance', methods=['POST'])
def admin_set_balance():
    """Установка точного баланса пользователя"""
    try:
        data = request.get_json()
        admin_id = data.get('admin_id')
        target_user_id = data.get('user_id')
        stars = data.get('stars', 0)
        tickets = data.get('tickets', 0)

        if not admin_id or int(admin_id) != ADMIN_ID:
            return jsonify({'success': False, 'error': 'Доступ запрещен'})

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT first_name FROM users WHERE id = ?', (target_user_id,))
        user = cursor.fetchone()

        if not user:
            conn.close()
            return jsonify({'success': False, 'error': 'Пользователь не найден'})

        cursor.execute('SELECT balance_stars, balance_tickets FROM users WHERE id = ?', (target_user_id,))
        old_balance = cursor.fetchone()

        cursor.execute('UPDATE users SET balance_stars = ?, balance_tickets = ? WHERE id = ?',
                     (stars, tickets, target_user_id))

        stars_diff = stars - old_balance[0]
        tickets_diff = tickets - old_balance[1]

        add_history_record(target_user_id, 'admin_set_balance',
                         stars_diff,
                         f'Админ установил баланс: {stars}⭐ и {tickets}🎫 (было: {old_balance[0]}⭐ и {old_balance[1]}🎫)')

        conn.commit()
        conn.close()

        logger.info(f"🛠️ Админ {admin_id} установил баланс пользователя {target_user_id}: {stars}⭐ и {tickets}🎫")
        return jsonify({
            'success': True,
            'message': f'Баланс установлен: {stars}⭐ и {tickets}🎫'
        })

    except Exception as e:
        logger.error(f"❌ Ошибка установки баланса: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/admin/update-balance', methods=['POST'])
def admin_update_balance():
    """Обновление баланса пользователя"""
    try:
        data = request.get_json()
        admin_id = data.get('admin_id')
        target_user_id = data.get('user_id')
        stars = data.get('stars', 0)
        tickets = data.get('tickets', 0)
        operation = data.get('operation', 'add')

        if not admin_id or int(admin_id) != ADMIN_ID:
            return jsonify({'success': False, 'error': 'Доступ запрещен'})

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT first_name FROM users WHERE id = ?', (target_user_id,))
        user = cursor.fetchone()

        if not user:
            conn.close()
            return jsonify({'success': False, 'error': 'Пользователь не найден'})

        if operation == 'add':
            cursor.execute('UPDATE users SET balance_stars = balance_stars + ?, balance_tickets = balance_tickets + ? WHERE id = ?',
                         (stars, tickets, target_user_id))
            operation_text = 'начислено'
        else:
            cursor.execute('UPDATE users SET balance_stars = balance_stars - ?, balance_tickets = balance_tickets - ? WHERE id = ?',
                         (stars, tickets, target_user_id))
            operation_text = 'списано'

        add_history_record(target_user_id, 'admin_operation',
                         stars if operation == 'add' else -stars,
                         f'Админ операция: {operation_text} {stars}⭐ и {tickets}🎫')

        conn.commit()
        conn.close()

        logger.info(f"🛠️ Админ {admin_id} изменил баланс пользователя {target_user_id}: {operation_text} {stars}⭐ и {tickets}🎫")
        return jsonify({
            'success': True,
            'message': f'Баланс обновлен: {operation_text} {stars}⭐ и {tickets}🎫'
        })

    except Exception as e:
        logger.error(f"❌ Ошибка обновления баланса: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/admin/withdrawals', methods=['GET'])
def get_withdrawals():
    """Получение списка заявок на вывод (для админа)"""
    try:
        admin_id = request.args.get('admin_id')
        status = request.args.get('status', 'all')

        if not admin_id or int(admin_id) != ADMIN_ID:
            return jsonify({'success': False, 'error': 'Доступ запрещен'})

        conn = get_db_connection()
        cursor = conn.cursor()

        if status == 'all':
            cursor.execute('''
                SELECT * FROM withdrawals
                ORDER BY
                    CASE status
                        WHEN 'pending' THEN 1
                        WHEN 'processing' THEN 2
                        WHEN 'approved' THEN 3
                        WHEN 'rejected' THEN 4
                        WHEN 'error' THEN 5
                        ELSE 6
                    END,
                    created_at DESC
            ''')
        else:
            cursor.execute('''
                SELECT * FROM withdrawals
                WHERE status = ?
                ORDER BY created_at DESC
            ''', (status,))

        withdrawals = cursor.fetchall()
        conn.close()

        withdrawals_list = []
        for w in withdrawals:
            withdrawals_list.append({
                'id': w[0],
                'user_id': w[1],
                'inventory_id': w[2],
                'gift_name': w[3],
                'gift_image': w[4],
                'gift_value': w[5],
                'status': w[6],
                'telegram_username': w[7],
                'user_photo_url': w[8],
                'user_first_name': w[9],
                'created_at': w[10],
                'processed_at': w[11],
                'admin_notes': w[12]
            })

        return jsonify({'success': True, 'withdrawals': withdrawals_list})

    except Exception as e:
        logger.error(f"❌ Ошибка получения заявок на вывод: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/admin/update-withdrawal-status', methods=['POST'])
def update_withdrawal_status():
    """Обновление статуса заявки на вывод"""
    try:
        data = request.get_json()
        admin_id = data.get('admin_id')
        withdrawal_id = data.get('withdrawal_id')
        status = data.get('status')
        admin_notes = data.get('admin_notes', '')

        if not admin_id or int(admin_id) != ADMIN_ID:
            return jsonify({'success': False, 'error': 'Доступ запрещен'})

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT user_id, inventory_id, gift_name, status FROM withdrawals WHERE id = ?', (withdrawal_id,))
        withdrawal = cursor.fetchone()

        if not withdrawal:
            conn.close()
            return jsonify({'success': False, 'error': 'Заявка не найдена'})

        user_id, inventory_id, gift_name, old_status = withdrawal

        cursor.execute('''
            UPDATE withdrawals
            SET status = ?, processed_at = CURRENT_TIMESTAMP, admin_notes = ?
            WHERE id = ?
        ''', (status, admin_notes, withdrawal_id))

        if status in ['approved', 'rejected', 'error']:
            if status == 'approved':
                cursor.execute('DELETE FROM inventory WHERE id = ?', (inventory_id,))
                add_history_record(user_id, 'withdraw_approved', 0, f'Вывод одобрен: {gift_name}')
            else:
                cursor.execute('UPDATE inventory SET is_withdrawing = FALSE WHERE id = ?', (inventory_id,))
                add_history_record(user_id, 'withdraw_rejected', 0, f'Вывод отклонен: {gift_name}')

        conn.commit()
        conn.close()

        logger.info(f"🛠️ Админ {admin_id} изменил статус заявки #{withdrawal_id} на {status}")
        return jsonify({
            'success': True,
            'message': f'Статус заявки обновлен на "{status}"'
        })

    except Exception as e:
        logger.error(f"❌ Ошибка обновления статуса вывода: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/crash/status')
def crash_status():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, status, current_multiplier
        FROM crash_games
        ORDER BY id DESC LIMIT 1
    """)
    game = cur.fetchone()

    if not game:
        cur.execute("INSERT INTO crash_games(status,current_multiplier) VALUES('waiting',1.0)")
        conn.commit()
        return jsonify({"status": "waiting", "multiplier": 1.0})

    return jsonify({
        "game_id": game[0],
        "status": game[1],
        "multiplier": float(game[2])
    })

@app.route('/api/crash/bet', methods=['POST'])
def crash_bet():
    data = request.json
    user_id = data['user_id']
    amount = int(data['amount'])

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT balance_stars FROM users WHERE id=?", (user_id,))
    balance = cur.fetchone()[0]

    if balance < amount:
        return jsonify({"error": "Недостаточно звёзд"})

    # списываем баланс
    cur.execute("UPDATE users SET balance_stars = balance_stars - ? WHERE id=?", (amount, user_id))

    # ищем подарок по цене
    gifts = load_gifts_cached()
    gift = min(gifts, key=lambda g: abs(g["value"] - amount))

    # активная игра
    cur.execute("SELECT id FROM crash_games ORDER BY id DESC LIMIT 1")
    game_id = cur.fetchone()[0]

    cur.execute("""
        INSERT INTO crash_bets(game_id,user_id,bet_amount,bet_type,
        gift_id,gift_name,gift_image,gift_value)
        VALUES(?,?,?,?,?,?,?,?)
    """, (
        game_id, user_id, amount, "stars",
        gift["id"], gift["name"], gift["image"], gift["value"]
    ))

    conn.commit()
    conn.close()

    return jsonify({"success": True, "gift": gift})

@app.route('/api/crash/cashout', methods=['POST'])
def crash_cashout():
    data = request.json
    user_id = data['user_id']

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT b.id,b.bet_amount,b.gift_value,g.current_multiplier
        FROM crash_bets b
        JOIN crash_games g ON b.game_id=g.id
        WHERE b.user_id=? AND b.status='active'
    """, (user_id,))

    bet = cur.fetchone()
    if not bet:
        return jsonify({"error":"Нет активной ставки"})

    bet_id, amount, gift_value, mult = bet
    win = int(amount * float(mult))

    # если выигрыш превращается в подарок
    gifts = load_gifts_cached()
    best_gift = min(gifts, key=lambda g: abs(g["value"] - win))

    cur.execute("""
        INSERT INTO inventory(user_id,gift_id,gift_name,gift_image,gift_value)
        VALUES(?,?,?,?,?)
    """, (user_id,best_gift["id"],best_gift["name"],best_gift["image"],best_gift["value"]))

    cur.execute("UPDATE crash_bets SET status='won', win_amount=? WHERE id=?", (win,bet_id))

    conn.commit()
    conn.close()

    return jsonify({
        "success":True,
        "multiplier": mult,
        "reward": best_gift
    })


@app.route('/api/admin/set-case-limit', methods=['POST'])
def admin_set_case_limit():
    """Установка лимита для конкретного кейса"""
    try:
        data = request.get_json()
        admin_id = data.get('admin_id')
        case_id = data.get('case_id')
        limit = data.get('limit', 0)

        if not admin_id or int(admin_id) != ADMIN_ID:
            return jsonify({'success': False, 'error': 'Доступ запрещен'})

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO case_limits (case_id, current_amount, last_updated)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (case_id, limit))

        conn.commit()
        conn.close()

        logger.info(f"🛠️ Админ {admin_id} установил лимит {limit} для кейса {case_id}")
        return jsonify({
            'success': True,
            'message': f'Лимит кейса установлен: {limit}'
        })

    except Exception as e:
        logger.error(f"❌ Ошибка установки лимита кейса: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/admin/update-case-order', methods=['POST'])
def admin_update_case_order():
    """Обновление порядка отображения кейсов"""
    try:
        data = request.get_json()
        admin_id = data.get('admin_id')
        case_order = data.get('case_order', [])

        if not admin_id or int(admin_id) != ADMIN_ID:
            return jsonify({'success': False, 'error': 'Доступ запрещен'})

        cases = load_cases()

        cases_dict = {case['id']: case for case in cases}

        updated_cases = []
        for order_item in case_order:
            case_id = order_item['id']
            display_order = order_item['display_order']

            if case_id in cases_dict:
                case = cases_dict[case_id]
                case['display_order'] = display_order
                updated_cases.append(case)
            else:
                logger.warning(f"⚠️ Кейс с ID {case_id} не найден при обновлении порядка")

        for case_id, case in cases_dict.items():
            if case not in updated_cases:
                updated_cases.append(case)

        updated_cases.sort(key=lambda x: x.get('display_order', 0))

        if save_cases(updated_cases):
            logger.info(f"🛠️ Админ {admin_id} обновил порядок кейсов")
            return jsonify({
                'success': True,
                'message': 'Порядок кейсов успешно обновлен!'
            })
        else:
            return jsonify({'success': False, 'error': 'Ошибка сохранения порядка кейсов'})

    except Exception as e:
        logger.error(f"❌ Ошибка обновления порядка кейсов: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/admin/cases', methods=['GET', 'POST', 'PUT', 'DELETE'])
def admin_cases_management():
    """Управление кейсами через админ-панель"""
    try:
        admin_id = request.args.get('admin_id') or (request.json and request.json.get('admin_id'))
        if not admin_id or int(admin_id) != ADMIN_ID:
            return jsonify({'success': False, 'error': 'Доступ запрещен'})

        if request.method == 'GET':
            cases = load_cases()
            cases.sort(key=lambda x: x.get('display_order', 0))
            return jsonify({'success': True, 'cases': cases})

        elif request.method == 'POST':
            data = request.json
            cases = load_cases()

            new_id = data.get('id')
            if not new_id:
                new_id = max([case['id'] for case in cases], default=0) + 1

            if any(case['id'] == new_id for case in cases):
                return jsonify({'success': False, 'error': 'Кейс с таким ID уже существует'})

            max_order = max([case.get('display_order', 0) for case in cases], default=0)

            image_filename = data.get('image_filename', '').strip()
            if image_filename and not image_filename.startswith('http'):
                image_url = f"/static/img/{image_filename}"
            else:
                image_url = data.get('image', '/static/img/default_case.png')

            open_date = data.get('open_date')
            if open_date:
                try:
                    open_date = datetime.fromisoformat(open_date.replace('Z', '+00:00')).isoformat()
                except:
                    open_date = None

            new_case = {
                'id': new_id,
                'name': data['name'],
                'image': image_url,
                'cost': data['cost'],
                'cost_type': data['cost_type'],
                'required_level': data.get('required_level', 1),
                'limited': data.get('limited', False),
                'amount': data.get('amount', 0),
                'description': data.get('description', ''),
                'display_order': max_order + 1,
                'tags': data.get('tags', []),
                'glow_effect': data.get('glow_effect', 'none'),
                'open_date': open_date,
                'gifts': data.get('gifts', [])
            }

            cases.append(new_case)

            if save_cases(cases):
                if new_case.get('limited'):
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute('INSERT OR REPLACE INTO case_limits (case_id, current_amount) VALUES (?, ?)',
                                 (new_case['id'], new_case['amount']))
                    conn.commit()
                    conn.close()

                logger.info(f"🛠️ Админ {admin_id} создал кейс: {new_case['name']}")
                return jsonify({'success': True, 'message': 'Кейс успешно создан', 'case': new_case})
            else:
                return jsonify({'success': False, 'error': 'Ошибка сохранения кейса'})

        elif request.method == 'PUT':
            data = request.json
            case_id = data['id']

            cases = load_cases()
            case_index = next((i for i, case in enumerate(cases) if case['id'] == case_id), -1)

            if case_index == -1:
                return jsonify({'success': False, 'error': 'Кейс не найден'})

            image_filename = data.get('image_filename', '').strip()
            if image_filename and not image_filename.startswith('http'):
                image_url = f"/static/img/{image_filename}"
            else:
                image_url = data.get('image', cases[case_index]['image'])

            open_date = data.get('open_date')
            if open_date:
                try:
                    open_date = datetime.fromisoformat(open_date.replace('Z', '+00:00')).isoformat()
                except:
                    open_date = None

            updated_case = {
                'id': case_id,
                'name': data['name'],
                'image': image_url,
                'cost': data['cost'],
                'cost_type': data['cost_type'],
                'required_level': data.get('required_level', 1),
                'limited': data.get('limited', False),
                'amount': data.get('amount', 0),
                'description': data.get('description', ''),
                'display_order': data.get('display_order', cases[case_index].get('display_order', 0)),
                'tags': data.get('tags', []),
                'glow_effect': data.get('glow_effect', 'none'),
                'open_date': open_date,
                'gifts': data.get('gifts', [])
            }

            cases[case_index] = updated_case

            if save_cases(cases):
                if updated_case.get('limited'):
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute('INSERT OR REPLACE INTO case_limits (case_id, current_amount) VALUES (?, ?)',
                                 (updated_case['id'], updated_case['amount']))
                    conn.commit()
                    conn.close()

                logger.info(f"🛠️ Админ {admin_id} обновил кейс: {updated_case['name']}")
                return jsonify({'success': True, 'message': 'Кейс успешно обновлен', 'case': updated_case})
            else:
                return jsonify({'success': False, 'error': 'Ошибка сохранения кейса'})

        elif request.method == 'DELETE':
            case_id = request.json['id']

            cases = load_cases()
            case_to_delete = next((case for case in cases if case['id'] == case_id), None)

            if not case_to_delete:
                return jsonify({'success': False, 'error': 'Кейс не найден'})

            cases = [case for case in cases if case['id'] != case_id]

            if save_cases(cases):
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('DELETE FROM case_limits WHERE case_id = ?', (case_id,))
                conn.commit()
                conn.close()

                logger.info(f"🛠️ Админ {admin_id} удалил кейс: {case_to_delete['name']}")
                return jsonify({'success': True, 'message': 'Кейс успешно удален'})
            else:
                return jsonify({'success': False, 'error': 'Ошибка удаления кейса'})

    except Exception as e:
        logger.error(f"❌ Ошибка управления кейсами: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/admin/create-case', methods=['POST'])
def admin_create_case():
    """Создание нового кейса"""
    try:
        data = request.get_json()
        admin_id = data.get('admin_id')

        if not admin_id or int(admin_id) != ADMIN_ID:
            return jsonify({'success': False, 'error': 'Доступ запрещен'})

        cases = load_cases()

        new_id = max([case['id'] for case in cases], default=0) + 1

        max_order = max([case.get('display_order', 0) for case in cases], default=0)

        image_filename = data.get('image_filename', '').strip()
        if image_filename and not image_filename.startswith('http'):
            image_url = f"/static/img/{image_filename}"
        else:
            image_url = data.get('image', '/static/img/default_case.png')

        open_date = data.get('open_date')
        if open_date:
            try:
                open_date = datetime.fromisoformat(open_date.replace('Z', '+00:00')).isoformat()
            except:
                open_date = None

        new_case = {
            'id': new_id,
            'name': data['name'],
            'image': image_url,
            'cost': data['cost'],
            'cost_type': data['cost_type'],
            'required_level': data.get('required_level', 1),
            'limited': data.get('limited', False),
            'amount': data.get('amount', 0),
            'description': data.get('description', ''),
            'display_order': max_order + 1,
            'tags': data.get('tags', []),
            'glow_effect': data.get('glow_effect', 'none'),
            'open_date': open_date,
            'gifts': data.get('gifts', [])
        }

        cases.append(new_case)

        if save_cases(cases):
            if new_case.get('limited'):
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('INSERT OR REPLACE INTO case_limits (case_id, current_amount) VALUES (?, ?)',
                             (new_case['id'], new_case['amount']))
                conn.commit()
                conn.close()

            logger.info(f"🛠️ Админ {admin_id} создал кейс: {new_case['name']}")
            return jsonify({'success': True, 'message': 'Кейс успешно создан', 'case': new_case})
        else:
            return jsonify({'success': False, 'error': 'Ошибка сохранения кейса'})

    except Exception as e:
        logger.error(f"❌ Ошибка создания кейса: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/admin/promo-codes', methods=['GET', 'POST', 'DELETE'])
def admin_promo_codes_management():
    """Управление промокодами"""
    try:
        admin_id = request.args.get('admin_id') or request.json.get('admin_id')
        if not admin_id or int(admin_id) != ADMIN_ID:
            return jsonify({'success': False, 'error': 'Доступ запрещен'})

        if request.method == 'GET':
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id, code, reward_stars, reward_tickets, max_uses, used_count,
                       created_at, expires_at, is_active
                FROM promo_codes
                ORDER BY created_at DESC
            ''')
            promos = cursor.fetchall()
            conn.close()

            promos_list = []
            for promo in promos:
                promos_list.append({
                    'id': promo[0],
                    'code': promo[1],
                    'reward_stars': promo[2],
                    'reward_tickets': promo[3],
                    'max_uses': promo[4],
                    'used_count': promo[5],
                    'created_at': promo[6],
                    'expires_at': promo[7],
                    'is_active': bool(promo[8])
                })

            return jsonify({'success': True, 'promo_codes': promos_list})

        elif request.method == 'POST':
            data = request.json

            code = data.get('code', '').upper().strip()
            if not code:
                characters = string.ascii_uppercase + string.digits
                code = ''.join(random.choice(characters) for _ in range(8))

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM promo_codes WHERE code = ?', (code,))
            existing = cursor.fetchone()

            if existing:
                conn.close()
                return jsonify({'success': False, 'error': 'Промокод с таким кодом уже существует'})

            reward_stars = data.get('reward_stars', 0)
            reward_tickets = data.get('reward_tickets', 0)
            max_uses = data.get('max_uses', 1)
            expires_days = data.get('expires_days', 30)

            expires_at = None
            if expires_days > 0:
                expires_at = (datetime.now() + timedelta(days=expires_days)).isoformat()

            cursor.execute('''
                INSERT INTO promo_codes (code, reward_stars, reward_tickets, max_uses, expires_at, created_by)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (code, reward_stars, reward_tickets, max_uses, expires_at, ADMIN_ID))

            promo_id = cursor.lastrowid
            conn.commit()
            conn.close()

            logger.info(f"🛠️ Админ {admin_id} создал промокод: {code}")
            return jsonify({
                'success': True,
                'message': f'Промокод {code} успешно создан!',
                'promo_code': {
                    'id': promo_id,
                    'code': code,
                    'reward_stars': reward_stars,
                    'reward_tickets': reward_tickets,
                    'max_uses': max_uses,
                    'expires_at': expires_at
                }
            })

        elif request.method == 'DELETE':
            promo_id = request.json['id']

            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute('DELETE FROM promo_codes WHERE id = ?', (promo_id,))
            conn.commit()
            conn.close()

            logger.info(f"🛠️ Админ {admin_id} удалил промокод #{promo_id}")
            return jsonify({'success': True, 'message': 'Промокод успешно удален'})

    except Exception as e:
        logger.error(f"❌ Ошибка управления промокодами: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/admin/referral-stats', methods=['GET'])
def admin_referral_stats():
    """Получение статистики по реферальной системе"""
    try:
        admin_id = request.args.get('admin_id')
        if not admin_id or int(admin_id) != ADMIN_ID:
            return jsonify({'success': False, 'error': 'Доступ запрещен'})

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT u.id, u.first_name, u.username, u.referral_count,
                   u.total_earned_stars, u.total_earned_tickets
            FROM users u
            WHERE u.referral_count > 0
            ORDER BY u.referral_count DESC
            LIMIT 10
        ''')
        top_referrers = cursor.fetchall()

        cursor.execute('SELECT COUNT(*) FROM referrals')
        total_referrals = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(DISTINCT referrer_id) FROM referrals')
        unique_referrers = cursor.fetchone()[0]

        cursor.execute('SELECT SUM(reward_amount) FROM referral_rewards WHERE reward_type = "stars"')
        total_stars_rewarded = cursor.fetchone()[0] or 0

        cursor.execute('SELECT SUM(reward_amount) FROM referral_rewards WHERE reward_type = "tickets"')
        total_tickets_rewarded = cursor.fetchone()[0] or 0

        conn.close()

        top_referrers_list = []
        for ref in top_referrers:
            top_referrers_list.append({
                'id': ref[0],
                'name': ref[1],
                'username': ref[2],
                'referral_count': ref[3],
                'total_earned_stars': ref[4] or 0,
                'total_earned_tickets': ref[5] or 0
            })

        return jsonify({
            'success': True,
            'stats': {
                'total_referrals': total_referrals,
                'unique_referrers': unique_referrers,
                'total_stars_rewarded': total_stars_rewarded,
                'total_tickets_rewarded': total_tickets_rewarded,
                'top_referrers': top_referrers_list
            }
        })

    except Exception as e:
        logger.error(f"❌ Ошибка получения реферальной статистики: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/admin/level-stats', methods=['GET'])
def admin_level_stats():
    """Получение статистики по уровням"""
    try:
        admin_id = request.args.get('admin_id')
        if not admin_id or int(admin_id) != ADMIN_ID:
            return jsonify({'success': False, 'error': 'Доступ запрещен'})

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT current_level, COUNT(*) as user_count
            FROM users
            GROUP BY current_level
            ORDER BY current_level
        ''')
        level_distribution = cursor.fetchall()

        cursor.execute('''
            SELECT id, first_name, username, current_level, experience, total_cases_opened
            FROM users
            ORDER BY current_level DESC, experience DESC
            LIMIT 10
        ''')
        top_users = cursor.fetchall()

        cursor.execute('SELECT AVG(current_level), MAX(current_level), SUM(experience) FROM users')
        stats = cursor.fetchone()
        avg_level = stats[0] or 1
        max_level = stats[1] or 1
        total_experience = stats[2] or 0

        conn.close()

        distribution_list = []
        for level, count in level_distribution:
            distribution_list.append({
                'level': level,
                'user_count': count
            })

        top_users_list = []
        for user in top_users:
            top_users_list.append({
                'id': user[0],
                'name': user[1],
                'username': user[2],
                'level': user[3],
                'experience': user[4],
                'cases_opened': user[5]
            })

        return jsonify({
            'success': True,
            'stats': {
                'average_level': round(avg_level, 2),
                'max_level': max_level,
                'total_experience': total_experience,
                'level_distribution': distribution_list,
                'top_users': top_users_list
            }
        })

    except Exception as e:
        logger.error(f"❌ Ошибка получения статистики по уровням: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/admin/case-limits', methods=['GET'])
def get_case_limits():
    """Получение детальной информации о лимитах всех кейсов"""
    try:
        admin_id = request.args.get('admin_id')
        if not admin_id or int(admin_id) != ADMIN_ID:
            return jsonify({'success': False, 'error': 'Доступ запрещен'})

        cases = load_cases()
        conn = get_db_connection()
        cursor = conn.cursor()

        case_limits = []
        for case in cases:
            if case.get('limited'):
                cursor.execute('SELECT current_amount FROM case_limits WHERE case_id = ?', (case['id'],))
                result = cursor.fetchone()
                current_amount = result[0] if result else case['amount']

                case_limits.append({
                    'id': case['id'],
                    'name': case['name'],
                    'max_amount': case['amount'],
                    'current_amount': current_amount,
                    'available': current_amount > 0 if result else True,
                    'percentage': round((current_amount / case['amount']) * 100, 1) if case['amount'] > 0 else 0
                })

        conn.close()
        return jsonify({'success': True, 'case_limits': case_limits})

    except Exception as e:
        logger.error(f"❌ Ошибка получения лимитов кейсов: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/admin/update-case-limit', methods=['POST'])
def admin_update_case_limit():
    """Обновление лимита конкретного кейса"""
    try:
        data = request.get_json()
        admin_id = data.get('admin_id')
        case_id = data.get('case_id')
        new_limit = data.get('limit')

        if not admin_id or int(admin_id) != ADMIN_ID:
            return jsonify({'success': False, 'error': 'Доступ запрещен'})

        cases = load_cases()
        case = next((c for c in cases if c['id'] == case_id), None)
        if not case:
            return jsonify({'success': False, 'error': 'Кейс не найден'})

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO case_limits (case_id, current_amount, last_updated)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (case_id, new_limit))

        conn.commit()
        conn.close()

        logger.info(f"🛠️ Админ {admin_id} обновил лимит кейса {case_id} на {new_limit}")
        return jsonify({
            'success': True,
            'message': f'Лимит кейса "{case["name"]}" обновлен: {new_limit}'
        })

    except Exception as e:
        logger.error(f"❌ Ошибка обновления лимита кейса: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/admin/reset-case-limit', methods=['POST'])
def admin_reset_case_limit():
    """Сброс лимита конкретного кейса"""
    try:
        data = request.get_json()
        admin_id = data.get('admin_id')
        case_id = data.get('case_id')

        if not admin_id or int(admin_id) != ADMIN_ID:
            return jsonify({'success': False, 'error': 'Доступ запрещен'})

        cases = load_cases()
        case = next((c for c in cases if c['id'] == case_id), None)
        if not case:
            return jsonify({'success': False, 'error': 'Кейс не найден'})

        if not case.get('limited'):
            return jsonify({'success': False, 'error': 'Этот кейс не лимитированный'})

        conn = get_db_connection()
        cursor = conn.cursor()

        original_amount = case['amount']
        cursor.execute('''
            INSERT OR REPLACE INTO case_limits (case_id, current_amount, last_updated)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (case_id, original_amount))

        conn.commit()
        conn.close()

        logger.info(f"🛠️ Админ {admin_id} сбросил лимит кейса {case_id} до {original_amount}")
        return jsonify({
            'success': True,
            'message': f'Лимит кейса "{case["name"]}" сброшен до {original_amount}'
        })

    except Exception as e:
        logger.error(f"❌ Ошибка сброса лимита кейса: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/admin/win-history', methods=['GET'])
def admin_win_history():
    """Получение полной истории побед"""
    try:
        admin_id = request.args.get('admin_id')
        limit = request.args.get('limit', 100, type=int)

        if not admin_id or int(admin_id) != ADMIN_ID:
            return jsonify({'success': False, 'error': 'Доступ запрещен'})

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT wh.id, wh.user_id, wh.user_name, wh.gift_name, wh.gift_image,
                   wh.gift_value, wh.case_name, wh.created_at, u.username
            FROM win_history wh
            LEFT JOIN users u ON wh.user_id = u.id
            ORDER BY wh.created_at DESC
            LIMIT ?
        ''', (limit,))

        wins = cursor.fetchall()
        conn.close()

        win_history_list = []
        for win in wins:
            win_id, user_id, user_name, gift_name, gift_image, gift_value, case_name, created_at, username = win

            file_extension = gift_image.lower().split('.')[-1] if '.' in gift_image else ''
            is_gif = file_extension == 'gif'
            is_image = file_extension in ['png', 'jpg', 'jpeg', 'webp']

            win_history_list.append({
                'id': win_id,
                'user_id': user_id,
                'user_name': user_name,
                'username': username,
                'gift_name': gift_name,
                'gift_image': gift_image,
                'gift_value': gift_value,
                'case_name': case_name,
                'created_at': created_at,
                'is_gif': is_gif,
                'is_image': is_image
            })

        return jsonify({
            'success': True,
            'win_history': win_history_list,
            'total_count': len(win_history_list)
        })

    except Exception as e:
        logger.error(f"❌ Ошибка получения истории побед для админки: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/admin/clear-win-history', methods=['POST'])
def admin_clear_win_history():
    """Очистка истории побед"""
    try:
        data = request.get_json()
        admin_id = data.get('admin_id')

        if not admin_id or int(admin_id) != ADMIN_ID:
            return jsonify({'success': False, 'error': 'Доступ запрещен'})

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('DELETE FROM win_history')
        conn.commit()
        conn.close()

        logger.info(f"🛠️ Админ {admin_id} очистил историю побед")
        return jsonify({
            'success': True,
            'message': 'История побед успешно очищена'
        })

    except Exception as e:
        logger.error(f"❌ Ошибка очистки истории побед: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/admin/case-open-history', methods=['GET'])
def admin_case_open_history():
    """Получение полной истории открытий кейсов"""
    try:
        admin_id = request.args.get('admin_id')
        limit = request.args.get('limit', 100, type=int)
        user_id = request.args.get('user_id')

        if not admin_id or int(admin_id) != ADMIN_ID:
            return jsonify({'success': False, 'error': 'Доступ запрещен'})

        conn = get_db_connection()
        cursor = conn.cursor()

        if user_id:
            cursor.execute('''
                SELECT coh.id, coh.user_id, coh.case_id, coh.case_name, coh.gift_id,
                       coh.gift_name, coh.gift_image, coh.gift_value, coh.cost, coh.cost_type,
                       coh.created_at, u.username, u.first_name
                FROM case_open_history coh
                LEFT JOIN users u ON coh.user_id = u.id
                WHERE coh.user_id = ?
                ORDER BY coh.created_at DESC
                LIMIT ?
            ''', (user_id, limit))
        else:
            cursor.execute('''
                SELECT coh.id, coh.user_id, coh.case_id, coh.case_name, coh.gift_id,
                       coh.gift_name, coh.gift_image, coh.gift_value, coh.cost, coh.cost_type,
                       coh.created_at, u.username, u.first_name
                FROM case_open_history coh
                LEFT JOIN users u ON coh.user_id = u.id
                ORDER BY coh.created_at DESC
                LIMIT ?
            ''', (limit,))

        opens = cursor.fetchall()
        conn.close()

        open_history_list = []
        for open_item in opens:
            (open_id, user_id, case_id, case_name, gift_id, gift_name, gift_image,
             gift_value, cost, cost_type, created_at, username, first_name) = open_item

            file_extension = gift_image.lower().split('.')[-1] if '.' in gift_image else ''
            is_gif = file_extension == 'gif'
            is_image = file_extension in ['png', 'jpg', 'jpeg', 'webp']

            open_history_list.append({
                'id': open_id,
                'user_id': user_id,
                'case_id': case_id,
                'case_name': case_name,
                'gift_id': gift_id,
                'gift_name': gift_name,
                'gift_image': gift_image,
                'gift_value': gift_value,
                'cost': cost,
                'cost_type': cost_type,
                'created_at': created_at,
                'username': username,
                'first_name': first_name,
                'is_gif': is_gif,
                'is_image': is_image
            })

        return jsonify({
            'success': True,
            'open_history': open_history_list,
            'total_count': len(open_history_list)
        })

    except Exception as e:
        logger.error(f"❌ Ошибка получения истории открытий кейсов для админки: {e}")
        return jsonify({'success': False, 'error': str(e)})

# ==================== ЗАПУСК ПРИЛОЖЕНИЯ ====================

def save_ultimate_crash_history(game_id, final_multiplier):
    """Сохраняет историю Ultimate Crash игры"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO ultimate_crash_history (game_id, final_multiplier, finished_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (game_id, final_multiplier))

        conn.commit()
        conn.close()
        logger.info(f"📝 Сохранена история игры #{game_id}, множитель: {final_multiplier}x")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения истории игры: {e}")
        return False

def get_ultimate_crash_history(limit=10):
    """Получает историю множителей"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, game_id, final_multiplier, finished_at
            FROM ultimate_crash_history
            ORDER BY finished_at DESC
            LIMIT ?
        ''', (limit,))

        history = cursor.fetchall()
        conn.close()

        history_list = []
        for item in history:
            history_list.append({
                'id': item[0],
                'game_id': item[1],
                'final_multiplier': float(item[2]),
                'finished_at': item[3]
            })

        logger.info(f"📊 Загружено {len(history_list)} записей истории")
        return history_list
    except Exception as e:
        logger.error(f"❌ Ошибка получения истории: {e}")
        return []

# ==================== ЗАПУСК ПРИЛОЖЕНИЯ ====================

# Инициализируем базу данных при старте приложения
with app.app_context():
    init_db()
    # НЕ запускаем игровой цикл автоматически - он мешает

if __name__ == '__main__':
    # Получаем параметры из переменных окружения или используем значения по умолчанию
    host = os.getenv('HOST', '127.0.0.1')
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'development') == 'development'
    
    logger.info(f"🚀 Запуск Flask приложения на {host}:{port}")
    logger.info(f"🔧 Debug mode: {debug}")
    
    # Инициализируем базу данных при запуске
    init_db()
    
    app.run(host=host, port=port, debug=debug)