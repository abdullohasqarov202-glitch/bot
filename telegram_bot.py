import os
from flask import Flask, request
import telebot
import yt_dlp
import tempfile
import time
from yt_dlp.utils import DownloadError

# 🔑 Telegram token
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise RuntimeError("❌ TELEGRAM_TOKEN aniqlanmadi! Render yoki lokal muhitda qo‘shing.")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

# 📢 Kanal username
CHANNEL_USERNAME = "@Asqarov_2007"

# 🍪 Cookie fayl (ixtiyoriy)
COOKIE_FILE = "cookies.txt"

# ✅ Obuna tekshirish funksiyasi
def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception:
        return False

# 🚀 /start komandasi
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    if not is_subscribed(user_id):
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("📢 Obuna bo‘lish", url=f"https://t.me/{CHANNEL_USERNAME[1:]}"),
            telebot.types.InlineKeyboardButton("✅ Tekshirish", callback_data="check_sub")
        )
        bot.send_message(
            user_id,
            f"👋 Assalomu alaykum!\n\nBotdan foydalanish uchun kanalga obuna bo‘ling: {CHANNEL_USERNAME}",
            reply_markup=markup
        )
        return

    bot.send_message(
        user_id,
        "🎥 Video yoki qo‘shiq havolasini yuboring (TikTok, YouTube, Instagram, Facebook yoki X)."
    )

# 🔁 Obunani tekshirish
@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_sub(call):
    user_id = call.message.chat.id
    if is_subscribed(user_id):
        bot.edit_message_text(
            "✅ Obuna tasdiqlandi! Endi botdan foydalanishingiz mumkin.",
            user_id,
            call.message.message_id
        )
    else:
        bot.answer_callback_query(call.id, "🚫 Hali obuna bo‘lmagansiz!")

# 🎬 Video yoki audio yuklash
@bot.message_handler(func=lambda message: any(x in message.text.lower() for x in ["youtu", "tiktok", "instagram", "facebook", "x.com"]))
def download_video(message):
    url = message.text.strip()
    bot.reply_to(message, "⏳ Yuklab olinmoqda, biroz kuting...")

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            ydl_opts = {
                'outtmpl': os.path.join(tmpdir, '%(title)s.%(ext)s'),
                'format': 'best',
                'quiet': True,
                'noplaylist': True,
                'cookiefile': COOKIE_FILE if os.path.exists(COOKIE_FILE) else None,
                # ⚙️ YouTube uchun 429 va SABR muammosini kamaytirish
                'extractor_args': {'youtube': {'player_client': ['web', 'android', 'ios']}},
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Linux; Android 10; Chrome/125.0.0.0 Mobile Safari/537.36)'
                },
                'retries': 5,
                'fragment_retries': 5,
                'skip_unavailable_fragments': True,
            }

            max_retries = 3
            for attempt in range(1, max_retries + 1):
                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url, download=True)
                        file_path = ydl.prepare_filename(info)
                        title = info.get("title", "video")
                    break
                except DownloadError as e:
                    if "429" in str(e) and attempt < max_retries:
                        wait = 3 * attempt
                        bot.send_message(message.chat.id, f"⚠️ 429 xato. {wait}s kutayapman ({attempt}/{max_retries})...")
                        time.sleep(wait)
                        continue
                    raise

            caption = f"🎬 <b>{title}</b>\n\nYuklab beruvchi: <a href='https://t.me/asqarov_uzbot'>@asqarov_uzbot</a>"
            with open(file_path, 'rb') as video:
                bot.send_video(message.chat.id, video, caption=caption, parse_mode="HTML")

    except Exception as e:
        bot.reply_to(message, f"❌ Xatolik: {e}")

# 🌐 Webhook yo‘li
@app.route(f"/webhook/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

# 🏠 Asosiy sahifa
@app.route("/")
def home():
    return "<h3>✅ Bot ishlayapti (TikTok, YouTube, Instagram, Facebook, X yuklab beruvchi)</h3>"

# ▶️ Ishga tushirish
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
