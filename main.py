import os
from fastapi import FastAPI, Request
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
from gtts import gTTS
from pydub import AudioSegment

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_DOMAIN = os.getenv("WEBHOOK_DOMAIN")  
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = WEBHOOK_DOMAIN + WEBHOOK_PATH

app = FastAPI()
bot = Bot(BOT_TOKEN)

# ----------------- TELEGRAM -----------------
application = Application.builder().token(BOT_TOKEN).build()

async def suara(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg:
        return
    if msg.reply_to_message and msg.reply_to_message.text:
        text = msg.reply_to_message.text
    elif context.args:
        text = " ".join(context.args)
    else:
        await msg.reply_text("💬 Reply pesan atau /suara teks")
        return

    tts = gTTS(text=text, lang="id")
    tts.save("tts.mp3")
    AudioSegment.from_mp3("tts.mp3").export("tts.ogg", format="ogg", codec="opus")
    await msg.reply_voice(open("tts.ogg", "rb"))

application.add_handler(CommandHandler("suara", suara))

# ----------------- STARTUP -----------------
@app.on_event("startup")
async def startup():
    # Initialize Bot dan Application sebelum dipakai process_update
    await bot.initialize()                  # 🔹 wajib!
    await application.initialize()          # 🔹 wajib!
    await bot.set_webhook(WEBHOOK_URL)
    print(f"✅ Webhook set to {WEBHOOK_URL}")

# ----------------- WEBHOOK -----------------
@app.post(WEBHOOK_PATH)
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, bot)
    await application.process_update(update)  # cukup ini, handler akan jalan
    return {"ok": True}
