import sys, os
from fastapi.responses import JSONResponse
from pymongo import MongoClient
from fastapi import FastAPI, HTTPException
import aiohttp
import logging

# Добавление пути к конфигурационным файлам
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config_reader import config
from config.models import Message

# Адрес и порт сервера
SERVER_HOST = config.web_server_host
SERVER_PORT = config.web_server_port

# URL для отправки сообщений в Telegram
TELEGRAM_API_URL = config.telegram_api_url

# URL для регистрации вебхука
WEBHOOK_REGISTRATION_URL = config.platform_registration_url

# URL вебхука сервера для обработки сообщений
SERVER_WEBHOOK_URL = config.server_webhook_url

# Настройка логгера
logging.basicConfig(level=logging.INFO)

# Инициализация FastAPI приложения
app = FastAPI()

# Инициализация подключения к MongoDB
client = MongoClient(config.mongodb_uri)
db = client["chat_db"]
collection_users = db["users"]


async def register_webhook():
    """
    Выполняет регистрацию вебхука на указанный URL при старте приложения.
    Отправляет POST-запрос на URL вебхука с информацией о платформе и URL сервиса.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                WEBHOOK_REGISTRATION_URL,
                json={"platform_name": "telegram", "url": SERVER_WEBHOOK_URL},
            ) as response:
                response_data = await response.json()
                logging.info(response_data)
                return response
    except Exception as e:
        logging.error(f"Возникла ошибка при регистрации вебхука: {e}")
        return None


@app.lifespan("startup")
async def on_startup():
    """
    Событие запуска приложения.
    Вызывает функцию регистрации вебхука при старте приложения.
    """
    response = await register_webhook()
    if response and response.status == 200:
        logging.info("Отправлен запрос на регистрацию вебхука")
    else:
        logging.error("Не удалось отправить запрос на регистрацию вебхука")
        raise HTTPException(
            status_code=500, detail="Не удалось отправить запрос на регистрацию вебхука"
        )


@app.post("/webhook")
async def send_message_to_chat(message: Message):
    """
    Обрабатывает входящие сообщения из вебхука.
    Ищет пользователя по chat_id в базе данных и отправляет сообщение в Telegram.
    """
    user = await collection_users.find_one({"chat_id": message.chat_id})

    if user:
        response = await send_message_to_telegram(
            user["telegram_user_id"], message.message_text
        )

        if response and response.status == 200:
            response_data = await response.json()
            logging.info("Сообщение было отправлено в Telegram")
            return JSONResponse(status_code=response.status, content=response_data)

        else:
            logging.error("Сообщение не было отправлено в Telegram.")
            raise HTTPException(
                status_code=500, detail="Сообщение не было отправлено в Telegram"
            )

    else:
        logging.warning(
            f"Пользователь с chat_id {message.chat_id} не существует в базе данных"
        )
        raise HTTPException(
            status_code=404, detail="Пользователь не найден в базе данных"
        )


async def send_message_to_telegram(telegram_user_id: int, text: str):
    """
    Отправляет сообщение в Telegram.
    Принимает telegram_user_id и текст сообщения в качестве параметров.
    """
    payload = {"chat_id": telegram_user_id, "text": text}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(TELEGRAM_API_URL, json=payload) as response:
                return response
    except Exception as e:
        logging.error(f"Возникла ошибка при отправке сообщения в Telegram: {e}")
        return None


if __name__ == "__main__":
    import uvicorn

    # Запуск FastAPI приложения
    uvicorn.run("main:app", host=SERVER_HOST, port=SERVER_PORT, reload=True)
