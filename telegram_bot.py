import os
from flask import Flask, request
import telebot
import yt_dlp
import tempfile
from datetime import datetime, timedelta

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
            "📽 <b>Men nimalar qila olaman:</b>\n"
            "• TikTok, Instagram, Facebook va X (Twitter) videolarini yuklab beraman 🎥\n"
            "• YouTube’dan qo‘shiqlarni yuklab beraman 🎵\n"
            "• Kinolar kanaliga yo‘naltiraman 🎬\n"
            "• Do‘stlaringizni taklif qilib olmos yig‘ish imkoniyati bor 💎\n"
            "• Har hafta eng ko‘p olmos to‘plagan foydalanuvchi — Premium yutadi 🏆\n\n"
            "👇 Quyidagi menyudan kerakli bo‘limni tanlang!"
        )
        bot.send_message(user_id, intro_text, parse_mode="HTML")

    # Referal tizimi
    if len(args) > 1:
        referrer_id = args[1]
        if referrer_id != str(user_id):
            user_balances[referrer_id] = user_balances.get(referrer_id, 0) + 10
            bot.send_message(referrer_id, "🎉 Do‘stingiz sizning havolangiz orqali kirdi! +10 💎 olmos!")

    show_menu(message)

# 🔄 Menyu
def show_menu(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🎥 Video yuklash", "🎵 Qo‘shiq yuklash")
    markup.add("🎬 Kinolar", "💎 Mening olmoslarim")
    markup.add("🔗 Referal havola", "📩 Admin bilan aloqa")
    bot.send_message(message.chat.id, "📍 Quyidagi menyudan tanlang:", reply_markup=markup)

# 🔁 Obuna qayta tekshirish
@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_subscription(call):
    user_id = call.message.chat.id
    if is_subscribed(user_id):
        bot.edit_message_text("✅ Obuna tasdiqlandi!", chat_id=user_id, message_id=call.message.message_id)
        send_welcome(call.message)
    else:
        bot.answer_callback_query(call.id, "🚫 Hali obuna bo‘lmagansiz!")

# 💎 Balans
@bot.message_handler(func=lambda message: message.text == "💎 Mening olmoslarim")
def my_diamonds(message):
    balance = user_balances.get(message.chat.id, 0)
    bot.reply_to(message, f"💎 Sizda hozir: {balance} olmos mavjud.")

# 🔗 Referal
@bot.message_handler(func=lambda message: message.text == "🔗 Referal havola")
def referral_link(message):
    link = f"https://t.me/{bot.get_me().username}?start={message.chat.id}"
    bot.reply_to(message, f"🔗 Sizning taklif havolangiz:\n{link}\n\nHar bir do‘st uchun +10 💎 olmos!")

# 📩 Aloqa
@bot.message_handler(func=lambda message: message.text == "📩 Admin bilan aloqa")
def contact_admin(message):
    bot.reply_to(message, "📞 Admin: @Asqarov_0207")

# 🎬 Kinolar
@bot.message_handler(func=lambda message: message.text == "🎬 Kinolar")
def open_movies_channel(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🎬 Kinolar kanaliga o‘tish", url="https://t.me/KINOLAR_UZB12"))
    bot.send_message(message.chat.id, "🍿 Quyidagi tugma orqali kinolar kanaliga o‘ting:", reply_markup=markup)

# 🎥 Video yuklash
@bot.message_handler(func=lambda message: message.text == "🎥 Video yuklash")
def ask_video_link(message):
    bot.reply_to(message, "🎥 Video havolasini yuboring (TikTok, Instagram, Facebook yoki Twitter).")

# 🎵 Qo‘shiq yuklash
@bot.message_handler(func=lambda message: message.text == "🎵 Qo‘shiq yuklash")
def ask_music_link(message):
    bot.reply_to(message, "🎵 YouTube havolasini yuboring (masalan: https://youtu.be/...)")

# 🎵 YouTube audio yuklash
@bot.message_handler(func=lambda message: "youtu" in message.text)
def download_music(message):
    url = message.text.strip()
    bot.reply_to(message, "🎶 Qo‘shiq yuklab olinmoqda, biroz kuting...")
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            ydl_opts = {
                'format': 'bestaudio/best',
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

            caption = f"🎵 <b>{title}</b>\n\nYuklab beruvchi: <a href='https://t.me/asqarov_uzbot'>@asqarov_uzbot</a>"
            with open(audio_path, 'rb') as audio:
                bot.send_audio(message.chat.id, audio, caption=caption, parse_mode="HTML")
    except Exception as e:
        bot.reply_to(message, f"❌ Xatolik: {e}")

# 🧠 Webhook yo‘lini sozlash
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
