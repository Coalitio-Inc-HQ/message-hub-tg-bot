from logger.log_config import logger

import aiohttp
from aiogram import F, Router
from aiogram.types import Message

from core.config import MESSAGE_SERVICE_SEND_MESSAGE_URL
from db.requests import get_user
from models.models import Message as MessageModel

import uuid

from core.config import OUT_API_KEY

aiogram_message_router = Router()

@aiogram_message_router.message(F.text)
async def message_handler(message: Message) -> None:
    try:
        user = await get_user(telegram_id=message.from_user.id)

        if not user:
            await message.answer(
                "Извините, мы не нашли Вас среди зарегистрированных пользователей.\n"
                "Пожалуйста, зарегистрируйтесь командой /start ."
            )
            return

        message_data = MessageModel(
            id=-1,
            chat_id=user.chat_id,
            sender_id=user.user_id,
            text=message.text,
            sended_at=message.date.isoformat(),
            attachments={}
        )

        url = MESSAGE_SERVICE_SEND_MESSAGE_URL
        payload = {
            "message": message_data.model_dump(),
            "event_id": str(uuid.uuid4()),
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url=url, json=payload, headers={"API-KEY": OUT_API_KEY}) as response:
                response.raise_for_status()

        logger.info(f"Обработано сообщение от пользователя {message.from_user.id}.")
        # logger.info(message_data.model_dump())
        # await message.reply("Ваше сообщение принято.")

    except Exception as err:
        await message.answer(
            "Приносим извинения! Ваше сообщение не было отправлено. Мы уже решаем данную проблему!"
        )
        logger.exception(f"Произошла ошибка: {str(err)}", exc_info=False)