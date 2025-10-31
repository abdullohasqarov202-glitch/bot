import os
from flask import Flask, request
import telebot
import yt_dlp
import tempfile
from datetime import datetime, timedelta
import threading
import time

# 🔑 Telegram token
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise RuntimeError("❌ TELEGRAM_TOKEN aniqlanmadi! Render environment variable orqali qo‘shing.")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

# 🍪 Cookie fayl
COOKIE_FILE = "cookies.txt"

# 📢 Kanal username
CHANNEL_USERNAME = "@Asqarov_2007"

# 👑 Admin
ADMIN_USERNAME = "@Asqarov_0207"

# 🧩 Foydalanuvchi ma’lumotlari
user_referrals = {}
user_balances = {}
all_users = {}
user_last_bonus = {}

# 🌟 Premium foydalanuvchilar
premium_users = set()
last_week_winner = None


# ✅ Kanalga obuna tekshirish
def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception:
        return False


# 🚀 Start komandasi
@bot.message_handler(commands=['start', 'help'])
def start(message):
    user_id = message.chat.id
    username = message.from_user.username or f"id:{user_id}"
    args = message.text.split()

    if user_id not in all_users:
        all_users[user_id] = username

    if not is_subscribed(user_id):
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("📢 Obuna bo‘lish", url=f"https://t.me/{CHANNEL_USERNAME[1:]}"),
            telebot.types.InlineKeyboardButton("✅ Tekshirish", callback_data="check_sub")
        )
        bot.send_message(user_id,
                         f"👋 Salom! Botdan foydalanish uchun kanalga obuna bo‘ling:\n{CHANNEL_USERNAME}",
                         reply_markup=markup)
        return

    if len(args) > 1:
        referrer = args[1]
        if referrer != str(user_id):
            user_balances[referrer] = user_balances.get(referrer, 0) + 10
            bot.send_message(referrer, "🎉 Do‘stingiz sizning havolangiz orqali kirdi! +10 💎 qo‘shildi!")

    show_menu(message)


# 📋 Asosiy menyu
def show_menu(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🎥 Video yuklash", "🎵 Musiqa yuklash")
    markup.add("🎬 Kinolar", "💰 Pul ishlash")
    markup.add("🎁 Bonus olish", "🔗 Referal havola")
    markup.add("💎 Mening olmoslarim", "📊 Statistika")
    markup.add("📢 Reklama berish", "📩 Admin bilan aloqa")
    markup.add("💎 Premium olish")

    if message.from_user.username == ADMIN_USERNAME[1:]:
        markup.add("👤 Foydalanuvchilar ro‘yxati")

    bot.send_message(message.chat.id, "📍 Quyidagi menyudan tanlang:", reply_markup=markup)


# ✅ Obuna qayta tekshirish
@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_sub(call):
    if is_subscribed(call.message.chat.id):
        bot.edit_message_text("✅ Obuna tasdiqlandi!", call.message.chat.id, call.message.message_id)
        show_menu(call.message)
    else:
        bot.answer_callback_query(call.id, "🚫 Hali obuna bo‘lmagansiz!")


# 👤 Foydalanuvchilar ro‘yxati
@bot.message_handler(func=lambda m: m.text == "👤 Foydalanuvchilar ro‘yxati")
def users_list(message):
    if message.from_user.username != ADMIN_USERNAME[1:]:
        bot.reply_to(message, "🚫 Ruxsat yo‘q.")
        return
    text = "\n".join([f"• @{v}" if not v.startswith("id:") else f"• {v}" for v in all_users.values()])
    bot.send_message(message.chat.id, f"👥 Foydalanuvchilar:\n{text}\n\nJami: {len(all_users)} ta")


# 🎵 Musiqa yuklash
@bot.message_handler(func=lambda message: message.text == "🎵 Musiqa yuklash")
def ask_music(message):
    bot.reply_to(message, "🎵 Qo‘shiq nomi yoki havolasini yuboring (YouTube, SoundCloud, TikTok Music...)")

@bot.message_handler(func=lambda message: "http" in message.text and not any(x in message.text for x in ["tiktok", "instagram", "facebook", "twitter", "x.com"]))
def download_music(message):
    url = message.text.strip()
    bot.reply_to(message, "🎧 Yuklab olinmoqda, kuting...")

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": os.path.join(tmpdir, "%(title)s.%(ext)s"),
                "quiet": True,
                "noplaylist": True,
                "cookiefile": COOKIE_FILE if os.path.exists(COOKIE_FILE) else None,
                "extractor_args": {"youtube": {"player_client": ["web", "ios", "android"]}},
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info).replace(".webm", ".mp3").replace(".m4a", ".mp3")
                title = info.get("title", "musiqa")

            with open(file_path, "rb") as audio:
                bot.send_audio(message.chat.id, audio, caption=f"🎶 {title}\n\nYuklab beruvchi: @shazam_uzzbot")
    except Exception as e:
        bot.reply_to(message, f"❌ Yuklab bo‘lmadi: {e}")


# 🔍 Nomi orqali qo‘shiq qidirish
@bot.message_handler(func=lambda message: not message.text.startswith("/") and not message.text.startswith("http"))
def search_music(message):
    query = message.text.strip()
    bot.reply_to(message, f"🎧 '{query}' qidirilmoqda...")

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": os.path.join(tmpdir, "%(title)s.%(ext)s"),
                "quiet": True,
                "noplaylist": True,
                "extractor_args": {"youtube": {"player_client": ["web", "ios", "android"]}},
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch1:{query}", download=True)
                entry = info['entries'][0]
                file_path = ydl.prepare_filename(entry).replace(".webm", ".mp3")
                title = entry.get("title", "musiqa")

            with open(file_path, "rb") as audio:
                bot.send_audio(message.chat.id, audio, caption=f"🎵 {title}\n\nYuklab beruvchi: @shazam_uzzbot")
    except Exception as e:
        bot.reply_to(message, f"❌ Yuklab bo‘lmadi: {e}")


# 🎥 Video yuklash (TikTok, Instagram, Facebook, X)
@bot.message_handler(func=lambda message: any(x in message.text for x in ["tiktok", "instagram", "facebook", "x.com", "twitter"]))
def download_video(message):
 
    bot.reply_to(message, "⏳ Video yuklanmoqda...")

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            ydl_opts = {
                "outtmpl": os.path.join(tmpdir, "%(title)s.%(ext)s"),
                "quiet": True,
                "cookiefile": COOKIE_FILE if os.path.exists(COOKIE_FILE) else None,
                "format": "best[ext=mp4]",
                "noplaylist": True
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                video_path = ydl.prepare_filename(info)
                title = info.get("title", "video")

            caption = f"🎬 <b>{title}</b>\n\nYuklab beruvchi: <a href='https://t.me/shazam_uzzbot'>@shazam_uzzbot</a>"
            with open(video_path, "rb") as video:
                bot.send_video(message.chat.id, video, caption=caption, parse_mode="HTML")
    except Exception as e:
        bot.reply_to(message, f"❌ Yuklab bo‘lmadi: {e}")


# 🧩 Flask webhook
@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
    bot.process_new_updates([update])
    return "OK", 200


@app.route("/")
def home():
    return "<h3>✅ Bot ishlayapti! Video & Musiqa yuklab beruvchi.</h3>"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
