from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Literal


class Message(BaseModel):
    message_id: int = Field(..., alias="id", description="Идентификатор сообщения")
    chat_id: int = Field(..., description="Идентификатор чата")
    sender_id: int = Field(..., description="Идентификатор отправителя")
    message_text: str = Field(..., alias="text", description="Текст сообщения")
    date: str = Field(..., alias="sended_at", description="Дата отправки сообщения")

class User(BaseModel):
    user_id: int = Field(..., description="Идентификатор пользователя")
    chat_id: int = Field(..., description="Идентификатор чата")
    telegram_user_id: int = Field(..., description="Идентификатор пользователя Telegram")
    name: str = Field(..., description="Имя пользователя")
    
    