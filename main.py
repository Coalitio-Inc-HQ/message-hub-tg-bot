from contextlib import asynccontextmanager

import aiohttp
from aiogram import types
from aiohttp import web
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

import handlers  # noqa: F401
from core.config import (
    BOT_TOKEN,
    MESSAGE_SERVICE_PLATFORM_REGISTRATION_URL,
    SERVER_HOST,
    SERVER_PORT,
    WEBHOOK_HOST,
    WEBHOOK_PATH,
    WEBHOOK_URI,
)
from core.loader import bot, dp
from db.database import db_run
from db.requests import get_destination
from logger.log_config import logger
from models.models import Message as MessageModel


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
    await bot.set_webhook(url=WEBHOOK_URI)
    logger.info("Вебхук установлен.")

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


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def handle_webhook(request: Request):
    url = str(request.url)
    index = url.rfind("/")
    token = url[index + 1 :]

    if token == BOT_TOKEN:
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
        await bot.send_message(chat_id=user.telegram_id, text=messageModel.text)
    return web.Response()


async def register_platform() -> None:
    url = MESSAGE_SERVICE_PLATFORM_REGISTRATION_URL
    payload = {"platform_name": "telegram", "url": WEBHOOK_HOST}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            response.raise_for_status()


if __name__ == "__main__":

    @app.get("/")
    async def hello():
        return "Hello, World!"

    @app.post(WEBHOOK_PATH)
    async def webhook_endpoint(request: Request):
        return await handle_webhook(request)

    @app.post("/webhook/send_message")
    async def message_service_endpoint(messageModel: MessageModel):
        return await send_message(messageModel)

    try:
        import uvicorn

        uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Компонент завершил работу.\n", exc_info=False)
