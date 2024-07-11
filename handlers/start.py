from logger.log_config import logger

import aiohttp
from aiogram.filters import CommandStart
from aiogram.types import Message

from core.config import MESSAGE_SERVICE_USER_REGISTRATION_URL
from core.loader import dp
from db.requests import add_user, get_user
from models.models import User as UserModel


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    """

    if await get_user(telegram_id=message.from_user.id):
        await message.answer(
            f"Здравствуйте, {message.from_user.full_name}! Вы уже зарегистрированы!"
        )
        return

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                MESSAGE_SERVICE_USER_REGISTRATION_URL,
                json={"platform_name": "telegram", "name": message.from_user.username},
            ) as response:
                if response.status != 200:
                    raise Exception(
                        f"Ошибка при регистрации пользователя на сервере мессенджера. "
                        f"Статус ответа: {response.status}"
                    )
                response_data = await response.json()
                user_id = response_data["user_id"]
                chat_id = response_data["chat_id"]

        user_data = UserModel(
            user_id=user_id,
            chat_id=chat_id,
            telegram_id=message.from_user.id,
            name=message.from_user.username,
        )
        await add_user(user_data)
        logger.info(
            "Новый пользователь добавлен в базу данных: ", user_data.model_dump()
        )
        await message.answer(
            f"Здравствуйте, {message.from_user.full_name}! Вы зарегистрированы."
        )

    except Exception as err:
        logger.error("Произошла ошибка: %s", str(err))
        await message.answer("Произошла ошибка: %s", str(err))
