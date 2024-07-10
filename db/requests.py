from sqlalchemy import select

from db.database import User, async_session
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


async def get_destination(chat_id: int, user_id: int):
    async with async_session() as session:
        response = await session.execute(
            select(User).where(User.chat_id == chat_id, User.user_id != user_id)
        )
        return response.scalars()


async def get_user(telegram_id: int):
    async with async_session() as session:
        response = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return response.scalar_one_or_none()
