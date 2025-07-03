import logging
import json
import random
import datetime
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Загрузим данные карт
with open("cards_data.json", "r", encoding="utf-8") as f:
    cards = json.load(f)

# Словарь для хранения, кому какая карта выпадала в какой день
user_sessions = {}

# Логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

BOT_TOKEN = "7974503657:AAGjUHrE4VWYIeiJ1YILovklhttFT4W5-vw"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    today = datetime.date.today().isoformat()

    if user_id in user_sessions and user_sessions[user_id]["date"] == today:
        card = user_sessions[user_id]["card"]
    else:
        card = random.choice(cards)
        user_sessions[user_id] = {"date": today, "card": card}

    image_path = f"images/{card['image']}"
    try:
        with open(image_path, "rb") as img:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=InputFile(img),
                caption=f"""✨ <b>{card['name']}</b>

{card['description']}

<b>Совет:</b> {card['advice']}""",
                parse_mode="HTML"
            )
    except FileNotFoundError:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"""✨ <b>{card['name']}</b>

{card['description']}

<b>Совет:</b> {card['advice']}""",
            parse_mode="HTML"
        )

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()