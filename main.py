import os
import json
import random
import time
from datetime import datetime, time as dt_time, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

# Настройки бота
API_TOKEN = '7974503657:AAGjUHrE4VWYIeiJ1YILovklhttFT4W5-vw'
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Загрузка данных карт
with open('cards_data.json', 'r', encoding='utf-8') as f:
    tarot_cards = json.load(f)

# Словари для учета запросов
user_last_request = {}
user_request_count = {}

def get_random_card():
    return random.choice(tarot_cards)

async def send_card(user_id):
    card = get_random_card()
    try:
        with open(card['image'], 'rb') as photo:
            await bot.send_photo(
                chat_id=user_id,
                photo=photo,
                caption=f"<b>{card['name']}</b>\n\n{card['description']}\n\n<b>Совет:</b> {card['advice']}",
                parse_mode="HTML"
            )
    except FileNotFoundError:
        await bot.send_message(
            chat_id=user_id,
            text=f"<b>{card['name']}</b>\n\n{card['description']}\n\n<b>Совет:</b> {card['advice']}",
            parse_mode="HTML"
        )

async def scheduled_card():
    while True:
        now = datetime.now()
        # Московское время (UTC+3)
        moscow_time = now + timedelta(hours=3)
        if moscow_time.time() >= dt_time(10, 0) and moscow_time.time() <= dt_time(10, 5):
            for user_id in list(user_last_request.keys()):
                last_request = user_last_request[user_id]
                if (now - last_request).total_seconds() >= 86400:  # 24 часа
                    await send_card(user_id)
                    user_last_request[user_id] = now
                    user_request_count[user_id] = 1
        time.sleep(300)  # Проверяем каждые 5 минут

@dp.message_handler(commands=['start'])
async def handle_start(message: types.Message):
    user_id = message.from_user.id
    now = datetime.now()
    
    # Инициализация счетчика
    if user_id not in user_request_count:
        user_request_count[user_id] = 0
    
    # Проверка времени последнего запроса
    if user_id in user_last_request:
        seconds_passed = (now - user_last_request[user_id]).total_seconds()
        if seconds_passed < 86400:  # 24 часа
            user_request_count[user_id] += 1
        else:
            user_request_count[user_id] = 1
    else:
        user_request_count[user_id] = 1
    
    # Логика выдачи карт
    if user_request_count[user_id] <= 2:
        await send_card(user_id)
        user_last_request[user_id] = now
    else:
        await message.reply(
            "Сегодня Таро дали все подсказки которые могли. Если вам интересно погрузиться в мир Таро, "
            "знать как себя поддержать, и уметь настроиться на нужный лад приходите в наш канал @Taro_Caezar, "
            "там вы найдете много полезного и красивого. А мы будем рады общению с вами.",
            parse_mode="HTML"
        )

if __name__ == '__main__':
    from aiogram import executor
    import asyncio
    
    # Запуск планировщика
    loop = asyncio.get_event_loop()
    loop.create_task(scheduled_card())
    
    # Запуск бота
    executor.start_polling(dp, skip_updates=True)
