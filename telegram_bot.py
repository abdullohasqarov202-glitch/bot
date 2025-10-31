import os
from flask import Flask, request
import telebot
import yt_dlp
import tempfile

# 🔑 Telegram token
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise RuntimeError("❌ TELEGRAM_TOKEN aniqlanmadi!")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

CHANNEL_USERNAME = "@Asqarov_2007"

def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception:
        return False


@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    if not is_subscribed(user_id):
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("📢 Obuna bo‘lish", url=f"https://t.me/{CHANNEL_USERNAME[1:]}"),
            telebot.types.InlineKeyboardButton("✅ Tekshirish", callback_data="check_sub")
        )
        bot.send_message(user_id, f"👋 Botdan foydalanish uchun kanalga obuna bo‘ling: {CHANNEL_USERNAME}", reply_markup=markup)
        return
    bot.send_message(user_id, "🎥 Video yoki qo‘shiq havolasini yuboring (TikTok, YouTube, Instagram, Facebook, X).")


@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_sub(call):
    user_id = call.message.chat.id
    if is_subscribed(user_id):
        bot.edit_message_text("✅ Obuna tasdiqlandi! Endi botdan foydalanishingiz mumkin.", user_id, call.message.message_id)
    else:
        bot.answer_callback_query(call.id, "🚫 Hali obuna bo‘lmagansiz!")


@bot.message_handler(func=lambda message: "youtu" in message.text or "tiktok" in message.text or "instagram" in message.text or "facebook" in message.text)
def download_video(message):
    url = message.text.strip()
    bot.reply_to(message, "⬇️ Yuklab olinmoqda, biroz kuting...")

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            ydl_opts = {
                'outtmpl': os.path.join(tmpdir, '%(title)s.%(ext)s'),
                'format': 'best',
                'quiet': True,
                'noplaylist': True,
                # 🔧 SABR bypass:
                'extractor_args': {'youtube': {'player_client': ['android']}},
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info)
                title = info.get("title", "video")

            caption = f"✅ <b>{title}</b>\n\nYuklab beruvchi: <a href='https://t.me/asqarov_uzbot'>@asqarov_uzbot</a>"
            with open(file_path, 'rb') as video:
                bot.send_video(message.chat.id, video, caption=caption, parse_mode="HTML")

    except Exception as e:
        bot.reply_to(message, f"❌ Xatolik: {e}")


@app.route(f"/webhook/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200


@app.route("/")
def home():
    return "<h3>✅ Bot ishlayapti (SABR format qo‘llab-quvvatlanadi)</h3>"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
