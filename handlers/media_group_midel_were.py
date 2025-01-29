import asyncio
from typing import Any, Dict, Union

from aiogram import BaseMiddleware
from aiogram.types import Message


class AlbumMiddleware(BaseMiddleware):
    def __init__(self, latency: Union[int, float] = 0.1):
        self.latency = latency
        self.album_data = {}
        self.tasks = {}

    def collect_album_messages(self, event: Message):
        """Добавляет сообщение в группу по media_group_id"""

        if event.media_group_id not in self.album_data:
            self.album_data[event.media_group_id] = {"messages": []}

        self.album_data[event.media_group_id]["messages"].append(event)

    async def process_album(self, media_group_id: str, handler, data: Dict[str, Any]):
        """Обрабатывает альбом сообщений после задержки"""

        await asyncio.sleep(self.latency)  # Даём время для сбора сообщений
        album_messages = self.album_data.pop(media_group_id, {}).get("messages", [])

        if album_messages:
            album_messages.sort(key=lambda x: x.message_id)  # Упорядочиваем по message_id
            data["album"] = album_messages
            await handler(album_messages[0], data)  # Передаём первый элемент в обработчик

        self.tasks.pop(media_group_id, None)  # Удаляем задачу из списка активных

    async def __call__(self, handler, event: Message, data: Dict[str, Any]) -> Any:
        """Логика обработки сообщений"""
        
        if not event.media_group_id:
            return await handler(event, data)  # Если нет media_group_id, обрабатываем сразу

        self.collect_album_messages(event)

        # Если уже есть запущенная задача обработки этого media_group_id — игнорируем
        if event.media_group_id not in self.tasks:
            self.tasks[event.media_group_id] = asyncio.create_task(
                self.process_album(event.media_group_id, handler, data)
            )
