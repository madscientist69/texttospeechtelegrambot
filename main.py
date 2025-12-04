import os
import asyncio
from fastapi import FastAPI, Request
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
from gtts import gTTS

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_DOMAIN = os.getenv("WEBHOOK_DOMAIN") 
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = WEBHOOK_DOMAIN + WEBHOOK_PATH

app = FastAPI()
bot = Bot(BOT_TOKEN)
application = Application.builder().token(BOT_TOKEN).build()


# ----------------- COMMAND HANDLER -----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Halo saya TTS Bot\n"
        "Gunakan /suara untuk membuat voice note dari pesanmu\n"
        "Contoh: balas pesan dan ketik /suara"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start - Memulai bot\n"
        "/help - Panduan penggunaan\n"
        "/suara - Balas pesan atau ketik teks untuk dijadikan suara"
    )

async def suara(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg:
        return

    if msg.reply_to_message and msg.reply_to_message.text:
        text = msg.reply_to_message.text
    elif msg.text:
        text = msg.text.replace("/suara", "").strip()
        if not text:
            await msg.reply_text("💬 Reply pesan atau tulis teks setelah /suara")
            return
    else:
        await msg.reply_text("💬 Reply pesan atau tulis teks setelah /suara")
        return

    tts_path = f"/tmp/tts_{msg.message_id}.mp3"

    async def generate_and_send():
        try:
            tts = gTTS(text=text, lang="id")
            tts.save(tts_path)
            with open(tts_path, "rb") as f:
                await msg.reply_voice(f)  # kirim MP3 sebagai voice note
            os.remove(tts_path)
        except Exception as e:
            await msg.reply_text(f"Terjadi kesalahan saat membuat voice note: {e}")

    asyncio.create_task(generate_and_send())


# ----------------- ADD HANDLERS -----------------
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_cmd))
application.add_handler(CommandHandler("suara", suara))


# ----------------- STARTUP -----------------
@app.on_event("startup")
async def startup():
    await bot.initialize()
    await application.initialize()
    await bot.set_webhook(WEBHOOK_URL)
    print(f"✅ Webhook set to {WEBHOOK_URL}")


# ----------------- WEBHOOK -----------------
@app.post(WEBHOOK_PATH)
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, bot)
    asyncio.create_task(application.process_update(update))
    return {"ok": True}
