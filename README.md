# Telegram Bot and FastAPI Project

Этот проект представляет собой Telegram-бота и веб-сервер на FastAPI, работающие в Docker-контейнере с использованием Supervisor для управления процессами и MongoDB для хранения данных.

# Инструкции по запуску

## Через докер
1. Склонируйте репозиторий.

2. Настройте параметры в docker-compose.yml, где:

    ```sh
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
    WEBHOOK_USER_REGISTRATION_PATH: /user_registration/bot
    WEBHOOK_SEND_MESSAGE_PATH: /send_a_message_to_chat
    WEBHOOK_PLATFORM_REGISTRATION_PATH: /platform_registration/bot

    # Не забудьте изменить другие параметры (порты).
    ```


3. Соберите и запустите контейнеры с помощью Docker Compose:
    ```sh
    docker-compose up --build
    ```

## Без докера
- Предварительные требования
    ```
    Python 3.11
    MongoDB
    ```
1. Установите mongodb. Рекомендую через docker:
    ```
    docker run -d -p 27017:27017 --name mongodb mongo
    ```
1. Склонируйте репозиторий.
2. Создайте виртуальное окружение и активируйте его.
    ```
    python -m venv venv
    venv\Scripts\activate
    ```
3. Установите зависимости
    ```
    pip install -r requirements.txt
    ```
4. Создайте .env файл в директории src/config со следующим содержимым:
    ```sh
    # IP-адрес, на котором будет запущен сервер
    WEB_SERVER_HOST=127.0.0.1

    # Порт, на котором будет запущен сервер
    WEB_SERVER_PORT=2323

    # URL для обработки вебхуков
    SERVER_WEBHOOK_URL=http://127.0.0.1:2323/webhook

    # Токен Telegram бота, используемый для взаимодействия с API Telegram
    TELEGRAM_BOT_TOKEN=token

    # URI для подключения к MongoDB
    MONGODB_URI=mongodb://localhost:27017/

    # URL вебхука, куда отправляются запросы 
    WEBHOOK_URL=http://message_host/message_service

    # Путь для регистрации пользователей через вебхук
    WEBHOOK_USER_REGISTRATION_PATH=/user_registration/bot

    # Путь для отправки сообщений через вебхук
    WEBHOOK_SEND_MESSAGE_PATH=/send_a_message_to_chat

    # Путь для регистрации платформы через вебхук
    WEBHOOK_PLATFORM_REGISTRATION_PATH=/platform_registration/bot
    ```

5. Откройте два терминала или командных окна. В первом терминале запустите FastAPI приложение:
    ```
    python src/main.py
    ```

    Во втором терминале запустите Telegram бота:
    ```
    python src/telegram_bot.py
    ```

## Описание файлов

- **/src**: Директория с исходным кодом проекта.
  - **/config**: Директория с конфигурационными файлами.
    - **.env**: Файл с переменными окружения.
    - **config_reader.py**: Файл для чтения конфигурационных параметров из `.env`.
    - **models.py**: Файл с моделями данных.
  - **main.py**: Основной скрипт приложения на FastAPI.
  - **telegram_bot.py**: Скрипт Telegram-бота.

# Текущая реализация
![excalidraw picture](./images/excalidraw.png)

