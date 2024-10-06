from pydantic import BaseModel, Field
from typing import Any

class Message(BaseModel):
    id: int = Field(..., description="Идентификатор сообщения")
    chat_id: int = Field(..., description="Идентификатор чата")
    sender_id: int = Field(..., description="Идентификатор отправителя")
    text: str = Field(..., description="Текст сообщения")
    sended_at: str = Field(..., description="Дата отправки сообщения")
    attachments: dict

class Event(BaseModel):
    name:str
    data:Any


class User(BaseModel):
    user_id: int = Field(..., description="Идентификатор пользователя")
    chat_id: int = Field(..., description="Идентификатор чата")
    telegram_id: int = Field(..., description="Идентификатор пользователя Telegram")
    name: str = Field(..., description="Имя пользователя")
