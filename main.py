import os
from fastapi import FastAPI, Request
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler
from gtts import gTTS
from pydub import AudioSegment
from dotenv import load_dotenv

# load env vars
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
DOMAIN = os.getenv("WEBHOOK_DOMAIN")  # bisa kosong dulu

WEBHOOK_PATH = f"/webhook/{TOKEN}"
WEBHOOK_URL = None

# safety check
if DOMAIN and DOMAIN.startswith("https://"):
    WEBHOOK_URL = DOMAIN + WEBHOOK_PATH
else:
    print("⚠ WEBHOOK_DOMAIN belum valid atau belum tersedia. Webhook tidak di-set otomatis.")

app = FastAPI()
bot = Bot(TOKEN)


def generate_voice(text: str) -> str:
    """Convert text to Telegram voice note (.ogg)"""
    tts = gTTS(text=text, lang="id")
    tts.save("tts.mp3")

    sound = AudioSegment.from_mp3("tts.mp3")
    sound.export("tts.ogg", format="ogg", codec="opus")

    return "tts.ogg"


async def suara(update, context):
    """Command handler /suara"""
    msg = update.message

    # 1️⃣ jika reply ke pesan
    if msg.reply_to_message and msg.reply_to_message.text:
        text = msg.reply_to_message.text

    # 2️⃣ jika argumen command
    elif context.args:
        text = " ".join(context.args)

    else:
        await msg.reply_text("💬 Reply pesan atau gunakan: /suara teks")
        return

    file_path = generate_voice(text)
    await msg.reply_voice(voice=open(file_path, "rb"))


# setup Telegram application
application = Application.builder().token(TOKEN).build()
application.add_handler(CommandHandler("suara", suara))


# FastAPI route for webhook
@app.post(WEBHOOK_PATH)
async def webhook(request: Request):
    raw = await request.json()
    update = Update.de_json(raw, bot)
    await application.process_update(update)
    return "ok"


# startup event
@app.on_event("startup")
async def startup():
    if WEBHOOK_URL:
        await bot.set_webhook(WEBHOOK_URL)
        print(f"✅ Webhook set to {WEBHOOK_URL}")
    else:
        print("⚠ Skipping webhook setup. Set WEBHOOK_DOMAIN to valid HTTPS after deploy.")
