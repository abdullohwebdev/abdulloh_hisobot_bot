import logging
import sqlite3
import pandas as pd
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InputFile, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
)

TOKEN = "1.7913542675:AAEvlNlHmWPFl1OTfHJAy5gbxeHCX_Gjz5U"
ADMIN_PHONE = "+998934803040"

conn = sqlite3.connect("data.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    phone TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    type TEXT,
    purpose TEXT,
    amount REAL,
    date TEXT
)
""")

conn.commit()

logging.basicConfig(level=logging.INFO)


# --- Contact qabul qilish ---
async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    user_id = update.message.from_user.id

    cursor.execute("INSERT OR REPLACE INTO users(user_id, phone) VALUES (?,?)",
                   (user_id, contact.phone_number))
    conn.commit()

    await update.message.reply_text("Ro‘yxatdan o‘tdingiz! Endi botdan foydalanishingiz mumkin.")
    await start(update, context)


# --- Admin tekshiruvi ---
def is_admin(phone):
    return phone == ADMIN_PHONE


# --- /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user = cursor.execute("SELECT phone FROM users WHERE user_id=?", (user_id,)).fetchone()

    if not user:
        kb = [[KeyboardButton("Telefon raqamni ulashish", request_contact=True)]]
        await update.message.reply_text(
            "Botdan foydalanish uchun telefon raqamingizni ulashing:",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True, one_time_keyboard=True)
        )
        return

    await update.message.reply_text(
        "Botga xush kelibsiz!\n\n"
        "Kirim qo‘shish: /kirim maqsad miqdor\n"
        "Chiqim qo‘shish: /chiqim maqsad miqdor\n"
        "Hisobot: /hisobot\n"
        "Excel: /excel\n"
        "Admin: /add userID"
    )


# --- /add (faqat admin) ---
async def add_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    phone = cursor.execute("SELECT phone FROM users WHERE user_id=?", (user_id,)).fetchone()

    if not phone or not is_admin(phone[0]):
        await update.message.reply_text("Siz admin emassiz!")
        return

    try:
        new_user = int(context.args[0])
        cursor.execute("INSERT OR IGNORE INTO users(user_id, phone) VALUES (?,?)", (new_user, "unknown"))
        conn.commit()
        await update.message.reply_text("Foydalanuvchi qo‘shildi!")
    except:
        await update.message.reply_text("To‘g‘ri format: /add userID")


# --- Kirim ---
async def kirim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        purpose = context.args[0]
        amount = float(context.args[1])
        user_id = update.message.from_user.id
        date = datetime.now().strftime("%Y-%m-%d")

        cursor.execute("INSERT INTO records(user_id, type, purpose, amount, date) VALUES (?,?,?,?,?)",
                       (user_id, "kirim", purpose, amount, date))
        conn.commit()

        await update.message.reply_text("Kirim qo‘shildi!")
    except:
        await update.message.reply_text("Foydalanish: /kirim maqsad miqdor")


# --- Chiqim ---
async def chiqim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        purpose = context.args[0]
        amount = float(context.args[1])
        user_id = update.message.from_user.id
        date = datetime.now().strftime("%Y-%m-%d")

        cursor.execute("INSERT INTO records(user_id, type, purpose, amount, date) VALUES (?,?,?,?,?)",
                       (user_id, "chiqim", purpose, amount, date))
        conn.commit()

        await update.message.reply_text("Chiqim qo‘shildi!")
    except:
        await update.message.reply_text("Foydalanish: /chiqim maqsad miqdor")


# --- Hisobot ---
async def hisobot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    rows = cursor.execute("SELECT type, amount FROM records WHERE user_id=?", (user_id,)).fetchall()

    if not rows:
        await update.message.reply_text("Hali ma'lumot yo‘q.")
        return

    kirim = sum(r[1] for r in rows if r[0] == "kirim")
    chiqim = sum(r[1] for r in rows if r[0] == "chiqim")

    await update.message.reply_text(
        f"📊 Hisobot:\n"
        f"🟢 Kirim: {kirim}\n🔴 Chiqim: {chiqim}\n💰 Balans: {kirim - chiqim}"
    )


# --- Excel ---
async def excel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    df = pd.read_sql_query(f"SELECT * FROM records WHERE user_id={user_id}", conn)

    path = "hisobot.xlsx"
    df.to_excel(path, index=False)

    await update.message.reply_document(InputFile(path))


async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.CONTACT, contact_handler))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("kirim", kirim))
    app.add_handler(CommandHandler("chiqim", chiqim))
    app.add_handler(CommandHandler("hisobot", hisobot))
    app.add_handler(CommandHandler("excel", excel))
    app.add_handler(CommandHandler("add", add_user))

    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())