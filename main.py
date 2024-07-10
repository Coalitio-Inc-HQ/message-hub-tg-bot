import logging
from aiogram import types
from aiohttp import web
import aiohttp
from fastapi import Request, FastAPI

from core.config import (
    MESSAGE_SERVICE_PLATFORM_REGISTRATION_URL,
    SERVER_HOST,
    SERVER_PORT,
    WEBHOOK_HOST,
    WEBHOOK_PATH,
    WEBHOOK_URI,
    BOT_TOKEN,
)
from core.loader import bot, dp

from db.database import db_run
from db.requests import get_destination
import handlers  # noqa: F401

from models.models import Message as MessageModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    # Можно указать список разрешенных источников, например ["https://example.com"]
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],  # Разрешенные методы, например ["GET", "POST"]
    allow_headers=["*"],  # Разрешенные заголовки
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
    users = await get_destination(chat_id=messageModel.chat_id, user_id=messageModel.sender_id)

    if not users:
        raise web.HTTPNotFound()

    for user in users:
        await bot.send_message(chat_id=user.telegram_id, text=messageModel.text)
    return web.Response()


async def register_platform() -> None:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                MESSAGE_SERVICE_PLATFORM_REGISTRATION_URL,
                json={"platform_name": "telegram", "url": WEBHOOK_HOST},
            ) as response:
                if response.status != 200:
                    raise Exception(
                        f"Ошибка при регистрации платформы на сервере мессенджера. "
                        f"Статус ответа: {response.status}"
                    )
        logging.info("Произведена регистрация платформы.")
    except Exception as err:
        logging.exception("Произошла ошибка: %s", str(err))


async def on_startup():
    await register_platform()
    await db_run()
    await bot.set_webhook(WEBHOOK_URI)


async def on_shutdown():
    await bot.delete_webhook()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    app.add_event_handler("startup", on_startup)
    app.add_event_handler("shutdown", on_shutdown)

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
    except KeyboardInterrupt:
        logging.info("Shutting down...")
