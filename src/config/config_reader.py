from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr, BaseModel
from typing import Optional
from datetime import datetime
import os


class Settings(BaseSettings):
    # Желательно вместо str использовать SecretStr
    # для конфиденциальных данных, например, токена бота
    telegram_bot_token: SecretStr
    mongodb_uri: str
    webhook_url: str  # URL-адрес вебхука
    service_url: str  # URL-адрес сервиса, где находится бот

    # Начиная со второй версии pydantic, настройки класса настроек задаются
    # через model_config
    # В данном случае будет использоваться файла .env, который будет прочитан
    # с кодировкой UTF-8
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), ".env")
    )


# При импорте файла сразу создастся
# и провалидируется объект конфига,
# который можно далее импортировать из разных мест
config = Settings()
