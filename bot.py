import os
import time
import sqlite3
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("8391032824:AAHLjXpBvOXmWKviIJwVb6omsvRWdeA7cek")
OWNER_USERNAME = "@stoke_777"

conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    downloads INTEGER DEFAULT 0,
    level INTEGER DEFAULT 0,
    last_time REAL DEFAULT 0
)
""")
conn.commit()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?,?)",
                   (user.id, user.username))
    conn.commit()

    cursor.execute("SELECT downloads, level FROM users WHERE user_id=?", (user.id,))
    downloads, level = cursor.fetchone()

    await update.message.reply_text(
        f"👤 @{user.username}\n⭐ Level: {level}\n\nSend Instagram Reel link."
    )

def download_video(url, filename):
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        return False
    with open(filename, "wb") as f:
        f.write(r.content)
    return True

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    now = time.time()

    if "instagram.com" not in text:
        await update.message.reply_text("Send valid Instagram link.")
        return

    cursor.execute("SELECT downloads, level, last_time FROM users WHERE user_id=?", (user_id,))
    downloads, level, last_time = cursor.fetchone()

    if now - last_time < 10:
        await update.message.reply_text("Wait 10 seconds.")
        return

    await update.message.reply_text("Downloading...")

    filename = f"{user_id}.mp4"
    success = download_video(text, filename)

    if not success:
        await update.message.reply_text("❌ Failed to download.")
        return

    with open(filename, "rb") as video:
        await update.message.reply_video(video)

    os.remove(filename)

    downloads += 1
    new_level = downloads // 10

    cursor.execute("""
    UPDATE users SET downloads=?, level=?, last_time=? WHERE user_id=?
    """, (downloads, new_level, now, user_id))
    conn.commit()

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

app.run_polling()
