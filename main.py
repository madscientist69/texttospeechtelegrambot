import os
from fastapi import FastAPI, Request
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
from gtts import gTTS
from pydub import AudioSegment
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
DOMAIN = os.getenv("WEBHOOK_DOMAIN")  # HTTPS after deploy
WEBHOOK_PATH = f"/webhook/{TOKEN}"
WEBHOOK_URL = None

if DOMAIN and DOMAIN.startswith("https://"):
    WEBHOOK_URL = DOMAIN + WEBHOOK_PATH
else:
    print("⚠ WEBHOOK_DOMAIN belum valid, webhook tidak akan di-set otomatis.")

app = FastAPI()
bot = Bot(TOKEN)

async def generate_voice(text: str) -> str:
    tts = gTTS(text=text, lang="id")
    tts.save("tts.mp3")
    sound = AudioSegment.from_mp3("tts.mp3")
    sound.export("tts.ogg", format="ogg", codec="opus")
    return "tts.ogg"

async def suara(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg:
        return

    if msg.reply_to_message and msg.reply_to_message.text:
        text = msg.reply_to_message.text
    elif context.args:
        text = " ".join(context.args)
    else:
        await msg.reply_text("💬 Reply pesan atau gunakan: /suara teks")
        return

    file_path = await generate_voice(text)
    await msg.reply_voice(voice=open(file_path, "rb"))

# ============================
# Telegram Application
# ============================
application = Application.builder().token(TOKEN).build()
application.add_handler(CommandHandler("suara", suara))

# ============================
# FastAPI Webhook Route
# ============================
@app.post(WEBHOOK_PATH)
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, bot)
    await application.process_update(update)
    return {"ok": True}

# ============================
# Startup Event: Set Webhook
# ============================
@app.on_event("startup")
async def startup():
    if WEBHOOK_URL:
        await bot.set_webhook(WEBHOOK_URL)
        print(f"✅ Webhook set to {WEBHOOK_URL}")
    else:
        print("⚠ Skipping webhook setup. Set WEBHOOK_DOMAIN to valid HTTPS after deploy.")
