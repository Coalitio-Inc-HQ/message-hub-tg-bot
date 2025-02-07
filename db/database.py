from sqlalchemy import BigInteger, String
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from core.config import DATABASE_URI

engine = create_async_engine(url=DATABASE_URI)
async_session = async_sessionmaker(engine)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[int] = mapped_column()

    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    name: Mapped[str] = mapped_column(String(32))

class MessageTranslate(Base):
    __tablename__ = "message_translate"

    mh_message_id: Mapped[int] =  mapped_column()
    tg_chat_id: Mapped[int] = mapped_column(primary_key=True)
    tg_message_id: Mapped[int] = mapped_column(primary_key=True)

async def db_run():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)