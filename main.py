import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Xotirada ma'lumot saqlanadi
user_data = {}

ADMIN = "998934803040"  # faqat siz admin

# start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tel = update.message.from_user.phone_number if update.message.contact else None
    await update.message.reply_text(
        "Assalomu alaykum!\nKirim/chiqim kiritish:\n"
        "kirim 20000 non\n"
        "chiqim 12000 choy\n"
        "/hisobot — hisobot ko‘rish"
    )

# Kirim
async def kirim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.split(maxsplit=2)
    if len(text) < 3:
        return await update.message.reply_text("❗ Misol: kirim 20000 non")

    summa, maqsad = text[1], text[2]
    uid = update.message.from_user.id

    user_data.setdefault(uid, {"kirim": [], "chiqim": []})
    user_data[uid]["kirim"].append((summa, maqsad))

    await update.message.reply_text(f"✔ Kirim qo‘shildi: {summa} — {maqsad}")

# Chiqim
async def chiqim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.split(maxsplit=2)
    if len(text) < 3:
        return await update.message.reply_text("❗ Misol: chiqim 12000 choy")

    summa, maqsad = text[1], text[2]
    uid = update.message.from_user.id

    user_data.setdefault(uid, {"kirim": [], "chiqim": []})
    user_data[uid]["chiqim"].append((summa, maqsad))

    await update.message.reply_text(f"✔ Chiqim qo‘shildi: {summa} — {maqsad}")

# Hisobot
async def hisobot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    data = user_data.get(uid)

    if not data:
        return await update.message.reply_text("📝 Hali hech narsa kiritilmagan!")

    jami_kirim = sum(int(x[0]) for x in data["kirim"])
    jami_chiqim = sum(int(x[0]) for x in data["chiqim"])
    balans = jami_kirim - jami_chiqim

    text = "📊 *HISOBOT*\n\n"

    text += "🟩 *Kirimlar:*\n"
    for s, m in data["kirim"]:
        text += f" + {s} — {m}\n"

    text += "\n🟥 *Chiqimlar:*\n"
    for s, m in data["chiqim"]:
        text += f" - {s} — {m}\n"

    text += (
        f"\n💰 Jami kirim: {jami_kirim}\n"
        f"💸 Jami chiqim: {jami_chiqim}\n"
        f"📦 Balans: {balans}"
    )

    await update.message.reply_text(text, parse_mode="Markdown")

# Run
def main():
    TOKEN = os.getenv("BOT_TOKEN")
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("hisobot", hisobot))

    app.add_handler(MessageHandler(filters.Regex("^kirim"), kirim))
    app.add_handler(MessageHandler(filters.Regex("^chiqim"), chiqim))

    print("Bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()
