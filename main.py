from contextlib import asynccontextmanager

import aiohttp
from aiogram import types
from aiohttp import web
from fastapi import FastAPI, Request

from aiogram.types import InputFile

import uuid

import os
import shutil

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
from models.models import Message as MessageModel, Event


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

    try:
        temp_dir = f"./temp/{str(uuid.uuid4())}"
        os.mkdir(temp_dir, mode=777)

        if (messageModel.attachments):
            if (messageModel.attachments["images"] and len(messageModel.attachments["images"]) >0):
                media_images = []
                for image in messageModel.attachments["images"]:
                    await download_file(image["url"], temp_dir+"/"+image["name"])
                    media_images.append(types.InputMediaPhoto(media=types.FSInputFile(path= temp_dir+"/"+image["name"])))

            if (messageModel.attachments["videos"] and len(messageModel.attachments["videos"]) >0):
                media_video = []
                for video in messageModel.attachments["videos"]:
                    await download_file(video["url"], temp_dir+"/"+video["name"])
                    media_video.append(types.InputMediaVideo(media=types.FSInputFile(path= temp_dir+"/"+video["name"])))

            if (messageModel.attachments["files"] and len(messageModel.attachments["files"]) >0):
                media_files = []
                for file in messageModel.attachments["files"]:
                    await download_file(file["url"], temp_dir+"/"+file["name"])
                    media_files.append(types.InputMediaDocument(media=types.FSInputFile(temp_dir+"/"+file["name"])))

        for user in users:
            try:
                if media_images:
                    await bot.send_media_group(chat_id=user.telegram_id, media=media_images)

                if media_video:
                    await bot.send_media_group(chat_id=user.telegram_id, media=media_video)
                
                if media_files:
                    await bot.send_media_group(chat_id=user.telegram_id, media=media_files)

                if (messageModel.text):
                    await bot.send_message(chat_id=user.telegram_id, text=messageModel.text)
            except Exception as e:
                logger.exception(
                    f"Не удалось отправить сообщение пользователю {user.telegram_id}: {e}",
                    exc_info=False,
                )

    except FailDownload as e:
        logger.exception(
            f"Не удалось скачать файл {e.url}.",
            exc_info=False,
        )
    except Exception as e:
        logger.exception(
            f"Непредвиденная ошибка: {e}",
            exc_info=False,
        )
        raise web.HTTPInternalServerError()
    finally:
        shutil.rmtree(temp_dir)

    return web.Response()


class FailDownload(Exception):
    url: str

    def __init__(self, *args, url: str):
        super().__init__(*args)
        self.url = url

async def download_file(url, save_path):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                with open(save_path, 'wb') as f:
                    while True:
                        chunk = await response.content.read(1024)  # Чтение файла по 1024 байта
                        if not chunk:
                            break
                        f.write(chunk)
                print(f"Файл успешно сохранен: {save_path}")
            else:
                logger.exception(
                    f"Не удалось скачать файл. Статус: {response.status}",
                    exc_info=False,
                )
                raise FailDownload(url)

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


@app.post("/webhook/send_personal_message")
async def message_service_endpoint(messageModel: MessageModel):
    logger.info("Получен запрос от сервера мессенджера.")
    return await send_message(messageModel)

@app.post("/webhook/event")
async def message_service_endpoint(event: Event):
    logger.info("Получен запрос от сервера мессенджера.")
    return {"status":"ok"}


if __name__ == "__main__":
    try:
        import uvicorn

        uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Компонент завершил работу.\n", exc_info=False)
