import os
import json
import random
import logging
import asyncio
from datetime import datetime, time as dt_time, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

# Настройка логов
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация бота
API_TOKEN = '7348274440:AAGtY3EC0NuA4Y8S5RP-oJLr2fWsG-QGhmM'
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Загрузка карт
with open('cards_data.json', 'r', encoding='utf-8') as f:
    tarot_cards = json.load(f)
logger.info(f"Успешно загружено {len(tarot_cards)} карт")

# Хранилище данных пользователей
user_data = {}
user_day_counter = {}  # Счётчик дней для роадмапа

# Тексты для роадмапа
ROADMAP_MESSAGES = {
    0: "✨ <b>Как использовать эту карту?</b>\n\n"
       "1. Запросить <b>вторую карту-подсказку</b> — нажмите /start ещё раз\n"
       "2. Сохраните изображение как <b>вдохновляющую заставку</b> на телефон\n"
       "3. Обратите внимание на <b>совет</b> под картой — иногда ответ уже там",

    3: "💫 <b>Заметили, как карты отражают ваше состояние?</b>\n\n"
       "В канале @Taro_Caesar разбираем, как работать с этими подсказками — "
       "вот пример → https://t.me/taro_caesar/40",

    6: "🧠 <b>Нейропрограммирование через Таро</b>\n\n"
       "Например Аркан «Императрица» помогает наполниться:\n"
       "— Теплом и нежностью\n"
       "— Уверенностью и статностью\n"
       "— Сексуальностью и изобилием\n\n"
       "Как это работает? Смотрите видео → "
       "https://www.instagram.com/reel/DLK2zLSCUSf/",

    9: "🌟 <b>Ваш личный аркан-талисман</b>\n\n"
       "Рассчитайте его по дате рождения → https://inpot.ru/?p=16952\n\n"
       "А в @Taro_Caesar — про все талисманы, и не только по дате рождения",

    12: "🌙 <b>Какая карта отозвалась сильнее всего?</b>\n\n"
        "Изучите все карты как талисманы → http://tarocaesar.tilda.ws\n\n"
        "В @Taro_Caesar — бесплатные консультации по подбору картин Таро на состояние",

    15: "🎉 <b>15 дней с Таро — ваши результаты:</b>\n\n"
        "— Заставки для поддержки\n"
        "— Личный аркан\n"
        "— Подсказки по состояниям\n"
        "— Нейровизаулы для дома\n\n"
        "<b>Продолжим глубже?</b> В канале:\n"
        "• Архетипы и таролог-запросы\n"
        "• Бесплатные консультации по подбору картины Таро\n"
        "• Сообщество единомышленников\n\n"
        "Присоединяйтесь → @Taro_Caesar"
}

def get_random_card():
    return random.choice(tarot_cards)

async def send_card(user_id: int):
    try:
        card = get_random_card()
        image_path = os.path.join('images', card['image'])
        
        if os.path.exists(image_path):
            with open(image_path, 'rb') as photo:
                message = await bot.send_photo(
                    chat_id=user_id,
                    photo=photo,
                    caption=f"<b>{card['name']}</b>\n\n{card['description']}\n\n<b>Совет:</b> {card['advice']}",
                    parse_mode="HTML"
                )
        else:
            message = await bot.send_message(
                chat_id=user_id,
                text=f"<b>{card['name']}</b>\n\n{card['description']}\n\n<b>Совет:</b> {card['advice']}",
                parse_mode="HTML"
            )
        
        # Закрепляем финальное сообщение на 15-й день
        if user_day_counter.get(user_id, 0) == 15:
            await bot.pin_chat_message(chat_id=user_id, message_id=message.message_id)
            
        return True
    except Exception as e:
        logger.error(f"Ошибка отправки карты пользователю {user_id}: {e}")
        return False

async def send_roadmap_message(user_id: int, day: int):
    if day in ROADMAP_MESSAGES:
        await bot.send_message(
            chat_id=user_id,
            text=ROADMAP_MESSAGES[day],
            parse_mode="HTML",
            disable_web_page_preview=(day != 3)  # Превью только для дня 3
        )

async def scheduled_morning_card():
    while True:
        try:
            now = datetime.now() + timedelta(hours=3)  # MSK (UTC+3)
            if now.time() >= dt_time(10, 0) and now.time() <= dt_time(10, 5):
                for user_id in list(user_data.keys()):
                    # Сброс счетчика и отправка карты
                    user_data[user_id]['count'] = 0
                    if await send_card(user_id):
                        user_data[user_id]['count'] += 1
                        user_data[user_id]['last_request'] = now
                        
                        # Обновляем счетчик дней и отправляем роадмап
                        user_day_counter[user_id] = user_day_counter.get(user_id, 0) + 1
                        await send_roadmap_message(user_id, user_day_counter[user_id])
            await asyncio.sleep(300)
        except Exception as e:
            logger.error(f"Ошибка в scheduled_morning_card: {e}")
            await asyncio.sleep(60)

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    now = datetime.now() + timedelta(hours=3)  # MSK (UTC+3)
    
    # Инициализация данных
    if user_id not in user_data:
        user_data[user_id] = {'count': 0, 'last_request': None}
        user_day_counter[user_id] = 0
    
    data = user_data[user_id]
    
    # Проверка на новый день
    if data['last_request'] and (now - data['last_request']).days >= 1:
        data['count'] = 0
    
    # Логика выдачи карт
    if data['count'] == 0:
        if await send_card(user_id):
            data['count'] += 1
            data['last_request'] = now
            # Сообщение после первой карты
            await message.answer(ROADMAP_MESSAGES[0], parse_mode="HTML")
    elif data['count'] == 1:
        if await send_card(user_id):
            data['count'] += 1
    else:
        await message.reply(
            "✨ Сегодня Таро дали все подсказки которые могли. "
            "А пока — загляните в мир Таро @Taro_Caesar у нас много чего ценного, красивого и интересного.✨",
            parse_mode="HTML"
        )

async def on_startup(dp):
    asyncio.create_task(scheduled_morning_card())

# --- Статистика пользователей ---
import json
from datetime import datetime, timedelta

# Загрузка данных из файла
try:
    with open('user_stats.json', 'r') as f:
        user_stats = json.load(f)
except:
    user_stats = {
        "all_users": {},  # {user_id: "первая_дата"}
        "last_active": {} # {user_id: "последняя_дата"}
    }

# Обновление данных при /start
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    user_id = str(message.from_user.id)
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Добавляем в общую статистику
    if user_id not in user_stats["all_users"]:
        user_stats["all_users"][user_id] = today
    
    # Обновляем последнюю активность
    user_stats["last_active"][user_id] = today
    
    # Сохраняем данные
    with open('user_stats.json', 'w') as f:
        json.dump(user_stats, f)
    
    # Ваш основной код отправки карт...

# Команда /stats (только для админа)
@dp.message_handler(commands=['stats'])
async def cmd_stats(message: types.Message):
    if message.from_user.id != 227001984:  
        return
    
    now = datetime.now()
    week_ago = (now - timedelta(days=7)).strftime("%Y-%m-%d")
    
    # Считаем активных за неделю
    active_users = [
        user_id for user_id, last_date in user_stats["last_active"].items()
        if last_date >= week_ago
    ]
    
    await message.answer(
        f"📊 <b>Статистика бота:</b>\n\n"
        f"• Всего пользователей: <code>{len(user_stats['all_users'])}</code>\n"
        f"• Активных за неделю: <code>{len(active_users)}</code>",
        parse_mode="HTML"
    )

# Автосохранение при выходе
import atexit
atexit.register(lambda: json.dump(user_stats, open('user_stats.json', 'w')))

if __name__ == '__main__':
    try:
        logger.info("Запуск бота...")
        executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
    except Exception as e:
        logger.error(f"Фатальная ошибка: {e}")
