# Используем официальный образ Python
FROM python:3.11-slim

# Устанавливаем рабочую директорию в контейнере
WORKDIR /app

# Копируем requirements.txt и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Устанавливаем Supervisor для управления процессами
RUN apt-get update && apt-get install -y supervisor

# Копируем содержимое проекта в рабочую директорию
COPY . .

# Создаем файл .env на основе переменных окружения, переданных через Docker Compose
COPY create_env.sh .
RUN chmod +x create_env.sh && ./create_env.sh

# Копируем конфигурацию Supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Указываем команду запуска Supervisor
CMD ["/usr/bin/supervisord"]
