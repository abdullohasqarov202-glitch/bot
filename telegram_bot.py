import os
from flask import Flask, request
import telebot
import yt_dlp
import tempfile

# 🔑 Telegram token
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise RuntimeError("❌ TELEGRAM_TOKEN topilmadi! Render environment variable orqali qo‘shing.")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

# 📁 Cookie fayl
COOKIE_FILE = "cookies.txt"

# 📢 Kanal username
CHANNEL_USERNAME = "@Asqarov_2007"
ADMIN_USERNAME = "@Asqarov_0207"

# 🧠 Obuna tekshirish
def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception:
        return False

# 🔹 Start komandasi
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    if not is_subscribed(user_id):
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("📢 Kanalga obuna bo‘lish", url=f"https://t.me/{CHANNEL_USERNAME[1:]}"),
            telebot.types.InlineKeyboardButton("✅ Obunani tekshirish", callback_data="check_sub")
        )
        bot.send_message(user_id, f"Botdan foydalanish uchun kanalga obuna bo‘ling: {CHANNEL_USERNAME}", reply_markup=markup)
        return

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🎥 Video yuklash", "🎵 Qo‘shiq yuklash")
    markup.add("🎬 Kinolar", "📩 Admin bilan aloqa")
    bot.send_message(message.chat.id, "👋 Assalomu alaykum! Kerakli bo‘limni tanlang:", reply_markup=markup)

# 🔁 Obunani qayta tekshirish
@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_subscription(call):
    user_id = call.message.chat.id
    if is_subscribed(user_id):
        bot.edit_message_text("✅ Obuna tasdiqlandi! /start ni yozing", chat_id=user_id, message_id=call.message.message_id)
    else:
        bot.answer_callback_query(call.id, "🚫 Hali obuna bo‘lmagansiz!")

# 🎬 Kinolar bo‘limi
@bot.message_handler(func=lambda message: message.text == "🎬 Kinolar")
def movies(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🎬 Kinolar kanaliga o‘tish", url="https://t.me/KINOLAR_UZB12"))
    bot.send_message(message.chat.id, "🍿 Quyidagi tugma orqali kinolar kanaliga o‘ting:", reply_markup=markup)

# 📩 Admin bilan aloqa
@bot.message_handler(func=lambda message: message.text == "📩 Admin bilan aloqa")
def contact_admin(message):
    bot.reply_to(message, f"📞 Admin: {ADMIN_USERNAME}")

# 🎥 Video yuklash
@bot.message_handler(func=lambda message: message.text == "🎥 Video yuklash")
def ask_video_link(message):
    bot.reply_to(message, "🎥 Yuklamoqchi bo‘lgan video havolasini yuboring (TikTok, Instagram, Facebook yoki Twitter).")

# 🎵 Qo‘shiq yuklash
@bot.message_handler(func=lambda message: message.text == "🎵 Qo‘shiq yuklash")
def ask_music_link(message):
    bot.reply_to(message, "🎵 YouTube havolasini yuboring (masalan: https://youtu.be/...).")

# 🎥 Video yuklab olish
@bot.message_handler(func=lambda message: "http" in message.text and not "youtu" in message.text)
def download_video(message):
    url = message.text.strip()
    bot.reply_to(message, "⏳ Video yuklab olinmoqda...")

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            ydl_opts = {
                'outtmpl': os.path.join(tmpdir, '%(title)s.%(ext)s'),
                'cookiefile': COOKIE_FILE if os.path.exists(COOKIE_FILE) else None,
                'format': 'mp4',
                'quiet': True
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                video_path = ydl.prepare_filename(info)

            caption = "✨ <b>Yuklab beruvchi:</b> <a href='https://t.me/@shazam_uzzbot'>@shazam_uzzbot</a>"
            with open(video_path, 'rb') as v:
                bot.send_video(message.chat.id, v, caption=caption, parse_mode='HTML')
    except Exception as e:
        bot.reply_to(message, f"❌ Xatolik: {e}")

# 🎵 YouTube audio yuklab olish
@bot.message_handler(func=lambda message: "youtu" in message.text)
def download_music(message):
    url = message.text.strip()
    bot.reply_to(message, "🎶 Qo‘shiq yuklab olinmoqda, kuting...")

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            ydl_opts = {
                'format': 'bestaudio/best',
                'cookiefile': COOKIE_FILE if os.path.exists(COOKIE_FILE) else None,
                'outtmpl': os.path.join(tmpdir, '%(title)s.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'quiet': True
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                audio_path = ydl.prepare_filename(info).replace(".webm", ".mp3").replace(".m4a", ".mp3")
                title = info.get("title", "Qo‘shiq")

            caption = f"🎵 <b>{title}</b>\n\nYuklab beruvchi: <a href='https://t.me/@shazam_uzzbot'>@shazam_uzzbot</a>"
            with open(audio_path, 'rb') as audio:
                bot.send_audio(message.chat.id, audio, caption=caption, parse_mode="HTML")
    except Exception as e:
        bot.reply_to(message, f"❌ Xatolik: {e}")

# 🌐 Webhook sozlash
@app.route(f"/webhook/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/")
def home():
    return "<h2>✅ Bot ishlayapti!</h2><p>Video va qo‘shiqlarni yuklab beruvchi bot.</p>"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
