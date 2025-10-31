import os
from flask import Flask, request
import telebot
import yt_dlp
import tempfile
from datetime import datetime, timedelta
import threading
import time

# 1️⃣ Telegram token
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise RuntimeError("❌ TELEGRAM_TOKEN aniqlanmadi! Render environment variable orqali qo‘shing.")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

# 2️⃣ Cookie fayl
COOKIE_FILE = "cookies.txt"

# 3️⃣ Kanal username
CHANNEL_USERNAME = "@Asqarov_2007"

# 4️⃣ Referal tizimi va foydalanuvchilar
user_referrals = {}
user_balances = {}
all_users = {}
user_last_bonus = {}

# 5️⃣ Admin username
ADMIN_USERNAME = "@Asqarov_0207"

# ✅ Obuna tekshirish
def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception:
        return False

# 🔹 Start / help
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_id = message.chat.id
    username = message.from_user.username or f"id:{user_id}"
    args = message.text.split()

    first_time = user_id not in all_users
    all_users[user_id] = username

    if not is_subscribed(user_id):
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("📢 Kanalga obuna bo‘lish", url=f"https://t.me/{CHANNEL_USERNAME[1:]}"),
            telebot.types.InlineKeyboardButton("✅ Obunani tekshirish", callback_data="check_sub")
        )
        bot.send_message(user_id,
            f"👋 Assalomu alaykum!\n\nBotdan foydalanish uchun kanalga obuna bo‘ling:\n{CHANNEL_USERNAME}",
            reply_markup=markup
        )
        return

    if first_time:
        intro_text = (
            "👋 <b>Salom!</b> Men sizga yordam beruvchi <b>video yuklab beruvchi botman</b>!\n\n"
            "📽 <b>Nimalar qila olaman:</b>\n"
            "
