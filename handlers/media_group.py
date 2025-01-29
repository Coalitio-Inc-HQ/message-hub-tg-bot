from logger.log_config import logger

import aiohttp
from aiogram import F, Router, types
from aiogram.types import Message

from core.config import MESSAGE_SERVICE_SEND_MESSAGE_URL, S3_BUCKET_URL, BOT_TOKEN
from db.requests import get_user
from models.models import Message as MessageModel

from .media_group_midel_were import AlbumMiddleware

import uuid

import os

import shutil

from moviepy import VideoFileClip
from PIL import Image

from aiogram import Bot
bot = Bot(token=BOT_TOKEN)

aiogram_group_router = Router()

aiogram_group_router.message.middleware(AlbumMiddleware(latency=1))

@aiogram_group_router.message()
async def message_handler(message: Message, album: list = None) -> None:
    if not message.media_group_id and (message.document or message.photo or message.video):
        album = [message]
    try:
        user = await get_user(telegram_id=message.from_user.id)

        if not user:
            await message.answer(
                "Извините, мы не нашли Вас среди зарегистрированных пользователей.\n"
                "Пожалуйста, зарегистрируйтесь командой /start ."
            )
            return

        attachments = {
            "images": [],
            "videos": [],
            "files": [],
        }

        text = None

        try:
            temp_dir = f"./temp/{str(uuid.uuid4())}"
            os.mkdir(temp_dir, mode=777)

            for message_album in album:
                if message_album.photo:
                    attachments["images"].append(await prepare_file(temp_dir, message_album.photo[-1].file_id, file_pref = ".jpg")) 

                if message_album.video:
                    if message_album.video.file_size> 20971520:
                        await message_album.answer("Размер видео превышает 20Мб. Видео не будет загружено.", reply_to_message_id=message_album.message_id)
                    else:
                        attachments["videos"].append(await prepare_file(temp_dir, message_album.video.file_id, file_name=message_album.video.file_name, video=True)) 

                if message_album.document:
                    if message_album.document.file_size> 20971520:
                        await message_album.answer("Размер файла превышает 20Мб. Файл не будет загружен.", reply_to_message_id=message_album.message_id)
                    else:                        
                        attachments["files"].append(await prepare_file(temp_dir, message_album.document.file_id, file_name=message_album.document.file_name)) 

                if message_album.caption:
                    text = message_album.caption

        finally:
            shutil.rmtree(temp_dir)


        message_data = MessageModel(
            id=0,
            chat_id=user.chat_id,
            sender_id=user.user_id,
            text= text,
            sended_at=message.date.isoformat(),
            attachments=attachments
        )

        url = MESSAGE_SERVICE_SEND_MESSAGE_URL
        payload = {
            "message": message_data.model_dump(),
            "event_id": str(uuid.uuid4()),
        }

        if text or attachments["files"] or attachments["images"] or attachments["videos"]:
            async with aiohttp.ClientSession() as session:
                async with session.post(url=url, json=payload) as response:
                    response.raise_for_status()

        logger.info(f"Обработано сообщение от пользователя {message.from_user.id}.")
        # logger.info(message_data.model_dump())
        # await message.reply("Ваше сообщение принято.")

    except Exception as err:
        await message.answer(
            "Приносим извинения! Ваше сообщение не было отправлено. Мы уже решаем данную проблему!"
        )
        logger.exception(f"Произошла ошибка: {str(err)}", exc_info=False)


async def prepare_file(temp_dir: str, bot_file_id, file_pref: str = None, file_name: str = None, video: bool = None) -> dict:
    file = await bot.get_file(bot_file_id)
    
    s3_id = uuid.uuid4()

    local_file_path = temp_dir+"/"+str(s3_id)+(file_pref if file_pref else "."+file_name.split(".")[-1])

    await bot.download_file(file.file_path, local_file_path)

    url = None

    with open(local_file_path, "rb") as f:
        async with aiohttp.ClientSession() as session:
            async with session.put(url=S3_BUCKET_URL+"/"+str(s3_id)+(file_pref if file_pref else "."+file_name.split(".")[-1]),data=f.read()) as response:
                url = S3_BUCKET_URL+"/"+str(s3_id)+(file_pref if file_pref else "."+file_name.split(".")[-1])
                response.raise_for_status()


    if video:
        return {
            "url": url,
            "name": str(s3_id)+file_pref if file_pref else file_name,
            "miniature":{
                "url": await generete_prevue(temp_dir, local_file_path)
            }
        }      
    else:
        return {
            "url": url,
            "name": str(s3_id)+file_pref if file_pref else file_name
        }

async def generete_prevue(temp_dir: str,video_name: str):
    clip = VideoFileClip(video_name)
    frame = clip.get_frame(2)
    image = Image.fromarray(frame)
    
    output_filename = str(uuid.uuid4())+".jpg"

    image.save(temp_dir+'/'+output_filename)

    clip.close()
    image.close()

    with open(temp_dir+'/'+output_filename, "rb") as f:
        async with aiohttp.ClientSession() as session:
            async with session.put(url=S3_BUCKET_URL+"/"+output_filename,data=f) as response:
                response.raise_for_status()
                return S3_BUCKET_URL+"/"+output_filename