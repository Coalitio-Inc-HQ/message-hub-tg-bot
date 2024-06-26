from config.models import Message, User
from config.config_reader import config
import sys
import os
import logging
import aiohttp
import asyncio
from pymongo import MongoClient
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command

# Добавление пути к конфигурационным файлам
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Настройка логгера
logging.basicConfig(level=logging.INFO)

# Создание экземпляра бота и диспетчера
bot = Bot(token=config.telegram_bot_token.get_secret_value())
dp = Dispatcher()

# Инициализация подключения к MongoDB
client = MongoClient(config.mongodb_uri)
db = client["chat_db"]
collection_users = db["users"]

# Создание индексов
collection_users.create_index("telegram_user_id")

# URL для регистрации пользователя и отправки сообщений
USER_REGISTRATION_URL = config.user_registration_url
SEND_MESSAGE_URL = config.send_message_url


@dp.message(Command("start"))
async def start_command(message: types.Message):
    """
    Обработчик команды /start. Регистрирует пользователя в системе.
    """
    telegram_user_id = message.from_user.id
    user = collection_users.find_one({"telegram_user_id": telegram_user_id})

    if user:
        await message.reply("Вы уже зарегистрированы!")
    else:
        name = message.from_user.username
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    USER_REGISTRATION_URL,
                    json={"platform_name": "telegram", "name": name},
                ) as response:
                    response_data = await response.json()
                    user_id = response_data["user_id"]
                    chat_id = response_data["chat_id"]

            user = User(
                user_id=user_id,
                chat_id=chat_id,
                telegram_user_id=telegram_user_id,
                name=name,
            )
            user_data = user.model_dump()
            collection_users.insert_one(user_data)
            await message.reply("Добро пожаловать! Вы зарегистрированы.")
            logging.info(f"Пользователь {user_data} добавлен в базу данных.")
        except Exception as e:
            logging.error(f"Ошибка при регистрации пользователя: {e}")
            await message.reply(
                "Произошла ошибка при регистрации. Пожалуйста, попробуйте позже."
            )


@dp.message()
async def handle_message(message: types.Message):
    """
    Обработчик обычного сообщения. Сохраняет сообщение в системе и отправляет его через вебхук.
    """
    telegram_user_id = message.from_user.id
    user = collection_users.find_one({"telegram_user_id": telegram_user_id})

    if user:
        payload = Message(
            id=message.message_id,
            chat_id=user["chat_id"],
            sender_id=user["user_id"],
            sended_at=message.date.isoformat(),
            text=message.text,
        )

        payload_data = payload.model_dump(by_alias=True)
        logging.info(payload_data)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    SEND_MESSAGE_URL, json=payload_data
                ) as response:
                    response.raise_for_status()
                    response_data = await response.json()
                    logging.info(response_data)
            await message.reply("Ваше сообщение получено и сохранено!")

        except Exception as e:
            logging.error(f"Ошибка при отправке сообщения: {e}")
            await message.reply(
                "Произошла ошибка при отправке сообщения. Пожалуйста, попробуйте позже."
            )
    else:
        await message.reply(
            "Пользователь не найден в базе данных. Пожалуйста, зарегистрируйтесь командой /start."
        )


async def main():
    """
    Основной процесс бота. Запускает диспетчер для обработки команд и сообщений.
    """
    try:
        await dp.start_polling(bot)
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен!")


if __name__ == "__main__":
    asyncio.run(main())
