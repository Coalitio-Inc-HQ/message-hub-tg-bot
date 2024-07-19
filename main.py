from contextlib import asynccontextmanager

import aiohttp
from aiogram import types
from aiohttp import web
from fastapi import FastAPI, Request

from core.config import (
    MESSAGE_SERVICE_PLATFORM_REGISTRATION_URL,
    SECRET_WORD,
    SERVER_HOST,
    SERVER_PORT,
    WEBHOOK_HOST_DOCKER,
    WEBHOOK_PATH,
    WEBHOOK_URI,
)
from core.loader import bot, dp
from db.database import db_run
from db.requests import get_destination
from logger.log_config import logger
from models.models import Message as MessageModel


async def handle_webhook(request: Request):
    secret_token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")

    if secret_token == SECRET_WORD:
        update = types.Update(**await request.json())
        await dp.feed_webhook_update(bot, update)
        return web.Response()
    else:
        raise web.HTTPForbidden()


async def send_message(messageModel: MessageModel):
    users = await get_destination(
        chat_id=messageModel.chat_id, user_id=messageModel.sender_id
    )

    if not users:
        raise web.HTTPNotFound()

    for user in users:
        try:
            await bot.send_message(chat_id=user.telegram_id, text=messageModel.text)
        except Exception as e:
            logger.exception(
                f"Не удалось отправить сообщение пользователю {user.telegram_id}: {e}",
                exc_info=False,
            )
    return web.Response()


# изменить WEBHOOK_HOST_DOCKER на WEBHOOK_HOST, если бот запущен не на сервере
async def register_platform() -> None:
    url = MESSAGE_SERVICE_PLATFORM_REGISTRATION_URL
    payload = {"platform_name": "telegram", "url": WEBHOOK_HOST_DOCKER}
    async with aiohttp.ClientSession() as session:
        async with session.post(url=url, json=payload) as response:
            response.raise_for_status()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Происходит инициализация компонента.")

    logger.info("Происходит регистрация платформы на сервере мессенджера.")
    await register_platform()
    logger.info("Регистрация платформы завершена.")

    logger.info("Происходит подключение к локальной базе данных.")
    await db_run()
    logger.info("Подключение к базе данных завершено.")

    logger.info("Происходит установка вебхука на бота.")
    await bot.set_webhook(url=WEBHOOK_URI, secret_token=SECRET_WORD)
    logger.info("Вебхук установлен.")

    logger.info("Информация об установленном вебхуке:")
    webhook = await bot.get_webhook_info()
    logger.info(webhook)

    logger.info("Инициализация компонента завершена.")

    yield

    logger.info("Происходит удаление вебхука бота.")
    await bot.delete_webhook()
    logger.info("Вебхук удален.")

    logger.info("Происходит закрытие сессии.")
    await bot.session.close()
    logger.info("Сессия закрыта.")


app = FastAPI(lifespan=lifespan)


@app.post(WEBHOOK_PATH)
async def webhook_endpoint(request: Request):
    logger.info("Получен запрос от Telegram.")
    return await handle_webhook(request)


@app.post("/webhook/send_message")
async def message_service_endpoint(messageModel: MessageModel):
    logger.info("Получен запрос от сервера мессенджера.")
    return await send_message(messageModel)


if __name__ == "__main__":
    try:
        import uvicorn

        uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Компонент завершил работу.\n", exc_info=False)
