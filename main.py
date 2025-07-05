import os
import json
import random
import logging
import asyncio
from datetime import datetime, time as dt_time, timedelta
from aiogram import Bot, Dispatcher, types, executor

# Настройка логов
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация бота
API_TOKEN = '7974503657:AAGjUHrE4VWYIeiJ1YILovklhttFT4W5-vw'
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Загрузка карт
try:
    with open('cards_data.json', 'r', encoding='utf-8') as f:
        tarot_cards = json.load(f)
    logger.info(f"Успешно загружено {len(tarot_cards)} карт")
except Exception as e:
    logger.error(f"Ошибка загрузки cards_data.json: {e}")
    raise

# Хранилище данных пользователей
user_data = {}

async def send_card(user_id: int):
    try:
        card = random.choice(tarot_cards)
        image_path = os.path.join('images', card['image'])
        
        if os.path.exists(image_path):
            with open(image_path, 'rb') as photo:
                await bot.send_photo(
                    chat_id=user_id,
                    photo=photo,
                    caption=f"<b>{card['name']}</b>\n\n{card['description']}\n\n<b>Совет:</b> {card['advice']}",
                    parse_mode="HTML"
                )
        else:
            await bot.send_message(
                chat_id=user_id,
                text=f"<b>{card['name']}</b>\n\n{card['description']}\n\n<b>Совет:</b> {card['advice']}",
                parse_mode="HTML"
            )
        return True
    except Exception as e:
        logger.error(f"Ошибка отправки карты пользователю {user_id}: {e}")
        return False

async def scheduled_task():
    while True:
        try:
            now = datetime.now() + timedelta(hours=3)  # MSK (UTC+3)
            if now.time() >= dt_time(10, 0) and now.time() <= dt_time(10, 5):
                for user_id, data in list(user_data.items()):
                    if (now - data['last_request']).total_seconds() >= 86400:  # 24 часа
                        if await send_card(user_id):
                            data['last_request'] = now
                            data['count'] = 1
            await asyncio.sleep(300)  # Проверка каждые 5 минут
        except Exception as e:
            logger.error(f"Ошибка в scheduled_task: {e}")
            await asyncio.sleep(60)

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    now = datetime.now()
    
    # Инициализация данных пользователя
    if user_id not in user_data:
        user_data[user_id] = {'count': 0, 'last_request': now - timedelta(days=1)}
    
    data = user_data[user_id]
    
    # Сброс счётчика, если прошло более 24 часов
    if (now - data['last_request']).total_seconds() >= 86400:
        data['count'] = 1
    else:
        data['count'] += 1
    
    # Логика выдачи карт
    if data['count'] <= 2:
        if await send_card(user_id):
            data['last_request'] = now
    else:
        await message.reply(
            "Сегодня Таро дали все подсказки которые могли. "
            "Если вам интересно погрузиться в мир Таро, приходите в @Taro_Caezar",
            parse_mode="HTML"
        )

if __name__ == '__main__':
    try:
        logger.info("Запуск бота...")
        loop = asyncio.get_event_loop()
        loop.create_task(scheduled_task())
        executor.start_polling(dp, skip_updates=True)
    except Exception as e:
        logger.error(f"Фатальная ошибка при запуске: {e}")
