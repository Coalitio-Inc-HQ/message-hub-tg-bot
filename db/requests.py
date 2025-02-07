from sqlalchemy import delete, select, update

from db.database import User, MessageTranslate, async_session
from models.models import User as UserModel


async def add_user(userModel: UserModel) -> None:
    async with async_session() as session:
        session.add(
            User(
                user_id=userModel.user_id,
                chat_id=userModel.chat_id,
                telegram_id=userModel.telegram_id,
                name=userModel.name,
            )
        )
        await session.commit()


async def delete_user(
    telegram_id: int = None, user_id: int = None, chat_id: int = None
) -> None:
    async with async_session() as session:
        query = delete(User)

        if telegram_id is not None:
            query = query.where(User.telegram_id == telegram_id)
        elif user_id is not None:
            query = query.where(User.user_id == user_id)
        elif chat_id is not None:
            query = query.where(User.chat_id == chat_id)
        else:
            raise ValueError("At least one parameter must be provided.")

        await session.execute(query)
        await session.commit()


async def update_chat_id(
    new_chat_id: int, telegram_id: int = None, user_id: int = None, chat_id: int = None
) -> None:
    async with async_session() as session:
        query = update(User).values(chat_id=new_chat_id)

        if telegram_id is not None:
            query = query.where(User.telegram_id == telegram_id)
        elif user_id is not None:
            query = query.where(User.user_id == user_id)
        elif chat_id is not None:
            query = query.where(User.chat_id == chat_id)
        else:
            raise ValueError("At least one parameter must be provided.")

        await session.execute(query)
        await session.commit()


async def get_user(telegram_id: int = None, user_id: int = None):
    async with async_session() as session:
        query = select(User)

        if telegram_id is not None:
            query = query.where(User.telegram_id == telegram_id)
        elif user_id is not None:
            query = query.where(User.user_id == user_id)
        else:
            raise ValueError("At least one parameter must be provided.")

        response = await session.execute(query)
        return response.scalar_one_or_none()


# находим адресатов по чату, за исключением самого отправителя
async def get_destination(chat_id: int, user_id: int):
    async with async_session() as session:
        response = await session.execute(
            select(User).where(User.chat_id == chat_id, User.user_id != user_id)
        )
        return response.scalars()


async def add_translate_message(tg_message_id: int, tg_chat_id: int, mh_message_id: int ) -> None:
    async with async_session() as session:
        session.add(
            MessageTranslate(
                tg_message_id=tg_message_id,
                tg_chat_id=tg_chat_id,
                mh_message_id=mh_message_id,
            )
        )
        await session.commit()



async def get_translate_message(tg_message_id: int = None, tg_chat_id: int = None, mh_message_id: int = None):
    async with async_session() as session:
        query = select(MessageTranslate)

        if tg_message_id is not None:
            query = query.where(MessageTranslate.tg_message_id == tg_message_id, MessageTranslate.tg_chat_id ==tg_chat_id )
        elif mh_message_id is not None:
            query = query.where(MessageTranslate.mh_message_id == mh_message_id)
        else:
            raise ValueError("At least one parameter must be provided.")

        response = await session.execute(query)
        return response.scalars()
