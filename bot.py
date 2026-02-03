import telebot
from telebot import types
import sqlite3
import os
import time
import logging
from datetime import datetime
import threading

# ==================== CONFIGURATION ====================
TELEGRAM_BOT_TOKEN = '8224991617:AAF2F7ub0XF9N6wsWyn3PmhdZnYt62KmpRE'
ADMIN_ID = 5257227756
WEBSITE_URL = 'https://rasswetik52.pythonanywhere.com'

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Состояния пользователей
user_states = {}

# ==================== DATABASE FUNCTIONS ====================
def get_db_connection():
    """Получает соединение с базой данных"""
    try:
        db_path = '/home/rasswetik52/mysite/data/raswet_gifts.db'
        conn = sqlite3.connect(db_path, timeout=30)
        conn.execute("PRAGMA busy_timeout = 30000")
        return conn
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к БД: {e}")
        return None

def add_user_to_db(user_id, first_name, username):
    """Добавляет пользователя в базу данных"""
    try:
        conn = get_db_connection()
        if not conn:
            return False

        cursor = conn.cursor()

        # Проверяем существование пользователя
        cursor.execute('SELECT id FROM users WHERE id = ?', (user_id,))
        if not cursor.fetchone():
            # Генерируем реферальный код
            import random
            import string
            referral_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

            cursor.execute('''
                INSERT INTO users (id, first_name, username, balance_stars, balance_tickets, referral_code, created_at)
                VALUES (?, ?, ?, 0, 0, ?, datetime('now'))
            ''', (user_id, first_name, username, referral_code))

            logger.info(f"✅ Новый пользователь: {first_name} (ID: {user_id})")
        else:
            # Обновляем данные
            cursor.execute('UPDATE users SET first_name = ?, username = ? WHERE id = ?',
                         (first_name, username, user_id))
            logger.info(f"✅ Обновлен пользователь: {first_name} (ID: {user_id})")

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        logger.error(f"❌ Ошибка добавления пользователя: {e}")
        return False

def get_all_users():
    """Получает всех пользователей из базы"""
    try:
        conn = get_db_connection()
        if not conn:
            return []

        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users')
        users = [row[0] for row in cursor.fetchall()]
        conn.close()
        logger.info(f"📊 Получено {len(users)} пользователей")
        return users
    except Exception as e:
        logger.error(f"❌ Ошибка получения пользователей: {e}")
        return []

def get_user_count():
    """Получает количество пользователей"""
    try:
        conn = get_db_connection()
        if not conn:
            return 0

        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users')
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except Exception as e:
        logger.error(f"❌ Ошибка получения количества пользователей: {e}")
        return 0

# ==================== BROADCAST FUNCTIONS ====================
def copy_message_to_user(user_id, message):
    """Копирует сообщение пользователю"""
    try:
        if message.content_type == 'text':
            bot.send_message(user_id, message.text)
            return True

        elif message.content_type == 'photo':
            caption = message.caption if message.caption else ""
            bot.send_photo(user_id, message.photo[-1].file_id, caption=caption)
            return True

        elif message.content_type == 'video':
            caption = message.caption if message.caption else ""
            bot.send_video(user_id, message.video.file_id, caption=caption)
            return True

        elif message.content_type == 'document':
            caption = message.caption if message.caption else ""
            bot.send_document(user_id, message.document.file_id, caption=caption)
            return True

        elif message.content_type == 'audio':
            caption = message.caption if message.caption else ""
            bot.send_audio(user_id, message.audio.file_id, caption=caption)
            return True

        elif message.content_type == 'voice':
            bot.send_voice(user_id, message.voice.file_id)
            return True

        elif message.content_type == 'animation':
            caption = message.caption if message.caption else ""
            bot.send_animation(user_id, message.animation.file_id, caption=caption)
            return True

        elif message.content_type == 'sticker':
            bot.send_sticker(user_id, message.sticker.file_id)
            return True

        else:
            logger.warning(f"⚠️ Неподдерживаемый тип: {message.content_type}")
            return False

    except Exception as e:
        error_msg = str(e).lower()
        if "blocked" in error_msg or "deactivated" in error_msg:
            logger.info(f"⏸️ Пользователь {user_id} заблокировал бота")
        elif "chat not found" in error_msg:
            logger.info(f"⏸️ Чат с {user_id} не найден")
        elif "forbidden" in error_msg:
            logger.info(f"⏸️ Нет доступа к {user_id}")
        else:
            logger.error(f"❌ Ошибка отправки {user_id}: {e}")
        return False

def send_broadcast_to_users(user_ids, message, admin_id):
    """Отправляет рассылку пользователям"""
    total = len(user_ids)
    successful = 0
    failed = 0

    # Отправляем сообщение о начале рассылки
    try:
        progress_msg = bot.send_message(
            admin_id,
            f"🔄 Начинаю рассылку...\nВсего: {total}\nУспешно: 0\nОшибок: 0\nПрогресс: 0%"
        )
        progress_msg_id = progress_msg.message_id
    except:
        progress_msg_id = None

    # Отправляем рассылку
    for i, user_id in enumerate(user_ids, 1):
        try:
            if copy_message_to_user(user_id, message):
                successful += 1
            else:
                failed += 1

            # Обновляем прогресс каждые 5 сообщений
            if i % 5 == 0 or i == total:
                progress = int((i / total) * 100)
                if progress_msg_id:
                    try:
                        bot.edit_message_text(
                            chat_id=admin_id,
                            message_id=progress_msg_id,
                            text=f"🔄 Рассылка...\nВсего: {total}\nУспешно: {successful}\nОшибок: {failed}\nПрогресс: {progress}%"
                        )
                    except:
                        pass

            # Пауза между сообщениями
            time.sleep(0.15)

        except Exception as e:
            failed += 1
            logger.error(f"❌ Ошибка в рассылке: {e}")

    return successful, failed

# ==================== USER HANDLERS ====================
@bot.message_handler(commands=['start'])
def start_command(message):
    """Обработчик команды /start"""
    try:
        user_id = message.from_user.id
        user_name = message.from_user.first_name
        username = message.from_user.username or ""

        logger.info(f"🚀 /start от {user_name} ({user_id})")

        # Добавляем в базу
        add_user_to_db(user_id, user_name, username)

        # Простое сообщение с кнопкой
        markup = types.InlineKeyboardMarkup()
        open_button = types.InlineKeyboardButton(
            text="🎮 ИГРАТЬ",
            web_app=types.WebAppInfo(url=WEBSITE_URL)
        )
        markup.add(open_button)

        bot.send_message(
            message.chat.id,
            f"Привет, {user_name}! 🎮\n\nНажми кнопку чтобы начать:",
            reply_markup=markup
        )

    except Exception as e:
        logger.error(f"❌ Ошибка в /start: {e}")

# ==================== ADMIN HANDLERS ====================
def get_admin_menu():
    """Создает инлайн-меню для админа"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast"),
        types.InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
        types.InlineKeyboardButton("👥 Пользователи", callback_data="admin_users"),
        types.InlineKeyboardButton("⚙️ Настройки", callback_data="admin_settings"),
        types.InlineKeyboardButton("❌ Закрыть", callback_data="admin_close")
    )
    return markup

@bot.message_handler(commands=['admin'])
def admin_command(message):
    """Админ-панель"""
    user_id = message.from_user.id

    if user_id != ADMIN_ID:
        bot.send_message(message.chat.id, "⛔")
        return

    markup = get_admin_menu()

    bot.send_message(
        message.chat.id,
        "🛠️ <b>АДМИН-ПАНЕЛЬ</b>\n\nВыберите действие:",
        reply_markup=markup,
        parse_mode='HTML'
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_'))
def admin_callback_handler(call):
    """Обработчик инлайн-кнопок админа"""
    user_id = call.from_user.id

    if user_id != ADMIN_ID:
        bot.answer_callback_query(call.id, "⛔ Нет доступа", show_alert=True)
        return

    action = call.data

    if action == 'admin_broadcast':
        # Начать рассылку
        user_states[user_id] = {'action': 'waiting_broadcast_message'}

        # Удаляем старое сообщение
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass

        bot.send_message(
            call.message.chat.id,
            "📢 <b>СОЗДАНИЕ РАССЫЛКИ</b>\n\n"
            "Отправьте сообщение для рассылки:\n"
            "• Текст\n"
            "• Фото (с подписью)\n"
            "• Видео\n"
            "• GIF\n"
            "• Документ\n"
            "• Стикер\n\n"
            "Сообщение будет отправлено <b>точно так же</b> как вы его отправите.\n\n"
            "Для отмены нажмите /cancel",
            parse_mode='HTML'
        )

    elif action == 'admin_stats':
        # Показать статистику
        count = get_user_count()

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔄 Обновить", callback_data="admin_stats"))
        markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="admin_back"))

        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"📊 <b>СТАТИСТИКА БОТА</b>\n\n"
                     f"👥 Пользователей: <b>{count}</b>\n"
                     f"⏰ Время сервера: <b>{datetime.now().strftime('%H:%M:%S')}</b>\n"
                     f"📅 Дата: <b>{datetime.now().strftime('%d.%m.%Y')}</b>\n\n"
                     f"🌐 Сайт: {WEBSITE_URL}",
                reply_markup=markup,
                parse_mode='HTML'
            )
        except:
            bot.send_message(
                call.message.chat.id,
                f"📊 <b>СТАТИСТИКА БОТА</b>\n\n"
                f"👥 Пользователей: <b>{count}</b>\n"
                f"⏰ Время сервера: <b>{datetime.now().strftime('%H:%M:%S')}</b>\n"
                f"📅 Дата: <b>{datetime.now().strftime('%d.%m.%Y')}</b>\n\n"
                f"🌐 Сайт: {WEBSITE_URL}",
                reply_markup=markup,
                parse_mode='HTML'
            )

    elif action == 'admin_users':
        # Показать пользователей
        users = get_all_users()

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 Рассылка всем", callback_data="admin_broadcast"))
        markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="admin_back"))

        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"👥 <b>ПОЛЬЗОВАТЕЛИ</b>\n\n"
                     f"Всего пользователей: <b>{len(users)}</b>\n\n"
                     f"Нажмите кнопку ниже чтобы начать рассылку:",
                reply_markup=markup,
                parse_mode='HTML'
            )
        except:
            bot.send_message(
                call.message.chat.id,
                f"👥 <b>ПОЛЬЗОВАТЕЛИ</b>\n\n"
                f"Всего пользователей: <b>{len(users)}</b>\n\n"
                f"Нажмите кнопку ниже чтобы начать рассылку:",
                reply_markup=markup,
                parse_mode='HTML'
            )

    elif action == 'admin_settings':
        # Настройки
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="admin_back"))

        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"⚙️ <b>НАСТРОЙКИ БОТА</b>\n\n"
                     f"🆔 ID администратора: <code>{ADMIN_ID}</code>\n"
                     f"🌐 URL сайта: {WEBSITE_URL}\n"
                     f"🔑 Токен: <code>{TELEGRAM_BOT_TOKEN[:10]}...</code>\n\n"
                     f"🔄 Бот работает и готов к работе!",
                reply_markup=markup,
                parse_mode='HTML'
            )
        except:
            bot.send_message(
                call.message.chat.id,
                f"⚙️ <b>НАСТРОЙКИ БОТА</b>\n\n"
                f"🆔 ID администратора: <code>{ADMIN_ID}</code>\n"
                f"🌐 URL сайта: {WEBSITE_URL}\n"
                f"🔑 Токен: <code>{TELEGRAM_BOT_TOKEN[:10]}...</code>\n\n"
                f"🔄 Бот работает и готов к работе!",
                reply_markup=markup,
                parse_mode='HTML'
            )

    elif action == 'admin_back':
        # Вернуться в главное меню
        markup = get_admin_menu()

        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="🛠️ <b>АДМИН-ПАНЕЛЬ</b>\n\nВыберите действие:",
                reply_markup=markup,
                parse_mode='HTML'
            )
        except:
            bot.send_message(
                call.message.chat.id,
                "🛠️ <b>АДМИН-ПАНЕЛЬ</b>\n\nВыберите действие:",
                reply_markup=markup,
                parse_mode='HTML'
            )

    elif action == 'admin_close':
        # Закрыть меню
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass

    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda m:
                     m.from_user.id in user_states and
                     user_states[m.from_user.id].get('action') == 'waiting_broadcast_message')
def receive_broadcast_message(message):
    """Получить сообщение для рассылки"""
    user_id = message.from_user.id

    if user_id != ADMIN_ID:
        return

    if message.text == '/cancel':
        del user_states[user_id]

        markup = get_admin_menu()
        bot.send_message(
            user_id,
            "🛠️ <b>АДМИН-ПАНЕЛЬ</b>\n\nВыберите действие:",
            reply_markup=markup,
            parse_mode='HTML'
        )
        return

    # Сохраняем сообщение
    user_states[user_id]['message'] = message

    # Показываем превью и запрашиваем подтверждение
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✅ Отправить всем", callback_data="confirm_broadcast_all"),
        types.InlineKeyboardButton("❌ Отменить", callback_data="cancel_broadcast")
    )

    if message.content_type == 'text':
        # Отправляем превью текста
        bot.send_message(
            user_id,
            f"📢 <b>ПРЕВЬЮ РАССЫЛКИ</b>\n\n{message.text}\n\n"
            f"Отправить это сообщение всем пользователям?",
            reply_markup=markup,
            parse_mode='HTML'
        )

    elif message.content_type == 'photo':
        # Отправляем превью фото
        caption = message.caption if message.caption else "📷 Фото"
        bot.send_photo(
            user_id,
            message.photo[-1].file_id,
            caption=f"📢 <b>ПРЕВЬЮ РАССЫЛКИ</b>\n\n{caption}\n\n"
                   f"Отправить это фото всем пользователям?",
            reply_markup=markup,
            parse_mode='HTML'
        )

    elif message.content_type == 'video':
        # Отправляем превью видео
        caption = message.caption if message.caption else "🎥 Видео"
        bot.send_video(
            user_id,
            message.video.file_id,
            caption=f"📢 <b>ПРЕВЬЮ РАССЫЛКИ</b>\n\n{caption}\n\n"
                   f"Отправить это видео всем пользователям?",
            reply_markup=markup,
            parse_mode='HTML'
        )

    elif message.content_type in ['document', 'audio', 'animation']:
        # Для документов, аудио и анимаций
        bot.send_message(
            user_id,
            f"📢 <b>ПРЕВЬЮ РАССЫЛКИ</b>\n\n"
            f"Тип: {message.content_type}\n"
            f"Отправить это сообщение всем пользователям?",
            reply_markup=markup,
            parse_mode='HTML'
        )

    elif message.content_type == 'sticker':
        # Для стикеров
        bot.send_sticker(user_id, message.sticker.file_id)
        time.sleep(0.5)
        bot.send_message(
            user_id,
            "📢 <b>ПРЕВЬЮ РАССЫЛКИ</b>\n\n"
            "Стикер выше будет отправлен всем пользователям.\n"
            "Продолжить?",
            reply_markup=markup,
            parse_mode='HTML'
        )

    elif message.content_type == 'voice':
        # Для голосовых сообщений
        bot.send_voice(user_id, message.voice.file_id)
        time.sleep(0.5)
        bot.send_message(
            user_id,
            "📢 <b>ПРЕВЬЮ РАССЫЛКИ</b>\n\n"
            "Голосовое сообщение выше будет отправлено всем пользователям.\n"
            "Продолжить?",
            reply_markup=markup,
            parse_mode='HTML'
        )

@bot.callback_query_handler(func=lambda call: call.data == "confirm_broadcast_all")
def confirm_broadcast_all(call):
    """Подтверждение рассылки всем"""
    user_id = call.from_user.id

    if user_id != ADMIN_ID:
        bot.answer_callback_query(call.id, "⛔ Нет доступа", show_alert=True)
        return

    if user_id not in user_states or 'message' not in user_states[user_id]:
        bot.answer_callback_query(call.id, "❌ Сообщение не найдено", show_alert=True)
        return

    broadcast_message = user_states[user_id]['message']

    # Удаляем состояние
    del user_states[user_id]

    # Получаем пользователей
    user_ids = get_all_users()

    if not user_ids:
        bot.answer_callback_query(call.id, "❌ Нет пользователей", show_alert=True)
        return

    # Удаляем старое сообщение и отправляем новое
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass

    start_msg = bot.send_message(
        call.message.chat.id,
        f"🔄 <b>НАЧИНАЮ РАССЫЛКУ...</b>\n\nВсего пользователей: {len(user_ids)}\nЭто займет некоторое время...",
        parse_mode='HTML'
    )

    # Запускаем рассылку в отдельном потоке
    thread = threading.Thread(
        target=run_broadcast,
        args=(call.message.chat.id, start_msg.message_id, user_ids, broadcast_message)
    )
    thread.start()

    bot.answer_callback_query(call.id, "✅ Рассылка начата")

@bot.callback_query_handler(func=lambda call: call.data == "cancel_broadcast")
def cancel_broadcast(call):
    """Отмена рассылки"""
    user_id = call.from_user.id

    if user_id != ADMIN_ID:
        bot.answer_callback_query(call.id, "⛔ Нет доступа", show_alert=True)
        return

    # Удаляем состояние
    if user_id in user_states:
        del user_states[user_id]

    # Удаляем старое сообщение и возвращаем в админ-панель
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass

    markup = get_admin_menu()

    bot.send_message(
        call.message.chat.id,
        "🛠️ <b>АДМИН-ПАНЕЛЬ</b>\n\nВыберите действие:",
        reply_markup=markup,
        parse_mode='HTML'
    )

    bot.answer_callback_query(call.id, "❌ Рассылка отменена")

def run_broadcast(chat_id, message_id, user_ids, broadcast_message):
    """Запуск рассылки в отдельном потоке"""
    try:
        # Отправляем рассылку
        successful, failed = send_broadcast_to_users(
            user_ids,
            broadcast_message,
            chat_id
        )

        # Отчет
        total = len(user_ids)
        success_rate = (successful / total * 100) if total > 0 else 0

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("⬅️ В админ-панель", callback_data="admin_back"))

        report = f"""
✅ <b>РАССЫЛКА ЗАВЕРШЕНА</b>

📊 <b>Результаты:</b>
• Всего пользователей: {total}
• Успешно отправлено: {successful}
• Не удалось отправить: {failed}
• Успешность: {success_rate:.1f}%

⏰ Завершено: {datetime.now().strftime('%H:%M:%S')}
        """

        try:
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=report,
                reply_markup=markup,
                parse_mode='HTML'
            )
        except:
            bot.send_message(
                chat_id,
                report,
                reply_markup=markup,
                parse_mode='HTML'
            )

        logger.info(f"📢 Рассылка завершена: {successful}/{total}")

    except Exception as e:
        logger.error(f"❌ Ошибка в потоке рассылки: {e}")

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("⬅️ В админ-панель", callback_data="admin_back"))

        try:
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=f"❌ <b>ОШИБКА ПРИ РАССЫЛКЕ</b>\n\n{str(e)[:200]}...",
                reply_markup=markup,
                parse_mode='HTML'
            )
        except:
            bot.send_message(
                chat_id,
                f"❌ <b>ОШИБКА ПРИ РАССЫЛКЕ</b>\n\n{str(e)[:200]}...",
                reply_markup=markup,
                parse_mode='HTML'
            )

# ==================== MEDIA HANDLER ====================
@bot.message_handler(content_types=['audio', 'document', 'animation', 'photo',
                                    'sticker', 'video', 'voice'])
def handle_all_media(message):
    """Обработчик медиа-сообщений для рассылки"""
    user_id = message.from_user.id

    if user_id in user_states and user_states[user_id].get('action') == 'waiting_broadcast_message':
        receive_broadcast_message(message)

# ==================== FALLBACK HANDLER ====================
@bot.message_handler(func=lambda m: True)
def handle_other_messages(message):
    """Обработчик всех остальных сообщений"""
    user_id = message.from_user.id

    # Для обычных пользователей
    if user_id != ADMIN_ID:
        markup = types.InlineKeyboardMarkup()
        open_button = types.InlineKeyboardButton(
            text="🎮 ИГРАТЬ",
            web_app=types.WebAppInfo(url=WEBSITE_URL)
        )
        markup.add(open_button)

        bot.send_message(
            message.chat.id,
            "Нажми кнопку чтобы начать:",
            reply_markup=markup
        )
        return

# ==================== BOT STARTUP ====================
def setup_bot():
    """Настройка бота"""
    try:
        # Устанавливаем команды
        bot.set_my_commands([
            types.BotCommand("/start", "Запустить бота"),
            types.BotCommand("/admin", "Админ-панель")
        ])

        logger.info("✅ Бот настроен")
    except Exception as e:
        logger.error(f"❌ Ошибка настройки бота: {e}")

def run_bot():
    """Запуск бота"""
    try:
        setup_bot()
        logger.info("🤖 Бот запущен и готов к работе!")
        logger.info(f"🆔 ID администратора: {ADMIN_ID}")
        logger.info(f"🌐 Ссылка на сайт: {WEBSITE_URL}")

        bot.infinity_polling(timeout=60, long_polling_timeout=30)

    except Exception as e:
        logger.error(f"❌ Критическая ошибка бота: {e}")
        logger.info("🔄 Перезапуск через 5 секунд...")
        time.sleep(5)
        run_bot()

# ==================== MAIN ====================
if __name__ == '__main__':
    run_bot()