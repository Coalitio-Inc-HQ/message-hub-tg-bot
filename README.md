# Telegram Bot and FastAPI Project

Этот проект представляет собой Telegram-бота и веб-сервер на FastAPI, работающие в Docker-контейнере с использованием Supervisor для управления процессами и MongoDB для хранения данных.

### Инструкции по запуску

1. Склонируйте репозиторий.

2. Настройте параметры в docker-compose.yml, где:

    ```python
    # Параметры веб-сервера
    WEB_SERVER_HOST: 127.0.0.1
    WEB_SERVER_PORT: 8000
    # URL вебхука сервера
    SERVER_WEBHOOK_URL: http://127.0.0.1:8000/webhook
    # Токен бота
    TELEGRAM_BOT_TOKEN: your-telegram-bot-token
    # URI для MongoDB
    MONGODB_URI: mongodb://root:example@mongo:27017/chat_db?authSource=admin
    # Вебхук сервиса, куда будут отправляться запросы
    WEBHOOK_URL: http://messege-hub.com/message_service
    WEBHOOK_USER_REGISTRATION_PATH: /register
    WEBHOOK_SEND_MESSAGE_PATH: /send_message
    WEBHOOK_PLATFORM_REGISTRATION_PATH: /register_platform
    ```

3. Соберите и запустите контейнеры с помощью Docker Compose:

    ```sh
    docker-compose up --build
    ```

