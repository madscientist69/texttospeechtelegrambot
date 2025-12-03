import os
from fastapi import FastAPI, Request
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler
from gtts import gTTS
from pydub import AudioSegment
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
DOMAIN = os.getenv("WEBHOOK_DOMAIN")

WEBHOOK_PATH = f"/webhook/{TOKEN}"
WEBHOOK_URL = DOMAIN + WEBHOOK_PATH

app = FastAPI()
bot = Bot(TOKEN)


def generate_voice(text):
    tts = gTTS(text=text, lang="id")
    tts.save("tts.mp3")

    sound = AudioSegment.from_mp3("tts.mp3")
    sound.export("tts.ogg", format="ogg", codec="opus")

    return "tts.ogg"


async def suara(update, context):
    msg = update.message

    if msg.reply_to_message and msg.reply_to_message.text:
        text = msg.reply_to_message.text
    elif context.args:
        text = " ".join(context.args)
    else:
        await msg.reply_text("💬 Reply pesan atau gunakan: /suara teks")
        return

    file = generate_voice(text)
    await msg.reply_voice(voice=open(file, "rb"))


application = Application.builder().token(TOKEN).build()
application.add_handler(CommandHandler("suara", suara))


@app.post(WEBHOOK_PATH)
async def webhook(request: Request):
    raw = await request.json()
    update = Update.de_json(raw, bot)
    await application.process_update(update)
    return "ok"


@app.on_event("startup")
async def startup():
    await bot.set_webhook(WEBHOOK_URL)
