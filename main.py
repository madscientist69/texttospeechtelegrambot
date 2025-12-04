import os
import json
from fastapi import FastAPI, Request
from telegram import Update, Bot
from telegram.ext import (
    Application, CommandHandler, ContextTypes,
    MessageHandler, filters
)
from gtts import gTTS

# -------------------- ENV --------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_DOMAIN = os.getenv("WEBHOOK_DOMAIN")

WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = WEBHOOK_DOMAIN + WEBHOOK_PATH

# -------------------- FASTAPI + TELEGRAM --------------------
app = FastAPI()
bot = Bot(BOT_TOKEN)
application = Application.builder().token(BOT_TOKEN).build()

DB_FILE = "db.json"

# -------------------- DATABASE UTILS --------------------
def load_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w") as f:
            f.write("{}")
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ==============================================================
#                            TTS
# ==============================================================

async def suara(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg:
        return

    if msg.reply_to_message and msg.reply_to_message.text:
        text = msg.reply_to_message.text
    elif context.args:
        text = " ".join(context.args)
    else:
        return await msg.reply_text("💬 Reply pesan atau /suara <teks>")

    tts_path = "/tmp/tts.mp3"
    tts = gTTS(text=text, lang="id")
    tts.save(tts_path)

    with open(tts_path, "rb") as f:
        await msg.reply_voice(f)

    os.remove(tts_path)

# ==============================================================
#                        REWARD & TASK
# ==============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    db = load_db()

    if str(user.id) not in db:
        db[str(user.id)] = {
            "points": 0,
            "rewards": [],
            "history": []
        }
        save_db(db)

    await update.message.reply_text(
        "Selamat datang!\n"
        "Gunakan /setrewards untuk mengisi daftar reward.\n"
        "Gunakan /suara untuk Text-to-Speech."
    )

async def setrewards(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Kirim daftar reward (format: Nama - poin)"
    )
    context.user_data["awaiting_rewards"] = True

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.message.from_user
    db = load_db()

    if context.user_data.get("awaiting_rewards"):
        lines = text.strip().split("\n")
        rewards = []

        for line in lines:
            if "-" not in line:
                continue
            name, pts = line.split("-", 1)
            rewards.append({
                "name": name.strip(),
                "points": int(pts.strip())
            })

        db[str(user.id)]["rewards"] = rewards
        save_db(db)

        context.user_data["awaiting_rewards"] = False
        return await update.message.reply_text("Reward list berhasil disimpan!")

async def rewards(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_db()
    user_data = db.get(str(update.message.from_user.id))

    if not user_data or not user_data["rewards"]:
        return await update.message.reply_text("Reward list kosong.")

    msg = "🎁 *Reward kamu:*\n"
    for i, r in enumerate(user_data["rewards"], start=1):
        msg += f"{i}. {r['name']} — {r['points']} poin\n"

    await update.message.reply_text(msg, parse_mode="Markdown")

async def points(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_db()
    pts = db[str(update.message.from_user.id)]["points"]

    await update.message.reply_text(
        f"💰 Poin kamu: *{pts}*",
        parse_mode="Markdown"
    )

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_db()
    user = update.message.from_user

    if len(context.args) < 2:
        return await update.message.reply_text("Format: /add <tugas> <poin>")

    task_name = " ".join(context.args[:-1])
    pts = int(context.args[-1])

    db[str(user.id)]["points"] += pts
    db[str(user.id)]["history"].append(
        f"Selesai: {task_name} (+{pts})"
    )
    save_db(db)

    await update.message.reply_text(
        f"✔ Ditambahkan!\nTugas: {task_name}\nPoin: {pts}"
    )

async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_db()
    hist = db[str(update.message.from_user.id)]["history"]

    if not hist:
        return await update.message.reply_text("History kosong.")

    msg = "📜 *History:*\n" + "\n".join(f"- {h}" for h in hist)
    await update.message.reply_text(msg, parse_mode="Markdown")

async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_db()
    user = update.message.from_user

    if len(context.args) != 1:
        return await update.message.reply_text("Format: /redeem <nomor reward>")

    idx = int(context.args[0]) - 1
    user_data = db[str(user.id)]
    rewards = user_data["rewards"]

    if idx < 0 or idx >= len(rewards):
        return await update.message.reply_text("Reward tidak ditemukan.")

    reward = rewards[idx]

    if user_data["points"] < reward["points"]:
        return await update.message.reply_text("Poin tidak cukup.")

    user_data["points"] -= reward["points"]
    user_data["history"].append(
        f"Redeem: {reward['name']} (-{reward['points']})"
    )
    save_db(db)

    await update.message.reply_text(
        f"🎉 Kamu mendapatkan reward:\n*{reward['name']}*",
        parse_mode="Markdown"
    )

async def helpcmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start - mulai\n"
        "/setrewards - isi reward\n"
        "/rewards - lihat daftar reward\n"
        "/points - lihat poin\n"
        "/add <tugas> <poin>\n"
        "/history - riwayat\n"
        "/redeem <no>\n"
        "/suara <teks> - text to speech"
    )

# ==============================================================
#                      REGISTER HANDLER
# ==============================================================

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("setrewards", setrewards))
application.add_handler(CommandHandler("rewards", rewards))
application.add_handler(CommandHandler("points", points))
application.add_handler(CommandHandler("add", add))
application.add_handler(CommandHandler("history", history))
application.add_handler(CommandHandler("redeem", redeem))
application.add_handler(CommandHandler("help", helpcmd))

# TTS
application.add_handler(CommandHandler("suara", suara))

# Text biasa
application.add_handler(MessageHandler(filters.TEXT, message_handler))

# ==============================================================
#                       STARTUP WEBHOOK (TTS STYLE)
# ==============================================================

@app.on_event("startup")
async def startup():
    await bot.initialize()
    await application.initialize()
    await bot.set_webhook(WEBHOOK_URL)
    print(f"✅ Webhook set to {WEBHOOK_URL}")

# ==============================================================
#                       WEBHOOK RECEIVER
# ==============================================================

@app.post(WEBHOOK_PATH)
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, bot)
    await application.process_update(update)
    return {"ok": True}
