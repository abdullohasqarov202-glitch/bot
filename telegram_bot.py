import os
import telebot
import yt_dlp
from flask import Flask, request
import tempfile

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
bot = telebot."TELEGRAM_TOKEN(TOKEN)
app = Flask(__name__)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

@app.route('/webhook/' + TOKEN, methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

@bot.message_handler(content_types=['text'])
def download_audio(message):
    url = message.text.strip()
    if not url.startswith("http"):
        bot.reply_to(message, "🎧 Havolani yuboring, masalan: https://soundcloud.com/... yoki https://tiktok.com/...")
        return

    bot.reply_to(message, "⏳ Yuklanmoqda...")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": "%(title)s.%(ext)s",
        "quiet": True,
        "nocheckcertificate": True,
        "extractor_retries": 3,
        "retries": 5,
        "ignoreerrors": True,
        "noplaylist": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "extractor_args": {
            "youtube": {"player_client": ["web"]},  # xavfsiz variant
        }
    }

    try:
        with tempfile.TemporaryDirectory() as tempdir:
            ydl_opts["outtmpl"] = os.path.join(tempdir, "%(title)s.%(ext)s")

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if not info:
                    raise Exception("Yuklab bo‘lmadi")

                file_path = ydl.prepare_filename(info).replace(".webm", ".mp3").replace(".m4a", ".mp3")

                with open(file_path, "rb") as audio:
                    bot.send_audio(message.chat.id, audio, title=info.get("title", "Qo‘shiq"), performer=info.get("uploader", ""))
    except Exception as e:
        bot.reply_to(message, f"❌ Yuklab bo‘lmadi.\n\nSabab: {str(e)[:300]}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
