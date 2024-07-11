from logger.log_config import logger

import aiohttp
from aiogram import F, types

from core.config import MESSAGE_SERVICE_SEND_MESSAGE_URL
from core.loader import dp
from db.requests import get_user
from models.models import Message as MessageModel


@dp.message(F.text)
async def message_handler(message: types.Message) -> None:
    """
    Handler messages
    """
    try:
        user = await get_user(telegram_id=message.from_user.id)

        if not user:
            raise Exception("Отправитель сообщения не найден в базе данных.")

        message_data = MessageModel(
            id=0,
            chat_id=user.chat_id,
            sender_id=user.user_id,
            text=message.text,
            sended_at=message.date.isoformat(),
        )

        async with aiohttp.ClientSession() as session:
            async with session.post(
                MESSAGE_SERVICE_SEND_MESSAGE_URL,
                json=message_data.model_dump(),
            ) as response:
                if response.status != 200:
                    raise Exception(
                        f"Ошибка при отправлении сообщения на сервер мессенджера. "
                        f"Статус ответа: {response.status}"
                    )
        logger.info("Отправлено сообщение: ")
        logger.info(message_data.model_dump())
        # await message.reply("Ваше сообщение принято.")

    except Exception as err:
        logger.exception("Произошла ошибка: %s", str(err))
        await message.reply("Произошла ошибка: %s", str(err))
