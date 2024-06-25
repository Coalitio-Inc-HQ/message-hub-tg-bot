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

# URL для отправки сообщений в Telegram
TELEGRAM_API_URL = f"https://api.telegram.org/bot{config.telegram_bot_token.get_secret_value()}/sendMessage"

# URL для регистрации вебхука
WEBHOOK_REGISTRATION_URL = f"{config.webhook_url}/platform_registration/bot"

# Настройка логгера
logging.basicConfig(level=logging.INFO)

# Инициализация FastAPI приложения
app = FastAPI()

# Инициализация подключения к MongoDB
client = MongoClient(config.mongodb_uri)
db = client["chat_db"]
collection_users = db["users"]


async def startup_event():
    """
    Выполняет регистрацию вебхука на указанный URL при старте приложения.
    Отправляет POST-запрос на URL вебхука с информацией о платформе и URL сервиса.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                WEBHOOK_REGISTRATION_URL,
                json={"platform_name": "telegram", "url": config.service_url},
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
    response = await startup_event()
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
    url = TELEGRAM_API_URL
    payload = {"chat_id": telegram_user_id, "text": text}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                response_data = await response.json()
                if response.status == 200:
                    logging.info(
                        f"Сообщение было отправлено в Telegram: {response_data}"
                    )
                    return response
                else:
                    logging.error(
                        f"Сообщение не было отправлено в Telegram: {response.status} {response_data}"
                    )
                    return response
    except Exception as e:
        logging.error(f"Возникла ошибка при отправке сообщения в Telegram: {e}")
        return None


if __name__ == "__main__":
    import uvicorn

    # Запуск FastAPI приложения
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)
