from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr
from typing import Optional
import os

class Settings(BaseSettings):
    # IP-адрес, на котором будет запущен сервер
    web_server_host: str
    # Порт, на котором будет запущен сервер
    web_server_port: int
    # URL для обработки вебхуков
    server_webhook_url: str
    # Токен Telegram бота, используемый для взаимодействия с API Telegram
    telegram_bot_token: SecretStr
    # URI для подключения к MongoDB
    mongodb_uri: str
    # URL вебхука, куда отправляются запросы
    webhook_url: str
    # Путь для регистрации пользователей через вебхук
    webhook_user_registration_path: str
    # Путь для отправки сообщений через вебхук
    webhook_send_message_path: str
    # Путь для регистрации платформы через вебхук
    webhook_platform_registration_path: str

    @property
    def telegram_api_url(self):
        return f"https://api.telegram.org/bot{self.telegram_bot_token.get_secret_value()}/sendMessage"

    @property
    def user_registration_url(self):
        return f"{self.webhook_url}{self.webhook_user_registration_path}"
    
    @property
    def send_message_url(self):
        return f"{self.webhook_url}{self.webhook_send_message_path}"
    
    @property
    def platform_registration_url(self):
        return f"{self.webhook_url}{self.webhook_platform_registration_path}"

    # Начиная со второй версии pydantic, настройки класса задаются через model_config
    # В данном случае будет использоваться файл .env, который будет прочитан с кодировкой UTF-8
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), ".env")
    )

# При импорте файла сразу создастся и провалидируется объект конфига,
# который можно далее импортировать из разных мест
config = Settings()
