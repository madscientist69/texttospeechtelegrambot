import os
from fastapi import FastAPI, Request
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
from gtts import gTTS
from pydub import AudioSegment

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_DOMAIN = os.getenv("WEBHOOK_DOMAIN")  # misal: https://tts-bot-production-68e7.up.railway.app
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
    # Ambil teks dari reply atau args
    if msg.reply_to_message and msg.reply_to_message.text:
        text = msg.reply_to_message.text
    elif context.args:
        text = " ".join(context.args)
    else:
        await msg.reply_text("💬 Reply pesan atau tulis teks setelah /suara")
        return

    tts_path = "tts.mp3"
    ogg_path = "tts.ogg"
    tts = gTTS(text=text, lang="id")
    tts.save(tts_path)
    AudioSegment.from_mp3(tts_path).export(ogg_path, format="ogg", codec="opus")

    # Kirim voice
    try:
        with open(ogg_path, "rb") as voice_file:
            await msg.reply_voice(voice_file)
    finally:
        # Hapus file sementara
        if os.path.exists(tts_path):
            os.remove(tts_path)
        if os.path.exists(ogg_path):
            os.remove(ogg_path)

application.add_handler(CommandHandler("suara", suara))

# ----------------- STARTUP -----------------
@app.on_event("startup")
async def startup():
    await bot.initialize()         # 🔹 Wajib untuk FastAPI webhook
    await application.initialize() # 🔹 Wajib untuk FastAPI webhook
    await bot.set_webhook(WEBHOOK_URL)
    print(f"✅ Webhook set to {WEBHOOK_URL}")

# ----------------- WEBHOOK -----------------
@app.post(WEBHOOK_PATH)
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, bot)
    await application.process_update(update)  # 🔹 cukup ini
    return {"ok": True}
