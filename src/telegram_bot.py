import sys, os

from pymongo import MongoClient

# Добавляем папку с конфигурационным файлом в путь поиска модулей
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Импортируем модуль с конфигурационными данными
from config.config_reader import config

from config.models import Message, User


# Импортируем библиотеку для работы с Telegram API
from aiogram import Bot, Dispatcher, types
import asyncio
import logging
import aiohttp
from aiogram.filters.command import Command


# Настройка логгера
logging.basicConfig(level=logging.INFO)

# Создание экземпляра бота
bot = Bot(token=config.telegram_bot_token.get_secret_value())

# Создание диспетчера
dp = Dispatcher()


client = MongoClient(config.mongodb_uri)
db = client["chat_db"]


# Обработчик команды /start
@dp.message(Command("start"))
async def start_command(message: types.Message):

    user_id = None
    chat_id = None
    name = message.from_user.username

    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{config.webhook_url}/user_registration/bot",
            json={"platform_name": "telegram", "name": name},
        ) as response:
            response_data = await response.json()
            user_id = response_data["user_id"]
            chat_id = response_data["chat_id"]

    collection = db["users"]
    existing_user = await collection.find_one({"telegram_user_id": user_id})
    if not existing_user:
        user = User(
            user_id=user_id, name=name, chat_id=chat_id, telegram_user_id=user_id
        )
        await collection.insert_one(user.model_dump())
        await message.reply("Вы зарегистрированы!")
    else:
        await message.reply("Вы уже зарегистрированы!")


# Обработчик обычного сообщения
@dp.message()
async def handle_message(message: types.Message):
    telegram_user_id = message.from_user.id
    text = message.text

    # Найти пользователя по telegram_user_id
    collection = db["users"]
    user = await collection.find_one({"telegram_user_id": telegram_user_id})

    if user:
        # Сохранение сообщения в базу данных
        payload = Message(
            chat_id=user["chat_id"],
            sender_id=user["user_id"],
            message_text=text,
            date=message.date.isoformat(),  # Assuming message.date is a datetime object
        )

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{config.webhook_url}/send_a_message_to_chat",
                json=payload.model_dump(),
            ) as response:
                response = await response.json()
                logging.info(response)

        # Ответ пользователю
        await message.reply("Ваше сообщение получено и сохранено!")
    else:
        # Если пользователь не найден
        await message.reply(
            "Пользователь не найден в базе данных. Пожалуйста, зарегистрируйтесь командой /start."
        )


# Основной процесс бота
async def main():
    try:
        # Запуск диспетчера
        await dp.start_polling(bot)
    except (KeyboardInterrupt, SystemExit):
        # Логирование остановки бота
        logging.info("Бот остановлен!")


# Запуск бота
if __name__ == "__main__":
    asyncio.run(main())
