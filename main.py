import os
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

    # langsung MP3, tidak perlu konversi ke OGG/Opus
    tts_path = "/tmp/tts.mp3"
    tts = gTTS(text=text, lang="id")
    tts.save(tts_path)

    with open(tts_path, "rb") as f:
        await msg.reply_voice(f)  # Telegram menerima voice MP3
    os.remove(tts_path)


application.add_handler(CommandHandler("suara", suara))


@app.on_event("startup")
async def startup():
    await bot.initialize()
    await application.initialize()
    await bot.set_webhook(WEBHOOK_URL)
    print(f"✅ Webhook set to {WEBHOOK_URL}")


@app.post(WEBHOOK_PATH)
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, bot)
    await application.process_update(update)
    return {"ok": True}
