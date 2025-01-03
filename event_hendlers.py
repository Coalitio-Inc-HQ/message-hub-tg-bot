from models.models import Event
from logger.log_config import logger

import aiohttp
from aiogram import types
from aiohttp import web

import uuid

import os
import shutil

from core.loader import bot
from db.requests import get_destination
from logger.log_config import logger
from models.models import Message as MessageModel, Event


async def send_message(event: Event):
    messageModel = MessageModel.model_validate(event.data["message"], from_attributes=True)
    
    users = await get_destination(
        chat_id=messageModel.chat_id, user_id=messageModel.sender_id
    )

    if not users:
        raise web.HTTPNotFound()

    try:
        temp_dir = f"./temp/{str(uuid.uuid4())}"
        os.mkdir(temp_dir, mode=777)
        media_images = []
        media_video = []
        media_files = []

        if (messageModel.attachments):
            if (messageModel.attachments["images"] and len(messageModel.attachments["images"]) >0):
                for image in messageModel.attachments["images"]:
                    await download_file(image["url"], temp_dir+"/"+image["name"])
                    media_images.append(types.InputMediaPhoto(media=types.FSInputFile(path= temp_dir+"/"+image["name"])))

            if (messageModel.attachments["videos"] and len(messageModel.attachments["videos"]) >0):
                for video in messageModel.attachments["videos"]:
                    await download_file(video["url"], temp_dir+"/"+video["name"])
                    media_video.append(types.InputMediaVideo(media=types.FSInputFile(path= temp_dir+"/"+video["name"])))

            if (messageModel.attachments["files"] and len(messageModel.attachments["files"]) >0):
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


event_handlers = {
    "chat.new_message": [
        send_message
    ],
}

async def emit_event(event: Event):
    arr = event_handlers[event.name]
    if arr:
        for item in arr:
            await item(event)
    else:
        logger.info(f"Ненайден обработчик для события {event.name}.\n", exc_info=False)