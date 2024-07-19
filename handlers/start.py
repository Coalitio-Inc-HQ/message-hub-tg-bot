from logger.log_config import logger

import aiohttp
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram import Router

from core.config import MESSAGE_SERVICE_USER_REGISTRATION_URL
from db.requests import add_user, get_user
from models.models import User as UserModel

aiogram_start_router = Router("Aiogram Start Handler Router")

@aiogram_start_router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    """

    if await get_user(telegram_id=message.from_user.id):
        await message.answer(
            f"Здравствуйте, {message.from_user.full_name}! Вы уже зарегистрированы!"
        )
        return

    url = MESSAGE_SERVICE_USER_REGISTRATION_URL
    payload = {"platform_name": "telegram", "name": message.from_user.full_name}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url=url, json=payload) as response:
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
            f"Здравствуйте, {message.from_user.full_name}! Вы зарегистрированы."
        )

    except Exception as err:
        await message.answer(
            "Приносим извинения! Ваше сообщение не было отправлено. Мы уже решаем данную проблему!"
        )
        logger.exception(f"Произошла ошибка: {str(err)}", exc_info=False)
