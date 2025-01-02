from aiogram import Dispatcher, Bot

from core.config import BOT_TOKEN

from handlers.start import aiogram_start_router
from handlers.message import aiogram_message_router
from handlers.media_group import aiogram_group_router

dp = Dispatcher()
bot = Bot(token=BOT_TOKEN)

dp.include_routers(aiogram_start_router, aiogram_message_router, aiogram_group_router)
