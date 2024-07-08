# Используем официальный образ Python
FROM python:3.11-slim

# Устанавливаем рабочую директорию в контейнере
WORKDIR /app

# Копируем requirements.txt и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем содержимое проекта в рабочую директорию
COPY . .

# Создаем файл .env на основе переменных окружения, переданных через Docker Compose
COPY create_env.sh .
RUN chmod a+x *.sh 
