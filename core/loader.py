from aiogram import Dispatcher, Bot

from core.config import BOT_TOKEN

dp = Dispatcher()
print(BOT_TOKEN)
bot = Bot(token=BOT_TOKEN)
