from logger.log_config import logger

import aiohttp
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram import Router

from core.config import MESSAGE_SERVICE_USER_REGISTRATION_URL, S3_BUCKET_URL, BOT_TOKEN
from db.requests import add_user, get_user
from models.models import User as UserModel

from uuid import uuid4

import os

from core.config import OUT_API_KEY

from aiogram import Bot
bot = Bot(token=BOT_TOKEN)

aiogram_start_router = Router()


@aiogram_start_router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    # Проверяем зарегестирован ли пользователь
    if await get_user(telegram_id=message.from_user.id):
        await message.answer(
            f"Здравствуйте, {message.from_user.full_name}! Вы уже зарегистрированы!"
        )
        return


    url = MESSAGE_SERVICE_USER_REGISTRATION_URL
    payload = {"platform_name": "telegram", "name": message.from_user.full_name}

    # Получаем аватарку пользователя
    user_photos = await bot.get_user_profile_photos(message.from_user.id)
    if user_photos.total_count > 0:
        s3_id = uuid4()

        file_id = user_photos.photos[0][-1].file_id
        file = await bot.get_file(file_id)
        await bot.download_file(file.file_path, f"./temp/{s3_id}.png")
        try:
            with open(f"./temp/{s3_id}.png", "rb") as f:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.put(url=S3_BUCKET_URL+"/"+str(s3_id)+".png",data=f) as response:
                            payload["icon_url"]=S3_BUCKET_URL+"/"+str(s3_id)+".png"
                except Exception as err:
                    logger.exception(f"Произошла ошибка: {str(err)}", exc_info=False)
        finally:
            os.remove(f"./temp/{s3_id}.png")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url=url, json=payload, headers={"API-KEY": OUT_API_KEY}) as response:
                response.raise_for_status()

                response_data = await response.json()
                user_id = response_data["user_id"]
                chat_id = response_data["chat_id"]

        user_data = UserModel(
            user_id=user_id,
            chat_id=chat_id,
            telegram_id=message.from_user.id,
            name=message.from_user.full_name,
        )
        await add_user(user_data)
        logger.info(
            "Новый пользователь добавлен в базу данных: ", user_data.model_dump()
        )
        await message.answer(
            f"Здравствуйте, {message.from_user.full_name}! Вы успешно зарегистрированы. Теперь вы можете отправлять сюда сообщения, и они будут переданы в организацию."
        )

    except Exception as err:
        await message.answer(
            "Приносим извинения! Произошла непредвиденная ошибка при регестрации. Мы уже решаем данную проблему!"
        )
        logger.exception(f"Произошла ошибка: {str(err)}", exc_info=False)
