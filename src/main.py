import sys, os

from pymongo import MongoClient

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config_reader import config

from fastapi import FastAPI, Request
import aiohttp
import logging

from config.models import Message


TELEGRAM_API_URL = f"https://api.telegram.org/bot{config.telegram_bot_token.get_secret_value()}/sendMessage"

# Настройка логгера
logging.basicConfig(level=logging.INFO)

app = FastAPI()

client = MongoClient(config.mongodb_uri)
db = client["chat_db"]


@app.lifespan("startup")
async def startup_event():
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{config.webhook_url}/platform_registreation/bot", json={'url': config.service_url, 'platform_name': 'telegram', }) as response:
            response = await response.json()
            logging.info(response)
    


@app.post("/webhook")
# получаем сообщение извне
async def send_message_to_chat(message: Message):
    # Реализовать отправку сообщений на TELEGRAM_API_URL
    
    collection = db["users"]
    user = await collection.find_one({"chat_id": message.chat_id})
    
    if user:
        await send_message_to_telegram( user["telegram_user_id"], message.message_text)

        return {"status": "ok"}



async def send_message_to_telegram(chat_id: int, text: str):
    url = TELEGRAM_API_URL
    payload = {
        'chat_id': chat_id,
        'text': text
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            response = await response.json()
            logging.info(response)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)
